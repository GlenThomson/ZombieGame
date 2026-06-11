"""Thrown grenade: cursor-aimed arc throw, wall bounces, radial damage.

Throw model (shared with MonkeyBomb): the projectile flies toward the
aimed point (clamped to max range) over a fixed flight time, decelerating
as it goes, while the sprite scales up then down to fake a height arc.
After landing it sits until the fuse pops.
"""
import math
import pygame

from settings import (
    GRENADE_SPEED,
    GRENADE_DURATION,
    GRENADE_EXPLOSION_RADIUS_TILES,
    GRENADE_DAMAGE,
)
from game import assets

vector = pygame.math.Vector2

GRENADE_MAX_RANGE = 340       # px — how far you can lob one
GRENADE_MIN_RANGE = 50
FLIGHT_FRAMES_BASE = 16       # short toss
FLIGHT_FRAMES_PER_PX = 0.055  # extra flight time with distance


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


def explosion_frames() -> list:
    global _explosion_frames_cache
    if not _explosion_frames_cache:
        _explosion_frames_cache = _load_explosion_frames()
    return _explosion_frames_cache


class ThrowArc:
    """Cursor-aimed lob: position + fake-height scale over a fixed flight.
    Used by Grenade and MonkeyBomb so both throw identically."""

    def __init__(self, start: vector, target: tuple | None, angle_deg: float,
                 max_range: float = GRENADE_MAX_RANGE):
        if target is not None:
            to = vector(target[0], target[1]) - start
            dist = to.length()
            if dist < 1:
                to, dist = vector(1, 0), 1.0
        else:
            # Legacy fallback: lob in the facing direction at 60% range.
            to = vector(1, 0).rotate(-angle_deg)
            dist = max_range * 0.6
        dist = max(GRENADE_MIN_RANGE, min(max_range, dist))
        self.direction = to.normalize()
        self.total_frames = max(8, int(FLIGHT_FRAMES_BASE + dist * FLIGHT_FRAMES_PER_PX))
        self.frame = 0
        # Linear deceleration that integrates to `dist` over total_frames.
        self.speed0 = 2.0 * dist / self.total_frames

    @property
    def landed(self) -> bool:
        return self.frame >= self.total_frames

    def step_velocity(self) -> vector:
        """Velocity for this frame; call once per frame while airborne."""
        if self.landed:
            return vector(0, 0)
        t = self.frame / self.total_frames
        speed = self.speed0 * (1.0 - t)
        self.frame += 1
        return self.direction * speed

    def height_scale(self) -> float:
        """1.0 on the ground, up to ~1.8 at the top of the arc."""
        if self.landed:
            return 1.0
        t = self.frame / self.total_frames
        return 1.0 + 0.8 * math.sin(math.pi * t)

    def bounce(self, normal_x: bool, normal_y: bool):
        """Reflect the remaining flight off a wall."""
        if normal_x:
            self.direction.x *= -1
        if normal_y:
            self.direction.y *= -1


class Grenade(pygame.sprite.Sprite):
    BASE_SIZE = 20

    def __init__(self, scene, x: float, y: float, angle_deg: float,
                 target: tuple | None = None):
        super().__init__(scene.all_sprites, scene.grenades)
        self.scene = scene
        self.base_image = assets.image("grenade.png", scale=(self.BASE_SIZE, self.BASE_SIZE))
        self.image = self.base_image
        self.rect = self.image.get_rect()
        self.pos = vector(x, y)
        self.rect.center = self.pos
        self.arc = ThrowArc(self.pos, target, angle_deg)
        self.vel = vector(0, 0)   # kept for compat (monkey-bomb tests etc.)

        self.spawn_time = pygame.time.get_ticks()
        self.bounce_cooldown = 0
        self.bounce_sound = assets.sound("Grenade Bounce.mp3")
        self.explosion_sound = assets.sound("grenade_explosion.mp3")
        self.explosion_frames = explosion_frames()

        self.exploding = False
        self.frame_index = 0
        self.last_frame_update = pygame.time.get_ticks()
        self.frame_rate_ms = 50

    @property
    def height_scale(self) -> float:
        return self.arc.height_scale()

    def update(self):
        if self.exploding:
            self._advance_explosion_animation()
            return

        if not self.arc.landed:
            step = self.arc.step_velocity()
            self.pos += step
            self._check_wall_collision()
            # Fake height: scale the sprite along the arc.
            s = self.arc.height_scale()
            size = max(8, int(self.BASE_SIZE * s))
            self.image = pygame.transform.scale(self.base_image, (size, size))
            self.rect = self.image.get_rect(center=self.pos)
            if self.arc.landed:
                self.bounce_sound.play()
                self.image = self.base_image
                self.rect = self.image.get_rect(center=self.pos)
        if pygame.time.get_ticks() - self.spawn_time > GRENADE_DURATION:
            self._explode()

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
        if self.bounce_cooldown > 0:
            self.bounce_cooldown -= 1
            return
        for wall in self.scene.walls:
            if not self.rect.colliderect(wall.rect):
                continue
            # Pick the bounce axis from which side penetrates least.
            dx = min(abs(self.rect.right - wall.rect.left),
                     abs(wall.rect.right - self.rect.left))
            dy = min(abs(self.rect.bottom - wall.rect.top),
                     abs(wall.rect.bottom - self.rect.top))
            self.arc.bounce(normal_x=dx <= dy, normal_y=dy <= dx)
            # Step out of the wall so we don't re-collide every frame.
            self.pos += self.arc.direction * 6
            self.bounce_cooldown = 4
            self.bounce_sound.play()
            break

    def _explode(self):
        radius = GRENADE_EXPLOSION_RADIUS_TILES * self.BASE_SIZE
        explosion_rect = pygame.Rect(0, 0, radius, radius)
        explosion_rect.center = self.rect.center
        self.explosion_sound.play()
        self.exploding = True
        # BO1 blast model: full damage at the centre falling off toward the
        # edge. Zombies that SURVIVE the blast lose their legs and crawl —
        # this is how you make an end-of-round crawler on purpose.
        cx, cy = self.rect.center
        half = radius / 2
        killed = 0
        for zombie in list(self.scene.zombies):
            if not explosion_rect.colliderect(zombie.rect):
                continue
            dist = ((zombie.pos.x - cx) ** 2 + (zombie.pos.y - cy) ** 2) ** 0.5
            falloff = max(0.15, 1.0 - dist / max(1.0, half * 1.4))
            was_alive = zombie.health > 0
            zombie.take_damage(GRENADE_DAMAGE * falloff)
            if was_alive and zombie.health <= 0:
                killed += 1
            elif zombie.alive() and zombie.health > 0:
                zombie.make_crawler()
        award_explosive_kills(self.scene, getattr(self, "thrower_id", None),
                              killed, self.rect.center)


def award_explosive_kills(scene, thrower_id, killed: int, pos):
    """Grenade / monkey-bomb kills pay out like bullet kills (BO1)."""
    if not killed or thrower_id is None:
        return
    from settings import POINTS_PER_KILL
    from game.entities.effects import FloatingText
    thrower = next((p for p in scene.players if p.player_id == thrower_id), None)
    if thrower is None:
        return
    pts = int(POINTS_PER_KILL * scene.points_multiplier) * killed
    thrower.points += pts
    thrower.kills += killed
    FloatingText(scene, vector(pos[0], pos[1]), f"+{pts}", color=(255, 215, 0))
