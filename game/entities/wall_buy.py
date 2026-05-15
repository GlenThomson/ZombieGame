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


class WallBuy(pygame.sprite.Sprite):
    def __init__(self, scene, x_tile: int, y_tile: int, weapon_name: str):
        super().__init__(scene.all_sprites, scene.wall_buys)
        self.scene = scene
        self.x_tile = x_tile
        self.y_tile = y_tile
        self.weapon_name = weapon_name
        self.buy_cost = WALL_BUY_BUY_COST
        self.ammo_cost = WALL_BUY_AMMO_COST

        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill((40, 40, 50))
        pygame.draw.rect(self.image, GOLD, self.image.get_rect(), 2)
        font = pygame.font.Font(None, 16)
        text = font.render(weapon_name[:6], True, GOLD)
        self.image.blit(text, (4, TILE_SIZE // 2 - 6))
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
            if player.points < self.buy_cost:
                return
            if not player.inventory.add(self.weapon_name):
                player.inventory.replace_equipped(self.weapon_name)
            player.points -= self.buy_cost
        else:
            if player.points < self.ammo_cost:
                return
            for slot in player.inventory.slots:
                if slot is not None and slot.definition.name == self.weapon_name:
                    slot.current_ammo = slot.magazine_size
                    slot.reserve_ammo = slot.reserve_max
                    slot.is_reloading = False
                    break
            player.points -= self.ammo_cost

    def _player_owns_weapon(self, player) -> bool:
        # Compare against the underlying definition name so a Pack-a-Punched
        # version (e.g. "Pistol PaP") still counts as owning "Pistol".
        return any(
            s is not None and s.definition.name == self.weapon_name
            for s in player.inventory.slots
        )
