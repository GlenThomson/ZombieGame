"""Perk catalog + PerkSystem.

A perk applies a set of named modifiers to the player (via ModifierStack).
The modifier `source` is set to the perk name so the perk can be removed
cleanly (on death, on swap-out).

CoD-faithful set:
- Juggernog:   max_health x 2.5    (2500 pts)
- Speed Cola:  reload_time x 0.5   (3000 pts)
- Double Tap:  fire_rate x 1.33, damage x 2  (2000 pts)
- Stamin-Up:   speed x 1.4         (2000 pts)
- Mule Kick:   third weapon slot   (4000 pts)
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Perk:
    name: str
    cost: int
    icon_color: tuple[int, int, int]
    # list of (stat, additive, multiplier) tuples to push onto ModifierStack
    modifiers: tuple[tuple[str, float, float], ...]


PERKS: dict[str, Perk] = {
    "Quick Revive": Perk(
        name="Quick Revive", cost=500, icon_color=(180, 220, 255),
        # No modifier stack entries — custom behaviour applied in
        # PerkSystem._apply (3 self-revive charges in SP, faster teammate
        # revives in MP).
        modifiers=(),
    ),
    "Juggernog": Perk(
        name="Juggernog", cost=2500, icon_color=(220, 0, 0),
        modifiers=(("max_health", 0.0, 2.5),),
    ),
    "Speed Cola": Perk(
        name="Speed Cola", cost=3000, icon_color=(0, 220, 80),
        modifiers=(("reload_time", 0.0, 0.5),),
    ),
    "Double Tap": Perk(
        name="Double Tap", cost=2000, icon_color=(220, 220, 0),
        modifiers=(("fire_rate", 0.0, 1.33), ("damage", 0.0, 2.0)),
    ),
    "Stamin-Up": Perk(
        name="Stamin-Up", cost=2000, icon_color=(0, 200, 220),
        modifiers=(("speed", 0.0, 1.4),),
    ),
    "Mule Kick": Perk(
        name="Mule Kick", cost=4000, icon_color=(220, 130, 0),
        modifiers=(("inventory_slots", 1.0, 1.0),),
    ),
}


class PerkSystem:
    """Tracks which perks the player owns, applies/removes their modifiers."""

    def __init__(self, player):
        self.player = player
        self._owned: list[Perk] = []

    def owned(self) -> list[Perk]:
        return list(self._owned)

    def has(self, perk_name: str) -> bool:
        return any(p.name == perk_name for p in self._owned)

    def buy(self, perk_name: str) -> bool:
        """Returns True if the perk was successfully purchased."""
        if self.has(perk_name):
            return False
        perk = PERKS.get(perk_name)
        if perk is None:
            return False
        if not self.player.spend(perk.cost):
            return False
        self._apply(perk)
        return True

    def _apply(self, perk: Perk):
        for stat, additive, multiplier in perk.modifiers:
            self.player.modifiers.add(stat, perk.name, additive=additive, multiplier=multiplier)
        self._owned.append(perk)
        if perk.name == "Juggernog":
            # Tops you off to the new max (CoD behavior).
            self.player.health = self.player.max_health
        elif perk.name == "Quick Revive":
            # 3 self-revive charges. In MP, also speeds up reviving teammates
            # (handled in PlayState._handle_revives).
            self.player.quick_revive_charges = 3
        elif perk.name == "Mule Kick":
            # Third weapon slot.
            self.player.inventory.max_slots = 3

    def clear_all(self):
        for perk in self._owned:
            self.player.modifiers.remove_source(perk.name)
        self._owned.clear()
