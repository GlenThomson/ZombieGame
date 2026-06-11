"""Tiny persistent user config (player name, future: volume etc.).

Stored in the user's home directory so it survives across runs of both
`python main.py` and the frozen .exe (whose working dir is a throwaway
PyInstaller temp folder)."""
import json
import os

_PATH = os.path.join(os.path.expanduser("~"), ".zombies_game.json")

_DEFAULTS = {
    "player_name": "Player",
}


def load() -> dict:
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return dict(_DEFAULTS)
        merged = dict(_DEFAULTS)
        merged.update(data)
        return merged
    except (OSError, ValueError):
        return dict(_DEFAULTS)


def save(**updates) -> None:
    data = load()
    data.update(updates)
    try:
        with open(_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        pass


def player_name() -> str:
    name = str(load().get("player_name", "Player")).strip()
    return name[:16] or "Player"
