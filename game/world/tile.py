"""Tile types stored in the map grid. The integer values are the on-disk
encoding; older maps still use the raw ints, so don't renumber casually.

Maps now have TWO grids:
- floor_grid: per-cell FloorType (always something, default CONCRETE)
- object_grid: per-cell TileType (0 = nothing on top of the floor)

Old maps with only `grid` are treated as object_grid with a default floor.
"""
from enum import IntEnum


class FloorType(IntEnum):
    """Floor tile under each cell. Pure visual — doesn't affect movement."""
    CONCRETE = 0
    WOOD = 1
    BRICK = 2
    METAL = 3
    DIRT = 4
    ASPHALT = 5
    CARPET = 6
    GRASS = 7
    CONCRETE_BLOODIED = 8


# Maps each FloorType to its asset filename (under assets/images/tiles/).
FLOOR_SPRITES: dict[int, str] = {
    int(FloorType.CONCRETE):          "floor_concrete.png",
    int(FloorType.CONCRETE_BLOODIED): "floor_concrete_bloodied.png",
    int(FloorType.WOOD):              "floor_wood.png",
    int(FloorType.BRICK):             "floor_brick.png",
    int(FloorType.METAL):             "floor_metal.png",
    int(FloorType.DIRT):              "floor_dirt.png",
    int(FloorType.ASPHALT):           "floor_asphalt.png",
    int(FloorType.CARPET):            "floor_carpet.png",
    int(FloorType.GRASS):             "floor_grass.png",
}


# Wall visual styles — one per map (stored in map metadata).
WALL_STYLES: dict[str, str] = {
    "brick":     "wall_brick.png",
    "concrete":  "wall_concrete.png",
    "wood":      "wall_wood.png",
    "metal":     "wall_metal.png",
    "wood_dark": "wall_wood_user.png",   # imported user sprite
    "planks_h":  "wall_planks_h.png",
    "panel":     "wall_panel.png",
}


# Decor (furniture / props) layer. Each map can hold a list of decor
# entries: {"pos": (x, y), "kind": "couch"}. Sprites live in
# assets/images/decor/ at their natural size — they may visually overflow
# the cell they sit in (a couch is 80x37, sits in one cell but spreads
# to its right).
DECOR_SPRITES: dict[str, str] = {
    "couch":       "couch.png",
    "sink":        "sink.png",
    "chest":       "chest.png",
    "tv":          "tv.png",
    "keyboard":    "keyboard.png",
    "chair":       "chair.png",
    "bed":         "bed.png",
    "wood_plank":  "wood_plank.png",
    "gold_box":    "gold_box.png",
    "plant_small": "plant_small.png",
    "plant_large": "plant_large.png",
}


# Whether each decor type physically blocks movement.
DECOR_BLOCKING: dict[str, bool] = {
    "couch":       True,
    "sink":        True,
    "chest":       True,
    "tv":          True,
    "keyboard":    False,
    "chair":       True,
    "bed":         True,
    "wood_plank":  False,   # decoration, walkable
    "gold_box":    True,
    "plant_small": False,
    "plant_large": False,
}


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
    POWER_SWITCH = 12
    TRAP_FLOGGER = 13
    TRAP_FIRE = 14
    INVISIBLE_WALL = 15  # blocks movement + bullets, never drawn

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
    TileType.INVISIBLE_WALL,
    TileType.DOOR_CLOSED,
    # WINDOW is deliberately NOT here: zombies must be able to PATH through
    # window tiles so they walk up to sealed buildings, get physically held
    # by the Window sprite (it sits in scene.walls until its planks are
    # smashed), break in, and continue — BO1 barrier behaviour. Movement is
    # still blocked because collision uses the sprite group, not this set.
    TileType.WALL_BUY,
    TileType.PERK_MACHINE,
    TileType.MYSTERY_BOX,
    TileType.PACK_A_PUNCH,
    TileType.POWER_SWITCH,
    # Traps don't block — they're floor tiles
})
