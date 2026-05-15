"""A* pathfinding over the tile grid. Caller passes the grid and start/end
tile coordinates; nothing here knows about Zombie or Player."""
import pygame

from settings import TILE_SIZE
from game.world.tile import TileType

vector = pygame.math.Vector2


class _Node:
    __slots__ = ("pos", "g_cost", "h_cost", "f_cost", "previous")

    def __init__(self, x, y, target, g_cost=0):
        self.pos = vector(x, y)
        self.g_cost = g_cost
        self.h_cost = abs(target.x - x) + abs(target.y - y)
        self.f_cost = self.g_cost + self.h_cost
        self.previous = None


def find_path(grid, start_world_pos, end_tile_pos) -> list:
    """Returns a list of tile vectors from start to end (inclusive of end).
    `start_world_pos` is in world (pixel) coords; `end_tile_pos` is in tile coords."""
    rows = len(grid)
    cols = len(grid[0])
    start_tile = vector(start_world_pos.x // TILE_SIZE, start_world_pos.y // TILE_SIZE)

    def is_wall(cx, cy):
        if not (0 <= cx < cols and 0 <= cy < rows):
            return True
        return TileType.is_blocking(grid[int(cy)][int(cx)])

    open_nodes = [_Node(start_tile.x, start_tile.y, end_tile_pos)]
    closed = []

    while open_nodes:
        open_nodes.sort(key=lambda n: n.f_cost)
        current = open_nodes.pop(0)
        closed.append(current)

        if current.pos == end_tile_pos:
            path = []
            n = current
            while n:
                path.insert(0, n.pos)
                n = n.previous
            return path

        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                x = current.pos.x + dx
                y = current.pos.y + dy
                if not (0 <= x < cols and 0 <= y < rows):
                    continue

                # Don't cut diagonal corners through walls.
                if dx != 0 and dy != 0:
                    if is_wall(current.pos.x + dx, current.pos.y) or is_wall(
                        current.pos.x, current.pos.y + dy
                    ):
                        continue

                if is_wall(x, y):
                    continue
                if any(n.pos.x == x and n.pos.y == y for n in open_nodes + closed):
                    continue

                new_node = _Node(x, y, end_tile_pos, current.g_cost + 1)
                new_node.previous = current
                open_nodes.append(new_node)

    return []
