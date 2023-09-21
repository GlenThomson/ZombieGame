import pygame
import random
import pickle
import os
from Toolbar import Toolbar
import tkinter as tk
from tkinter import filedialog
import sys
from tkinter import simpledialog
from Bullet import Bullet
from Game_settings import *
from Sprites import *
import math
pygame.init()


class game_main():
    def __init__(self):
        self.grid = []
        self.display = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
        #set up the different sprite groups
        self.all_sprites=self.bullets = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.zombies = pygame.sprite.Group()
        self.walls = pygame.sprite.Group()
        self.player = Player(self,400,400)
        #set up the different mode variables
        self.mode = "MENU"
        self.menu_mode = MenuMode(self)
        self.map_maker_mode = MapMakerMode(self)
        #creates tool bar
        self.toolbar = Toolbar(self)

#
#Main game loop
    def run_game(self):
        while True:
            if self.mode == "MENU":
                self.menu_mode.menu_events()
                self.menu_mode.draw_menu()
            elif self.mode == "PLAY":
                self.update()
                self.events()
                self.draw()
            elif self.mode == "MAPMAKING_START":
                self.map_maker_mode.mapmaker_start()
                self.map_maker_mode.handle_events_start()
            elif self.mode == "MAPMAKING":
                self.map_maker_mode.events()
                self.map_maker_mode.draw()


    def update(self):
        self.bullets.update()
        self.zombies.update((self.player.rect.x, self.player.rect.y))
        self.player.update()
        self.walls.update()


    def create(self):
        for row, tiles in enumerate(self.grid):
            for col,tile in enumerate(tiles):
                if tile == 1:
                    Wall(self,col,row)

        #spawns zombies at random locations
        for _ in range(2):
            x = random.randint(100, SCREEN_WIDTH - 100)
            y = random.randint(100, SCREEN_HEIGHT - 100)
            new_zombie = Zombie(x, y,self)
            self.zombies.add(new_zombie)



    def draw(self):#draws everything to the screen
        self.display.fill(WHITE)
        self.draw_grid()
        self.walls.draw(self.display)
        #self.all_sprites.draw(self.display)
        self.bullets.draw(self.display)
        self.display.blit(self.player.image, self.player.rect.topleft)
        self.toolbar.draw()
        self.zombies.draw(self.display)
        pygame.display.flip()

    def draw_grid(self):#draws the grid to the screen
        for x_pos in range(0,SCREEN_WIDTH,TILE_SIZE):
            pygame.draw.line(self.display,BLACK,(x_pos,0),(x_pos,SCREEN_HEIGHT),2)
        for y_pos in range(0,SCREEN_WIDTH,TILE_SIZE):
            pygame.draw.line(self.display,BLACK,(0,y_pos),(SCREEN_WIDTH,y_pos),2)

    def events(self):#checks for any events e.g(quit or player move)
        for event in pygame.event.get():
            self.toolbar.handle_events(event) # checks for tool bar events
            if event.type == pygame.QUIT:
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Getting the direction from the player to the mouse
                mx, my = pygame.mouse.get_pos()
                dx, dy = mx - self.player.rect.centerx, my - self.player.rect.centery
                # Calculating angle in degrees
                direction = pygame.math.Vector2(dx, dy).normalize()
                # Creating a new bullet and adding it to the bullets group
                new_bullet = Bullet(self.player.rect.centerx, self.player.rect.centery,direction, self.player.angle)
                self.bullets.add(new_bullet)

    def open_map(self):
        # Open a file dialog to select a map file to open
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        file_path = filedialog.askopenfilename(initialdir=os.path.join(os.getcwd(), "maps"), title="Select a Map", filetypes=[("Pickle Files", "*.pkl")])

        if file_path:
            # Load the map data from the selected file
            with open(file_path, 'rb') as f:
                self.grid = pickle.load(f)
                self.create()
    def quit(self): #quits the game and window
        pygame.quit()
        sys.exit()



class MenuMode:
    def __init__(self, game):
        self.game = game

    #MENU CODE
    def draw_menu(self):
        #set up text and font
        game.display.fill(WHITE)
        font = pygame.font.Font(None, 74)
        title_text = font.render('My Game', True, BLACK)
        font = pygame.font.Font(None, 50)
        play_text = font.render('Play', True, BLACK)
        map_maker_text = font.render('Map Maker', True, BLACK)
        # Calculate positions
        title_pos = (SCREEN_WIDTH // 2 - title_text.get_width() // 2, SCREEN_HEIGHT // 4 - title_text.get_height() // 2)
        play_pos = (SCREEN_WIDTH // 2 - play_text.get_width() // 2, SCREEN_HEIGHT // 2 - play_text.get_height() // 2)
        map_maker_pos = (SCREEN_WIDTH // 2 - map_maker_text.get_width() // 2, SCREEN_HEIGHT // 2 + map_maker_text.get_height())

        # Draw text on screen at calculated positions
        game.display.blit(title_text, title_pos)
        game.display.blit(play_text, play_pos)
        game.display.blit(map_maker_text, map_maker_pos)

        # Creating rectangles for button collision
        self.play_rect = pygame.Rect(play_pos[0], play_pos[1], play_text.get_width(), play_text.get_height())
        self.map_maker_rect = pygame.Rect(map_maker_pos[0], map_maker_pos[1], map_maker_text.get_width(), map_maker_text.get_height())
        self.game.toolbar.draw()
        pygame.display.flip()

    #checks for players decision in the menu
    def menu_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()

                # define the rectangles where your options are and check if they are clicked
                play_rect = pygame.Rect(SCREEN_WIDTH//2 - 70, SCREEN_HEIGHT//2 - 25, 140, 50)
                map_maker_rect = pygame.Rect(SCREEN_WIDTH//2 - 110, SCREEN_HEIGHT//2 + 55, 220, 50)
                # Check if user clicks on one of the choices using the rectangles created in draw_menu
                if self.play_rect.collidepoint((x, y)):
                    game.open_map()
                    game.mode = "PLAY"
                elif self.map_maker_rect.collidepoint((x, y)):
                    game.mode = "MAPMAKING_START"

class MapMakerMode:
    def __init__(self, game):
        self.game = game
        self.grid = [[0 for _ in range(SCREEN_WIDTH // TILE_SIZE)] for _ in range(SCREEN_HEIGHT // TILE_SIZE)]
        self.state = "START"

    def mapmaker_start(self):
        self.draw_mapmaker_start()
        pass

    def draw_mapmaker_start(self):
        self.game.display.fill(WHITE)

        font = pygame.font.Font(None, 50)
        new_map_text = font.render('Create New Map', True, BLACK)
        open_map_text = font.render('Open Existing Map', True, BLACK)

        self.game.display.blit(new_map_text, (SCREEN_WIDTH//2 - new_map_text.get_width()//2, SCREEN_HEIGHT//3 - new_map_text.get_height()//2))
        self.game.display.blit(open_map_text, (SCREEN_WIDTH//2 - open_map_text.get_width()//2, 2*SCREEN_HEIGHT//3 - open_map_text.get_height()//2))
        self.game.toolbar.draw()
        pygame.display.flip()

    def handle_events_start(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game.quit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()

                # define the rectangles for your options
                new_map_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//3 - 30, 400, 60)
                open_map_rect = pygame.Rect(SCREEN_WIDTH//2 - 200, 2*SCREEN_HEIGHT//3 - 30, 400, 60)

                if new_map_rect.collidepoint((x, y)):
                    self.game.mode = "MAPMAKING"
                    # Here proceed with new map creation
                elif open_map_rect.collidepoint((x, y)):
                    self.game.mode = "OPEN_MAP"
                    # Here proceed with opening an existing map

    def draw(self):
        self.game.display.fill(WHITE)
        self.game.draw_grid()
        self.draw_walls()
        self.game.toolbar.draw()
        pygame.display.flip()

    #loops through the walls if the wall is a 1 then it draws a wall
    def draw_walls(self):
        for y, row in enumerate(self.grid):
            for x, tile in enumerate(row):
                if tile == 1:
                    pygame.draw.rect(self.game.display, BLACK, (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))


    def events(self):
        for event in pygame.event.get():
            game.toolbar.handle_events(event) # checks for tool bar events
            if event.type == pygame.QUIT:
                self.game.quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:  # Press 's' to save
                    self.save_map()

        # Get the state of the mouse
        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]:  # If left mouse button is pressed
            x, y = pygame.mouse.get_pos()
            grid_x, grid_y = x // TILE_SIZE, y // TILE_SIZE
            self.grid[grid_y][grid_x] = 1  # Set to wall
        elif mouse_pressed[2]:  # If right mouse button is pressed
            x, y = pygame.mouse.get_pos()
            grid_x, grid_y = x // TILE_SIZE, y // TILE_SIZE
            self.grid[grid_y][grid_x] = 0  # Set to empty


    def save_map(self):
        # Ask user for the map name using a Tkinter input dialog
        root = tk.Tk()
        root.withdraw() # Hide the root window
        map_name = simpledialog.askstring("Input", "Please enter the map name:")

        with open(f"maps/{map_name}.pkl", 'wb') as f:
            pickle.dump(self.grid, f)

    def open_map(self):
        # Open a file dialog to select a map file to open
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        file_path = filedialog.askopenfilename(initialdir=os.path.join(os.getcwd(), "maps"), title="Select a Map", filetypes=[("Pickle Files", "*.pkl")])

        if file_path:
            # Load the map data from the selected file
            with open(file_path, 'rb') as f:
                self.grid = pickle.load(f)


game = game_main()
game.run_game()