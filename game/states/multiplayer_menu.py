"""Multiplayer landing screen: pick your name, then Host or Join."""
import pygame

from settings import SCREEN_WIDTH, MENU_TITLE, MENU_TEXT, MENU_TEXT_DIM, GOLD
from game import config
from game.states.base import State
from game.ui.menu_widgets import Button, draw_menu_background

NAME_MAX_LEN = 16


class MultiplayerMenuState(State):
    def on_enter(self, **kwargs):
        title_font = pygame.font.Font(None, 92)
        sub_font = pygame.font.Font(None, 26)
        button_font = pygame.font.Font(None, 44)
        self.input_font = pygame.font.Font(None, 40)
        self.label_font = pygame.font.Font(None, 28)

        self._title_surf = title_font.render("MULTIPLAYER", True, MENU_TITLE)
        self._sub_surf = sub_font.render("up to 4 players, host or join", True, MENU_TEXT_DIM)
        self._title_pos = (SCREEN_WIDTH // 2 - self._title_surf.get_width() // 2, 120)
        self._sub_pos = (SCREEN_WIDTH // 2 - self._sub_surf.get_width() // 2, 200)

        self.name_text = config.player_name()
        self.editing_name = False
        cx = SCREEN_WIDTH // 2
        self.name_rect = pygame.Rect(cx - 150, 290, 300, 44)
        self.buttons = [
            ("host", Button("Host Game", (cx, 430), button_font)),
            ("join", Button("Join Game", (cx, 510), button_font)),
            ("back", Button("Back", (cx, 620), button_font, width=200)),
        ]

    def _save_name(self):
        name = self.name_text.strip()[:NAME_MAX_LEN] or "Player"
        config.save(player_name=name)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            for _, b in self.buttons:
                b.update_hover(event.pos)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._save_name()
                self.app.switch("menu")
                return
            if self.editing_name:
                if event.key in (pygame.K_RETURN, pygame.K_TAB):
                    self.editing_name = False
                    self._save_name()
                elif event.key == pygame.K_BACKSPACE:
                    self.name_text = self.name_text[:-1]
                else:
                    ch = event.unicode
                    if ch and ch.isprintable() and len(self.name_text) < NAME_MAX_LEN:
                        self.name_text += ch
                return
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.editing_name = self.name_rect.collidepoint(event.pos)
            if self.editing_name:
                return
            for action, button in self.buttons:
                if button.clicked(event):
                    self._save_name()
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

        # Name field — used as your in-game label whether hosting or joining.
        label = self.label_font.render("Your name:", True, MENU_TEXT_DIM)
        self.surface.blit(
            label, (self.name_rect.x, self.name_rect.y - 28))
        border = GOLD if self.editing_name else (80, 80, 90)
        pygame.draw.rect(self.surface, (28, 28, 32), self.name_rect, border_radius=4)
        pygame.draw.rect(self.surface, border, self.name_rect, width=2, border_radius=4)
        shown = self.name_text + ("|" if self.editing_name
                                  and pygame.time.get_ticks() % 1000 < 500 else "")
        text = self.input_font.render(shown, True, MENU_TEXT)
        self.surface.blit(
            text, text.get_rect(midleft=(self.name_rect.x + 10, self.name_rect.centery)))

        for _, b in self.buttons:
            b.draw(self.surface)
        pygame.display.flip()
