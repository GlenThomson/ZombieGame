"""Main menu screen. Redesigned: dark themed background, hover-able buttons,
title + subtitle."""
import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, MENU_TITLE, MENU_TEXT_DIM
from game.states.base import State
from game.ui.menu_widgets import Button, draw_menu_background


class MenuState(State):
    def on_enter(self, **kwargs):
        title_font = pygame.font.Font(None, 130)
        sub_font = pygame.font.Font(None, 32)
        button_font = pygame.font.Font(None, 44)

        self._title_surf = title_font.render("ZOMBIES", True, MENU_TITLE)
        self._subtitle_surf = sub_font.render("the dead don't stop coming.", True, MENU_TEXT_DIM)
        self._title_pos = (
            SCREEN_WIDTH // 2 - self._title_surf.get_width() // 2,
            120,
        )
        self._subtitle_pos = (
            SCREEN_WIDTH // 2 - self._subtitle_surf.get_width() // 2,
            220,
        )

        cx = SCREEN_WIDTH // 2
        self.buttons = [
            ("play",         Button("Play",         (cx, 360), button_font)),
            ("multiplayer",  Button("Multiplayer",  (cx, 430), button_font)),
            ("mapmaker",     Button("Map Maker",    (cx, 500), button_font)),
            ("controls",     Button("Controls",     (cx, 570), button_font)),
            ("quit",         Button("Quit",         (cx, 640), button_font)),
        ]
        self.show_controls = False
        self._controls_font = pygame.font.Font(None, 30)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            for _, b in self.buttons:
                b.update_hover(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.show_controls:
                self.show_controls = False
                return
            for action, button in self.buttons:
                if button.clicked(event):
                    self._dispatch(action)
                    return

    def _dispatch(self, action: str):
        if action == "play":
            self.app.switch("map_select")
        elif action == "multiplayer":
            self.app.switch("multiplayer_menu")
        elif action == "mapmaker":
            self.app.switch("map_maker_landing")
        elif action == "controls":
            self.show_controls = True
        elif action == "quit":
            self.app.quit()

    def draw(self):
        draw_menu_background(self.surface, pygame.time.get_ticks())
        self.surface.blit(self._title_surf, self._title_pos)
        self.surface.blit(self._subtitle_surf, self._subtitle_pos)
        for _, button in self.buttons:
            button.draw(self.surface)
        if self.show_controls:
            self._draw_controls_overlay()

    def _draw_controls_overlay(self):
        from game.ui.controls import CONTROLS
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 215))
        self.surface.blit(overlay, (0, 0))

        title_font = pygame.font.Font(None, 56)
        title = title_font.render("CONTROLS", True, (255, 215, 0))
        self.surface.blit(
            title, title.get_rect(center=(SCREEN_WIDTH // 2, 90)))

        key_x = SCREEN_WIDTH // 2 - 220
        desc_x = SCREEN_WIDTH // 2 - 60
        y = 160
        for key, desc in CONTROLS:
            key_surf = self._controls_font.render(key, True, (255, 215, 0))
            desc_surf = self._controls_font.render(desc, True, (220, 220, 220))
            self.surface.blit(key_surf, (key_x, y))
            self.surface.blit(desc_surf, (desc_x, y))
            y += 38

        hint = self._controls_font.render(
            "Click anywhere to go back", True, (140, 140, 140))
        self.surface.blit(
            hint, hint.get_rect(center=(SCREEN_WIDTH // 2, y + 30)))
