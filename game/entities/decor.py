"""Furniture / prop sprite. Visual only by default; if its kind is in
DECOR_BLOCKING, it joins scene.walls so movement collides with it."""
import os
import pygame

from settings import TILE_SIZE
from game import assets
from game.world.tile import DECOR_SPRITES, DECOR_BLOCKING


class Decor(pygame.sprite.Sprite):
    def __init__(self, scene, x_tile: int, y_tile: int, kind: str):
        groups = [scene.all_sprites, scene.decor]
        if DECOR_BLOCKING.get(kind, False):
            groups.append(scene.walls)
        super().__init__(*groups)
        self.scene = scene
        self.kind = kind
        self.x_tile = x_tile
        self.y_tile = y_tile
        png = DECOR_SPRITES.get(kind)
        if png is None:
            self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(self.image, (200, 0, 200), self.image.get_rect())
        else:
            full = os.path.join("assets", "images", "decor", png)
            if os.path.isfile(full):
                self.image = assets.image(os.path.join("decor", png))
            else:
                self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
                pygame.draw.rect(self.image, (200, 0, 200), self.image.get_rect())
        # Anchor: the sprite's bottom-left aligns with the tile's bottom-left,
        # so a tall item like a bed extends UP from its anchor. This mirrors
        # how Tiled places oversize tiles.
        self.rect = self.image.get_rect(
            bottomleft=(x_tile * TILE_SIZE, (y_tile + 1) * TILE_SIZE),
        )
        # Hit box: only the bottom 1-tile-tall portion blocks (so tall
        # furniture like a bed doesn't block tiles ABOVE its anchor).
        self.hit_box = pygame.Rect(
            x_tile * TILE_SIZE, y_tile * TILE_SIZE, TILE_SIZE, TILE_SIZE,
        )
