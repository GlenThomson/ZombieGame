"""A* pathfinding over the tile grid. Caller passes the grid and start/end
tile coordinates; nothing here knows about Zombie or Player."""
import heapq
import pygame

from settings import TILE_SIZE
from game.world.tile import TileType

vector = pygame.math.Vector2


def find_path(grid, start_world_pos, end_tile_pos) -> list:
    """Returns a list of tile vectors from start to end (inclusive of end).
    `start_world_pos` is in world (pixel) coords; `end_tile_pos` is in tile
    coords. Uses a binary heap + dict-based closed set so it scales on big
    maps (the previous list-sort version was O(N^3))."""
    rows = len(grid)
    cols = len(grid[0])
    sx = int(start_world_pos.x // TILE_SIZE)
    sy = int(start_world_pos.y // TILE_SIZE)
    tx = int(end_tile_pos.x)
    ty = int(end_tile_pos.y)

    if not (0 <= sx < cols and 0 <= sy < rows):
        return []
    if not (0 <= tx < cols and 0 <= ty < rows):
        return []

    def is_blocking(cx, cy):
        return TileType.is_blocking(grid[cy][cx])

    if (sx, sy) == (tx, ty):
        return [vector(sx, sy)]

    # Heap entries: (f_cost, counter, x, y). counter breaks ties so heap
    # never compares Vector2s.
    counter = 0
    open_heap = [(abs(tx - sx) + abs(ty - sy), 0, sx, sy)]
    came_from: dict[tuple[int, int], tuple[int, int] | None] = {(sx, sy): None}
    g_score: dict[tuple[int, int], int] = {(sx, sy): 0}

    neighbours = ((-1, -1), (0, -1), (1, -1),
                  (-1,  0),          (1,  0),
                  (-1,  1), (0,  1), (1,  1))

    while open_heap:
        _f, _c, cx, cy = heapq.heappop(open_heap)
        if (cx, cy) == (tx, ty):
            # Reconstruct
            path: list = []
            cur = (cx, cy)
            while cur is not None:
                path.append(vector(cur[0], cur[1]))
                cur = came_from[cur]
            path.reverse()
            return path

        cur_g = g_score[(cx, cy)]
        for dx, dy in neighbours:
            nx = cx + dx
            ny = cy + dy
            if not (0 <= nx < cols and 0 <= ny < rows):
                continue
            if is_blocking(nx, ny):
                continue
            # Don't cut diagonal corners through walls.
            if dx != 0 and dy != 0:
                if is_blocking(cx + dx, cy) or is_blocking(cx, cy + dy):
                    continue
            tentative_g = cur_g + 1
            key = (nx, ny)
            if tentative_g >= g_score.get(key, 1 << 30):
                continue
            g_score[key] = tentative_g
            came_from[key] = (cx, cy)
            counter += 1
            f = tentative_g + abs(tx - nx) + abs(ty - ny)
            heapq.heappush(open_heap, (f, counter, nx, ny))

    return []
