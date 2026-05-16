"""Generate two handcrafted tile-based maps:
- nacht.pkl  : tiny starter (Nacht der Untoten clone). Wood floor + wood walls.
- verruckt.pkl : two-half map split by power-room. Concrete floor + brick walls.
"""
from game.world.tile import TileType, FloorType
from game.world import map_loader


def make_grid(w, h, fill=TileType.EMPTY):
    return [[fill for _ in range(w)] for _ in range(h)]


def make_floor_grid(w, h, fill: FloorType):
    return [[int(fill) for _ in range(w)] for _ in range(h)]


def outer_walls(grid):
    h, w = len(grid), len(grid[0])
    for y in range(h):
        grid[y][0] = TileType.WALL
        grid[y][w - 1] = TileType.WALL
    for x in range(w):
        grid[0][x] = TileType.WALL
        grid[h - 1][x] = TileType.WALL


def vertical_wall(grid, x, y0, y1, except_at=()):
    for y in range(y0, y1 + 1):
        if y in except_at:
            continue
        grid[y][x] = TileType.WALL


def horizontal_wall(grid, y, x0, x1, except_at=()):
    for x in range(x0, x1 + 1):
        if x in except_at:
            continue
        grid[y][x] = TileType.WALL


# ============================================================
# NACHT DER UNTOTEN — wooden cabin theme
# ============================================================

def build_nacht():
    W, H = 25, 18
    g = make_grid(W, H)
    floors = make_floor_grid(W, H, FloorType.WOOD)
    outer_walls(g)

    g[H // 2][W // 2] = TileType.PLAYER_SPAWN

    # Windows on each side
    for x in (6, 18):
        g[0][x] = TileType.WINDOW
        g[H - 1][x] = TileType.WINDOW
    for y in (6, H - 7):
        g[y][0] = TileType.WINDOW
        g[y][W - 1] = TileType.WINDOW

    # Mystery box near a corner
    g[3][3] = TileType.MYSTERY_BOX

    # Two wall buys on opposite walls
    g[H // 2][1] = TileType.WALL_BUY
    g[H // 2][W - 2] = TileType.WALL_BUY

    # Zombie spawn points outside the windows
    g[1][2] = TileType.ZOMBIE_SPAWN
    g[1][W - 3] = TileType.ZOMBIE_SPAWN
    g[H - 2][2] = TileType.ZOMBIE_SPAWN
    g[H - 2][W - 3] = TileType.ZOMBIE_SPAWN

    # A blood splatter floor accent in the centre for atmosphere
    floors[H // 2 - 1][W // 2 + 2] = int(FloorType.CONCRETE_BLOODIED)

    wall_buys = {
        (1, H // 2): "Shotgun",
        (W - 2, H // 2): "MP40",
    }

    map_loader.save(
        g,
        background_image_path=None,   # tile-based, no big bg
        name="nacht",
        wall_buy_weapons=wall_buys,
        floor_grid=floors,
        wall_style="wood",
    )
    print(f"saved nacht ({W}x{H}) wood-themed")


# ============================================================
# VERRÜCKT — concrete + brick, multi-room with power gating
# ============================================================

def build_verruckt():
    W, H = 40, 28
    g = make_grid(W, H)
    floors = make_floor_grid(W, H, FloorType.CONCRETE)
    outer_walls(g)

    # Vertical wall down the middle, with a 3-tile door near the centre
    midx = W // 2
    vertical_wall(g, midx, 1, H - 2)
    door_y = H // 2
    g[door_y - 1][midx] = TileType.DOOR_CLOSED
    g[door_y][midx]     = TileType.DOOR_CLOSED
    g[door_y + 1][midx] = TileType.DOOR_CLOSED

    # Player spawn (south-west)
    g[H - 4][3] = TileType.PLAYER_SPAWN

    # Wall buys in starting room
    g[H - 4][1] = TileType.WALL_BUY
    g[H - 4][W - 2] = TileType.WALL_BUY

    # Inner-room walls in the LEFT half (a bedroom-ish area in the upper left)
    horizontal_wall(g, 8, 1, midx - 1, except_at=(5, 6))
    g[8][5] = TileType.DOOR_CLOSED
    g[8][6] = TileType.DOOR_CLOSED
    g[3][4] = TileType.MYSTERY_BOX
    g[7][1] = TileType.WALL_BUY

    # Inner-room walls in the RIGHT half (PaP room)
    horizontal_wall(g, 8, midx + 1, W - 2, except_at=(W - 5, W - 6))
    g[8][W - 5] = TileType.DOOR_CLOSED
    g[8][W - 6] = TileType.DOOR_CLOSED
    g[3][W - 4] = TileType.PACK_A_PUNCH

    # Power switch on the central wall, accessible after the door opens
    g[H - 4][midx - 1] = TileType.POWER_SWITCH

    # Perks
    g[H - 6][2] = TileType.PERK_MACHINE
    g[2][3] = TileType.PERK_MACHINE
    g[2][W - 4] = TileType.PERK_MACHINE
    g[H - 6][W - 3] = TileType.PERK_MACHINE

    # Map traps near the doorway
    g[H // 2][midx - 6] = TileType.TRAP_FLOGGER
    g[H // 2][midx + 6] = TileType.TRAP_FIRE

    # Windows + zombie spawns on the perimeter
    for x in (3, 8, midx - 4, midx + 4, W - 9, W - 4):
        if g[0][x] == TileType.WALL:
            g[0][x] = TileType.WINDOW
        if g[H - 1][x] == TileType.WALL:
            g[H - 1][x] = TileType.WINDOW
    for y in (4, 10, H - 6):
        if g[y][0] == TileType.WALL:
            g[y][0] = TileType.WINDOW
        if g[y][W - 1] == TileType.WALL:
            g[y][W - 1] = TileType.WINDOW

    g[1][1] = TileType.ZOMBIE_SPAWN
    g[1][W - 2] = TileType.ZOMBIE_SPAWN
    g[H - 2][1] = TileType.ZOMBIE_SPAWN
    g[H - 2][W - 2] = TileType.ZOMBIE_SPAWN

    # Floor accents — bloodied concrete patches scattered around
    for (fx, fy) in ((6, 5), (12, 12), (25, 16), (W - 7, 6), (3, H - 8)):
        floors[fy][fx] = int(FloorType.CONCRETE_BLOODIED)
    # PaP room gets metal grating floor
    for y in range(2, 7):
        for x in range(midx + 2, W - 2):
            floors[y][x] = int(FloorType.METAL)
    # Bedroom in left has carpet
    for y in range(2, 7):
        for x in range(2, midx - 1):
            floors[y][x] = int(FloorType.CARPET)

    wall_buys = {
        (1, H - 4): "Shotgun",
        (W - 2, H - 4): "AK74u",
        (1, 7): "MP40",
    }
    perks = {
        (2, H - 6): "Quick Revive",
        (3, 2): "Juggernog",
        (W - 4, 2): "Speed Cola",
        (W - 3, H - 6): "Double Tap",
    }
    door_costs = {
        (midx, door_y - 1): 1000,
        (midx, door_y):     1000,
        (midx, door_y + 1): 1000,
        (5, 8): 750,
        (6, 8): 750,
        (W - 5, 8): 1500,
        (W - 6, 8): 1500,
    }

    map_loader.save(
        g,
        background_image_path=None,
        name="verruckt",
        door_costs=door_costs,
        wall_buy_weapons=wall_buys,
        perk_machine_perks=perks,
        floor_grid=floors,
        wall_style="brick",
    )
    print(f"saved verruckt ({W}x{H}) concrete+brick themed")


if __name__ == "__main__":
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    import pygame
    pygame.init()
    pygame.display.set_mode((800, 600))
    build_nacht()
    build_verruckt()
