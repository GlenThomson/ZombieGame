"""Landing screen shown when the user clicks Map Maker.

Lets them either start fresh (which kicks off the existing flow that asks
for a background image) or pick an existing .pkl to edit in place."""
import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, MENU_TEXT, MENU_TITLE, MENU_TEXT_DIM
from game.states.base import State
from game.ui.menu_widgets import Button, draw_menu_background
from game.world import map_loader


class MapMakerLandingState(State):
    def on_enter(self, **kwargs):
        self.title_font = pygame.font.Font(None, 72)
        self.body_font = pygame.font.Font(None, 32)
        self.button_font = pygame.font.Font(None, 36)

        self.title_surf = self.title_font.render("MAP MAKER", True, MENU_TITLE)
        self.title_pos = (SCREEN_WIDTH // 2 - self.title_surf.get_width() // 2, 80)

        cx = SCREEN_WIDTH // 2
        self.new_button = Button("New Map", (cx, 200), self.button_font, width=240)
        self.back_button = Button("Back", (140, SCREEN_HEIGHT - 60), self.button_font, width=160, height=46)

        self.maps = map_loader.list_maps()
        self.map_buttons: list[tuple[str, Button]] = []
        if self.maps:
            spacing = 56
            start_y = 320
            for i, fname in enumerate(self.maps):
                btn = Button(fname[:-4], (cx, start_y + i * spacing), self.button_font, width=320, height=46)
                self.map_buttons.append((fname, btn))

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.new_button.update_hover(event.pos)
            self.back_button.update_hover(event.pos)
            for _, b in self.map_buttons:
                b.update_hover(event.pos)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.switch("menu")
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_button.clicked(event):
                self.app.switch("menu")
                return
            if self.new_button.clicked(event):
                self.app.switch("mapmaking")
                return
            for fname, btn in self.map_buttons:
                if btn.clicked(event):
                    self.app.switch("mapmaking", editing=fname)
                    return

    def draw(self):
        draw_menu_background(self.surface, pygame.time.get_ticks())
        self.surface.blit(self.title_surf, self.title_pos)

        if self.maps:
            label = self.body_font.render("Or edit an existing map:", True, MENU_TEXT_DIM)
            self.surface.blit(label, (SCREEN_WIDTH // 2 - label.get_width() // 2, 270))

        self.new_button.draw(self.surface)
        for _, btn in self.map_buttons:
            btn.draw(self.surface)
        self.back_button.draw(self.surface)
        pygame.display.flip()
