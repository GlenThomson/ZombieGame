"""Reusable button + background helpers for menu screens."""
import math
import pygame

from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    MENU_BG,
    MENU_BG_ACCENT,
    MENU_TEXT,
    MENU_HOVER,
)


class Button:
    def __init__(self, label: str, center: tuple[int, int], font: pygame.font.Font,
                 width: int = 280, height: int = 56):
        self.label = label
        self.font = font
        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = center
        self.hovered = False

    def draw(self, surface):
        # subtle background fill, brighter when hovered
        bg = (50, 12, 12) if self.hovered else (28, 28, 32)
        border = MENU_HOVER if self.hovered else (80, 80, 90)
        pygame.draw.rect(surface, bg, self.rect, border_radius=6)
        pygame.draw.rect(surface, border, self.rect, width=2, border_radius=6)

        text_color = MENU_HOVER if self.hovered else MENU_TEXT
        text_surf = self.font.render(self.label, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def set_label(self, label: str):
        self.label = label

    def update_hover(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def clicked(self, event) -> bool:
        return event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos)


_menu_bg_cache: pygame.Surface | None = None


def _load_menu_bg() -> pygame.Surface | None:
    """Load and cache the AI-generated menu background. Returns None if the
    file is missing (caller falls back to gradient)."""
    global _menu_bg_cache
    if _menu_bg_cache is not None:
        return _menu_bg_cache
    import os
    path = os.path.join("assets", "images", "menu_bg.jpeg")
    if not os.path.isfile(path):
        return None
    img = pygame.image.load(path).convert()
    _menu_bg_cache = pygame.transform.scale(img, (SCREEN_WIDTH, SCREEN_HEIGHT))
    return _menu_bg_cache


def draw_menu_background(surface, tick_ms: int = 0):
    """Atmospheric horror background. Uses the AI-generated menu_bg if
    present, falls back to a programmatic gradient otherwise. A subtle
    pulsing dark vignette over the top either way."""
    bg = _load_menu_bg()
    if bg is not None:
        surface.blit(bg, (0, 0))
    else:
        surface.fill(MENU_BG)
        band_h = SCREEN_HEIGHT // 80
        for i in range(80):
            t = i / 80
            r = int(MENU_BG[0] + (MENU_BG_ACCENT[0] - MENU_BG[0]) * (1 - t) ** 2)
            g = int(MENU_BG[1] + (MENU_BG_ACCENT[1] - MENU_BG[1]) * (1 - t) ** 2)
            b = int(MENU_BG[2] + (MENU_BG_ACCENT[2] - MENU_BG[2]) * (1 - t) ** 2)
            pygame.draw.rect(surface, (r, g, b), (0, i * band_h, SCREEN_WIDTH, band_h + 1))

    # Pulsing dark vignette so text reads against the busy background.
    pulse = (math.sin(tick_ms / 800.0) + 1) / 2
    radial_alpha = int(120 + 50 * pulse)
    edge = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    edge.fill((0, 0, 0, radial_alpha))
    pygame.draw.circle(
        edge, (0, 0, 0, 0),
        (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2),
        int(SCREEN_WIDTH * 0.55),
    )
    surface.blit(edge, (0, 0))
