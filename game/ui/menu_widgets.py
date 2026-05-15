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

    def update_hover(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

    def clicked(self, event) -> bool:
        return event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos)


def draw_menu_background(surface, tick_ms: int = 0):
    """Vertical-gradient dark red → near-black with a slow pulsing vignette so
    the menu doesn't feel completely static."""
    surface.fill(MENU_BG)
    # vertical gradient overlay
    band_h = SCREEN_HEIGHT // 80
    for i in range(80):
        t = i / 80
        r = int(MENU_BG[0] + (MENU_BG_ACCENT[0] - MENU_BG[0]) * (1 - t) ** 2)
        g = int(MENU_BG[1] + (MENU_BG_ACCENT[1] - MENU_BG[1]) * (1 - t) ** 2)
        b = int(MENU_BG[2] + (MENU_BG_ACCENT[2] - MENU_BG[2]) * (1 - t) ** 2)
        pygame.draw.rect(surface, (r, g, b), (0, i * band_h, SCREEN_WIDTH, band_h + 1))

    # vignette pulse
    pulse = (math.sin(tick_ms / 800.0) + 1) / 2  # 0..1
    vignette = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    radial_alpha = int(80 + 40 * pulse)
    pygame.draw.circle(
        vignette,
        (0, 0, 0, 0),
        (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2),
        SCREEN_WIDTH // 2,
    )
    # cheap edge darkening: fill black, then cut hole at center
    edge = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    edge.fill((0, 0, 0, radial_alpha))
    pygame.draw.circle(
        edge,
        (0, 0, 0, 0),
        (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2),
        int(SCREEN_WIDTH * 0.55),
    )
    surface.blit(edge, (0, 0))
