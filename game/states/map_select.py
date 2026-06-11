"""Map selection screen — lists every .pkl in maps/ as a button."""
import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, MENU_TEXT
from game.states.base import State
from game.ui.menu_widgets import Button, draw_menu_background
from game.world import map_loader


class MapSelectState(State):
    def on_enter(self, **kwargs):
        self.title_font = pygame.font.Font(None, 80)
        self.button_font = pygame.font.Font(None, 38)
        self.empty_font = pygame.font.Font(None, 40)

        self.title_surf = self.title_font.render("Select a Map", True, MENU_TEXT)
        self.title_pos = (SCREEN_WIDTH // 2 - self.title_surf.get_width() // 2, 80)

        files = map_loader.list_maps()
        self.buttons = []
        if files:
            spacing = 70
            start_y = 220
            cx = SCREEN_WIDTH // 2
            for i, fname in enumerate(files):
                label = fname[:-4]
                btn = Button(label, (cx, start_y + i * spacing), self.button_font, width=320, height=54)
                self.buttons.append((fname, btn))

        self.back_button = Button("Back", (90, SCREEN_HEIGHT - 60), self.button_font, width=140, height=46)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            for _, b in self.buttons:
                b.update_hover(event.pos)
            self.back_button.update_hover(event.pos)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.switch("menu")
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_button.clicked(event):
                self.app.switch("menu")
                return
            for fname, btn in self.buttons:
                if btn.clicked(event):
                    data = map_loader.load(f"maps/{fname}")
                    self.app.switch(
                        "play",
                        grid=data["grid"],
                        background=data["background_image_path"],
                        door_costs=data["door_costs"],
                        wall_buy_weapons=data["wall_buy_weapons"],
                        perk_machine_perks=data["perk_machine_perks"],
                        floor_grid=data.get("floor_grid"),
                        wall_style=data.get("wall_style", "brick"),
                        decor=data.get("decor", []),
                    )
                    return

    def draw(self):
        draw_menu_background(self.surface, pygame.time.get_ticks())
        self.surface.blit(self.title_surf, self.title_pos)
        if not self.buttons:
            text = self.empty_font.render("No maps in maps/", True, MENU_TEXT)
            self.surface.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2))
        for _, btn in self.buttons:
            btn.draw(self.surface)
        self.back_button.draw(self.surface)
