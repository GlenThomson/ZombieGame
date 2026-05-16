"""A single equipped weapon instance. Holds its own ammo + reload state.

Stats are computed from the WeaponDef + the owner's ModifierStack (perks
like Speed Cola affect *all* weapons) + the weapon's own ModifierStack
(Pack-a-Punch affects *this* weapon only)."""
import pygame

from game import assets
from game.entities.bullet import Bullet
from game.stats.modifiers import ModifierStack
from game.utils import adjusted_mouse_position
from game.weapons.definitions import WEAPON_DEFS

vector = pygame.math.Vector2


class Weapon:
    def __init__(self, owner, def_name: str):
        self.owner = owner
        self.definition = WEAPON_DEFS[def_name]
        self.modifiers = ModifierStack()
        self.shoot_sound = assets.sound(self.definition.shoot_sound)
        self.reload_sound = assets.sound("reload_sound.mp3")
        self.current_ammo = self.definition.magazine_size
        self.reserve_ammo = self.definition.reserve_max
        self.is_reloading = False
        self.last_shot_time = 0
        self.reload_started_at = 0
        self.is_packed = False  # set True when Pack-a-Punched

    def _stat(self, key: str, base: float) -> float:
        # Owner perks first, then this weapon's own modifiers (PaP etc).
        owner_adjusted = self.owner.modifiers.apply(key, base)
        return self.modifiers.apply(key, owner_adjusted)

    @property
    def name(self) -> str:
        if not self.is_packed:
            return self.definition.name
        from game.weapons.definitions import PACKED_NAMES
        return PACKED_NAMES.get(self.definition.name, f"{self.definition.name} PaP")

    @property
    def magazine_size(self) -> int:
        return int(self._stat("magazine_size", self.definition.magazine_size))

    @property
    def reserve_max(self) -> int:
        return int(self._stat("reserve_max", self.definition.reserve_max))

    @property
    def fire_rate(self) -> float:
        return self._stat("fire_rate", self.definition.fire_rate)

    @property
    def reload_time(self) -> float:
        return self._stat("reload_time", self.definition.reload_time)

    @property
    def damage(self) -> int:
        return int(self._stat("damage", self.definition.damage))

    @property
    def penetration(self) -> int:
        return int(self._stat("penetration", self.definition.penetration))

    def apply_pack_a_punch(self):
        from settings import (
            PACK_A_PUNCH_DAMAGE_MULT,
            PACK_A_PUNCH_FIRE_RATE_MULT,
            PACK_A_PUNCH_MAG_MULT,
        )
        self.modifiers.add("damage", "PaP", multiplier=PACK_A_PUNCH_DAMAGE_MULT)
        self.modifiers.add("fire_rate", "PaP", multiplier=PACK_A_PUNCH_FIRE_RATE_MULT)
        self.modifiers.add("magazine_size", "PaP", multiplier=PACK_A_PUNCH_MAG_MULT)
        self.is_packed = True
        # Refill to the new bigger mag.
        self.current_ammo = self.magazine_size
        self.is_reloading = False

    def shoot(self):
        now = pygame.time.get_ticks()
        if self.is_reloading:
            return
        if self.current_ammo <= 0:
            self.reload()
            return
        if now - self.last_shot_time < 1000 / self.fire_rate:
            return

        self.last_shot_time = now
        self.current_ammo -= 1
        self._announce("shoot", self.definition.shoot_sound)
        for _ in range(self.definition.pellets_per_shot):
            self._fire_bullet()
        from game.entities.effects import MuzzleFlash
        MuzzleFlash(
            self.owner.scene,
            (self.owner.rect.centerx, self.owner.rect.centery),
        )
        if self.current_ammo <= 0:
            self.reload()

    def reload(self):
        if self.is_reloading:
            return
        if self.current_ammo >= self.magazine_size:
            return
        if self.reserve_ammo <= 0 and self.definition.reserve_max > 0:
            # Out of reserve — nothing to load. (Wonder weapons with no
            # reserve concept skip this check.)
            return
        self.is_reloading = True
        self.reload_started_at = pygame.time.get_ticks()
        self._announce("reload", "reload_sound.mp3")

    def update(self):
        if not self.is_reloading:
            return
        elapsed = pygame.time.get_ticks() - self.reload_started_at
        if elapsed >= self.reload_time * 1000:
            self.is_reloading = False
            self._finish_reload()

    def _finish_reload(self):
        if self.definition.reserve_max == 0:
            # No reserve concept — top up freely.
            self.current_ammo = self.magazine_size
            return
        needed = self.magazine_size - self.current_ammo
        transferred = min(needed, self.reserve_ammo)
        self.current_ammo += transferred
        self.reserve_ammo -= transferred

    def _announce(self, event_name: str, sound_name: str):
        """Play locally and (if there's a host) broadcast so clients hear it."""
        scene = self.owner.scene
        announcer = getattr(scene, "announce_event", None)
        if announcer is not None:
            announcer(event_name, {"sound": sound_name, "player_id": self.owner.player_id})
        else:
            # Plain SP — just play.
            assets.sound(sound_name).play()

    def _fire_bullet(self):
        scene = self.owner.scene
        # Direction comes from the player's aim angle (kept by Player from its
        # input source — same logic for local + remote players, no camera math
        # here so this works regardless of whose camera we are).
        import math
        rad = math.radians(self.owner.angle)
        dx = math.cos(rad)
        dy = -math.sin(rad)  # screen-y is inverted relative to math sin
        direction = vector(dx, dy)
        Bullet(
            scene,
            self.owner.rect.centerx,
            self.owner.rect.centery,
            direction,
            self.owner.angle,
            self.definition.bullet_spread,
            self.definition.bullet_speed,
            shooter_id=self.owner.player_id,
            damage=self.damage,
            penetration=self.penetration,
            effect_kind=self.definition.effect_kind,
        )
