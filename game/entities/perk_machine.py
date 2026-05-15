"""A perk-cola machine. Stand near, press F, pay points → perk."""
import pygame

from settings import TILE_SIZE, INTERACT_KEY_LABEL
from game.stats.perks import PERKS


class PerkMachine(pygame.sprite.Sprite):
    def __init__(self, scene, x_tile: int, y_tile: int, perk_name: str):
        super().__init__(scene.all_sprites, scene.walls, scene.perk_machines)
        self.scene = scene
        self.x_tile = x_tile
        self.y_tile = y_tile
        self.perk = PERKS.get(perk_name) or next(iter(PERKS.values()))
        self.rect = pygame.Rect(
            x_tile * TILE_SIZE, y_tile * TILE_SIZE, TILE_SIZE, TILE_SIZE
        )
        self._render()

    def _render(self):
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        # Machine body
        pygame.draw.rect(self.image, (20, 20, 28), self.image.get_rect())
        # Perk-tinted strip down the middle (vending machine front)
        strip = pygame.Rect(8, 6, TILE_SIZE - 16, TILE_SIZE - 12)
        pygame.draw.rect(self.image, self.perk.icon_color, strip)
        pygame.draw.rect(self.image, (220, 220, 220), self.image.get_rect(), 2)
        # First letter as a label
        font = pygame.font.Font(None, 28)
        ch = self.perk.name[0]
        text = font.render(ch, True, (0, 0, 0))
        self.image.blit(text, text.get_rect(center=(TILE_SIZE // 2, TILE_SIZE // 2)))

    # --- Interactable ---

    def get_world_pos(self) -> tuple[float, float]:
        return (self.rect.centerx, self.rect.centery)

    def get_prompt(self, player) -> str | None:
        ps = self.scene.perk_system_by_player.get(player.player_id)
        if ps is None:
            return None
        if ps.has(self.perk.name):
            return f"{self.perk.name} (owned)"
        affordable = player.points >= self.perk.cost
        prefix = "" if affordable else "(need points) "
        return f"{prefix}[{INTERACT_KEY_LABEL}] {self.perk.name}  -  {self.perk.cost}"

    def interact(self, player) -> None:
        ps = self.scene.perk_system_by_player.get(player.player_id)
        if ps is None:
            return
        ps.buy(self.perk.name)
