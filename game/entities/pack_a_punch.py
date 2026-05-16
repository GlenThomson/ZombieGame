"""Pack-a-Punch machine. Pay points → upgrade currently-equipped weapon."""
import pygame

from settings import (
    TILE_SIZE,
    INTERACT_KEY_LABEL,
    PACK_A_PUNCH_COST,
)


class PackAPunch(pygame.sprite.Sprite):
    def __init__(self, scene, x_tile: int, y_tile: int):
        super().__init__(scene.all_sprites, scene.walls, scene.pack_a_punch_machines)
        self.scene = scene
        self.x_tile = x_tile
        self.y_tile = y_tile
        self.cost = PACK_A_PUNCH_COST
        self.rect = pygame.Rect(
            x_tile * TILE_SIZE, y_tile * TILE_SIZE, TILE_SIZE, TILE_SIZE
        )
        self._render()

    def _render(self):
        import os
        from game import assets
        png = "pack_a_punch.png"
        if os.path.isfile(os.path.join("assets", "images", png)):
            self.image = assets.image(png).copy()
        else:
            self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(self.image, (200, 160, 0), self.image.get_rect())
            pygame.draw.rect(self.image, (255, 230, 80), self.image.get_rect(), 3)

    def get_world_pos(self) -> tuple[float, float]:
        return (self.rect.centerx, self.rect.centery)

    def get_prompt(self, player) -> str | None:
        weapon = player.weapon
        if weapon is None:
            return None
        if not getattr(self.scene, "power_on", True):
            return "Pack-a-Punch (power off)"
        if weapon.is_packed:
            return f"{weapon.name} already packed"
        affordable = player.points >= self.cost
        prefix = "" if affordable else "(need points) "
        return f"{prefix}[{INTERACT_KEY_LABEL}] Pack-a-Punch  -  {self.cost}"

    def interact(self, player) -> None:
        if not getattr(self.scene, "power_on", True):
            return
        weapon = player.weapon
        if weapon is None or weapon.is_packed:
            return
        if not player.spend(self.cost):
            return
        weapon.apply_pack_a_punch()
