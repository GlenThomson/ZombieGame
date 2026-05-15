"""Visual-only sprites: blood splatter, screen shake markers, etc."""
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
