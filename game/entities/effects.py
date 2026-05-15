"""Visual-only sprites: blood splatter, muzzle flash, floating point text."""
import pygame
from game import assets


class BloodSplatter(pygame.sprite.Sprite):
    def __init__(self, scene, world_pos, duration_ms: int = 500):
        super().__init__(scene.blood_splatters)
        self.scene = scene
        self.image = assets.image("bloodSplatter.png").copy()
        self.original_pos = world_pos
        self.rect = self.image.get_rect(center=self.original_pos + scene.camera.pos)
        self.spawn_time = pygame.time.get_ticks()
        self.duration = duration_ms
        self.alpha = 200

    def update(self):
        self.alpha -= 1
        self.rect.center = self.original_pos + self.scene.camera.pos
        self.image.set_alpha(max(self.alpha, 0))
        if pygame.time.get_ticks() - self.spawn_time > self.duration:
            self.kill()


class MuzzleFlash(pygame.sprite.Sprite):
    """Tiny yellow burst at the player's barrel for ~3 frames."""
    LIFETIME_MS = 60

    def __init__(self, scene, world_pos):
        super().__init__(scene.all_sprites, scene.muzzle_flashes)
        self.scene = scene
        self.spawn_time = pygame.time.get_ticks()
        self.image = pygame.Surface((18, 18), pygame.SRCALPHA)
        # bright yellow centre, fading orange edge
        pygame.draw.circle(self.image, (255, 240, 120), (9, 9), 9)
        pygame.draw.circle(self.image, (255, 180, 40), (9, 9), 6)
        pygame.draw.circle(self.image, (255, 240, 200), (9, 9), 3)
        self.rect = self.image.get_rect(center=world_pos)

    def update(self):
        if pygame.time.get_ticks() - self.spawn_time > self.LIFETIME_MS:
            self.kill()


class FloatingText(pygame.sprite.Sprite):
    """Drifts up and fades. Used for "+50" point pops near killed zombies."""
    LIFETIME_MS = 700

    def __init__(self, scene, world_pos, text: str, color=(255, 215, 0)):
        super().__init__(scene.floating_texts)
        self.scene = scene
        self.spawn_time = pygame.time.get_ticks()
        self.text = text
        self.color = color
        font = pygame.font.Font(None, 22)
        self._base_image = font.render(text, True, color)
        self.image = self._base_image.copy()
        self.world_pos = pygame.math.Vector2(world_pos)
        self.rect = self.image.get_rect(center=self.world_pos + scene.camera.pos)

    def update(self):
        elapsed = pygame.time.get_ticks() - self.spawn_time
        if elapsed > self.LIFETIME_MS:
            self.kill()
            return
        t = elapsed / self.LIFETIME_MS
        self.world_pos.y -= 0.6  # drift up
        self.rect.center = self.world_pos + self.scene.camera.pos
        # Fade out toward the end
        alpha = int(255 * (1 - max(0.0, t - 0.4) / 0.6))
        self.image = self._base_image.copy()
        self.image.set_alpha(max(0, alpha))
