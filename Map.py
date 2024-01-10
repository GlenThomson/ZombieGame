import os
import pickle
import tkinter as tk
from tkinter import filedialog
import pygame

from Game_settings import *


class Map:
    def __init__(self, game):
        # Open a file dialog to select a map file to open
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        file_path = filedialog.askopenfilename(initialdir=os.path.join(os.getcwd(), "maps"), title="Select a Map",
                                               filetypes=[("Pickle Files", "*.pkl")])

        if file_path:
            # Load the map data from the selected file
            with open(file_path, 'rb') as f:
                game.grid = pickle.load(f)
                print("hello")
        print(game.grid)
        self.map_height = 0
        self.map_width = 0
        self.map_name = ""


class Camera:
    def __init__(self, width, height, game):
        self.camera = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.width = width
        self.height = height
        self.game = game
        self.pos = (0,0)
    # applys the ajustmets to all the sprites to make it sedem like camera is moving
    def apply(self, entity):
        return entity.rect.move(self.camera.topleft)

    def update(self, target):

        x = self.camera.x
        y = self.camera.y
        self.pos = (x,y)
        # Calculate the boundaries where the camera should stop
        min_x = -self.width + SCREEN_WIDTH
        max_x = 0
        min_y = -self.height + SCREEN_HEIGHT
        max_y = 0

        # Calculate the target position considering the camera's center
        target_x = target.rect.centerx - SCREEN_WIDTH // 2
        target_y = target.rect.centery - SCREEN_HEIGHT // 2

        # Ensure the camera doesn't go beyond the map edges
        x = max(min_x, min(max_x, -target_x))
        y = max(min_y, min(max_y, -target_y))
        self.camera = pygame.Rect(x, y, self.width, self.height)
