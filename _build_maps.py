"""Generate two new handcrafted maps:
- nacht.pkl  : tiny starter map (Nacht der Untoten clone). No power. No PaP. No perks.
- verruckt.pkl : two halves split by a central power-room. Perks + PaP gated by power.
"""
from game.world.tile import TileType
from game.world import map_loader


def make_grid(w, h, fill=TileType.EMPTY):
    return [[fill for _ in range(w)] for _ in range(h)]


def outer_walls(grid):
    h = len(grid)
    w = len(grid[0])
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
# NACHT DER UNTOTEN
#
# 25x18, single building with 4 windows for zombie entry,
# a mystery box, two wall-buys. Player spawns in the centre.
# No perks, no power, no PaP — true to the original.
# ============================================================

def build_nacht():
    W, H = 25, 18
    g = make_grid(W, H)
    outer_walls(g)

    # Player spawn (centre)
    g[H // 2][W // 2] = TileType.PLAYER_SPAWN

    # Windows on each wall
    g[0][6]  = TileType.WINDOW
    g[0][18] = TileType.WINDOW
    g[H - 1][6]  = TileType.WINDOW
    g[H - 1][18] = TileType.WINDOW
    g[6][0]  = TileType.WINDOW
    g[H - 7][0] = TileType.WINDOW
    g[6][W - 1]  = TileType.WINDOW
    g[H - 7][W - 1] = TileType.WINDOW

    # Mystery box near a corner
    g[3][3] = TileType.MYSTERY_BOX

    # Two wall buys on opposite walls
    g[H // 2][1] = TileType.WALL_BUY
    g[H // 2][W - 2] = TileType.WALL_BUY

    # Zombie spawn points behind each window so attackers come from outside.
    # (Each window is on the perimeter; we set the window tile to ZOMBIE_SPAWN
    #  is wrong because that destroys the window. Instead, place spawn points
    #  one tile in from each wall NEAR but not on a window, so that pathfinding
    #  paths to the windows then through them once broken.)
    # Actually: putting spawns at the window tile would conflict. Instead the
    # auto-seed already creates spawns at empty perimeter tiles — we put
    # explicit spawns at the four corners (which are walls, so pick adjacent).
    g[1][2]      = TileType.ZOMBIE_SPAWN
    g[1][W - 3]  = TileType.ZOMBIE_SPAWN
    g[H - 2][2]      = TileType.ZOMBIE_SPAWN
    g[H - 2][W - 3]  = TileType.ZOMBIE_SPAWN

    # Wall_buy weapons + door-cost dicts — Nacht has no doors
    wall_buys = {
        (1, H // 2): "Shotgun",
        (W - 2, H // 2): "MP40",
    }

    map_loader.save(
        g,
        background_image_path="assets/images/bg_cabin.jpeg",
        name="nacht",
        wall_buy_weapons=wall_buys,
    )
    print(f"saved nacht ({W}x{H})")


# ============================================================
# VERRÜCKT (multi-room, power gating)
# ============================================================

def build_verruckt():
    W, H = 40, 28
    g = make_grid(W, H)
    outer_walls(g)

    # ------- Room layout -------
    # Two starting halves separated by a central wall (vertical).
    # Doors connect each half to the central power room.
    midx = W // 2
    # Vertical wall splitting left/right halves
    vertical_wall(g, midx, 1, H - 2)

    # ------- Doors connecting halves to centre -------
    # We carve a 3-tile-tall door in the central wall around the middle.
    door_y = H // 2
    g[door_y - 1][midx] = TileType.DOOR_CLOSED
    g[door_y][midx]     = TileType.DOOR_CLOSED
    g[door_y + 1][midx] = TileType.DOOR_CLOSED

    # ------- Sub-rooms in the LEFT half -------
    # Player spawn (south-west)
    g[H - 4][3] = TileType.PLAYER_SPAWN

    # Wall buys in starting room
    g[H - 4][1] = TileType.WALL_BUY  # M1911 ammo / Olympia
    g[H - 4][W - 2] = TileType.WALL_BUY  # something on the other side

    # Carve a small inner room in the LEFT half
    horizontal_wall(g, 8, 1, midx - 1, except_at=(5, 6))  # door gap at x=5,6
    g[8][5] = TileType.DOOR_CLOSED
    g[8][6] = TileType.DOOR_CLOSED
    # Mystery box inside the upper-left room
    g[3][4] = TileType.MYSTERY_BOX

    # Wall buy on the inner-room wall
    g[7][1] = TileType.WALL_BUY

    # ------- Sub-rooms in the RIGHT half -------
    # Carve an upper-right room
    horizontal_wall(g, 8, midx + 1, W - 2, except_at=(W - 5, W - 6))
    g[8][W - 5] = TileType.DOOR_CLOSED
    g[8][W - 6] = TileType.DOOR_CLOSED
    # Pack-a-Punch in the upper-right room (gated by both door + power)
    g[3][W - 4] = TileType.PACK_A_PUNCH

    # ------- POWER ROOM (central, narrow corridor between halves) -------
    # The central column (x=midx) was already walled. We need a small power
    # room. Use a 3-tile-wide corridor along x = midx +/- 1.
    # Carve out the center corridor once doors open.
    # Place the power switch INSIDE the corridor, accessible after doors open.
    # We position it on the inside of the central wall at the bottom.
    g[H - 4][midx - 1] = TileType.POWER_SWITCH

    # ------- Perks (gated by power) -------
    # Quick Revive in starting room (cheap, available before power)
    g[H - 6][2] = TileType.PERK_MACHINE  # Quick Revive (auto-seed picks first PERKS entry which is QR)
    # Juggernog in upper-left
    g[2][3] = TileType.PERK_MACHINE
    # Speed Cola in upper-right
    g[2][W - 4] = TileType.PERK_MACHINE
    # Double Tap in lower-right
    g[H - 6][W - 3] = TileType.PERK_MACHINE

    # ------- Traps -------
    g[H // 2][midx - 6] = TileType.TRAP_FLOGGER
    g[H // 2][midx + 6] = TileType.TRAP_FIRE

    # ------- Windows + zombie spawns on the outer perimeter -------
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

    # Zombie spawn points
    g[1][1] = TileType.ZOMBIE_SPAWN
    g[1][W - 2] = TileType.ZOMBIE_SPAWN
    g[H - 2][1] = TileType.ZOMBIE_SPAWN
    g[H - 2][W - 2] = TileType.ZOMBIE_SPAWN

    # Per-tile wall-buy weapon assignments
    wall_buys = {
        (1, H - 4): "Shotgun",       # starting wall buy
        (W - 2, H - 4): "AK74u",     # starting other side
        (1, 7): "MP40",              # inner-room
    }

    # Per-tile perk assignments
    perks = {
        (2, H - 6): "Quick Revive",
        (3, 2): "Juggernog",
        (W - 4, 2): "Speed Cola",
        (W - 3, H - 6): "Double Tap",
    }

    # Per-tile door costs
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
        background_image_path="assets/images/bg_warehouse.jpeg",
        name="verruckt",
        door_costs=door_costs,
        wall_buy_weapons=wall_buys,
        perk_machine_perks=perks,
    )
    print(f"saved verruckt ({W}x{H})")


if __name__ == "__main__":
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    import pygame
    pygame.init()
    pygame.display.set_mode((800, 600))
    build_nacht()
    build_verruckt()
