"""Zombie subclasses. Each just overrides a few attributes — the AI lives
in the base Zombie class.

Visual differentiation is done by tinting the base zombie sprite (no new art
yet). Replace `_TINT` per class once real sprites land."""
import pygame

from settings import TILE_SIZE
from game import assets
from game.entities.zombie import Zombie


def _tinted_sprite(tint: tuple[int, int, int], scale_factor: float = 1.0) -> pygame.Surface:
    """Return a tinted copy of the base zombie sprite."""
    base = assets.image("zombie.png")
    side = max(8, int(TILE_SIZE * scale_factor))
    scaled = pygame.transform.scale(base, (side, side))
    out = scaled.copy()
    overlay = pygame.Surface(scaled.get_size(), pygame.SRCALPHA)
    overlay.fill((*tint, 110))
    out.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return out


class Crawler(Zombie):
    """Slow but tougher per HP. Half-sized."""
    _SPEED_MULT = 0.5
    _HEALTH_MULT = 1.5
    _SCALE = 0.6
    _TINT = (180, 220, 80)

    def __init__(self, scene, x: float, y: float):
        super().__init__(scene, x, y)
        self.original_image = _tinted_sprite(self._TINT, self._SCALE)
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self.hit_box = pygame.Rect(0, 0, self.rect.width * 0.7, self.rect.height * 0.7)
        self.hit_box.center = self.rect.center
        self.speed_base *= self._SPEED_MULT
        self.speed = self.speed_base
        self.health *= self._HEALTH_MULT


class Runner(Zombie):
    """Fast, lower HP. Normal size, red-tinted."""
    _SPEED_MULT = 1.6
    _HEALTH_MULT = 0.7
    _TINT = (255, 90, 60)

    def __init__(self, scene, x: float, y: float):
        super().__init__(scene, x, y)
        self.original_image = _tinted_sprite(self._TINT)
        self.image = self.original_image.copy()
        self.speed_base *= self._SPEED_MULT
        self.speed = self.speed_base
        self.health *= self._HEALTH_MULT


class Hellhound(Zombie):
    """Sprints in straight lines at the player. Very fast, glass cannon."""
    _SPEED_MULT = 2.2
    _HEALTH_MULT = 0.5
    _SCALE = 0.7
    _TINT = (40, 0, 90)

    def __init__(self, scene, x: float, y: float):
        super().__init__(scene, x, y)
        self.original_image = _tinted_sprite(self._TINT, self._SCALE)
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self.hit_box = pygame.Rect(0, 0, self.rect.width * 0.7, self.rect.height * 0.7)
        self.hit_box.center = self.rect.center
        self.speed_base *= self._SPEED_MULT
        self.speed = self.speed_base
        self.health *= self._HEALTH_MULT

    def update(self, player_pos):
        # Skip pathfinding — always bee-line. (Override of Zombie.update.)
        if self.health <= 0:
            self.kill()
            return
        self._aim(player_pos)
