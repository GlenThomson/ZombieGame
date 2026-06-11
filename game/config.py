"""Tiny persistent user config (player name, future: volume etc.).

Stored in the user's home directory so it survives across runs of both
`python main.py` and the frozen .exe (whose working dir is a throwaway
PyInstaller temp folder)."""
import json
import os

_PATH = os.path.join(os.path.expanduser("~"), ".zombies_game.json")

_DEFAULTS = {
    "player_name": "Player",
    "volume": 1.0,
    "fps_cap": 60,
    "best_rounds": {},   # map filename -> highest round reached
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


def fps_cap() -> int:
    try:
        return max(30, min(240, int(load().get("fps_cap", 60))))
    except (TypeError, ValueError):
        return 60


def volume() -> float:
    try:
        return max(0.0, min(1.0, float(load().get("volume", 1.0))))
    except (TypeError, ValueError):
        return 1.0


def best_round(map_name: str) -> int:
    rounds = load().get("best_rounds") or {}
    try:
        return int(rounds.get(map_name, 0))
    except (TypeError, ValueError):
        return 0


def record_best_round(map_name: str, round_reached: int) -> bool:
    """Persist the round if it beats the stored best. True = new record."""
    if not map_name:
        return False
    if round_reached <= best_round(map_name):
        return False
    data = load()
    rounds = dict(data.get("best_rounds") or {})
    rounds[map_name] = int(round_reached)
    save(best_rounds=rounds)
    return True
