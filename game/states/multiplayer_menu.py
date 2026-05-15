"""Multiplayer landing screen: Host vs Join."""
import pygame

from settings import SCREEN_WIDTH, MENU_TITLE, MENU_TEXT_DIM
from game.states.base import State
from game.ui.menu_widgets import Button, draw_menu_background


class MultiplayerMenuState(State):
    def on_enter(self, **kwargs):
        title_font = pygame.font.Font(None, 92)
        sub_font = pygame.font.Font(None, 26)
        button_font = pygame.font.Font(None, 44)

        self._title_surf = title_font.render("MULTIPLAYER", True, MENU_TITLE)
        self._sub_surf = sub_font.render("up to 4 players, host or join", True, MENU_TEXT_DIM)
        self._title_pos = (SCREEN_WIDTH // 2 - self._title_surf.get_width() // 2, 140)
        self._sub_pos = (SCREEN_WIDTH // 2 - self._sub_surf.get_width() // 2, 220)

        cx = SCREEN_WIDTH // 2
        self.buttons = [
            ("host", Button("Host Game", (cx, 380), button_font)),
            ("join", Button("Join Game", (cx, 460), button_font)),
            ("back", Button("Back", (cx, 580), button_font, width=200)),
        ]

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            for _, b in self.buttons:
                b.update_hover(event.pos)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.switch("menu")
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            for action, button in self.buttons:
                if button.clicked(event):
                    if action == "host":
                        self.app.switch("host_lobby")
                    elif action == "join":
                        self.app.switch("join_lobby")
                    elif action == "back":
                        self.app.switch("menu")
                    return

    def draw(self):
        draw_menu_background(self.surface, pygame.time.get_ticks())
        self.surface.blit(self._title_surf, self._title_pos)
        self.surface.blit(self._sub_surf, self._sub_pos)
        for _, b in self.buttons:
            b.draw(self.surface)
        pygame.display.flip()
