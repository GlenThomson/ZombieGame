"""Map maker top-bar with menu/save/open/items buttons + the items pop-up."""
import pygame

from settings import BLACK
from game.world import map_loader


class _PopUpMenu:
    def __init__(self, screen, options: list[str], font, pos=(100, 100), size=(200, 30)):
        self.screen = screen
        self.options = options
        self.font = font
        self.pos = pos
        self.size = size
        self.bg_color = (200, 200, 200)
        self.text_color = (0, 0, 0)
        self.option_rects = [
            pygame.Rect(pos[0], pos[1] + i * size[1], size[0], size[1])
            for i in range(len(options))
        ]
        self.is_open = False
        self.selected_option = None
        self.item_number = 1

    def draw(self):
        if not self.is_open:
            return
        for i, rect in enumerate(self.option_rects):
            pygame.draw.rect(self.screen, self.bg_color, rect)
            text = self.font.render(self.options[i], True, self.text_color)
            self.screen.blit(text, rect.topleft)

    def handle_event(self, event):
        if not (event.type == pygame.MOUSEBUTTONDOWN and self.is_open):
            return None
        x, y = event.pos
        for i, rect in enumerate(self.option_rects):
            if rect.collidepoint(x, y):
                self.item_number = i
                self.selected_option = self.options[i]
                self.is_open = False
                return self.selected_option
        return None


class MapMakerToolbar:
    def __init__(self, surface):
        self.surface = surface
        self.menu_button = pygame.Rect(0, 0, 100, 50)
        self.save_button = pygame.Rect(100, 0, 100, 50)
        self.open_button = pygame.Rect(200, 0, 100, 50)
        self.item_button = pygame.Rect(300, 0, 100, 50)
        self.button_font = pygame.font.Font(None, 36)
        self.text_font = pygame.font.Font(None, 36)
        self.pop_up_menu = _PopUpMenu(
            surface,
            ["delete", "wall", "barb wire", "zombie spawn", "player spawn",
             "door", "door open", "window", "wall buy"],
            self.text_font,
        )
        self.button_clicked = False

    def draw(self):
        for label, rect, color in (
            ("Menu",  self.menu_button, (200, 200, 0)),
            ("Save",  self.save_button, (0, 200, 0)),
            ("Open",  self.open_button, (100, 200, 0)),
            ("Items", self.item_button, (200, 200, 0)),
        ):
            pygame.draw.rect(self.surface, color, rect)
            text = self.button_font.render(label, True, BLACK)
            self.surface.blit(text, (rect.x + 20, rect.y + 10))
        self.pop_up_menu.draw()

    def handle_event(self, event, on_menu, on_save, on_open):
        if event.type != pygame.MOUSEBUTTONDOWN:
            return
        x, y = event.pos
        if self.item_button.collidepoint(x, y):
            self.pop_up_menu.is_open = True
            self.button_clicked = True
        elif self.save_button.collidepoint(x, y):
            on_save()
            self.button_clicked = True
        elif self.menu_button.collidepoint(x, y):
            on_menu()
            self.button_clicked = True
        elif self.open_button.collidepoint(x, y):
            on_open()
            self.button_clicked = True
