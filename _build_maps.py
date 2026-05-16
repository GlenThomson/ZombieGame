"""Generate two handcrafted tile-based maps with proper room-and-corridor
layouts (not just rectangles)."""
from game.world.tile import TileType, FloorType
from game.world import map_loader

T = TileType
F = FloorType


# ---------------- helpers ----------------

def make_grid(w, h, fill=T.EMPTY):
    return [[int(fill) for _ in range(w)] for _ in range(h)]


def room(grid, floors, x, y, w, h, *, floor=F.CONCRETE, walls=True):
    """Open a rectangular room: floor everywhere inside, optional border of
    wall tiles. Pre-existing walls AT the border are preserved (so adjacent
    rooms share their wall instead of doubling it)."""
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
    # interior is empty (carve any pre-existing walls inside)
    for ry in range(y + 1, y + h - 1):
        for rx in range(x + 1, x + w - 1):
            grid[ry][rx] = int(T.EMPTY)


def open_doorway(grid, x, y, *, vertical=False, length=2):
    """Carve a doorway in a wall (sets cells to EMPTY)."""
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


def fill_floor(floors, x, y, w, h, ftype: FloorType):
    for ry in range(y, y + h):
        for rx in range(x, x + w):
            floors[ry][rx] = int(ftype)


def place(grid, x, y, ttype: TileType):
    grid[y][x] = int(ttype)


def corridor(grid, floors, x, y, w, h, *, floor=F.CONCRETE):
    """A corridor (no walls — caller responsible for surrounding walls)."""
    fill_floor(floors, x, y, w, h, floor)
    for ry in range(y, y + h):
        for rx in range(x, x + w):
            if grid[ry][rx] == int(T.WALL):
                grid[ry][rx] = int(T.EMPTY)


def pillar(grid, x, y):
    grid[y][x] = int(T.WALL)


# ============================================================
# NACHT DER UNTOTEN — small single-building cabin with several
# distinct rooms + a central hallway. Player starts in a small
# bedroom; mystery box is in a back storage room behind a door;
# wall buys are mounted in nooks off the main hallway.
# ============================================================

def build_nacht():
    W, H = 28, 20
    g = make_grid(W, H)
    floors = make_grid(W, H, F.GRASS)  # outside everything is grass

    # Main building footprint — wood floor
    room(g, floors, 2, 2, 24, 16, floor=F.WOOD)

    # Internal partitions:
    # Vertical wall splitting interior at col 12 (forms left/right wings)
    for y in range(3, 17):
        g[y][12] = int(T.WALL)
    open_doorway(g, 12, 9, vertical=True, length=3)  # central doorway

    # Upper-left bedroom (small starting area)
    for x in range(3, 12):
        g[7][x] = int(T.WALL)
    open_doorway(g, 7, 7, vertical=False, length=2)
    fill_floor(floors, 3, 3, 9, 4, F.CARPET)  # bedroom carpet
    place(g, 5, 4, T.PLAYER_SPAWN)
    place(g, 3, 6, T.WALL_BUY)   # wall buy on bedroom wall

    # Lower-left main living area (open, with debris pillars)
    for x in (5, 9):
        pillar(g, x, 13)
    pillar(g, 7, 11)
    fill_floor(floors, 4, 13, 4, 2, F.CONCRETE_BLOODIED)  # blood smear
    place(g, 11, 16, T.WALL_BUY)  # wall buy on south wall

    # Right wing — divided into TWO rooms (storage + back porch)
    for x in range(13, 26):
        g[10][x] = int(T.WALL)
    open_doorway(g, 17, 10, vertical=False, length=2)
    fill_floor(floors, 13, 3, 13, 7, F.WOOD)  # storage room
    fill_floor(floors, 13, 11, 13, 7, F.DIRT)  # back porch (dirt floor)

    # Mystery box in storage room (top-right corner)
    place(g, 23, 4, T.MYSTERY_BOX)

    # Door between right rooms cost something
    door_tiles(g, [(17, 10), (18, 10)])

    # Door between left/right wings
    door_tiles(g, [(12, 9), (12, 10), (12, 11)])

    # Windows on the building exterior (alternating sides)
    for wx in (4, 8, 16, 21):
        window_tile(g, wx, 2)
        window_tile(g, wx, 17)
    for wy in (4, 8, 13, 16):
        window_tile(g, 2, wy)
        window_tile(g, 25, wy)

    # Zombie spawns just outside (in the grass)
    for sx, sy in ((1, 1), (W - 2, 1), (1, H - 2), (W - 2, H - 2),
                   (W // 2, 1), (W // 2, H - 2)):
        place(g, sx, sy, T.ZOMBIE_SPAWN)

    door_costs = {
        (12, 9): 750, (12, 10): 750, (12, 11): 750,
        (17, 10): 1000, (18, 10): 1000,
    }
    wall_buys = {
        (3, 6): "Shotgun",
        (11, 16): "MP40",
    }

    map_loader.save(
        g, background_image_path=None, name="nacht",
        wall_buy_weapons=wall_buys,
        door_costs=door_costs,
        floor_grid=floors,
        wall_style="wood",
    )
    print(f"saved nacht ({W}x{H}) — multi-room cabin layout")


# ============================================================
# VERRÜCKT — sanatorium. Lobby in the south, two corridors heading
# north (east + west wings), each lined with small rooms. Central
# courtyard with the power switch. Pack-a-Punch behind a 1500-pt door
# in the back. Each room has its own floor type.
# ============================================================

def build_verruckt():
    W, H = 42, 30
    g = make_grid(W, H)
    floors = make_grid(W, H, F.ASPHALT)  # exterior asphalt

    # Outer building (the sanitorium proper)
    room(g, floors, 2, 4, 38, 24, floor=F.CONCRETE)

    # ---- LOBBY (south-centre) ----
    # The entrance hall where the player starts. 14 wide x 6 tall.
    LX, LY, LW, LH = 14, 22, 14, 6
    fill_floor(floors, LX, LY, LW, LH, F.CARPET)
    # Inner walls separating lobby from adjacent areas
    for x in range(LX, LX + LW):
        g[LY][x] = int(T.WALL)
    for y in range(LY, LY + LH):
        g[y][LX] = int(T.WALL)
        g[y][LX + LW - 1] = int(T.WALL)
    # Entrance from outside (south wall of building)
    g[H - 4][20] = int(T.PLAYER_SPAWN)
    # Lobby has 2 wall buys
    place(g, LX + 1, LY + 2, T.WALL_BUY)
    place(g, LX + LW - 2, LY + 2, T.WALL_BUY)
    # Door from lobby north into central courtyard
    door_tiles(g, [(20, LY), (21, LY)])

    # ---- WEST CORRIDOR (column ~6, runs north from lobby outside) ----
    # Two doors gating it.
    fill_floor(floors, 4, 8, 6, 16, F.CONCRETE)
    # West wing inner walls
    for y in range(8, 24):
        g[y][10] = int(T.WALL)
    for x in range(4, 11):
        g[8][x] = int(T.WALL)
    open_doorway(g, 7, 8, vertical=False, length=2)
    # West sub-rooms — 3 rooms stacked vertically off the corridor
    # Room A (top): kitchen
    fill_floor(floors, 4, 5, 6, 4, F.METAL)
    g[9][6] = int(T.WALL); g[9][7] = int(T.WALL); g[9][8] = int(T.WALL)
    open_doorway(g, 5, 9, vertical=False, length=1)
    # Mystery box in kitchen
    place(g, 5, 6, T.MYSTERY_BOX)
    # Room B (mid): office (perk)
    g[15][4] = int(T.WALL); g[15][5] = int(T.WALL); g[15][6] = int(T.WALL); g[15][7] = int(T.WALL); g[15][8] = int(T.WALL); g[15][9] = int(T.WALL)
    open_doorway(g, 9, 15, vertical=False, length=1)
    fill_floor(floors, 3, 11, 7, 4, F.CARPET)
    place(g, 5, 12, T.PERK_MACHINE)
    # Room C (bottom): bedroom (perk)
    fill_floor(floors, 3, 17, 7, 5, F.CARPET)
    place(g, 5, 19, T.PERK_MACHINE)
    place(g, 4, 20, T.WALL_BUY)

    # Connect lobby to west corridor
    door_tiles(g, [(LX, 24), (LX, 25)])
    g[24][LX - 1] = int(T.EMPTY)  # carve through

    # ---- EAST CORRIDOR (mirror) ----
    fill_floor(floors, 32, 8, 6, 16, F.CONCRETE)
    for y in range(8, 24):
        g[y][31] = int(T.WALL)
    for x in range(31, 38):
        g[8][x] = int(T.WALL)
    open_doorway(g, 33, 8, vertical=False, length=2)
    # East sub-rooms
    # Room A (top): supply room (PaP behind door)
    fill_floor(floors, 32, 5, 6, 4, F.METAL)
    g[9][32] = int(T.WALL); g[9][33] = int(T.WALL); g[9][34] = int(T.WALL); g[9][35] = int(T.WALL); g[9][36] = int(T.WALL); g[9][37] = int(T.WALL)
    door_tiles(g, [(35, 9), (36, 9)])  # the famous PaP gate
    place(g, 35, 6, T.PACK_A_PUNCH)
    # Room B (mid): perk + wall buy
    fill_floor(floors, 32, 11, 7, 4, F.CARPET)
    g[15][32] = int(T.WALL); g[15][33] = int(T.WALL); g[15][34] = int(T.WALL); g[15][35] = int(T.WALL); g[15][36] = int(T.WALL); g[15][37] = int(T.WALL)
    open_doorway(g, 33, 15, vertical=False, length=1)
    place(g, 36, 12, T.PERK_MACHINE)
    place(g, 37, 14, T.WALL_BUY)
    # Room C (bottom): perk
    fill_floor(floors, 32, 17, 7, 5, F.CARPET)
    place(g, 36, 19, T.PERK_MACHINE)

    # Connect lobby to east corridor
    door_tiles(g, [(LX + LW - 1, 24), (LX + LW - 1, 25)])
    g[24][LX + LW] = int(T.EMPTY)

    # ---- CENTRAL COURTYARD (between the wings) ----
    # Outdoor-feeling open area with the power switch.
    fill_floor(floors, 11, 9, 20, 13, F.DIRT)
    # Power switch in the dead centre (visible target)
    place(g, 21, 15, T.POWER_SWITCH)

    # Few interior debris pillars in the courtyard (for cover/interest)
    for px, py in ((14, 12), (28, 12), (14, 19), (28, 19), (21, 11), (21, 20)):
        pillar(g, px, py)

    # Couple of bloodied accents
    for fx, fy in ((16, 14), (24, 18), (20, 13)):
        floors[fy][fx] = int(F.CONCRETE_BLOODIED)

    # ---- TRAPS (one in each corridor) ----
    place(g, 6, 12, T.TRAP_FLOGGER)
    place(g, 36, 18, T.TRAP_FIRE)

    # ---- WINDOWS along the exterior ----
    for wx in (5, 12, 20, 28, 36):
        window_tile(g, wx, 4)
        window_tile(g, wx, H - 4)
    for wy in (8, 14, 20):
        window_tile(g, 2, wy)
        window_tile(g, 39, wy)

    # ---- ZOMBIE SPAWNS outside the building ----
    for sx, sy in ((1, 1), (W - 2, 1), (1, H - 2), (W - 2, H - 2),
                   (W // 2, 1), (W // 2, H - 2),
                   (1, H // 2), (W - 2, H // 2)):
        place(g, sx, sy, T.ZOMBIE_SPAWN)

    door_costs = {
        # Lobby ↔ courtyard
        (20, LY): 750, (21, LY): 750,
        # Lobby ↔ corridors (west + east)
        (LX, 24): 1000, (LX, 25): 1000,
        (LX + LW - 1, 24): 1000, (LX + LW - 1, 25): 1000,
        # PaP gate
        (35, 9): 1500, (36, 9): 1500,
    }
    wall_buys = {
        (LX + 1, LY + 2): "Shotgun",
        (LX + LW - 2, LY + 2): "AK74u",
        (4, 20): "MP40",
        (37, 14): "Galil",
    }
    perks = {
        (5, 12): "Quick Revive",
        (5, 19): "Juggernog",
        (36, 12): "Speed Cola",
        (36, 19): "Double Tap",
    }

    map_loader.save(
        g, background_image_path=None, name="verruckt",
        door_costs=door_costs, wall_buy_weapons=wall_buys,
        perk_machine_perks=perks,
        floor_grid=floors, wall_style="brick",
    )
    print(f"saved verruckt ({W}x{H}) — sanitorium-style multi-room layout")


if __name__ == "__main__":
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    import pygame
    pygame.init()
    pygame.display.set_mode((800, 600))
    build_nacht()
    build_verruckt()
