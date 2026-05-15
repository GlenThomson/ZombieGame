"""Camera that follows a target sprite, clamped to map edges."""
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT


class Camera:
    def __init__(self, map_width: int, map_height: int):
        self.camera = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.width = map_width
        self.height = map_height
        self.pos = (0, 0)

    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def update(self, target):
        target_x = target.rect.centerx - SCREEN_WIDTH // 2
        target_y = target.rect.centery - SCREEN_HEIGHT // 2

        x = max(-self.width + SCREEN_WIDTH, min(0, -target_x))
        y = max(-self.height + SCREEN_HEIGHT, min(0, -target_y))

        self.pos = (x, y)
        self.camera = pygame.Rect(x, y, self.width, self.height)
