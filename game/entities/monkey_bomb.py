"""Monkey Bomb. THROWN like a grenade (cursor-aimed arc), lands, bangs its
cymbals to a wind-up jingle, attracts every zombie in the scene, flashes
as the timer runs out, then explodes killing everything in radius.

Registers itself in scene.zombie_attractors when it LANDS (not at throw)
so zombies chase the toy, not the ballistic arc."""
import os
import pygame

from settings import (
    MONKEY_BOMB_DURATION_MS,
    MONKEY_BOMB_RADIUS_PX,
    MONKEY_BOMB_DAMAGE,
)
from game import assets
from game.entities.grenade import ThrowArc, explosion_frames

vector = pygame.math.Vector2

SIZE = 30                 # on-ground sprite size, px
CYMBAL_SWAP_MS = 160      # cymbal clash animation rate
WIGGLE_DEG = 10           # rocking while it plays
FLASH_WINDOW_MS = 1200    # white-flash warning before detonation


def _frames() -> list[pygame.Surface]:
    out = []
    for i in (0, 1):
        name = f"monkey_bomb_{i}.png"
        if os.path.isfile(os.path.join("assets", "images", name)):
            out.append(assets.image(name, scale=(SIZE, SIZE)))
    if not out:  # stale checkout fallback
        ph = pygame.Surface((SIZE, SIZE), pygame.SRCALPHA)
        pygame.draw.circle(ph, (220, 100, 160), (SIZE // 2, SIZE // 2), SIZE // 2)
        out = [ph, ph]
    return out


class MonkeyBomb(pygame.sprite.Sprite):
    def __init__(self, scene, x: float, y: float, thrower_id: int = 0,
                 target: tuple | None = None, angle_deg: float = 0.0):
        super().__init__(scene.all_sprites, scene.monkey_bombs)
        self.scene = scene
        self.thrower_id = thrower_id
        self.frames = _frames()
        self.image = self.frames[0]
        self.pos = vector(x, y)
        self.rect = self.image.get_rect(center=self.pos)
        self.arc = ThrowArc(self.pos, target, angle_deg)
        self.landed = False
        self.landed_at_ms = 0
        self.exploded = False
        self.exploding = False
        self.frame_index = 0
        self.last_frame_update = 0
        self.explosion_frames = explosion_frames()

    def update(self):
        now = pygame.time.get_ticks()
        if self.exploding:
            self._advance_explosion_animation(now)
            return
        if not self.landed:
            if self.arc.landed:
                self._land(now)
            else:
                self.pos += self.arc.step_velocity()
                s = self.arc.height_scale()
                size = max(10, int(SIZE * s))
                self.image = pygame.transform.scale(self.frames[0], (size, size))
                self.rect = self.image.get_rect(center=self.pos)
            return

        # On the ground: cymbal clash + rocking wiggle.
        elapsed = now - self.landed_at_ms
        frame = self.frames[(now // CYMBAL_SWAP_MS) % 2]
        wig = WIGGLE_DEG if (now // CYMBAL_SWAP_MS) % 2 else -WIGGLE_DEG
        img = pygame.transform.rotate(frame, wig)
        # Final-second white flash so everyone knows it's about to pop.
        remaining = MONKEY_BOMB_DURATION_MS - elapsed
        if remaining < FLASH_WINDOW_MS and (now // 90) % 2 == 0:
            img = img.copy()
            img.fill((120, 120, 120), special_flags=pygame.BLEND_RGB_ADD)
        self.image = img
        self.rect = self.image.get_rect(center=self.pos)

        if elapsed > MONKEY_BOMB_DURATION_MS:
            self._explode()

    def _land(self, now: int):
        self.landed = True
        self.landed_at_ms = now
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=self.pos)
        # NOW it starts attracting zombies + playing its tune.
        self.scene.zombie_attractors.append(self)
        self.scene.announce_event("monkey_jingle", {"sound": "monkey_jingle.wav"})

    def _advance_explosion_animation(self, now: int):
        if now - self.last_frame_update <= 50:
            return
        self.last_frame_update = now
        self.frame_index += 1
        if self.frame_index >= len(self.explosion_frames):
            self.kill()
            return
        center = self.rect.center
        self.image = self.explosion_frames[self.frame_index]
        self.rect = self.image.get_rect(center=center)

    def _explode(self):
        self.exploded = True
        self.exploding = True
        self.frame_index = 0
        if self in self.scene.zombie_attractors:
            self.scene.zombie_attractors.remove(self)
        self.scene.announce_event("monkey_explode", {"sound": "kaboom.mp3"})
        # Kill anything in radius — kills pay out to the thrower.
        from game.entities.grenade import award_explosive_kills
        killed = 0
        for zombie in list(self.scene.zombies):
            d2 = (zombie.pos.x - self.pos.x) ** 2 + (zombie.pos.y - self.pos.y) ** 2
            if d2 <= MONKEY_BOMB_RADIUS_PX ** 2:
                was_alive = zombie.health > 0
                zombie.take_damage(MONKEY_BOMB_DAMAGE)
                if was_alive and zombie.health <= 0:
                    killed += 1
        award_explosive_kills(self.scene, self.thrower_id, killed,
                              (self.pos.x, self.pos.y))
        self.image = self.explosion_frames[0]
        self.rect = self.image.get_rect(center=self.pos)
