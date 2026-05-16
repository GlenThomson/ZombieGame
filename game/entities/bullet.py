"""Player projectile. Carries shooter_id so PlayState can credit points to
the right player on hit/kill, and damage/penetration so collisions don't
have to look up the equipped weapon (which may have changed since the shot)."""
import math
import random
import pygame

from settings import BARREL_OFFSET, GOLD

vector = pygame.math.Vector2

# How many times a laser bullet ricochets before fizzling out.
LASER_MAX_BOUNCES = 3
LASER_COLOR = (120, 255, 160)  # bright green
LASER_CORE = (255, 255, 255)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, scene, x: float, y: float, direction, angle_deg: float,
                 spread: float, speed: float, *,
                 shooter_id: int = 0, damage: int = 1, penetration: int = 1,
                 effect_kind: str = "normal"):
        super().__init__(scene.all_sprites, scene.bullets)
        self.scene = scene
        # Lasers get a longer, brighter sprite. Other bullets stay 3x3.
        if effect_kind == "laser":
            self.image = pygame.Surface((14, 4), pygame.SRCALPHA)
            pygame.draw.rect(self.image, LASER_COLOR, self.image.get_rect(), border_radius=2)
            pygame.draw.line(self.image, LASER_CORE, (1, 2), (12, 2), 1)
        else:
            self.image = pygame.Surface((3, 3))
            if effect_kind == "chain":
                self.image.fill((140, 200, 255))
            elif effect_kind == "blast":
                self.image.fill((255, 140, 0))
            else:
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
        self.effect_kind = effect_kind
        self.bounces_remaining = LASER_MAX_BOUNCES if effect_kind == "laser" else 0
        # For lasers, we rotate the sprite so the beam points along its velocity.
        if effect_kind == "laser":
            self._render_rotated()

    @property
    def angle_deg(self) -> float:
        return -math.degrees(math.atan2(self.vel.y, self.vel.x))

    def _render_rotated(self):
        base = pygame.Surface((14, 4), pygame.SRCALPHA)
        pygame.draw.rect(base, LASER_COLOR, base.get_rect(), border_radius=2)
        pygame.draw.line(base, LASER_CORE, (1, 2), (12, 2), 1)
        self.image = pygame.transform.rotate(base, self.angle_deg)
        self.rect = self.image.get_rect(center=self.hit_box.center)

    def update(self):
        prev_pos = vector(self.pos)
        self.pos += self.vel
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
