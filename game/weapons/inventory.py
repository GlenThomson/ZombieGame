"""A small, ordered inventory of Weapon instances. Foundation for mystery box,
pack-a-punch (which can swap an inventory slot for an upgraded weapon), and
weapon switching with number keys."""
from game.weapons.weapon import Weapon


class Inventory:
    MAX_SLOTS = 4

    def __init__(self, owner):
        self.owner = owner
        self.slots: list[Weapon | None] = [None] * self.MAX_SLOTS
        self.equipped_index = 0

    @property
    def equipped(self) -> Weapon | None:
        return self.slots[self.equipped_index]

    def add(self, def_name: str) -> bool:
        """Put a new weapon in the first empty slot. Returns False if full."""
        for i, slot in enumerate(self.slots):
            if slot is None:
                self.slots[i] = Weapon(self.owner, def_name)
                return True
        return False

    def replace_equipped(self, def_name: str):
        self.slots[self.equipped_index] = Weapon(self.owner, def_name)

    def equip(self, index: int):
        if 0 <= index < self.MAX_SLOTS and self.slots[index] is not None:
            self.equipped_index = index

    def cycle(self, direction: int = 1):
        for offset in range(1, self.MAX_SLOTS + 1):
            i = (self.equipped_index + offset * direction) % self.MAX_SLOTS
            if self.slots[i] is not None:
                self.equipped_index = i
                return
