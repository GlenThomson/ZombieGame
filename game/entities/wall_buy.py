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

        import os
        from game import assets
        if os.path.isfile(os.path.join("assets", "images", "wall_buy_generic.png")):
            self.image = assets.image("wall_buy_generic.png").copy()
            label = _fit_label(weapon_name, GOLD, TILE_SIZE - 4)
            self.image.blit(label, label.get_rect(midbottom=(TILE_SIZE // 2, TILE_SIZE - 1)))
        else:
            self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.image.fill((40, 40, 50))
            pygame.draw.rect(self.image, GOLD, self.image.get_rect(), 2)
            label = _fit_label(weapon_name, GOLD, TILE_SIZE - 4)
            self.image.blit(label, label.get_rect(center=(TILE_SIZE // 2, TILE_SIZE // 2)))
        self.rect = self.image.get_rect(topleft=(x_tile * TILE_SIZE, y_tile * TILE_SIZE))

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
