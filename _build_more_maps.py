"""Build two more art-composed maps in the estate pipeline:

  motel    (52x34) — a row of motel rooms you unlock west->east, office
                     start, storage shed with PaP off the parking lot
  compound (56x40) — concrete warehouse + brick bunker on an asphalt pad,
                     office start room

Outputs per map: assets/images/<name>_bg.jpg, maps/<name>.pkl, and a
half-scale _render_<name>.png with the collision overlaid for eyeballing.

Run: python _build_more_maps.py
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

TILES_DIR = r"C:/Users/glent/OneDrive/Desktop/gametiles"
WALLS_DIR = os.path.join(TILES_DIR, "Tilesets", "Walls")
OBJS_DIR = os.path.join(TILES_DIR, "Tilesets", "house_objects")
GRASS_PATH = os.path.join(TILES_DIR, "sprBackground",
                          "5e33c0d9-a609-48fc-a978-cf46374fe105.png")

WALL_STRIPS = {
    "wood":     "walls_0005_Layer-6.png",
    "concrete": "walls_0031_Layer-32.png",
    "brick":    "walls_0048_Layer-49.png",
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

FLOOR_WOOD = os.path.join("assets", "images", "imported", "floorwood.png")
FLOOR_CONCRETE = os.path.join("assets", "images", "tiles", "floor_concrete.png")
FLOOR_BRICK = os.path.join("assets", "images", "tiles", "floor_brick.png")
FLOOR_CARPET = os.path.join("assets", "images", "tiles", "floor_carpet.png")
FLOOR_METAL = os.path.join("assets", "images", "tiles", "floor_metal.png")
FLOOR_ASPHALT = os.path.join("assets", "images", "tiles", "floor_asphalt.png")


def _load(path):
    return pygame.image.load(path).convert_alpha()


class MapBuilder:
    """Parametrized version of the estate builder: composes the background
    art AND the collision grid from the same calls."""

    def __init__(self, w_tiles: int, h_tiles: int):
        self.W, self.H = w_tiles, h_tiles
        self.px_w, self.px_h = w_tiles * TILE, h_tiles * TILE
        self.bg = pygame.Surface((self.px_w, self.px_h))
        self.grid = [[int(T.EMPTY)] * w_tiles for _ in range(h_tiles)]
        self.door_costs: dict = {}
        self.wall_buys: dict = {}
        self.perks: dict = {}
        self.strips = {}
        for mat, fname in WALL_STRIPS.items():
            piece = _load(os.path.join(WALLS_DIR, fname))
            w, h = piece.get_size()
            scale_w = max(TILE, int(w * (TILE / h)))
            self.strips[mat] = pygame.transform.smoothscale(piece, (scale_w, TILE))
        self.furn = {k: _load(os.path.join(OBJS_DIR, v)) for k, v in FURNITURE.items()}

    # ---------- art ----------

    def lay_grass(self):
        grass = _load(GRASS_PATH)
        crop = grass.subsurface(pygame.Rect(1400, 300, 2400, 2100))
        self.bg.blit(pygame.transform.smoothscale(crop, (self.px_w, self.px_h)), (0, 0))

    def lay_floor(self, x0, y0, x1, y1, texture_path, tex_tiles=1):
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
        img = self.furn[name]
        if rotate:
            img = pygame.transform.rotate(img, rotate)
        w, h = img.get_size()
        out_w = tiles_wide * TILE
        out_h = int(h * out_w / w)
        img = pygame.transform.smoothscale(img, (out_w, out_h))
        self.bg.blit(img, (x_tile * TILE, y_tile * TILE))
        if block:
            for ty in range(y_tile, min(self.H, y_tile + max(1, out_h // TILE))):
                for tx in range(x_tile, min(self.W, x_tile + tiles_wide)):
                    if self.grid[ty][tx] == int(T.EMPTY):
                        self.grid[ty][tx] = int(T.INVISIBLE_WALL)

    # ---------- grid ----------

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

    def border(self):
        for x in range(self.W):
            self.set(x, 0, T.INVISIBLE_WALL)
            self.set(x, self.H - 1, T.INVISIBLE_WALL)
        for y in range(self.H):
            self.set(0, y, T.INVISIBLE_WALL)
            self.set(self.W - 1, y, T.INVISIBLE_WALL)

    # ---------- save ----------

    def save(self, name: str):
        bg_path = os.path.join("assets", "images", f"{name}_bg.jpg")
        pygame.image.save(self.bg, bg_path)
        map_loader.save(
            self.grid, background_image_path=bg_path, name=name,
            door_costs=self.door_costs, wall_buy_weapons=self.wall_buys,
            perk_machine_perks=self.perks, floor_grid=None,
            wall_style="wood", decor=[],
        )
        print(f"saved maps/{name}.pkl + {bg_path}")

        preview = self.bg.copy()
        colors = {
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
        for y in range(self.H):
            for x in range(self.W):
                color = colors.get(self.grid[y][x])
                if color is None:
                    continue
                cell.fill(color)
                preview.blit(cell, (x * TILE, y * TILE))
        small = pygame.transform.smoothscale(preview, (self.px_w // 2, self.px_h // 2))
        pygame.image.save(small, f"_render_{name}.png")
        print(f"wrote _render_{name}.png")


# ====================================================================
# MOTEL — 52x34. A roadside motel: office on the west end, five rooms
# in a row you buy through west->east (power is in room 5), a walkway
# along the front, a parking lot, and a storage shed with the PaP.
# ====================================================================

def build_motel():
    b = MapBuilder(52, 34)
    b.lay_grass()

    BY0, BY1 = 6, 16          # motel block rows (walls at BY0 and BY1)
    OFF_X0, OFF_X1 = 4, 12    # office
    ROOM_W = 7                # each room is 7 tiles incl. shared wall
    rooms = []                # (x0, x1) per room interior bounds
    x = OFF_X1
    for i in range(5):
        rooms.append((x, x + ROOM_W))
        x += ROOM_W

    # Floors: office concrete, rooms carpet, walkway concrete, lot brick
    b.lay_floor(OFF_X0 + 1, BY0 + 1, OFF_X1, BY1, FLOOR_CONCRETE)
    for (rx0, rx1) in rooms:
        b.lay_floor(rx0 + 1, BY0 + 1, rx1, BY1, FLOOR_CARPET)
    b.lay_floor(OFF_X0, BY1 + 1, rooms[-1][1] + 1, BY1 + 4, FLOOR_CONCRETE)   # walkway
    b.lay_floor(6, BY1 + 4, 48, 28, FLOOR_BRICK)                              # parking lot

    # Motel exterior: north wall with one window per room, office window
    north_skips = [OFF_X0 + 4]
    for (rx0, rx1) in rooms:
        north_skips.append((rx0 + rx1) // 2 + 1)
    b.wall_h("wood", OFF_X0, rooms[-1][1], BY0, skip=tuple(north_skips))
    for sx in north_skips:
        b.window(sx, BY0)
    # South wall: office door onto the walkway; rooms get windows
    south_skips = [OFF_X0 + 4]
    for (rx0, rx1) in rooms:
        south_skips.append((rx0 + rx1) // 2 + 1)
    b.wall_h("wood", OFF_X0, rooms[-1][1], BY1, skip=tuple(south_skips))
    b.door([(OFF_X0 + 4, BY1)], 0)        # office front door — free, it's the exit
    for sx in south_skips[1:]:
        b.window(sx, BY1)
    # West + east ends
    b.wall_v("wood", OFF_X0, BY0, BY1, skip=(BY0 + 5,))
    b.window(OFF_X0, BY0 + 5)
    b.wall_v("wood", rooms[-1][1], BY0, BY1, skip=(BY0 + 5,))
    b.window(rooms[-1][1], BY0 + 5)

    # Internal walls between office/rooms with BUYABLE doors west->east
    door_costs = [750, 750, 1000, 1000, 1250]
    mid_y = (BY0 + BY1) // 2
    for i, (rx0, rx1) in enumerate(rooms):
        b.wall_v("wood", rx0, BY0, BY1, skip=(mid_y, mid_y + 1))
        b.door([(rx0, mid_y), (rx0, mid_y + 1)], door_costs[i])

    # Player spawns — office
    for sx, sy in ((6, 9), (10, 9), (6, 13), (10, 13)):
        b.set(sx, sy, T.PLAYER_SPAWN)

    # Room contents (furniture + machines)
    b.place_furniture("table_rect", 6, 11, 3)               # office desk
    b.place_furniture("plant1", 11, BY0 + 2, 1, block=False)
    b.perk(OFF_X0 + 1, BY0 + 1, "Quick Revive")
    b.wall_buy(OFF_X0 + 1, BY1 - 1, "Shotgun")

    r = rooms[0]
    b.place_furniture("bed_double", r[0] + 1, BY0 + 1, 3)
    b.wall_buy(r[1] - 1, BY0 + 1, "SMG")
    r = rooms[1]
    b.place_furniture("bed_single", r[0] + 1, BY0 + 1, 2)
    b.place_furniture("dresser", r[1] - 3, BY1 - 2, 2)
    b.perk(r[1] - 1, BY0 + 1, "Juggernog")
    r = rooms[2]
    b.place_furniture("bed_double2", r[0] + 1, BY0 + 1, 3)
    b.set(r[1] - 1, BY0 + 1, T.MYSTERY_BOX)
    r = rooms[3]
    b.place_furniture("bed_single", r[0] + 1, BY0 + 1, 2)
    b.place_furniture("armchair_tan", r[1] - 3, BY0 + 1, 2)
    b.perk(r[1] - 1, BY1 - 1, "Speed Cola")
    b.wall_buy(r[0] + 1, BY1 - 1, "AK74u")
    r = rooms[4]
    b.place_furniture("bed_double", r[0] + 1, BY0 + 1, 3)
    b.set(r[1] - 1, BY0 + 1, T.POWER_SWITCH)
    b.perk(r[1] - 1, BY1 - 1, "Mule Kick")

    # Storage shed (brick) in the SE corner of the lot — PaP inside
    SX0, SY0, SX1, SY1 = 38, 22, 48, 30
    b.lay_floor(SX0 + 1, SY0 + 1, SX1, SY1, FLOOR_CONCRETE)
    b.wall_h("brick", SX0, SX1, SY0, skip=(SX0 + 5, SX0 + 6))
    b.door([(SX0 + 5, SY0), (SX0 + 6, SY0)], 1500)
    b.wall_h("brick", SX0, SX1, SY1, skip=(SX0 + 8,))
    b.window(SX0 + 8, SY1)
    b.wall_v("brick", SX0, SY0, SY1, skip=(SY0 + 4,))
    b.window(SX0, SY0 + 4)
    b.wall_v("brick", SX1, SY0, SY1)
    b.set(SX0 + 5, SY0 + 4, T.PACK_A_PUNCH)
    b.perk(SX1 - 1, SY1 - 1, "Double Tap")
    b.wall_buy(SX0 + 1, SY1 - 1, "Galil")
    b.place_furniture("dresser", SX1 - 3, SY0 + 1, 2)

    # Stamin-Up out on the walkway east end
    b.perk(rooms[-1][1] + 2, BY1 + 2, "Stamin-Up")

    # Traps: walkway middle + shed door
    b.set(rooms[1][0] + 3, BY1 + 2, T.TRAP_FLOGGER)
    b.set(SX0 + 5, SY0 - 2, T.TRAP_FIRE)

    # Greenery
    for px, py in ((2, 2), (20, 2), (38, 2), (49, 3), (2, 20), (2, 30),
                   (20, 30), (32, 31), (49, 32)):
        b.place_furniture("tuft1", px, py, 2, block=False)

    # Zombie spawns: grass north + lot south + flanks
    for sx, sy in ((2, 3), (14, 2), (26, 2), (38, 3), (49, 6),
                   (2, 24), (14, 31), (26, 31), (49, 24), (49, 12)):
        if b.grid[sy][sx] == int(T.EMPTY):
            b.set(sx, sy, T.ZOMBIE_SPAWN)

    b.border()
    b.save("motel")


# ====================================================================
# COMPOUND — 56x40. Military depot: office start room, big concrete
# warehouse (power + box), brick bunker (PaP), asphalt yard between.
# ====================================================================

def build_compound():
    b = MapBuilder(56, 40)
    b.lay_grass()
    # Asphalt pad covering the working area of the depot
    b.lay_floor(4, 4, 52, 36, FLOOR_ASPHALT)

    # ---- OFFICE (start, wood walls, concrete floor): x6..18, y26..36
    b.lay_floor(7, 27, 18, 36, FLOOR_CONCRETE)
    b.wall_h("wood", 6, 18, 26, skip=(11, 12))
    b.door([(11, 26), (12, 26)], 750)              # north door -> yard
    b.wall_h("wood", 6, 18, 36, skip=(9, 15))
    b.window(9, 36)
    b.window(15, 36)
    b.wall_v("wood", 6, 26, 36, skip=(31,))
    b.window(6, 31)
    b.wall_v("wood", 18, 26, 36, skip=(31,))
    b.window(18, 31)
    for sx, sy in ((9, 29), (15, 29), (9, 33), (15, 33)):
        b.set(sx, sy, T.PLAYER_SPAWN)
    b.place_furniture("couch_red", 8, 27, 3)
    b.place_furniture("table_oval", 13, 31, 2)
    b.perk(7, 35, "Quick Revive")
    b.wall_buy(17, 27, "Shotgun")

    # ---- WAREHOUSE (concrete walls, metal floor): x6..38, y6..20
    b.lay_floor(7, 7, 38, 20, FLOOR_METAL)
    b.wall_h("concrete", 6, 38, 6, skip=(14, 26))
    b.window(14, 6)
    b.window(26, 6)
    b.wall_h("concrete", 6, 38, 20, skip=(11, 12, 30))
    b.door([(11, 20), (12, 20)], 1000)             # south doors -> yard
    b.window(30, 20)
    b.wall_v("concrete", 6, 6, 20, skip=(12,))
    b.window(6, 12)
    b.wall_v("concrete", 38, 6, 20, skip=(13, 14))
    b.door([(38, 13), (38, 14)], 1250)             # east door -> bunker side
    # Internal divider: storage west | hall east
    b.wall_v("concrete", 20, 6, 20, skip=(12, 13))
    b.door([(20, 12), (20, 13)], 1000)
    # Storage (west): mystery box + Jug
    b.set(8, 8, T.MYSTERY_BOX)
    b.perk(8, 18, "Juggernog")
    b.wall_buy(7, 12, "SMG")
    b.place_furniture("dresser", 12, 8, 2)
    b.place_furniture("dresser", 15, 8, 2)
    b.place_furniture("table_rect", 11, 15, 3)
    # Hall (east): power + Mule Kick
    b.set(36, 8, T.POWER_SWITCH)
    b.perk(36, 18, "Mule Kick")
    b.wall_buy(21, 7, "AK74u")
    b.place_furniture("dresser", 26, 8, 2)
    b.place_furniture("dresser", 29, 8, 2)
    b.place_furniture("table_rect", 25, 14, 3)
    b.place_furniture("couch_blue", 31, 16, 3)

    # ---- BUNKER (brick, concrete floor): x42..52, y22..34 — PaP
    b.lay_floor(43, 23, 52, 34, FLOOR_CONCRETE)
    b.wall_h("brick", 42, 52, 22, skip=(46, 47))
    b.door([(46, 22), (47, 22)], 1500)
    b.wall_h("brick", 42, 52, 34, skip=(48,))
    b.window(48, 34)
    b.wall_v("brick", 42, 22, 34, skip=(28,))
    b.window(42, 28)
    b.wall_v("brick", 52, 22, 34, skip=(27,))
    b.window(52, 27)
    b.set(47, 28, T.PACK_A_PUNCH)
    b.perk(51, 23, "Speed Cola")
    b.wall_buy(43, 23, "Galil")
    b.place_furniture("dresser", 49, 32, 2)

    # Yard extras
    b.perk(46, 10, "Double Tap")     # NE yard pocket
    b.perk(24, 24, "Stamin-Up")      # mid-yard
    b.set(11, 23, T.TRAP_FLOGGER)    # office->yard chokepoint
    b.set(46, 18, T.TRAP_FIRE)       # approach to bunker

    # Yard furniture as cover
    b.place_furniture("table_rect", 28, 28, 3)
    b.place_furniture("dresser", 33, 30, 2)
    b.place_furniture("couch_red", 42, 8, 3)
    for px, py in ((2, 2), (28, 1), (52, 2), (2, 37), (30, 37), (53, 37),
                   (2, 20), (21, 32)):
        b.place_furniture("tuft1", px, py, 2, block=False)

    # Zombie spawns around the perimeter
    for sx, sy in ((2, 4), (14, 2), (32, 2), (50, 3), (54, 12), (54, 30),
                   (40, 38), (22, 38), (4, 38), (2, 14), (30, 23)):
        if b.grid[sy][sx] == int(T.EMPTY):
            b.set(sx, sy, T.ZOMBIE_SPAWN)

    b.border()
    b.save("compound")


if __name__ == "__main__":
    build_motel()
    build_compound()
