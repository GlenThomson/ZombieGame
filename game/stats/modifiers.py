"""Stack of additive + multiplicative stat modifiers.

A stat is computed as: base * product(multipliers) + sum(additives).
Modifiers are tagged with a source key so a perk can be removed by name.
This is the foundation for perks (Juggernog, Speed Cola, etc.) and weapon
upgrades (Pack-a-Punch).
"""
from collections import defaultdict


class ModifierStack:
    def __init__(self):
        # key: stat name -> list of (source, additive, multiplier)
        self._mods: dict[str, list[tuple[str, float, float]]] = defaultdict(list)

    def add(self, stat: str, source: str, additive: float = 0.0, multiplier: float = 1.0):
        # Replace any existing modifier from the same source on the same stat.
        self.remove(stat, source)
        self._mods[stat].append((source, additive, multiplier))

    def remove(self, stat: str, source: str):
        self._mods[stat] = [m for m in self._mods[stat] if m[0] != source]

    def remove_source(self, source: str):
        for stat in list(self._mods):
            self.remove(stat, source)

    def has(self, source: str) -> bool:
        return any(m[0] == source for mods in self._mods.values() for m in mods)

    def apply(self, stat: str, base: float) -> float:
        mods = self._mods.get(stat, ())
        mult = 1.0
        add = 0.0
        for _src, a, m in mods:
            mult *= m
            add += a
        return base * mult + add
