import pickle
import os
import tkinter as tk
from tkinter import filedialog

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