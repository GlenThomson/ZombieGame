"""Wall buy: a weapon mounted on a wall the player can purchase points-style.

If you don't own the weapon yet → pay BUY_COST to add it to your inventory.
If you already own it → pay AMMO_COST to refill its magazine."""
import pygame

from settings import (
    TILE_SIZE,
    INTERACT_KEY_LABEL,
    WALL_BUY_BUY_COST,
    WALL_BUY_AMMO_COST,
    GOLD,
)


def _fit_label(text: str, color, max_width: int) -> pygame.Surface:
    """Render `text` at the largest font size that still fits within
    max_width. Caps at size 18 so it doesn't get silly on short names."""
    for size in (18, 16, 14, 12, 10):
        font = pygame.font.Font(None, size)
        rendered = font.render(text, True, color)
        if rendered.get_width() <= max_width:
            return rendered
    return rendered  # smallest tried, even if it's still too wide


def build_wall_buy_image(weapon_name: str) -> pygame.Surface:
    """Wall-buy sprite: the gun icon on its tile with a READABLE name
    plaque hanging beneath. The plaque is as wide as the name needs, not
    crammed into 40px. Shared by host (WallBuy entity) and MP client."""
    import os
    from game import assets

    font = pygame.font.Font(None, 20)
    label = font.render(weapon_name, True, GOLD)
    plaque_w = label.get_width() + 12
    plaque_h = label.get_height() + 6
    total_w = max(TILE_SIZE, plaque_w)
    total_h = TILE_SIZE + plaque_h + 2

    surf = pygame.Surface((total_w, total_h), pygame.SRCALPHA)
    icon_x = total_w // 2 - TILE_SIZE // 2
    if os.path.isfile(os.path.join("assets", "images", "wall_buy_generic.png")):
        surf.blit(assets.image("wall_buy_generic.png"), (icon_x, 0))
    else:
        pygame.draw.rect(surf, (40, 40, 50), (icon_x, 0, TILE_SIZE, TILE_SIZE))
        pygame.draw.rect(surf, GOLD, (icon_x, 0, TILE_SIZE, TILE_SIZE), 2)
    plaque = pygame.Rect(total_w // 2 - plaque_w // 2, TILE_SIZE + 2, plaque_w, plaque_h)
    pygame.draw.rect(surf, (12, 12, 16), plaque, border_radius=3)
    pygame.draw.rect(surf, (120, 100, 30), plaque, width=1, border_radius=3)
    surf.blit(label, label.get_rect(center=plaque.center))
    return surf


class WallBuy(pygame.sprite.Sprite):
    def __init__(self, scene, x_tile: int, y_tile: int, weapon_name: str):
        super().__init__(scene.all_sprites, scene.wall_buys)
        self.scene = scene
        self.x_tile = x_tile
        self.y_tile = y_tile
        self.weapon_name = weapon_name
        # Per-weapon pricing (BO1): the gun's wall price, refill = half.
        # Unknown weapon names fall back to the flat legacy costs.
        from game.weapons.definitions import WEAPON_DEFS
        wdef = WEAPON_DEFS.get(weapon_name)
        self.buy_cost = wdef.wall_cost if wdef else WALL_BUY_BUY_COST
        self.ammo_cost = wdef.ammo_cost if wdef else WALL_BUY_AMMO_COST

        self.image = build_wall_buy_image(weapon_name)
        # The icon part of the image aligns with the tile; the name plaque
        # hangs below into the room. Collision is grid-based (WALL_BUY tile)
        # so the oversized rect is visual-only.
        self.rect = self.image.get_rect(
            midtop=(x_tile * TILE_SIZE + TILE_SIZE // 2, y_tile * TILE_SIZE))

    def get_world_pos(self) -> tuple[float, float]:
        return (self.rect.centerx, self.rect.centery)

    def get_prompt(self, player) -> str | None:
        if not self._player_owns_weapon(player):
            cost = self.buy_cost
            prefix = "" if player.points >= cost else "(need points) "
            return f"{prefix}[{INTERACT_KEY_LABEL}] Buy {self.weapon_name}  -  {cost}"
        cost = self.ammo_cost
        prefix = "" if player.points >= cost else "(need points) "
        return f"{prefix}[{INTERACT_KEY_LABEL}] Refill {self.weapon_name}  -  {cost}"

    def interact(self, player) -> None:
        if not self._player_owns_weapon(player):
            if not player.spend(self.buy_cost):
                return
            if not player.inventory.add(self.weapon_name):
                player.inventory.replace_equipped(self.weapon_name)
        else:
            if not player.spend(self.ammo_cost):
                return
            for slot in player.inventory.slots:
                if slot is not None and slot.definition.name == self.weapon_name:
                    slot.current_ammo = slot.magazine_size
                    slot.reserve_ammo = slot.reserve_max
                    slot.is_reloading = False
                    break

    def _player_owns_weapon(self, player) -> bool:
        # Compare against the underlying definition name so a Pack-a-Punched
        # version (e.g. "Pistol PaP") still counts as owning "Pistol".
        return any(
            s is not None and s.definition.name == self.weapon_name
            for s in player.inventory.slots
        )
