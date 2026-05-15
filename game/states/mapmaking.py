"""Map editor — paint walls / barb wire / spawns onto a grid, then save."""
import os
import pickle
import tkinter as tk
from tkinter import filedialog, simpledialog

import pygame

from settings import (
    TILE_SIZE,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    BLACK,
    WHITE,
    LIGHTGREY,
    RED,
    PURPLE,
)
from game.states.base import State
from game.ui.toolbar import MapMakerToolbar
from game.utils import adjusted_mouse_position
from game.world import map_loader

vector = pygame.math.Vector2


class MapMakingState(State):
    def on_enter(self, **kwargs):
        self.toolbar = MapMakerToolbar(self.surface)
        self.offset = vector(0, 0)
        self.scroll_speed = 5
        self.background_image_path: str | None = None
        self.background_image: pygame.Surface | None = None
        self.map_width = 0
        self.map_height = 0
        self.grid: list[list[int]] = []
        self.item_number = self.toolbar.pop_up_menu.item_number
        self._tk_root = None

        self._select_background_and_size()
        self._create_outer_wall()

    def _select_background_and_size(self):
        self._tk_root = tk.Tk()
        self._tk_root.withdraw()
        path = filedialog.askopenfilename(
            initialdir=os.getcwd(),
            title="Select Background Image",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")],
        )
        self._tk_root.destroy()
        self._tk_root = None
        if not path:
            self.app.switch("menu")
            return
        self.background_image_path = path
        self.background_image = pygame.image.load(path).convert()
        self.map_width = self.background_image.get_width()
        self.map_height = self.background_image.get_height()
        self.grid = [
            [0 for _ in range(self.map_width // TILE_SIZE)]
            for _ in range(self.map_height // TILE_SIZE)
        ]

    def _create_outer_wall(self):
        if not self.grid:
            return
        h = len(self.grid)
        w = len(self.grid[0])
        for y in range(h):
            for x in range(w):
                if x == 0 or y == 0 or x == w - 1 or y == h - 1:
                    self.grid[y][x] = 1

    # ---- per-frame ----

    def handle_event(self, event):
        self.toolbar.handle_event(
            event,
            on_menu=lambda: self.app.switch("menu"),
            on_save=self._save_map,
            on_open=self._open_map,
        )
        sel = self.toolbar.pop_up_menu.handle_event(event)
        if sel:
            self.item_number = self.toolbar.pop_up_menu.item_number
            return
        if self.toolbar.button_clicked:
            self.toolbar.button_clicked = False
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self._paint_tile(self.item_number)
            elif event.button == 3:
                self._paint_tile(0)

    def _paint_tile(self, value: int):
        if not self.grid:
            return
        x, y = adjusted_mouse_position(int(self.offset.x), int(self.offset.y))
        gx, gy = x // TILE_SIZE, y // TILE_SIZE
        if not (0 <= gy < len(self.grid) and 0 <= gx < len(self.grid[0])):
            return
        # Don't allow two player spawns.
        if value == 4 and any(4 in row for row in self.grid):
            return
        self.grid[gy][gx] = value

    def _save_map(self):
        self._tk_root = tk.Tk()
        self._tk_root.withdraw()
        name = simpledialog.askstring("Input", "Please enter the map name:")
        self._tk_root.destroy()
        self._tk_root = None
        if not name:
            return
        map_loader.save(self.grid, self.background_image_path, name)

    def _open_map(self):
        self._tk_root = tk.Tk()
        self._tk_root.withdraw()
        path = filedialog.askopenfilename(
            initialdir=os.path.join(os.getcwd(), "maps"),
            title="Select a Map",
            filetypes=[("Pickle Files", "*.pkl")],
        )
        self._tk_root.destroy()
        self._tk_root = None
        if not path:
            return
        with open(path, "rb") as f:
            data = pickle.load(f)
        self.grid = data["grid"] if isinstance(data, dict) else data

    def update(self):
        self._scroll_camera()

    def _scroll_camera(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.offset.x = min(self.offset.x + self.scroll_speed, 0)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.offset.x = max(self.offset.x - self.scroll_speed, -self.map_width + SCREEN_WIDTH)
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.offset.y = min(self.offset.y + self.scroll_speed, 0)
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.offset.y = max(self.offset.y - self.scroll_speed, -self.map_height + SCREEN_HEIGHT)

    def draw(self):
        if self.background_image:
            self.surface.blit(self.background_image, (self.offset.x, self.offset.y))
        else:
            self.surface.fill(WHITE)
        self._draw_grid_lines()
        self._draw_items()
        self.toolbar.draw()
        pygame.display.flip()

    def _draw_grid_lines(self):
        for x in range(0, self.map_width, TILE_SIZE):
            pygame.draw.line(
                self.surface, BLACK, (x + self.offset.x, self.offset.y),
                (x + self.offset.x, self.map_height + self.offset.y), 1,
            )
        for y in range(0, self.map_height, TILE_SIZE):
            pygame.draw.line(
                self.surface, BLACK, (self.offset.x, y + self.offset.y),
                (self.map_width + self.offset.x, y + self.offset.y), 1,
            )

    def _draw_items(self):
        # Map tile-int → (fill, border)
        # Keep in sync with TileType: 1=WALL, 2=BARB, 3=ZSPAWN, 4=PSPAWN,
        # 5=DOOR_CLOSED, 6=DOOR_OPEN, 7=WINDOW, 8=WALL_BUY.
        styles = {
            1: (BLACK, None),
            2: (LIGHTGREY, None),
            3: (RED, None),
            4: (PURPLE, None),
            5: ((110, 60, 20), (255, 215, 0)),     # closed door
            6: ((60, 35, 15), (120, 80, 40)),      # open door (dimmer)
            7: ((140, 100, 50), (200, 180, 200)),  # window
            8: ((40, 40, 50), (255, 215, 0)),      # wall buy
            9: ((220, 0, 0), (220, 220, 220)),     # perk machine (Juggernog red)
        }
        for y, row in enumerate(self.grid):
            for x, tile in enumerate(row):
                style = styles.get(tile)
                if style is None:
                    continue
                fill, border = style
                rect = (
                    x * TILE_SIZE + self.offset.x,
                    y * TILE_SIZE + self.offset.y,
                    TILE_SIZE,
                    TILE_SIZE,
                )
                pygame.draw.rect(self.surface, fill, rect)
                if border is not None:
                    pygame.draw.rect(self.surface, border, rect, 2)
