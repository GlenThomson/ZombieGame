"""Static blocking tiles. Walls are now visibly rendered using one of the
wall_<style>.png tiles selected per-map."""
import os
import pygame

from settings import TILE_SIZE
from game import assets
from game.world.tile import WALL_STYLES


class Wall(pygame.sprite.Sprite):
    def __init__(self, scene, x_tile: int, y_tile: int):
        super().__init__(scene.all_sprites, scene.walls)
        self.scene = scene
        png = WALL_STYLES.get(getattr(scene, "wall_style", "brick"), "wall_brick.png")
        full_path = os.path.join("assets", "images", "tiles", png)
        if os.path.isfile(full_path):
            self.image = assets.image(os.path.join("tiles", png))
        else:
            self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.image.fill((110, 60, 40))
        self.rect = self.image.get_rect(topleft=(x_tile * TILE_SIZE, y_tile * TILE_SIZE))


class BarbWire(pygame.sprite.Sprite):
    def __init__(self, scene, x_tile: int, y_tile: int):
        super().__init__(scene.all_sprites, scene.barb_wire)
        self.scene = scene
        # Visible barb wire — gray with criss-cross pattern.
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.image.fill((40, 40, 45, 180))
        for i in range(0, TILE_SIZE, 6):
            pygame.draw.line(self.image, (200, 200, 200), (i, 0), (i + TILE_SIZE, TILE_SIZE), 1)
            pygame.draw.line(self.image, (200, 200, 200), (i, TILE_SIZE), (i + TILE_SIZE, 0), 1)
        self.rect = self.image.get_rect(topleft=(x_tile * TILE_SIZE, y_tile * TILE_SIZE))


class ZombieSpawn:
    """Pure data — not a Sprite. Marks a tile where zombies may spawn."""
    __slots__ = ("x", "y")

    def __init__(self, x_tile: int, y_tile: int):
        self.x = x_tile * TILE_SIZE
        self.y = y_tile * TILE_SIZE
