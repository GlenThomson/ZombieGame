"""Door tile entity. Costs points to open; once open, the grid tile becomes
EMPTY so pathfinding and movement let everyone through."""
import pygame

from settings import TILE_SIZE, INTERACT_KEY_LABEL, GOLD
from game.world.tile import TileType


class Door(pygame.sprite.Sprite):
    def __init__(self, scene, x_tile: int, y_tile: int, cost: int):
        # Doors are in the wall sprite group while closed so collision works.
        super().__init__(scene.all_sprites, scene.walls, scene.doors)
        self.scene = scene
        self.x_tile = x_tile
        self.y_tile = y_tile
        self.cost = cost
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill((110, 60, 20))  # brown door
        # Subtle plank lines for visual interest
        for y in range(0, TILE_SIZE, 8):
            pygame.draw.line(self.image, (70, 35, 10), (0, y), (TILE_SIZE, y), 1)
        pygame.draw.rect(self.image, GOLD, self.image.get_rect(), 2)
        self.rect = self.image.get_rect(topleft=(x_tile * TILE_SIZE, y_tile * TILE_SIZE))

    # --- Interactable protocol ---

    def get_world_pos(self) -> tuple[float, float]:
        return (self.rect.centerx, self.rect.centery)

    def get_prompt(self, player) -> str | None:
        affordable = player.points >= self.cost
        prefix = "" if affordable else "(need points) "
        return f"{prefix}[{INTERACT_KEY_LABEL}] Open Door  -  {self.cost}"

    def interact(self, player) -> None:
        if player.points < self.cost:
            return
        player.points -= self.cost
        self.scene.grid[self.y_tile][self.x_tile] = TileType.DOOR_OPEN
        self.scene.interactables.discard(self)
        self.kill()
