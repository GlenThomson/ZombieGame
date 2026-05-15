"""Tile types stored in the map grid. The integer values are the on-disk
encoding; older maps still use the raw ints, so don't renumber casually."""
from enum import IntEnum


class TileType(IntEnum):
    EMPTY = 0
    WALL = 1
    BARB_WIRE = 2
    ZOMBIE_SPAWN = 3
    PLAYER_SPAWN = 4
    DOOR_CLOSED = 5
    DOOR_OPEN = 6
    WINDOW = 7
    WALL_BUY = 8
    PERK_MACHINE = 9
    MYSTERY_BOX = 10
    PACK_A_PUNCH = 11

    @classmethod
    def is_blocking(cls, value: int) -> bool:
        """Whether this tile blocks movement and pathfinding.

        Includes every entity that gets added to scene.walls so zombies
        path AROUND machines/boxes/intact-windows instead of trying to
        walk through and getting wedged."""
        return value in _BLOCKING_TILES


# Module-level set so the lookup is cheap.
_BLOCKING_TILES: frozenset[int] = frozenset({
    TileType.WALL,
    TileType.DOOR_CLOSED,
    TileType.WINDOW,
    TileType.WALL_BUY,
    TileType.PERK_MACHINE,
    TileType.MYSTERY_BOX,
    TileType.PACK_A_PUNCH,
})
