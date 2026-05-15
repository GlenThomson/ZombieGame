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
    else:
        grid = raw
        bg = None
        door_costs = {}
        wall_buy_weapons = {}
    return {
        "grid": grid,
        "background_image_path": bg,
        "door_costs": door_costs,
        "wall_buy_weapons": wall_buy_weapons,
    }


def save(grid: list, background_image_path: str | None, name: str,
         door_costs: dict | None = None, wall_buy_weapons: dict | None = None) -> None:
    os.makedirs(MAPS_DIR, exist_ok=True)
    payload = {
        "grid": grid,
        "background_image_path": background_image_path,
        "door_costs": door_costs or {},
        "wall_buy_weapons": wall_buy_weapons or {},
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
