"""Render an entire map (.pkl) into a single PNG so you can eyeball the
layout without launching the game.

Usage: python _render_map.py <map_name>
       python _render_map.py nacht
       python _render_map.py verruckt
"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
pygame.init()
pygame.display.set_mode((100, 100))   # bare display so convert_alpha works

from settings import TILE_SIZE
from game import assets
from game.world import map_loader
from game.world.tile import (
    TileType, FloorType, FLOOR_SPRITES, WALL_STYLES,
    DECOR_SPRITES,
)


def render(name: str) -> str:
    path = f"maps/{name}.pkl"
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    data = map_loader.load(path)
    grid = data["grid"]
    floor_grid = data.get("floor_grid")
    wall_style = data.get("wall_style", "brick")
    decor = data.get("decor", []) or []

    rows, cols = len(grid), len(grid[0])
    if floor_grid is None:
        floor_grid = [[int(FloorType.CONCRETE)] * cols for _ in range(rows)]

    surf = pygame.Surface((cols * TILE_SIZE, rows * TILE_SIZE))
    surf.fill((0, 0, 0))

    # Floor
    for y in range(rows):
        for x in range(cols):
            png = FLOOR_SPRITES.get(int(floor_grid[y][x]))
            if png is None:
                continue
            img = assets.image(os.path.join("tiles", png))
            surf.blit(img, (x * TILE_SIZE, y * TILE_SIZE))

    # Walls
    wall_png = WALL_STYLES.get(wall_style)
    if wall_png and os.path.isfile(os.path.join("assets", "images", "tiles", wall_png)):
        wall_img = assets.image(os.path.join("tiles", wall_png))
        for y in range(rows):
            for x in range(cols):
                if int(grid[y][x]) == int(TileType.WALL):
                    surf.blit(wall_img, (x * TILE_SIZE, y * TILE_SIZE))

    # Decor (sorted by bottom-y so taller items render correctly behind shorter)
    decor_drawn = []
    for entry in decor:
        kind = entry.get("kind")
        pos = entry.get("pos")
        if not (kind and pos):
            continue
        png = DECOR_SPRITES.get(kind)
        if png is None:
            continue
        full = os.path.join("assets", "images", "decor", png)
        if not os.path.isfile(full):
            continue
        img = assets.image(os.path.join("decor", png))
        x, y = pos
        rect = img.get_rect(bottomleft=(x * TILE_SIZE, (y + 1) * TILE_SIZE))
        decor_drawn.append((rect.bottom, rect, img))
    for _bottom, rect, img in sorted(decor_drawn, key=lambda t: t[0]):
        surf.blit(img, rect)

    # Other tile-grid items (doors, machines, spawns, windows) drawn as
    # coloured boxes with a small letter so the layout reads cleanly.
    overlay_styles = {
        2:  ((140, 100, 50), (200, 180, 200), "B"),  # barb wire (now likely none)
        3:  ((200, 30, 30), None, "Z"),              # zombie spawn
        4:  ((180, 30, 200), None, "P"),             # player spawn
        5:  ((110, 60, 20), (255, 215, 0), "D"),     # door closed
        6:  ((60, 35, 15), (120, 80, 40), "d"),      # door open
        7:  ((140, 100, 50), (200, 180, 200), "W"),  # window
        8:  ((40, 40, 50), (255, 215, 0), "$"),      # wall buy
        9:  ((220, 0, 0), (255, 255, 255), "!"),     # perk machine
        10: ((60, 30, 10), (255, 215, 0), "?"),      # mystery box
        11: ((200, 160, 0), (255, 230, 80), "*"),    # PaP
        12: ((50, 50, 60), (255, 220, 80), "+"),     # power switch
        13: ((60, 60, 60), (200, 200, 200), "X"),    # flogger
        14: ((180, 60, 0), (255, 130, 0), "F"),      # fire trap
        15: ((255, 0, 255), (255, 255, 255), "I"),   # invisible wall (debug only)
    }
    font = pygame.font.Font(None, 22)
    for y in range(rows):
        for x in range(cols):
            tile = int(grid[y][x])
            style = overlay_styles.get(tile)
            if style is None:
                continue
            fill, border, label = style
            rect = (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(surf, fill, rect)
            if border:
                pygame.draw.rect(surf, border, rect, 2)
            text = font.render(label, True, (255, 255, 255))
            surf.blit(text, text.get_rect(center=(x * TILE_SIZE + TILE_SIZE // 2,
                                                    y * TILE_SIZE + TILE_SIZE // 2)))

    out = f"_render_{name}.png"
    pygame.image.save(surf, out)
    print(f"wrote {out}  ({cols}x{rows} tiles, {cols * TILE_SIZE}x{rows * TILE_SIZE} px)")
    return out


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "nacht"
    render(name)
