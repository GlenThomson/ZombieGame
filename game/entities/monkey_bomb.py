"""Monkey Bomb. Lands at a position, plays a music loop, attracts every
zombie in the scene to it, then explodes and kills everything within radius.

Each MonkeyBomb registers itself in scene.zombie_attractors so the Zombie
AI prefers it over the nearest player while it's active."""
import pygame

from settings import (
    TILE_SIZE,
    MONKEY_BOMB_DURATION_MS,
    MONKEY_BOMB_RADIUS_PX,
    MONKEY_BOMB_DAMAGE,
)
from game import assets

vector = pygame.math.Vector2


class MonkeyBomb(pygame.sprite.Sprite):
    def __init__(self, scene, x: float, y: float, thrower_id: int = 0):
        super().__init__(scene.all_sprites, scene.monkey_bombs)
        self.scene = scene
        self.thrower_id = thrower_id
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        # Pink-ish monkey body
        pygame.draw.circle(self.image, (220, 100, 160), (12, 12), 12)
        pygame.draw.circle(self.image, (60, 30, 50), (12, 12), 12, 2)
        pygame.draw.circle(self.image, (255, 255, 255), (8, 10), 2)
        pygame.draw.circle(self.image, (255, 255, 255), (16, 10), 2)
        self.pos = vector(x, y)
        self.rect = self.image.get_rect(center=self.pos)
        self.spawn_time = pygame.time.get_ticks()
        self.exploded = False
        scene.zombie_attractors.append(self)

    def update(self):
        if self.exploded:
            return
        if pygame.time.get_ticks() - self.spawn_time > MONKEY_BOMB_DURATION_MS:
            self._explode()

    def _explode(self):
        self.exploded = True
        if self in self.scene.zombie_attractors:
            self.scene.zombie_attractors.remove(self)
        self.scene.announce_event("monkey_explode", {"sound": "kaboom.mp3"})
        # Kill anything in radius.
        for zombie in self.scene.zombies:
            d2 = (zombie.pos.x - self.pos.x) ** 2 + (zombie.pos.y - self.pos.y) ** 2
            if d2 <= MONKEY_BOMB_RADIUS_PX ** 2:
                zombie.take_damage(MONKEY_BOMB_DAMAGE)
        self.kill()
