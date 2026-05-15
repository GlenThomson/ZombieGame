"""Player projectile. Carries shooter_id so PlayState can credit points to
the right player on hit/kill, and damage/penetration so collisions don't
have to look up the equipped weapon (which may have changed since the shot)."""
import math
import random
import pygame

from settings import BARREL_OFFSET, GOLD

vector = pygame.math.Vector2


class Bullet(pygame.sprite.Sprite):
    def __init__(self, scene, x: float, y: float, direction, angle_deg: float,
                 spread: float, speed: float, *,
                 shooter_id: int = 0, damage: int = 1, penetration: int = 1):
        super().__init__(scene.all_sprites, scene.bullets)
        self.scene = scene
        self.image = pygame.Surface((3, 3))
        self.image.fill(GOLD)
        self.rect = self.image.get_rect()

        self.angle_rad = math.radians(angle_deg)
        applied_spread = random.uniform(-spread, spread)
        self.vel = vector(direction.x * speed, direction.y * speed).rotate(applied_spread)
        self.pos = vector(x, y) + BARREL_OFFSET.rotate(-angle_deg)
        self.hit_box = pygame.Rect(0, 0, self.rect.width, self.rect.height)
        self.hit_box.center = self.rect.center
        self.hit_count = 0
        self.shooter_id = shooter_id
        self.damage = damage
        self.penetration = penetration

    def update(self):
        self.pos += self.vel
        self.hit_box.center = self.pos
        self.rect.center = self.hit_box.center
        if pygame.sprite.spritecollideany(self, self.scene.walls):
            self.kill()
