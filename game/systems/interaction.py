"""Interactable contract + per-frame proximity check.

Anything a player can stand near and press F on implements `Interactable`.
The PlayState scans all interactables once per frame and surfaces the prompt
of the nearest one to the HUD; key handling fires `interact()` on it."""
from __future__ import annotations
from typing import Protocol


class Interactable(Protocol):
    def get_world_pos(self) -> tuple[float, float]: ...
    def get_prompt(self, player) -> str | None: ...
    def interact(self, player) -> None: ...


def find_focused(player_pos, interactables, range_px: float):
    """Return the closest interactable within range_px, or None."""
    px, py = player_pos
    best = None
    best_d2 = range_px * range_px
    for it in interactables:
        ix, iy = it.get_world_pos()
        d2 = (ix - px) ** 2 + (iy - py) ** 2
        if d2 < best_d2:
            best = it
            best_d2 = d2
    return best
