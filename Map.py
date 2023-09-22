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
    def __init__(self):
        self.camera = pygame.Rect(0,0,SCREEN_WIDTH,SCREEN_HEIGHT)