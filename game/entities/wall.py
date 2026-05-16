"""Static blocking tiles. Walls are now visibly rendered using one of the
wall_<style>.png tiles selected per-map."""
import os
import pygame

from settings import TILE_SIZE
from game import assets
from game.world.tile import WALL_STYLES


class Wall(pygame.sprite.Sprite):
    def __init__(self, scene, x_tile: int, y_tile: int):
        # plain_walls is a perf-only group: lets the draw loop blit walls
        # without testing membership in 8 other groups.
        groups = [scene.all_sprites, scene.walls]
        if hasattr(scene, "plain_walls"):
            groups.append(scene.plain_walls)
        super().__init__(*groups)
        self.scene = scene
        png = WALL_STYLES.get(getattr(scene, "wall_style", "brick"), "wall_brick.png")
        full_path = os.path.join("assets", "images", "tiles", png)
        if os.path.isfile(full_path):
            self.image = assets.image(os.path.join("tiles", png))
        else:
            self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.image.fill((110, 60, 40))
        self.rect = self.image.get_rect(topleft=(x_tile * TILE_SIZE, y_tile * TILE_SIZE))


class InvisibleWall(pygame.sprite.Sprite):
    """Blocking tile with no visible sprite. For layering over background
    art / decor that should appear solid. Lives in scene.walls so movement
    + bullets respect it; deliberately NOT in plain_walls so the draw loop
    skips it."""
    def __init__(self, scene, x_tile: int, y_tile: int):
        super().__init__(scene.all_sprites, scene.walls)
        self.scene = scene
        # Fully transparent 1x1 surface — never visible. We can't omit
        # `image` because some pygame internals expect it, but a SRCALPHA
        # surface with no fill blits nothing.
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(x_tile * TILE_SIZE, y_tile * TILE_SIZE))


class BarbWire(pygame.sprite.Sprite):
    def __init__(self, scene, x_tile: int, y_tile: int):
        super().__init__(scene.all_sprites, scene.barb_wire)
        self.scene = scene
        # Plain transparent surface (kept so legacy code paths still work).
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        self.rect = self.image.get_rect(topleft=(x_tile * TILE_SIZE, y_tile * TILE_SIZE))


class ZombieSpawn:
    """Pure data — not a Sprite. Marks a tile where zombies may spawn."""
    __slots__ = ("x", "y")

    def __init__(self, x_tile: int, y_tile: int):
        self.x = x_tile * TILE_SIZE
        self.y = y_tile * TILE_SIZE
