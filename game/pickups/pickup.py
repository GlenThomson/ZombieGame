"""On-ground pickup that flickers, expires, and applies a registered effect
when the player walks over it."""
import random
import pygame

from settings import TILE_SIZE, PICKUP_DURATION_MS
from game import assets
from game.pickups import effects


class Pickup(pygame.sprite.Sprite):
    def __init__(self, scene, x: float, y: float, kind: str | None = None):
        super().__init__(scene.all_sprites, scene.pickups)
        self.scene = scene
        if kind is None:
            names, weights = effects.weighted_names()
            kind = random.choices(names, weights=weights, k=1)[0]
        self.kind = kind
        self.image = assets.image(f"{self.kind}.png", scale=(TILE_SIZE, TILE_SIZE)).copy()
        self.rect = self.image.get_rect(topleft=(x, y))

        self.spawn_time = pygame.time.get_ticks()
        self.flicker_period_ms = 1000
        self.next_flicker_at = self.spawn_time + self.flicker_period_ms
        self.visible = True

    def update(self):
        now = pygame.time.get_ticks()
        elapsed = now - self.spawn_time
        if elapsed > PICKUP_DURATION_MS:
            self.kill()
            return

        # Speed up flicker as expiry approaches.
        time_left = PICKUP_DURATION_MS - elapsed
        if time_left < PICKUP_DURATION_MS / 2:
            self.flicker_period_ms = max(80, self.flicker_period_ms - 3)

        if now >= self.next_flicker_at:
            self.visible = not self.visible
            self.image.set_alpha(255 if self.visible else 0)
            self.next_flicker_at = now + self.flicker_period_ms

        if pygame.sprite.collide_rect(self, self.scene.player):
            effects.apply(self.kind, self.scene)
            self.kill()
