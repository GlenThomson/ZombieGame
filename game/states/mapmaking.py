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
    def on_enter(self, *, editing: str | None = None, **kwargs):
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
        # When editing an existing map, save defaults to overwriting it
        # without prompting (Save) and we also keep its metadata.
        self.editing_filename: str | None = editing
        self.door_costs: dict = {}
        self.wall_buy_weapons: dict = {}
        self.perk_machine_perks: dict = {}

        if editing:
            self._load_existing(editing)
        else:
            self._select_background_and_size()
            self._create_outer_wall()

    def _load_existing(self, filename: str):
        data = map_loader.load(f"maps/{filename}")
        self.grid = data["grid"]
        self.background_image_path = data["background_image_path"]
        self.door_costs = dict(data.get("door_costs") or {})
        self.wall_buy_weapons = dict(data.get("wall_buy_weapons") or {})
        self.perk_machine_perks = dict(data.get("perk_machine_perks") or {})
        if self.background_image_path and os.path.isfile(self.background_image_path):
            self.background_image = pygame.image.load(self.background_image_path).convert()
            self.map_width = self.background_image.get_width()
            self.map_height = self.background_image.get_height()
        else:
            # No background image — sizes derive from the grid itself.
            self.background_image = None
            self.map_width = len(self.grid[0]) * TILE_SIZE if self.grid else SCREEN_WIDTH
            self.map_height = len(self.grid) * TILE_SIZE if self.grid else SCREEN_HEIGHT

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
        # When editing an existing map, default to overwriting it without
        # prompting (the user already chose this map). Pre-fill the dialog
        # with the existing name when prompting.
        default_name = self.editing_filename[:-4] if self.editing_filename else ""
        self._tk_root = tk.Tk()
        self._tk_root.withdraw()
        name = simpledialog.askstring(
            "Save map", "Map name:", initialvalue=default_name,
        )
        self._tk_root.destroy()
        self._tk_root = None
        if not name:
            return
        map_loader.save(
            self.grid,
            self.background_image_path,
            name,
            door_costs=self.door_costs,
            wall_buy_weapons=self.wall_buy_weapons,
            perk_machine_perks=self.perk_machine_perks,
        )
        # Now editing the saved file (so a subsequent Save defaults to it).
        self.editing_filename = f"{name}.pkl"

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
        # Use map_loader so we get all the metadata too.
        data = map_loader.load(path)
        self.grid = data["grid"]
        self.door_costs = dict(data.get("door_costs") or {})
        self.wall_buy_weapons = dict(data.get("wall_buy_weapons") or {})
        self.perk_machine_perks = dict(data.get("perk_machine_perks") or {})
        bg = data.get("background_image_path")
        if bg and os.path.isfile(bg):
            self.background_image_path = bg
            self.background_image = pygame.image.load(bg).convert()
            self.map_width = self.background_image.get_width()
            self.map_height = self.background_image.get_height()
        self.editing_filename = os.path.basename(path)

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
            10: ((60, 30, 10), (255, 215, 0)),     # mystery box
            11: ((200, 160, 0), (255, 230, 80)),   # pack-a-punch
            12: ((50, 50, 60), (255, 220, 80)),    # power switch
            13: ((60, 60, 60), (200, 200, 200)),   # flogger trap
            14: ((180, 60, 0), (255, 130, 0)),     # fire trap
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
