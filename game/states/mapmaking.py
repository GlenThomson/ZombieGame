"""Tile-based map editor.

Two layers: the "floor" layer (every cell is a FloorType) and the "object"
layer (TileType — walls, doors, perks, etc., 0 = nothing). Tab toggles
which layer your clicks paint into. The floor palette is displayed when
the floor layer is active; the object palette otherwise.

Wall sprites are themed via wall_style (brick / concrete / wood / metal) —
press W to cycle while editing."""
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
    GOLD,
    MENU_TEXT,
)
from game import assets
from game.states.base import State
from game.ui.toolbar import MapMakerToolbar
from game.utils import adjusted_mouse_position
from game.world import map_loader
from game.world.tile import FloorType, FLOOR_SPRITES, WALL_STYLES

vector = pygame.math.Vector2


# Floor palette — mirrors FloorType enum order
FLOOR_PALETTE: list[tuple[str, FloorType]] = [
    ("concrete",          FloorType.CONCRETE),
    ("concrete bloodied", FloorType.CONCRETE_BLOODIED),
    ("wood",              FloorType.WOOD),
    ("brick",             FloorType.BRICK),
    ("metal",             FloorType.METAL),
    ("dirt",              FloorType.DIRT),
    ("asphalt",           FloorType.ASPHALT),
    ("carpet",            FloorType.CARPET),
    ("grass",             FloorType.GRASS),
]
WALL_STYLE_CYCLE = ["brick", "concrete", "wood", "metal"]


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
        self.floor_grid: list[list[int]] = []
        self.wall_style: str = "brick"
        self.current_layer: str = "object"   # "object" | "floor"
        self.floor_palette_idx: int = 0
        self.item_number = self.toolbar.pop_up_menu.item_number
        self._tk_root = None
        self.editing_filename: str | None = editing
        self.door_costs: dict = {}
        self.wall_buy_weapons: dict = {}
        self.perk_machine_perks: dict = {}

        if editing:
            self._load_existing(editing)
        else:
            self._init_blank_map()

    def _init_blank_map(self):
        """No file dialog — ask for size, then create a blank grid."""
        self._tk_root = tk.Tk()
        self._tk_root.withdraw()
        size = simpledialog.askstring(
            "New Map", "Map size (e.g. 30x20):", initialvalue="30x20",
        )
        self._tk_root.destroy()
        self._tk_root = None
        if not size:
            self.app.switch("menu")
            return
        try:
            w_str, h_str = size.lower().split("x")
            w = max(8, min(120, int(w_str.strip())))
            h = max(8, min(80, int(h_str.strip())))
        except (ValueError, AttributeError):
            self.app.switch("menu")
            return
        self.map_width = w * TILE_SIZE
        self.map_height = h * TILE_SIZE
        self.grid = [[0 for _ in range(w)] for _ in range(h)]
        self.floor_grid = [[int(FloorType.CONCRETE) for _ in range(w)] for _ in range(h)]
        # Outer wall
        for y in range(h):
            self.grid[y][0] = 1
            self.grid[y][w - 1] = 1
        for x in range(w):
            self.grid[0][x] = 1
            self.grid[h - 1][x] = 1

    def _load_existing(self, filename: str):
        data = map_loader.load(f"maps/{filename}")
        self.grid = data["grid"]
        self.background_image_path = data["background_image_path"]
        self.door_costs = dict(data.get("door_costs") or {})
        self.wall_buy_weapons = dict(data.get("wall_buy_weapons") or {})
        self.perk_machine_perks = dict(data.get("perk_machine_perks") or {})
        self.wall_style = data.get("wall_style", "brick")
        loaded_floor = data.get("floor_grid")
        if loaded_floor is None:
            # Legacy map: synthesize a floor grid (all concrete).
            self.floor_grid = [
                [int(FloorType.CONCRETE) for _ in row] for row in self.grid
            ]
        else:
            self.floor_grid = loaded_floor
        self.map_width = len(self.grid[0]) * TILE_SIZE
        self.map_height = len(self.grid) * TILE_SIZE
        if self.background_image_path and os.path.isfile(self.background_image_path):
            try:
                self.background_image = pygame.image.load(self.background_image_path).convert()
            except pygame.error:
                self.background_image = None

    # ---- per-frame ----

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                self.current_layer = "floor" if self.current_layer == "object" else "object"
                return
            if event.key == pygame.K_w:
                idx = WALL_STYLE_CYCLE.index(self.wall_style) if self.wall_style in WALL_STYLE_CYCLE else 0
                self.wall_style = WALL_STYLE_CYCLE[(idx + 1) % len(WALL_STYLE_CYCLE)]
                return
            if self.current_layer == "floor" and pygame.K_1 <= event.key <= pygame.K_9:
                idx = event.key - pygame.K_1
                if 0 <= idx < len(FLOOR_PALETTE):
                    self.floor_palette_idx = idx
                return

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
                self._paint(active=True)
            elif event.button == 3:
                self._paint(active=False)

    def _paint(self, active: bool):
        if not self.grid:
            return
        x, y = adjusted_mouse_position(int(self.offset.x), int(self.offset.y))
        gx, gy = x // TILE_SIZE, y // TILE_SIZE
        if not (0 <= gy < len(self.grid) and 0 <= gx < len(self.grid[0])):
            return

        if self.current_layer == "floor":
            ftype = (
                FLOOR_PALETTE[self.floor_palette_idx][1]
                if active else FloorType.CONCRETE
            )
            self.floor_grid[gy][gx] = int(ftype)
        else:
            value = self.item_number if active else 0
            if value == 4 and any(4 in row for row in self.grid):
                return
            self.grid[gy][gx] = value

    def _save_map(self):
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
            floor_grid=self.floor_grid,
            wall_style=self.wall_style,
        )
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
        data = map_loader.load(path)
        self.grid = data["grid"]
        self.door_costs = dict(data.get("door_costs") or {})
        self.wall_buy_weapons = dict(data.get("wall_buy_weapons") or {})
        self.perk_machine_perks = dict(data.get("perk_machine_perks") or {})
        self.wall_style = data.get("wall_style", "brick")
        loaded_floor = data.get("floor_grid")
        if loaded_floor is None:
            self.floor_grid = [
                [int(FloorType.CONCRETE) for _ in row] for row in self.grid
            ]
        else:
            self.floor_grid = loaded_floor
        self.map_width = len(self.grid[0]) * TILE_SIZE
        self.map_height = len(self.grid) * TILE_SIZE
        bg = data.get("background_image_path")
        self.background_image_path = bg
        if bg and os.path.isfile(bg):
            try:
                self.background_image = pygame.image.load(bg).convert()
            except pygame.error:
                self.background_image = None
        self.editing_filename = os.path.basename(path)

    def update(self):
        self._scroll_camera()

    def _scroll_camera(self):
        keys = pygame.key.get_pressed()
        # Use arrow keys for scrolling so WASD doesn't trip wall-style toggle.
        if keys[pygame.K_LEFT]:
            self.offset.x = min(self.offset.x + self.scroll_speed, 0)
        if keys[pygame.K_RIGHT]:
            self.offset.x = max(self.offset.x - self.scroll_speed, -self.map_width + SCREEN_WIDTH)
        if keys[pygame.K_UP]:
            self.offset.y = min(self.offset.y + self.scroll_speed, 0)
        if keys[pygame.K_DOWN]:
            self.offset.y = max(self.offset.y - self.scroll_speed, -self.map_height + SCREEN_HEIGHT)

    def draw(self):
        self.surface.fill(WHITE)
        # Floor tiles first
        self._draw_floors()
        # Then a thin grid line pass for legibility
        self._draw_grid_lines()
        # Then objects (walls, machines, etc.) coloured to match game appearance
        self._draw_objects()
        self.toolbar.draw()
        self._draw_status_bar()
        pygame.display.flip()

    def _draw_floors(self):
        if not self.floor_grid:
            return
        for y, row in enumerate(self.floor_grid):
            for x, ftype in enumerate(row):
                png = FLOOR_SPRITES.get(int(ftype))
                if png is None:
                    continue
                img = assets.image(os.path.join("tiles", png))
                self.surface.blit(
                    img, (x * TILE_SIZE + self.offset.x, y * TILE_SIZE + self.offset.y),
                )

    def _draw_grid_lines(self):
        h = len(self.grid) * TILE_SIZE
        w = len(self.grid[0]) * TILE_SIZE if self.grid else 0
        for x in range(0, w + 1, TILE_SIZE):
            pygame.draw.line(
                self.surface, (40, 40, 40),
                (x + self.offset.x, self.offset.y),
                (x + self.offset.x, h + self.offset.y), 1,
            )
        for y in range(0, h + 1, TILE_SIZE):
            pygame.draw.line(
                self.surface, (40, 40, 40),
                (self.offset.x, y + self.offset.y),
                (w + self.offset.x, y + self.offset.y), 1,
            )

    def _draw_objects(self):
        # Wall colour reflects the chosen style for visual feedback.
        wall_png = WALL_STYLES.get(self.wall_style, "wall_brick.png")
        wall_img = None
        wall_path = os.path.join("assets", "images", "tiles", wall_png)
        if os.path.isfile(wall_path):
            wall_img = assets.image(os.path.join("tiles", wall_png))
        styles = {
            2: (LIGHTGREY, None),                  # barb wire
            3: (RED, None),                        # zombie spawn
            4: (PURPLE, None),                     # player spawn
            5: ((110, 60, 20), GOLD),              # closed door
            6: ((60, 35, 15), (120, 80, 40)),      # open door
            7: ((140, 100, 50), (200, 180, 200)),  # window
            8: ((40, 40, 50), GOLD),               # wall buy
            9: ((220, 0, 0), (220, 220, 220)),     # perk machine
            10: ((60, 30, 10), GOLD),              # mystery box
            11: ((200, 160, 0), (255, 230, 80)),   # pack-a-punch
            12: ((50, 50, 60), (255, 220, 80)),    # power switch
            13: ((60, 60, 60), (200, 200, 200)),   # flogger trap
            14: ((180, 60, 0), (255, 130, 0)),     # fire trap
        }
        for y, row in enumerate(self.grid):
            for x, tile in enumerate(row):
                rect = (
                    x * TILE_SIZE + self.offset.x,
                    y * TILE_SIZE + self.offset.y,
                    TILE_SIZE, TILE_SIZE,
                )
                if tile == 1:
                    if wall_img is not None:
                        self.surface.blit(wall_img, rect[:2])
                    else:
                        pygame.draw.rect(self.surface, BLACK, rect)
                    continue
                style = styles.get(tile)
                if style is None:
                    continue
                fill, border = style
                pygame.draw.rect(self.surface, fill, rect)
                if border is not None:
                    pygame.draw.rect(self.surface, border, rect, 2)

    def _draw_status_bar(self):
        font = pygame.font.Font(None, 22)
        bar = pygame.Surface((SCREEN_WIDTH, 26), pygame.SRCALPHA)
        bar.fill((0, 0, 0, 180))
        self.surface.blit(bar, (0, SCREEN_HEIGHT - 26))
        if self.current_layer == "floor":
            label = (
                f"FLOOR mode  [TAB to switch]  "
                f"painting: {FLOOR_PALETTE[self.floor_palette_idx][0]}  "
                f"(1-9 = pick)  W = wall style ({self.wall_style})"
            )
        else:
            label = (
                f"OBJECT mode  [TAB to switch]  W = wall style ({self.wall_style})"
            )
        text = font.render(label, True, GOLD)
        self.surface.blit(text, (10, SCREEN_HEIGHT - 22))
