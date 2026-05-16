"""Load and save map files. Backwards-compatible across three formats:
- v1: a bare 2D list (just the grid)
- v2: dict with 'grid' + optional 'background_image_path'
- v3: v2 plus optional metadata: 'door_costs', 'wall_buy_weapons'.
   (Windows currently carry no metadata.)
"""
import os
import pickle


MAPS_DIR = "maps"


def list_maps() -> list[str]:
    if not os.path.isdir(MAPS_DIR):
        return []
    return sorted(f for f in os.listdir(MAPS_DIR) if f.endswith(".pkl"))


def load(path: str) -> dict:
    with open(path, "rb") as f:
        raw = pickle.load(f)
    if isinstance(raw, dict):
        grid = raw["grid"]
        bg = _resolve_bg_path(raw.get("background_image_path"))
        door_costs = raw.get("door_costs") or {}
        wall_buy_weapons = raw.get("wall_buy_weapons") or {}
        perk_machine_perks = raw.get("perk_machine_perks") or {}
        floor_grid = raw.get("floor_grid")
        wall_style = raw.get("wall_style", "brick")
    else:
        grid = raw
        bg = None
        door_costs = {}
        wall_buy_weapons = {}
        perk_machine_perks = {}
        floor_grid = None
        wall_style = "brick"
    return {
        "grid": grid,
        "background_image_path": bg,
        "door_costs": door_costs,
        "wall_buy_weapons": wall_buy_weapons,
        "perk_machine_perks": perk_machine_perks,
        "floor_grid": floor_grid,   # may be None for legacy maps
        "wall_style": wall_style,
    }


def save(grid: list, background_image_path: str | None, name: str,
         door_costs: dict | None = None, wall_buy_weapons: dict | None = None,
         perk_machine_perks: dict | None = None,
         floor_grid: list | None = None,
         wall_style: str = "brick") -> None:
    os.makedirs(MAPS_DIR, exist_ok=True)
    payload = {
        "grid": grid,
        "background_image_path": background_image_path,
        "door_costs": door_costs or {},
        "wall_buy_weapons": wall_buy_weapons or {},
        "perk_machine_perks": perk_machine_perks or {},
        "floor_grid": floor_grid,
        "wall_style": wall_style,
    }
    with open(os.path.join(MAPS_DIR, f"{name}.pkl"), "wb") as f:
        pickle.dump(payload, f)


def _resolve_bg_path(stored_path: str | None) -> str | None:
    if not stored_path:
        return None
    if os.path.isfile(stored_path):
        return stored_path
    basename = os.path.basename(stored_path)
    local = os.path.join("assets", "images", basename)
    return local if os.path.isfile(local) else None
