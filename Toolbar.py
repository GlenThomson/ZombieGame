from Map import *
from utility_functions import *


class Toolbar:
    def __init__(self, game):
        self.game = game
        self.save_button = pygame.Rect(100, 0, 100, 50)
        self.menu_button = pygame.Rect(0, 0, 100, 50)
        self.open_button = pygame.Rect(200, 0, 100, 50)
        self.item_button = pygame.Rect(300, 0, 100, 50)
        self.button_font = pygame.font.Font(None, 36)
        self.text_font = pygame.font.Font(None, 36)
        self.pop_up_menu = PopUpMenu(self.game.display, ['delete','wall','barb wire', 'zombie spawn','player spawn'], self.text_font)

    def draw(self):
        # Draw the main menu button always
        pygame.draw.rect(self.game.display, (200, 200, 0), self.menu_button)
        menu_text = self.button_font.render('Menu', True, (0, 0, 0))
        self.game.display.blit(menu_text, (self.menu_button.x + 20, self.menu_button.y + 10))

        # Draw the save button conditionally based on the game mode
        if self.game.mode == "MAPMAKING":
            self.draw_mapmaking_toolbar()
        elif self.game.mode == "PLAY":
            self.draw_play_toolbar()
        # ... (repeat for other modes)

    def draw_mapmaking_toolbar(self):
        # draw the save button
        pygame.draw.rect(self.game.display, (0, 200, 0), self.save_button)
        save_text = self.button_font.render('Save', True, (0, 0, 0))
        self.game.display.blit(save_text, (self.save_button.x + 20, self.save_button.y + 10))
        # draw the open button
        pygame.draw.rect(self.game.display, (100, 200, 0), self.open_button)
        open_text = self.button_font.render('Open', True, (0, 0, 0))
        self.game.display.blit(open_text, (self.open_button.x + 20, self.open_button.y + 10))
        # draw the item button
        pygame.draw.rect(self.game.display, (200, 200, 0), self.item_button)
        item_text = self.button_font.render('Items', True, (0, 0, 0))
        self.game.display.blit(item_text, (self.item_button.x + 20, self.item_button.y + 10))
        self.pop_up_menu.draw()


    def draw_play_toolbar(self):
        # code to draw the toolbar when in "PLAY" mode
        pass

    def handle_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            if self.item_button.collidepoint((x,y)):
                self.pop_up_menu.is_open = True
            # Check if save or menu button is clicked
            if self.save_button.collidepoint((x, y)):
                self.game.map_maker_mode.save_map()
            elif self.menu_button.collidepoint((x, y)):
                self.game.mode = "MENU"
            elif self.open_button.collidepoint((x, y)):
                self.game.grid = load_map_from_file()
                # self.game.map = Map(self.game)


class PopUpMenu:
    def __init__(self, screen, options, font, pos=(100, 100), size=(200, 30), bg_color=(200, 200, 200), text_color=(0, 0, 0)):
        self.screen = screen
        self.options = options
        self.font = font
        self.pos = pos
        self.size = size
        self.bg_color = bg_color
        self.text_color = text_color
        self.option_rects = self._create_option_rects()
        self.is_open = False
        self.selected_option = None
        self.item_number = 1

    def _create_option_rects(self):
        rects = []
        for i, option in enumerate(self.options):
            rect = pygame.Rect(self.pos[0], self.pos[1] + i * self.size[1], self.size[0], self.size[1])
            rects.append(rect)
        return rects

    def draw(self):
        if self.is_open:
            for i, rect in enumerate(self.option_rects):
                pygame.draw.rect(self.screen, self.bg_color, rect)
                text_surface = self.font.render(self.options[i], True, self.text_color)
                self.screen.blit(text_surface, rect.topleft)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.is_open:
            x, y = event.pos
            for i, rect in enumerate(self.option_rects):
                if rect.collidepoint(x, y):
                    self.item_number = i
                    self.selected_option = self.options[i]
                    self.is_open = False
                    return self.selected_option

    def toggle_menu(self):
        self.is_open = not self.is_open