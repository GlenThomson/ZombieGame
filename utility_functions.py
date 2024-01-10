import pickle
import os
import tkinter as tk
from tkinter import filedialog
import pygame
import sys

def load_map_from_file(initial_directory=None):
    """
    Opens a file dialog to select a map file to open, and then returns the loaded data.
    If no file is selected, returns None.
    """
    root = tk.Tk()
    root.withdraw()  # Hide the root window

    if not initial_directory:
        initial_directory = os.path.join(os.getcwd(), "maps")

    file_path = filedialog.askopenfilename(initialdir=initial_directory, title="Select a Map", filetypes=[("Pickle Files", "*.pkl")])

    if not file_path:
        return None

    with open(file_path, 'rb') as f:
        return pickle.load(f)

# Create a function to get the adjusted mouse position
def get_adjusted_mouse_position(offset_x=0, offset_y=0):
    mouse_x, mouse_y = pygame.mouse.get_pos()
    adjusted_x = mouse_x - offset_x
    adjusted_y = mouse_y - offset_y
    return adjusted_x, adjusted_y



def quit_application(): #quits the game and window
    pygame.quit()
    sys.exit()