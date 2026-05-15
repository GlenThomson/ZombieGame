"""Thrown grenade with bounce + radial damage explosion."""
import pygame

from settings import (
    GRENADE_SPEED,
    GRENADE_DURATION,
    GRENADE_EXPLOSION_RADIUS_TILES,
    GRENADE_DAMAGE,
)
from game import assets

vector = pygame.math.Vector2


def _load_explosion_frames():
    sheet = assets.image("grenade_explosion.png")
    frames = []
    for row in range(4):
        for col in range(4):
            frame = sheet.subsurface((col * 64, row * 64, 64, 64))
            frame = pygame.transform.scale(frame, (100, 100))
            frames.append(frame)
    return frames


_explosion_frames_cache: list = []


class Grenade(pygame.sprite.Sprite):
    def __init__(self, scene, x: float, y: float, angle_deg: float):
        super().__init__(scene.all_sprites, scene.grenades)
        self.scene = scene
        self.image = assets.image("grenade.png", scale=(20, 20))
        self.rect = self.image.get_rect()
        self.pos = vector(x, y)
        self.rect.center = self.pos
        self.vel = vector(GRENADE_SPEED, 0).rotate(-angle_deg)

        self.spawn_time = pygame.time.get_ticks()
        self.bounce_delay = 0
        self.damping = 0.6
        self.time_between_bounce = 30
        self.time_until_bounce = self.time_between_bounce

        self.bounce_sound = assets.sound("Grenade Bounce.mp3")
        self.explosion_sound = assets.sound("grenade_explosion.mp3")

        global _explosion_frames_cache
        if not _explosion_frames_cache:
            _explosion_frames_cache = _load_explosion_frames()
        self.explosion_frames = _explosion_frames_cache

        self.exploding = False
        self.frame_index = 0
        self.last_frame_update = pygame.time.get_ticks()
        self.frame_rate_ms = 50

    def update(self):
        if self.exploding:
            self._advance_explosion_animation()
            return

        self.bounce_delay -= 1
        self.pos += self.vel
        self.rect.center = self.pos

        if self.vel.length() < 1:
            self.vel = vector(0, 0)
        else:
            self._check_wall_collision()
            self.time_until_bounce -= 1

        if pygame.time.get_ticks() - self.spawn_time > GRENADE_DURATION:
            self._explode()
            return

        if self.vel != vector(0, 0) and self.time_until_bounce <= 0:
            self.bounce_sound.play()
            self.time_between_bounce *= 0.6
            self.time_until_bounce = self.time_between_bounce
            self.vel *= self.damping

    def _advance_explosion_animation(self):
        now = pygame.time.get_ticks()
        if now - self.last_frame_update <= self.frame_rate_ms:
            return
        self.last_frame_update = now
        self.frame_index += 1
        if self.frame_index >= len(self.explosion_frames):
            self.kill()
            return
        center = self.rect.center
        self.image = self.explosion_frames[self.frame_index]
        self.rect = self.image.get_rect(center=center)

    def _check_wall_collision(self):
        for wall in self.scene.walls:
            if self.rect.colliderect(wall.rect):
                self._bounce(wall)

    def _bounce(self, wall):
        self.bounce_sound.play()
        if self.bounce_delay > 0:
            return
        self.bounce_delay = 2
        if abs(self.rect.left - wall.rect.right) < 20 or abs(self.rect.right - wall.rect.left) < 20:
            self.vel.x *= -1
        if abs(self.rect.top - wall.rect.bottom) < 20 or abs(self.rect.bottom - wall.rect.top) < 20:
            self.vel.y *= -1
        self.vel *= self.damping

    def _explode(self):
        radius = GRENADE_EXPLOSION_RADIUS_TILES * self.rect.width
        explosion_rect = pygame.Rect(0, 0, radius, radius)
        explosion_rect.center = self.rect.center
        self.explosion_sound.play()
        self.exploding = True
        for zombie in self.scene.zombies:
            if explosion_rect.colliderect(zombie.rect):
                zombie.health -= GRENADE_DAMAGE
