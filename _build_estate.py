"""Build the "estate" map — a big multi-building map in the style of `real`:
hand-composed background art (grass photo + tiled floors + wall-strip art +
furniture) with INVISIBLE_WALL collision generated from the same plan.

Outputs:
  assets/images/estate_bg.png   the composed background
  maps/estate.pkl               grid (invisible walls, doors, windows,
                                perks, box, PaP, power, traps, spawns)
  _render_estate.png            bg + collision overlay for eyeballing

Run: python _build_estate.py
"""
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
pygame.init()
pygame.display.set_mode((100, 100))

from game.world import map_loader
from game.world.tile import TileType

T = TileType
TILE = 40
W, H = 64, 44                      # tiles
PX_W, PX_H = W * TILE, H * TILE    # 2560 x 1760

TILES_DIR = r"C:/Users/glent/OneDrive/Desktop/gametiles"
WALLS_DIR = os.path.join(TILES_DIR, "Tilesets", "Walls")
OBJS_DIR = os.path.join(TILES_DIR, "Tilesets", "house_objects")
GRASS_PATH = os.path.join(TILES_DIR, "sprBackground",
                          "5e33c0d9-a609-48fc-a978-cf46374fe105.png")

# Straight wall strips per material (chosen from the classified contact
# sheet: H pieces ~341x99, V drawn by rotating the H piece).
WALL_STRIPS = {
    "wood":     "walls_0005_Layer-6.png",    # light wood
    "concrete": "walls_0031_Layer-32.png",   # grey concrete
    "brick":    "walls_0048_Layer-49.png",   # brown brick
}

FURNITURE = {
    "couch_blue":   "objects_house_0004_Layer-5.png",
    "couch_red":    "objects_house_0006_Layer-7.png",
    "armchair_tan": "objects_house_0010_Layer-11.png",
    "armchair_red": "objects_house_0013_Layer-14.png",
    "bed_double":   "objects_house_0033_Layer-34.png",
    "bed_double2":  "objects_house_0035_Layer-36.png",
    "bed_single":   "objects_house_0036_Layer-37.png",
    "table_rect":   "objects_house_0041_Layer-42.png",
    "table_oval":   "objects_house_0045_Layer-46.png",
    "dresser":      "objects_house_0049_Layer-50.png",
    "plant1":       "objects_house_0054_Layer-55.png",
    "plant2":       "objects_house_0055_Layer-56.png",
    "tuft1":        "objects_house_0056_Layer-57.png",
}


def _load(path):
    return pygame.image.load(path).convert_alpha()


class EstateBuilder:
    def __init__(self):
        self.bg = pygame.Surface((PX_W, PX_H))
        self.grid = [[int(T.EMPTY)] * W for _ in range(H)]
        self.door_costs: dict = {}
        self.wall_buys: dict = {}
        self.perks: dict = {}
        # Pre-scale wall strips to 40px thickness.
        self.strips = {}
        for mat, fname in WALL_STRIPS.items():
            piece = _load(os.path.join(WALLS_DIR, fname))
            w, h = piece.get_size()
            scale_w = max(TILE, int(w * (TILE / h)))
            self.strips[mat] = pygame.transform.smoothscale(piece, (scale_w, TILE))
        self.furn = {k: _load(os.path.join(OBJS_DIR, v)) for k, v in FURNITURE.items()}

    # ---------- art helpers ----------

    def lay_grass(self):
        grass = _load(GRASS_PATH)
        # Crop the most uniform region (right half avoids the horses) and
        # scale to cover the whole canvas.
        crop = grass.subsurface(pygame.Rect(1400, 300, 2400, 2100))
        self.bg.blit(pygame.transform.smoothscale(crop, (PX_W, PX_H)), (0, 0))

    def lay_floor(self, x0, y0, x1, y1, texture_path, tex_tiles=4):
        """Tile a floor texture across tile-rect [x0..x1) x [y0..y1)."""
        tex = _load(texture_path)
        side = TILE * tex_tiles
        tex = pygame.transform.smoothscale(tex, (side, side))
        area = pygame.Rect(x0 * TILE, y0 * TILE, (x1 - x0) * TILE, (y1 - y0) * TILE)
        prev_clip = self.bg.get_clip()
        self.bg.set_clip(area)
        ty = area.y
        while ty < area.bottom:
            tx = area.x
            while tx < area.right:
                self.bg.blit(tex, (tx, ty))
                tx += side
            ty += side
        self.bg.set_clip(prev_clip)

    def _wall_cell_art(self, mat, x, y, vertical):
        strip = self.strips[mat]
        L = strip.get_width()
        if vertical:
            strip = pygame.transform.rotate(strip, 90)
            off = (y * 53) % max(1, L - TILE)
            self.bg.blit(strip, (x * TILE, y * TILE),
                         area=pygame.Rect(0, off, TILE, TILE))
        else:
            off = (x * 53) % max(1, L - TILE)
            self.bg.blit(strip, (x * TILE, y * TILE),
                         area=pygame.Rect(off, 0, TILE, TILE))

    def wall_h(self, mat, x0, x1, y, skip=()):
        """Horizontal wall run, tiles x0..x1 inclusive. `skip` cells get no
        art and no collision (doorways / windows handled separately)."""
        for x in range(x0, x1 + 1):
            if x in skip:
                continue
            self._wall_cell_art(mat, x, y, vertical=False)
            self.grid[y][x] = int(T.INVISIBLE_WALL)

    def wall_v(self, mat, x, y0, y1, skip=()):
        for y in range(y0, y1 + 1):
            if y in skip:
                continue
            self._wall_cell_art(mat, x, y, vertical=True)
            self.grid[y][x] = int(T.INVISIBLE_WALL)

    def place_furniture(self, name, x_tile, y_tile, tiles_wide, *,
                        block=True, rotate=0):
        """Paste furniture art scaled to `tiles_wide` tiles wide at the tile
        position; mark its (rounded-down) footprint blocking."""
        img = self.furn[name]
        if rotate:
            img = pygame.transform.rotate(img, rotate)
        w, h = img.get_size()
        out_w = tiles_wide * TILE
        out_h = int(h * out_w / w)
        img = pygame.transform.smoothscale(img, (out_w, out_h))
        px, py = x_tile * TILE, y_tile * TILE
        self.bg.blit(img, (px, py))
        if block:
            for ty in range(y_tile, min(H, y_tile + max(1, out_h // TILE))):
                for tx in range(x_tile, min(W, x_tile + tiles_wide)):
                    if self.grid[ty][tx] == int(T.EMPTY):
                        self.grid[ty][tx] = int(T.INVISIBLE_WALL)

    # ---------- grid helpers ----------

    def set(self, x, y, t):
        self.grid[y][x] = int(t)

    def door(self, cells, cost):
        for x, y in cells:
            self.grid[y][x] = int(T.DOOR_CLOSED)
            self.door_costs[(x, y)] = cost

    def window(self, x, y):
        self.grid[y][x] = int(T.WINDOW)

    def perk(self, x, y, name):
        self.grid[y][x] = int(T.PERK_MACHINE)
        self.perks[(x, y)] = name

    def wall_buy(self, x, y, weapon):
        self.grid[y][x] = int(T.WALL_BUY)
        self.wall_buys[(x, y)] = weapon


def main():
    b = EstateBuilder()
    b.lay_grass()

    FLOOR_WOOD = os.path.join("assets", "images", "imported", "floorwood.png")
    FLOOR_CONCRETE = os.path.join("assets", "images", "tiles", "floor_concrete.png")
    FLOOR_BRICK = os.path.join("assets", "images", "tiles", "floor_brick.png")

    # ================= MANOR (wood) — x6..30, y6..26 =================
    b.lay_floor(7, 7, 30, 26, FLOOR_WOOD, tex_tiles=2)
    # patio path between manor and garage (brick path)
    b.lay_floor(31, 17, 38, 23, FLOOR_BRICK, tex_tiles=1)
    # garage floor (concrete)
    b.lay_floor(39, 9, 58, 20, FLOOR_CONCRETE, tex_tiles=1)
    # shed floor
    b.lay_floor(41, 27, 56, 38, FLOOR_WOOD, tex_tiles=2)

    # Manor exterior walls (windows are gaps with WINDOW tiles)
    b.wall_h("wood", 6, 30, 6, skip=(9, 14, 22, 27))       # north
    for x in (9, 14, 22, 27):
        b.window(x, 6)
    b.wall_h("wood", 6, 30, 26, skip=(10, 11, 21))         # south (door + window)
    b.window(21, 26)
    b.door([(10, 26), (11, 26)], 1000)                     # south exit
    b.wall_v("wood", 6, 6, 26, skip=(9, 13, 20, 23))       # west
    for y in (9, 13, 20, 23):
        b.window(6, y)
    b.wall_v("wood", 30, 6, 26, skip=(20, 21))             # east (door)
    b.door([(30, 20), (30, 21)], 1000)                     # east exit → patio

    # Manor internal walls
    b.wall_v("wood", 18, 6, 26, skip=(10, 11))             # west|east split
    b.door([(18, 10), (18, 11)], 750)                      # living → bedroom
    b.wall_h("wood", 6, 18, 17, skip=(11, 12))             # living | dining
    b.door([(11, 17), (12, 17)], 750)
    b.wall_h("wood", 18, 30, 16, skip=(23, 24))            # bedroom | kitchen
    b.door([(23, 16), (24, 16)], 1000)

    # ================= GARAGE (concrete) — x38..58, y8..20 =================
    b.wall_h("concrete", 38, 58, 8, skip=(44, 51))
    b.window(44, 8)
    b.window(51, 8)
    b.wall_h("concrete", 38, 58, 20, skip=(48,))
    b.window(48, 20)
    b.wall_v("concrete", 38, 8, 20, skip=(13, 14))
    b.door([(38, 13), (38, 14)], 1250)                     # west door ← patio
    b.wall_v("concrete", 58, 8, 20, skip=(12, 16))
    b.window(58, 12)
    b.window(58, 16)

    # ================= SHED (brick) — x40..56, y26..38 =================
    b.wall_h("brick", 40, 56, 26, skip=(47, 48))
    b.door([(47, 26), (48, 26)], 1500)                     # north door
    b.wall_h("brick", 40, 56, 38, skip=(45, 52))
    b.window(45, 38)
    b.window(52, 38)
    b.wall_v("brick", 40, 26, 38, skip=(32,))
    b.window(40, 32)
    b.wall_v("brick", 56, 26, 38, skip=(33,))
    b.window(56, 33)

    # ================= Map border =================
    for x in range(W):
        b.set(x, 0, T.INVISIBLE_WALL)
        b.set(x, H - 1, T.INVISIBLE_WALL)
    for y in range(H):
        b.set(0, y, T.INVISIBLE_WALL)
        b.set(W - 1, y, T.INVISIBLE_WALL)

    # ================= Furniture =================
    # Living room (start, x6..18 y6..17)
    b.place_furniture("couch_blue", 8, 8, 3)
    b.place_furniture("armchair_tan", 13, 8, 2)
    b.place_furniture("table_oval", 10, 12, 2)
    b.place_furniture("plant1", 16, 15, 1, block=False)
    # Dining (x6..18 y17..26)
    b.place_furniture("table_rect", 10, 20, 4)
    b.place_furniture("dresser", 7, 24, 2)
    b.place_furniture("plant2", 16, 18, 1, block=False)
    # Bedroom (x18..30 y6..16)
    b.place_furniture("bed_double", 20, 8, 3)
    b.place_furniture("bed_single", 26, 8, 2)
    b.place_furniture("dresser", 27, 13, 2)
    # Kitchen (x18..30 y16..26)
    b.place_furniture("table_rect", 21, 19, 3)
    b.place_furniture("dresser", 27, 23, 2)
    b.place_furniture("plant1", 19, 24, 1, block=False)
    # Garage — mostly open (power room)
    b.place_furniture("dresser", 54, 10, 2)
    b.place_furniture("couch_red", 41, 17, 3)
    # Shed
    b.place_furniture("dresser", 42, 35, 2)
    b.place_furniture("table_oval", 50, 30, 2)
    # Yard greenery (visual only)
    for px, py in ((3, 3), (33, 3), (60, 4), (3, 38), (33, 40),
                   (60, 40), (34, 28), (3, 28), (20, 39), (59, 23)):
        b.place_furniture("tuft1", px, py, 2, block=False)
    b.place_furniture("plant2", 33, 12, 1, block=False)
    b.place_furniture("plant1", 35, 25, 1, block=False)

    # ================= Gameplay tiles =================
    # Player spawns — living room
    for sx, sy in ((9, 10), (15, 10), (9, 15), (15, 15)):
        b.set(sx, sy, T.PLAYER_SPAWN)
    # Perks
    b.perk(7, 11, "Quick Revive")          # living room (free-ish start perk)
    b.perk(16, 25, "Juggernog")            # dining
    b.perk(57, 18, "Speed Cola")           # garage
    b.perk(55, 36, "Double Tap")           # shed
    b.perk(36, 30, "Stamin-Up")            # yard, outside shed NW corner
    b.perk(39, 16, "Mule Kick")            # garage, south of the west door
    # Wall buys
    b.wall_buy(16, 7, "Shotgun")           # living room north wall
    b.wall_buy(7, 18, "SMG")               # dining west wall
    b.wall_buy(39, 9, "AK74u")             # garage NW inner corner
    b.wall_buy(41, 28, "Galil")            # shed NW inner corner
    # Mystery box — bedroom; PaP — shed; power — garage
    b.set(28, 10, T.MYSTERY_BOX)
    b.set(51, 35, T.PACK_A_PUNCH)
    b.set(48, 10, T.POWER_SWITCH)
    # Traps
    b.set(25, 17, T.TRAP_FLOGGER)          # kitchen mid
    b.set(36, 13, T.TRAP_FIRE)             # patio, before garage door
    # Zombie spawns — around the yard
    for sx, sy in ((2, 2), (32, 2), (50, 2), (61, 6), (61, 24), (61, 41),
                   (32, 41), (10, 41), (2, 32), (2, 16), (34, 33), (20, 2)):
        b.set(sx, sy, T.ZOMBIE_SPAWN)

    # ================= Save =================
    # JPEG: the bg is an opaque photo-based composite; PNG of it is ~7MB,
    # JPEG ~1MB — matters because the host streams these bytes to every
    # client in S_START_GAME.
    bg_path = os.path.join("assets", "images", "estate_bg.jpg")
    pygame.image.save(b.bg, bg_path)
    map_loader.save(
        b.grid,
        background_image_path=bg_path,
        name="estate",
        door_costs=b.door_costs,
        wall_buy_weapons=b.wall_buys,
        perk_machine_perks=b.perks,
        floor_grid=None,          # bg-art map: flat default floor under bg
        wall_style="wood",
        decor=[],
    )
    print(f"saved maps/estate.pkl ({W}x{H}) + {bg_path}")

    # ================= Debug preview =================
    preview = b.bg.copy()
    overlay_colors = {
        int(T.INVISIBLE_WALL): (255, 0, 255, 70),
        int(T.DOOR_CLOSED):    (255, 215, 0, 160),
        int(T.WINDOW):         (80, 180, 255, 160),
        int(T.PLAYER_SPAWN):   (180, 30, 200, 200),
        int(T.ZOMBIE_SPAWN):   (255, 0, 0, 200),
        int(T.PERK_MACHINE):   (255, 80, 80, 220),
        int(T.WALL_BUY):       (255, 255, 0, 220),
        int(T.MYSTERY_BOX):    (255, 140, 0, 220),
        int(T.PACK_A_PUNCH):   (255, 230, 80, 220),
        int(T.POWER_SWITCH):   (80, 255, 80, 220),
        int(T.TRAP_FLOGGER):   (200, 200, 200, 200),
        int(T.TRAP_FIRE):      (255, 120, 0, 200),
    }
    cell = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
    for y in range(H):
        for x in range(W):
            color = overlay_colors.get(b.grid[y][x])
            if color is None:
                continue
            cell.fill(color)
            preview.blit(cell, (x * TILE, y * TILE))
    small = pygame.transform.smoothscale(preview, (PX_W // 2, PX_H // 2))
    pygame.image.save(small, "_render_estate.png")
    print("wrote _render_estate.png (half scale, collision overlaid)")


if __name__ == "__main__":
    main()
