from Game_settings import *
import pygame
from Map import *

class Toolbar:
    def __init__(self, game):
        self.game = game
        self.navbar_height = 30  # Adjust as necessary
        self.save_button = pygame.Rect(100, 0, 100, 50)
        self.menu_button = pygame.Rect(0, 0, 100, 50)
        self.open_button = pygame.Rect(200, 0, 100, 50)
        self.button_font = pygame.font.Font(None, 36)


    def draw(self):
        pygame.draw.rect(self.game.display, (100, 100, 100), (0, 0, SCREEN_WIDTH, self.navbar_height))
        # Draw the main menu button always
        pygame.draw.rect(self.game.display, (0, 0, 200), self.menu_button)
        menu_text = self.button_font.render('Menu', True, (0, 0, 0))
        self.game.display.blit(menu_text, (self.menu_button.x + 20, self.menu_button.y + 10))

        # Draw the save button conditionally based on the game mode
        if self.game.mode == "MAPMAKING":
            self.draw_mapmaking_toolbar()


        if self.game.mode == "MENU":
            self.draw_menu_toolbar()
        elif self.game.mode == "PLAY":
            self.draw_play_toolbar()
        #... (repeat for other modes)

    def draw_menu_toolbar(self):
        # code to draw the toolbar when in "MENU" mode
        pass

    def draw_mapmaking_toolbar(self):
        #draw the save button
        pygame.draw.rect(self.game.display, (0, 200, 0), self.save_button)
        save_text = self.button_font.render('Save', True, (0, 0, 0))
        self.game.display.blit(save_text, (self.save_button.x + 20, self.save_button.y + 10))
        #draw the open button
        pygame.draw.rect(self.game.display, (100, 200, 0), self.open_button)
        save_text = self.button_font.render('Open', True, (0, 0, 0))
        self.game.display.blit(save_text, (self.open_button.x + 20, self.open_button.y + 10))

    def draw_play_toolbar(self):
        # code to draw the toolbar when in "PLAY" mode
        pass

    def handle_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            # Check if save or menu button is clicked
            if self.save_button.collidepoint((x, y)) :
                self.game.map_maker_mode.save_map()
            elif self.menu_button.collidepoint((x, y)):
                self.game.mode = "MENU"
            elif self.open_button.collidepoint((x, y)):
                self.game.map = Map(self.game)


