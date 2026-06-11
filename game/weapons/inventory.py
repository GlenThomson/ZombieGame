"""A small, ordered inventory of Weapon instances. Foundation for mystery box,
pack-a-punch (which can swap an inventory slot for an upgraded weapon), and
weapon switching with number keys.

BO1 rules: you carry TWO guns. Mule Kick raises the cap to three (the
PerkSystem bumps `max_slots`)."""
from game.weapons.weapon import Weapon


class Inventory:
    MAX_SLOTS = 4          # physical slot array size (never shrinks)
    DEFAULT_CAP = 2        # BO1: two weapons without Mule Kick

    def __init__(self, owner):
        self.owner = owner
        self.slots: list[Weapon | None] = [None] * self.MAX_SLOTS
        self.equipped_index = 0
        self.max_slots = self.DEFAULT_CAP

    @property
    def equipped(self) -> Weapon | None:
        return self.slots[self.equipped_index]

    def add(self, def_name: str) -> bool:
        """Put a new weapon in the first empty usable slot. Returns False
        when you're already carrying max_slots weapons (caller then swaps
        the equipped gun instead, CoD-style)."""
        for i in range(self.max_slots):
            if self.slots[i] is None:
                self.slots[i] = Weapon(self.owner, def_name)
                return True
        return False

    def replace_equipped(self, def_name: str):
        self.slots[self.equipped_index] = Weapon(self.owner, def_name)

    def equip(self, index: int):
        if 0 <= index < self.max_slots and self.slots[index] is not None:
            self.equipped_index = index

    def cycle(self, direction: int = 1):
        for offset in range(1, self.max_slots + 1):
            i = (self.equipped_index + offset * direction) % self.max_slots
            if self.slots[i] is not None:
                self.equipped_index = i
                return
