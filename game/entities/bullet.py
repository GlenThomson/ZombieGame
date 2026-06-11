"""Player projectile. Carries shooter_id so PlayState can credit points to
the right player on hit/kill, and damage/penetration so collisions don't
have to look up the equipped weapon (which may have changed since the shot)."""
import math
import random
import pygame

from settings import BARREL_OFFSET, GOLD

vector = pygame.math.Vector2

# How many times a laser bullet ricochets before fizzling out. PaP doubles it.
LASER_MAX_BOUNCES = 3
LASER_PAP_MAX_BOUNCES = 6
LASER_COLOR = (120, 255, 160)        # bright green
LASER_PAP_COLOR = (255, 100, 255)    # vivid magenta when Pack-a-Punched
LASER_CORE = (255, 255, 255)

# Thundergun shockwave: each pellet is an expanding translucent air-ripple
# ring with a short lifetime (the gun is a close-range wall of force).
BLAST_MAX_AGE_FRAMES = 16
BLAST_START_RADIUS = 6
BLAST_GROWTH_PER_FRAME = 1.9


def _blast_ring(radius: int, age_frac: float) -> pygame.Surface:
    """Translucent expanding air-ring, fading as it travels."""
    d = radius * 2
    surf = pygame.Surface((d, d), pygame.SRCALPHA)
    fade = max(0.0, 1.0 - age_frac)
    pygame.draw.circle(surf, (200, 220, 255, int(150 * fade)),
                       (radius, radius), radius, max(2, radius // 4))
    pygame.draw.circle(surf, (255, 255, 255, int(90 * fade)),
                       (radius, radius), max(1, int(radius * 0.65)),
                       max(1, radius // 6))
    pygame.draw.circle(surf, (160, 190, 255, int(36 * fade)),
                       (radius, radius), radius)
    return surf

# Standard bullet colour by effect_kind, for both base + PaP variants.
# PaP keeps the same hue family but more saturated / brighter so you can
# read at a glance whether a flying round is upgraded.
_BULLET_COLORS: dict[str, tuple] = {
    "normal":     (GOLD,             (255, 80, 255)),     # gold -> magenta
    "chain":      ((140, 200, 255),  (200, 240, 255)),    # softer/brighter blue
    "blast":      ((255, 140, 0),    (255, 240, 80)),     # orange -> yellow
}


class Bullet(pygame.sprite.Sprite):
    def __init__(self, scene, x: float, y: float, direction, angle_deg: float,
                 spread: float, speed: float, *,
                 shooter_id: int = 0, damage: int = 1, penetration: int = 1,
                 effect_kind: str = "normal", is_packed: bool = False):
        super().__init__(scene.all_sprites, scene.bullets)
        self.scene = scene
        self.is_packed = is_packed
        # Lasers get a longer, brighter sprite; blast (Thundergun) pellets
        # are expanding shockwave rings; other bullets stay 3x3 (4x4 PaP'd).
        if effect_kind == "laser":
            color = LASER_PAP_COLOR if is_packed else LASER_COLOR
            self.image = pygame.Surface((16 if is_packed else 14, 5 if is_packed else 4), pygame.SRCALPHA)
            pygame.draw.rect(self.image, color, self.image.get_rect(), border_radius=2)
            pygame.draw.line(self.image, LASER_CORE, (1, self.image.get_height() // 2),
                             (self.image.get_width() - 2, self.image.get_height() // 2), 1)
        elif effect_kind == "blast":
            self.blast_age = 0
            self.blast_radius = BLAST_START_RADIUS
            self.image = _blast_ring(self.blast_radius, 0.0)
        else:
            size = 4 if is_packed else 3
            self.image = pygame.Surface((size, size))
            base, packed = _BULLET_COLORS.get(effect_kind, _BULLET_COLORS["normal"])
            self.image.fill(packed if is_packed else base)
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
        self.effect_kind = effect_kind
        self.bounces_remaining = (
            (LASER_PAP_MAX_BOUNCES if is_packed else LASER_MAX_BOUNCES)
            if effect_kind == "laser" else 0
        )
        # For lasers, we rotate the sprite so the beam points along its velocity.
        if effect_kind == "laser":
            self._render_rotated()

    @property
    def angle_deg(self) -> float:
        return -math.degrees(math.atan2(self.vel.y, self.vel.x))

    def _render_rotated(self):
        color = LASER_PAP_COLOR if self.is_packed else LASER_COLOR
        w = 16 if self.is_packed else 14
        h = 5 if self.is_packed else 4
        base = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(base, color, base.get_rect(), border_radius=2)
        pygame.draw.line(base, LASER_CORE, (1, h // 2), (w - 2, h // 2), 1)
        self.image = pygame.transform.rotate(base, self.angle_deg)
        self.rect = self.image.get_rect(center=self.hit_box.center)

    def update(self):
        prev_pos = vector(self.pos)
        self.pos += self.vel

        # Thundergun shockwave: grow + fade, die at max range.
        if self.effect_kind == "blast":
            self.blast_age += 1
            if self.blast_age > BLAST_MAX_AGE_FRAMES:
                self.kill()
                return
            self.blast_radius = int(BLAST_START_RADIUS
                                    + self.blast_age * BLAST_GROWTH_PER_FRAME)
            self.image = _blast_ring(self.blast_radius,
                                     self.blast_age / BLAST_MAX_AGE_FRAMES)
            self.rect = self.image.get_rect(center=self.pos)
            # The wavefront's hitbox grows with the ring so the cone
            # actually connects like a wall of force.
            self.hit_box.size = (self.blast_radius * 2, self.blast_radius * 2)

        self.hit_box.center = self.pos
        self.rect.center = self.hit_box.center

        wall = pygame.sprite.spritecollideany(self, self.scene.walls)
        if wall is not None:
            if self.effect_kind == "laser" and self.bounces_remaining > 0:
                self._bounce_off(wall, prev_pos)
                self.bounces_remaining -= 1
                self._render_rotated()
            else:
                self.kill()

    def _bounce_off(self, wall, prev_pos):
        """Reflect velocity off the wall side that was crossed this frame.
        Uses the previous position to decide whether we entered horizontally
        or vertically (mirrors the grenade-bounce logic)."""
        # Step the bullet back to its pre-collision position so it doesn't
        # stay overlapping the wall after the bounce.
        self.pos = prev_pos
        self.hit_box.center = self.pos
        crossed_x = (
            (prev_pos.x < wall.rect.left and self.pos.x + self.vel.x >= wall.rect.left)
            or (prev_pos.x > wall.rect.right and self.pos.x + self.vel.x <= wall.rect.right)
        )
        crossed_y = (
            (prev_pos.y < wall.rect.top and self.pos.y + self.vel.y >= wall.rect.top)
            or (prev_pos.y > wall.rect.bottom and self.pos.y + self.vel.y <= wall.rect.bottom)
        )
        if crossed_x and not crossed_y:
            self.vel.x *= -1
        elif crossed_y and not crossed_x:
            self.vel.y *= -1
        else:
            # Corner / ambiguous — pick the axis with smaller penetration.
            dx = min(abs(self.pos.x - wall.rect.left), abs(self.pos.x - wall.rect.right))
            dy = min(abs(self.pos.y - wall.rect.top), abs(self.pos.y - wall.rect.bottom))
            if dx < dy:
                self.vel.x *= -1
            else:
                self.vel.y *= -1
        # Step forward so the bullet is clear of the wall after reflecting.
        self.pos += self.vel
        self.hit_box.center = self.pos
        self.rect.center = self.hit_box.center
