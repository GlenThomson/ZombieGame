"""Shown when the player dies."""
import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, MENU_TEXT, MENU_TEXT_DIM
from game.states.base import State
from game.ui.menu_widgets import Button, draw_menu_background


class GameOverState(State):
    def on_enter(self, *, final_round: int = 1, final_kills: int = 0, **kwargs):
        title_font = pygame.font.Font(None, 110)
        stat_font = pygame.font.Font(None, 40)
        button_font = pygame.font.Font(None, 40)

        self.title_surf = title_font.render("YOU DIED", True, (200, 30, 30))
        self.title_pos = (SCREEN_WIDTH // 2 - self.title_surf.get_width() // 2, 200)

        self.stats_surfs = [
            stat_font.render(f"Survived to round {final_round}", True, MENU_TEXT),
            stat_font.render(f"Kills: {final_kills}", True, MENU_TEXT_DIM),
        ]

        cx = SCREEN_WIDTH // 2
        self.retry_button = Button("Back to Menu", (cx, 600), button_font)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.retry_button.update_hover(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and self.retry_button.clicked(event):
            self.app.switch("menu")
        elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
            self.app.switch("menu")

    def draw(self):
        draw_menu_background(self.surface, pygame.time.get_ticks())
        self.surface.blit(self.title_surf, self.title_pos)
        y = 360
        for surf in self.stats_surfs:
            self.surface.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, y))
            y += 50
        self.retry_button.draw(self.surface)
        pygame.display.flip()
