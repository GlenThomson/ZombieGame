import tkinter as tk
from tkinter import filedialog
from tkinter import simpledialog
import pickle
import os
from Game_settings import *
import pygame


class Map:
    def __init__(self,game):
        # Open a file dialog to select a map file to open
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        file_path = filedialog.askopenfilename(initialdir=os.path.join(os.getcwd(), "maps"), title="Select a Map", filetypes=[("Pickle Files", "*.pkl")])

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
    def __init__(self,width ,height,game):
        self.camera = pygame.Rect(0,0,SCREEN_WIDTH,SCREEN_HEIGHT)
        self.width = width
        self.height = height
        self.game = game

    def apply(self,entity):
        return entity.rect.move(self.camera.topleft)

    def update(self, target):
        x = self.camera.x
        y = self.camera.y
        #first checks to see if player is close to edge of map and stops camera moving if it is
        if  target.rect.x - int(SCREEN_WIDTH/2) >=0 and target.rect.x - self.game.map_width +int(SCREEN_WIDTH/2) <=0:
            x = -target.rect.centerx + int(SCREEN_WIDTH/2)

        #first checks to see if player is close to edge of map and stops camera moving if it is
        if  target.rect.y - int(SCREEN_HEIGHT/2) >=0 and target.rect.y - self.game.map_height +int(SCREEN_HEIGHT/2) <=0:
            y = -target.rect.centery + int(SCREEN_HEIGHT/2)
        self.camera = pygame.Rect(x,y,self.width,self.height)

