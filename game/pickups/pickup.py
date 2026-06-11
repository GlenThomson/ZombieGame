"""On-ground pickup that flickers, expires, and applies a registered effect
when the player walks over it."""
import os
import random
import pygame

from settings import TILE_SIZE, PICKUP_DURATION_MS
from game import assets
from game.pickups import effects


def _placeholder_icon(label: str, fill: tuple[int, int, int]) -> pygame.Surface:
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    pygame.draw.rect(surf, fill, surf.get_rect())
    pygame.draw.rect(surf, (255, 255, 255), surf.get_rect(), 2)
    font = pygame.font.Font(None, 22)
    text = font.render(label, True, (255, 255, 255))
    surf.blit(text, text.get_rect(center=(TILE_SIZE // 2, TILE_SIZE // 2)))
    return surf


class Pickup(pygame.sprite.Sprite):
    def __init__(self, scene, x: float, y: float, kind: str | None = None):
        super().__init__(scene.all_sprites, scene.pickups)
        self.scene = scene
        if kind is None:
            names, weights = effects.weighted_names()
            kind = random.choices(names, weights=weights, k=1)[0]
        self.kind = kind
        self.image = self._load_image(kind)
        self.rect = self.image.get_rect(topleft=(x, y))
        self._anchor_y = self.rect.y   # for bob animation
        self.spawn_time = pygame.time.get_ticks()
        self.flicker_period_ms = 1000
        self.next_flicker_at = self.spawn_time + self.flicker_period_ms
        self.visible = True

    def _load_image(self, kind: str) -> pygame.Surface:
        png_path = os.path.join("assets", "images", f"{kind}.png")
        if os.path.isfile(png_path):
            return assets.image(f"{kind}.png", scale=(TILE_SIZE, TILE_SIZE)).copy()
        icon = effects.icon_for(kind) or (kind[:2].upper(), (180, 180, 180))
        return _placeholder_icon(*icon)

    def update(self):
        import math
        from settings import PICKUP_FLICKER_WINDOW_MS
        now = pygame.time.get_ticks()
        elapsed = now - self.spawn_time
        if elapsed > PICKUP_DURATION_MS:
            self.kill()
            return

        # Any standing player walking over a pickup collects it for everyone.
        for player in self.scene.players:
            if player.is_dead() or player.is_down:
                continue
            if pygame.sprite.collide_rect(self, player):
                effects.apply(self.kind, self.scene, collector=player)
                self.kill()
                return

        # Floating bob.
        self.rect.y = self._anchor_y + int(math.sin(now / 200) * 3)

        # Solid for most of the lifetime; only blink during the final
        # window (BO1 style), speeding up as expiry approaches.
        time_left = PICKUP_DURATION_MS - elapsed
        if time_left >= PICKUP_FLICKER_WINDOW_MS:
            if not self.visible:
                self.visible = True
                self.image.set_alpha(255)
            return
        # Blink faster the closer we are to disappearing.
        urgency = 1.0 - (time_left / PICKUP_FLICKER_WINDOW_MS)
        self.flicker_period_ms = max(80, int(600 - 520 * urgency))

        if now >= self.next_flicker_at:
            self.visible = not self.visible
            self.image.set_alpha(255 if self.visible else 0)
            self.next_flicker_at = now + self.flicker_period_ms
