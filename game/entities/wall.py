"""Static blocking tiles."""
import pygame
from settings import TILE_SIZE


class Wall(pygame.sprite.Sprite):
    def __init__(self, scene, x_tile: int, y_tile: int):
        super().__init__(scene.all_sprites, scene.walls)
        self.scene = scene
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.rect = self.image.get_rect(topleft=(x_tile * TILE_SIZE, y_tile * TILE_SIZE))


class BarbWire(pygame.sprite.Sprite):
    def __init__(self, scene, x_tile: int, y_tile: int):
        super().__init__(scene.all_sprites, scene.barb_wire)
        self.scene = scene
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.rect = self.image.get_rect(topleft=(x_tile * TILE_SIZE, y_tile * TILE_SIZE))


class ZombieSpawn:
    """Pure data — not a Sprite. Marks a tile where zombies may spawn."""
    __slots__ = ("x", "y")

    def __init__(self, x_tile: int, y_tile: int):
        self.x = x_tile * TILE_SIZE
        self.y = y_tile * TILE_SIZE
