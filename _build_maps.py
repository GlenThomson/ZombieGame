"""Generate two handcrafted tile-based maps with proper room-and-corridor
layouts, real architecture, and furniture/decor.

NACHT  : 38x28 — abandoned cabin (multiple rooms + porch + barn)
VERRUCKT: 52x38 — sanitorium (lobby, two wings, courtyard, PaP gate)
"""
from game.world.tile import TileType, FloorType
from game.world import map_loader

T = TileType
F = FloorType


# ---------------- helpers ----------------

def make_grid(w, h, fill=T.EMPTY):
    return [[int(fill) for _ in range(w)] for _ in range(h)]


def fill_floor(floors, x, y, w, h, ftype: FloorType):
    for ry in range(y, y + h):
        for rx in range(x, x + w):
            floors[ry][rx] = int(ftype)


def room(grid, floors, x, y, w, h, *, floor=F.CONCRETE, walls=True):
    for ry in range(y, y + h):
        for rx in range(x, x + w):
            floors[ry][rx] = int(floor)
    if walls:
        for rx in range(x, x + w):
            grid[y][rx] = int(T.WALL)
            grid[y + h - 1][rx] = int(T.WALL)
        for ry in range(y, y + h):
            grid[ry][x] = int(T.WALL)
            grid[ry][x + w - 1] = int(T.WALL)
    for ry in range(y + 1, y + h - 1):
        for rx in range(x + 1, x + w - 1):
            grid[ry][rx] = int(T.EMPTY)


def vwall(grid, x, y0, y1):
    for y in range(y0, y1 + 1):
        grid[y][x] = int(T.WALL)


def hwall(grid, x0, x1, y):
    for x in range(x0, x1 + 1):
        grid[y][x] = int(T.WALL)


def open_doorway(grid, x, y, *, vertical=False, length=2):
    for i in range(length):
        if vertical:
            grid[y + i][x] = int(T.EMPTY)
        else:
            grid[y][x + i] = int(T.EMPTY)


def door_tiles(grid, positions: list[tuple[int, int]]):
    for x, y in positions:
        grid[y][x] = int(T.DOOR_CLOSED)


def window_tile(grid, x, y):
    grid[y][x] = int(T.WINDOW)


def place(grid, x, y, ttype: TileType):
    grid[y][x] = int(ttype)


def pillar(grid, x, y):
    grid[y][x] = int(T.WALL)


# ============================================================
# NACHT DER UNTOTEN — 38x28 (was 56x40 — too big)
# Single-storey cabin with 4 rooms + a covered porch + a separate
# barn behind a 1500-pt door. Player starts in the bedroom.
# ============================================================

def build_nacht():
    W, H = 38, 28
    g = make_grid(W, H)
    floors = make_grid(W, H, F.GRASS)
    decor: list[dict] = []

    # ---- MAIN HOUSE (left side) ----
    HX, HY, HW, HH = 2, 2, 21, 19
    room(g, floors, HX, HY, HW, HH, floor=F.WOOD)

    # Internal partitions: cross-shaped, dividing into 4 rooms +
    # a small central hallway around the cross.
    vwall(g, 12, HY + 1, HY + HH - 2)         # vertical divider
    hwall(g, HX + 1, HX + HW - 2, 10)         # horizontal divider
    # Doorways at each cross arm
    open_doorway(g, 12, 5, vertical=True, length=2)
    open_doorway(g, 12, 13, vertical=True, length=2)
    open_doorway(g, 6, 10, vertical=False, length=2)
    open_doorway(g, 17, 10, vertical=False, length=2)

    # ---- BEDROOM (top-left, carpet) ----
    fill_floor(floors, HX + 1, HY + 1, 10, 8, F.CARPET)
    place(g, 4, 4, T.PLAYER_SPAWN)
    place(g, 9, 4, T.PLAYER_SPAWN)
    place(g, 4, 7, T.PLAYER_SPAWN)
    place(g, 9, 7, T.PLAYER_SPAWN)
    decor.append({"pos": (3, 4), "kind": "bed"})
    decor.append({"pos": (8, 4), "kind": "chest"})
    decor.append({"pos": (3, 8), "kind": "plant_large"})
    place(g, HX, 4, T.WALL_BUY)

    # ---- KITCHEN (top-right, metal) ----
    fill_floor(floors, 13, HY + 1, 10, 8, F.METAL)
    decor.append({"pos": (14, 3), "kind": "sink"})
    decor.append({"pos": (17, 3), "kind": "sink"})
    decor.append({"pos": (20, 3), "kind": "sink"})
    decor.append({"pos": (15, 8), "kind": "chair"})
    decor.append({"pos": (17, 8), "kind": "chair"})
    decor.append({"pos": (19, 8), "kind": "chair"})
    place(g, 22, 4, T.MYSTERY_BOX)

    # ---- LIVING ROOM (bot-left, carpet) ----
    fill_floor(floors, HX + 1, 11, 10, 9, F.CARPET)
    decor.append({"pos": (3, 13), "kind": "couch"})
    decor.append({"pos": (3, 17), "kind": "couch"})
    decor.append({"pos": (9, 14), "kind": "tv"})
    decor.append({"pos": (9, 19), "kind": "plant_large"})
    place(g, HX, 14, T.WALL_BUY)

    # ---- DINING / POWER (bot-right, wood) ----
    fill_floor(floors, 13, 11, 10, 9, F.WOOD)
    decor.append({"pos": (15, 14), "kind": "chair"})
    decor.append({"pos": (15, 16), "kind": "chair"})
    decor.append({"pos": (17, 14), "kind": "chair"})
    decor.append({"pos": (17, 16), "kind": "chair"})
    decor.append({"pos": (19, 14), "kind": "chair"})
    decor.append({"pos": (19, 16), "kind": "chair"})
    place(g, 22, 18, T.PERK_MACHINE)
    place(g, 21, 14, T.POWER_SWITCH)

    # ---- HOUSE EXTERIOR DOORS / WINDOWS ----
    door_tiles(g, [(11, HY + HH - 1)])     # front door (south)
    door_tiles(g, [(17, HY)])              # kitchen side door (north)
    door_tiles(g, [(HX + HW - 1, 5), (HX + HW - 1, 6)])  # storage→barn east

    for wx in (4, 9, 16, 21):
        window_tile(g, wx, HY)
        window_tile(g, wx, HY + HH - 1)
    for wy in (4, 8, 14, 18):
        window_tile(g, HX, wy)
        window_tile(g, HX + HW - 1, wy)

    # ---- COVERED PORCH (south of house) ----
    fill_floor(floors, 3, HY + HH, 19, 3, F.WOOD)
    decor.append({"pos": (4, HY + HH + 1), "kind": "couch"})
    decor.append({"pos": (10, HY + HH + 1), "kind": "chair"})
    decor.append({"pos": (16, HY + HH + 1), "kind": "plant_large"})

    # ---- BARN (right side) ----
    BX, BY, BW, BH = 26, 4, 11, 18
    room(g, floors, BX, BY, BW, BH, floor=F.DIRT)
    for px in (BX + 3, BX + 7):
        pillar(g, px, BY + 6)
        pillar(g, px, BY + 12)
    decor.append({"pos": (BX + 1, BY + 2), "kind": "chest"})
    decor.append({"pos": (BX + 5, BY + 2), "kind": "chest"})
    decor.append({"pos": (BX + 8, BY + 2), "kind": "chest"})
    decor.append({"pos": (BX + 1, BY + 15), "kind": "wood_plank"})
    decor.append({"pos": (BX + 7, BY + 15), "kind": "wood_plank"})
    place(g, BX + 5, BY + 9, T.PACK_A_PUNCH)
    decor.append({"pos": (BX + 8, BY + 9), "kind": "gold_box"})
    place(g, BX, BY + 4, T.WALL_BUY)
    door_tiles(g, [(BX, BY + 8), (BX, BY + 9), (BX, BY + 10)])
    for wy in (BY + 3, BY + 8, BY + 14):
        window_tile(g, BX, wy)
        window_tile(g, BX + BW - 1, wy)
    for wx in (BX + 3, BX + 7):
        window_tile(g, wx, BY)
        window_tile(g, wx, BY + BH - 1)

    # Path between house and barn
    fill_floor(floors, HX + HW, 5, BX - (HX + HW), 4, F.DIRT)

    # ---- TRAP ----
    place(g, 6, 10, T.TRAP_FLOGGER)

    # ---- DECOR PLANTS scattered outside ----
    for px, py in ((1, 1), (1, 26), (36, 1), (36, 26),
                   (10, 26), (20, 26), (30, 26)):
        decor.append({"pos": (px, py), "kind": "plant_large"})

    # ---- ZOMBIE SPAWNS ----
    for sx, sy in ((1, 1), (W // 2, 1), (W - 2, 1),
                   (1, H - 2), (W // 2, H - 2), (W - 2, H - 2),
                   (1, H // 2), (W - 2, H // 2)):
        if g[sy][sx] == int(T.EMPTY):
            place(g, sx, sy, T.ZOMBIE_SPAWN)

    door_costs = {
        (11, HY + HH - 1): 750,
        (17, HY): 750,
        (HX + HW - 1, 5): 1000,
        (HX + HW - 1, 6): 1000,
        (BX, BY + 8): 1500,
        (BX, BY + 9): 1500,
        (BX, BY + 10): 1500,
    }
    wall_buys = {
        (HX, 4): "Shotgun",
        (HX, 14): "SMG",
        (BX, BY + 4): "Galil",
    }
    perks = {
        (22, 18): "Quick Revive",
    }

    map_loader.save(
        g, background_image_path=None, name="nacht",
        wall_buy_weapons=wall_buys,
        door_costs=door_costs,
        perk_machine_perks=perks,
        floor_grid=floors,
        wall_style="wood",
        decor=decor,
    )
    print(f"saved nacht ({W}x{H}) — {len(decor)} decor items")


# ============================================================
# VERRÜCKT — 52x38 (was 72x52 — too big)
# Sanitorium: lobby south, two wings, courtyard, PaP behind a gate.
# ============================================================

def build_verruckt():
    W, H = 52, 38
    g = make_grid(W, H)
    floors = make_grid(W, H, F.ASPHALT)
    decor: list[dict] = []

    BX, BY, BW, BH = 2, 2, 48, 34
    room(g, floors, BX, BY, BW, BH, floor=F.CONCRETE)

    # ---------------- LOBBY (south-centre) ----------------
    LX, LY, LW, LH = 19, 26, 14, 10
    fill_floor(floors, LX, LY, LW, LH, F.CARPET)
    for x in range(LX, LX + LW):
        g[LY][x] = int(T.WALL)
    for y in range(LY, LY + LH):
        g[y][LX] = int(T.WALL)
        g[y][LX + LW - 1] = int(T.WALL)
    for sx, sy in ((LX + 2, LY + 4), (LX + LW - 3, LY + 4),
                   (LX + 2, LY + 7), (LX + LW - 3, LY + 7)):
        place(g, sx, sy, T.PLAYER_SPAWN)
    place(g, LX + 1, LY + 2, T.WALL_BUY)
    place(g, LX + LW - 2, LY + 2, T.WALL_BUY)
    decor.append({"pos": (LX + 2, LY + 1), "kind": "couch"})
    decor.append({"pos": (LX + 8, LY + 1), "kind": "tv"})
    decor.append({"pos": (LX + 1, LY + 8), "kind": "plant_small"})
    decor.append({"pos": (LX + LW - 2, LY + 8), "kind": "plant_small"})
    door_tiles(g, [(LX + LW // 2 - 1, LY), (LX + LW // 2, LY)])

    # ---------------- WEST WING ----------------
    WCX0, WCX1 = 8, 11
    fill_floor(floors, WCX0, BY + 1, WCX1 - WCX0 + 1, BH - 2, F.CONCRETE)
    vwall(g, WCX0, BY, BY + BH - 1)
    vwall(g, WCX1, BY, BY + BH - 1)

    # West Room A — KITCHEN (top)
    fill_floor(floors, BX + 1, 4, 6, 7, F.METAL)
    hwall(g, BX, 7, 11)
    open_doorway(g, WCX0, 7, vertical=True, length=2)
    decor.append({"pos": (BX + 1, 5), "kind": "sink"})
    decor.append({"pos": (BX + 4, 5), "kind": "sink"})
    decor.append({"pos": (BX + 1, 9), "kind": "chair"})
    decor.append({"pos": (BX + 3, 9), "kind": "chair"})
    decor.append({"pos": (BX + 5, 9), "kind": "chair"})
    place(g, BX + 1, 6, T.MYSTERY_BOX)

    # West Room B — OFFICE / PERK (mid)
    fill_floor(floors, BX + 1, 12, 7, 7, F.CARPET)
    hwall(g, BX, 8, 11)
    hwall(g, BX, 8, 19)
    open_doorway(g, WCX0, 14, vertical=True, length=2)
    place(g, BX + 4, 14, T.PERK_MACHINE)
    place(g, BX, 16, T.WALL_BUY)
    decor.append({"pos": (BX + 1, 13), "kind": "tv"})
    decor.append({"pos": (BX + 3, 13), "kind": "keyboard"})
    decor.append({"pos": (BX + 5, 13), "kind": "chair"})
    decor.append({"pos": (BX + 1, 17), "kind": "couch"})

    # West Room C — BEDROOM / PERK (bottom)
    fill_floor(floors, BX + 1, 20, 7, 7, F.CARPET)
    hwall(g, BX, 8, 20)
    hwall(g, BX, 8, 27)
    open_doorway(g, WCX0, 22, vertical=True, length=2)
    place(g, BX + 4, 22, T.PERK_MACHINE)
    decor.append({"pos": (BX + 1, 21), "kind": "bed"})
    decor.append({"pos": (BX + 4, 21), "kind": "bed"})
    decor.append({"pos": (BX + 1, 25), "kind": "chest"})
    decor.append({"pos": (BX + 5, 25), "kind": "plant_large"})

    # ---------------- EAST WING (mirror) ----------------
    ECX0, ECX1 = 40, 43
    fill_floor(floors, ECX0, BY + 1, ECX1 - ECX0 + 1, BH - 2, F.CONCRETE)
    vwall(g, ECX0, BY, BY + BH - 1)
    vwall(g, ECX1, BY, BY + BH - 1)

    # East Room A — SUPPLY / PaP (top)
    fill_floor(floors, 44, 4, 5, 7, F.METAL)
    hwall(g, ECX1, BX + BW - 1, 11)
    open_doorway(g, ECX1, 7, vertical=True, length=2)
    place(g, 47, 6, T.PACK_A_PUNCH)
    decor.append({"pos": (44, 5), "kind": "chest"})
    decor.append({"pos": (46, 5), "kind": "chest"})
    decor.append({"pos": (44, 9), "kind": "wood_plank"})

    # East Room B — STAFF (mid)
    fill_floor(floors, 44, 12, 5, 7, F.CARPET)
    hwall(g, ECX1, BX + BW - 1, 12)
    hwall(g, ECX1, BX + BW - 1, 19)
    open_doorway(g, ECX1, 14, vertical=True, length=2)
    place(g, 47, 14, T.PERK_MACHINE)
    place(g, BX + BW - 1, 16, T.WALL_BUY)
    decor.append({"pos": (44, 13), "kind": "couch"})
    decor.append({"pos": (47, 13), "kind": "tv"})

    # East Room C — WARD (bottom)
    fill_floor(floors, 44, 20, 5, 7, F.CARPET)
    hwall(g, ECX1, BX + BW - 1, 20)
    hwall(g, ECX1, BX + BW - 1, 27)
    open_doorway(g, ECX1, 22, vertical=True, length=2)
    place(g, 47, 22, T.PERK_MACHINE)
    decor.append({"pos": (44, 21), "kind": "bed"})
    decor.append({"pos": (47, 21), "kind": "bed"})
    decor.append({"pos": (44, 25), "kind": "sink"})

    # ---------------- COURTYARD ----------------
    fill_floor(floors, 12, BY + 1, 28, BH - 2, F.DIRT)
    place(g, 25, 17, T.POWER_SWITCH)
    for px, py in ((16, 7), (24, 7), (32, 7),
                   (16, 26), (24, 26), (32, 26),
                   (16, 16), (32, 16)):
        pillar(g, px, py)
    for fx, fy in ((20, 12), (28, 18), (24, 24)):
        floors[fy][fx] = int(F.CONCRETE_BLOODIED)
        floors[fy + 1][fx] = int(F.CONCRETE_BLOODIED)
        floors[fy][fx + 1] = int(F.CONCRETE_BLOODIED)
    decor.append({"pos": (15, 5), "kind": "couch"})
    decor.append({"pos": (33, 5), "kind": "couch"})
    decor.append({"pos": (20, 9), "kind": "chair"})
    decor.append({"pos": (30, 9), "kind": "chair"})
    decor.append({"pos": (22, 22), "kind": "chest"})
    decor.append({"pos": (28, 22), "kind": "tv"})
    decor.append({"pos": (18, 14), "kind": "plant_large"})
    decor.append({"pos": (30, 14), "kind": "plant_large"})

    # Connect lobby to courtyard already done; corridors -> courtyard
    door_tiles(g, [(WCX1, 13), (WCX1, 14)])
    door_tiles(g, [(ECX0, 13), (ECX0, 14)])

    # ---------------- TRAPS ----------------
    place(g, 10, 24, T.TRAP_FLOGGER)
    place(g, 41, 24, T.TRAP_FIRE)

    # ---------------- WINDOWS ----------------
    for wy in (6, 12, 18, 24, 30):
        window_tile(g, BX, wy)
        window_tile(g, BX + BW - 1, wy)
    for wx in (8, 16, 24, 32, 40):
        window_tile(g, wx, BY)
        window_tile(g, wx, BY + BH - 1)

    # ---------------- ZOMBIE SPAWNS ----------------
    for sx, sy in ((1, 1), (W // 2, 1), (W - 2, 1),
                   (1, H - 2), (W // 2, H - 2), (W - 2, H - 2),
                   (1, H // 2), (W - 2, H // 2)):
        if g[sy][sx] == int(T.EMPTY):
            place(g, sx, sy, T.ZOMBIE_SPAWN)

    door_costs = {
        (LX + LW // 2 - 1, LY): 750,
        (LX + LW // 2, LY): 750,
        (WCX1, 13): 1000,
        (WCX1, 14): 1000,
        (ECX0, 13): 1000,
        (ECX0, 14): 1000,
    }
    wall_buys = {
        (LX + 1, LY + 2): "Shotgun",
        (LX + LW - 2, LY + 2): "AK74u",
        (BX, 16): "SMG",
        (BX + BW - 1, 16): "Galil",
    }
    perks = {
        (BX + 4, 14): "Juggernog",
        (BX + 4, 22): "Speed Cola",
        (47, 14): "Double Tap",
        (47, 22): "Stamin-Up",
    }

    map_loader.save(
        g, background_image_path=None, name="verruckt",
        door_costs=door_costs, wall_buy_weapons=wall_buys,
        perk_machine_perks=perks,
        floor_grid=floors, wall_style="brick",
        decor=decor,
    )
    print(f"saved verruckt ({W}x{H}) — {len(decor)} decor items")


if __name__ == "__main__":
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    import pygame
    pygame.init()
    pygame.display.set_mode((800, 600))
    build_nacht()
    build_verruckt()
