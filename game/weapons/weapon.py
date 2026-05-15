"""A single equipped weapon instance. Holds its own ammo + reload state.

Reads its base stats from a WeaponDef and applies the player's ModifierStack
on demand, so perks like Speed Cola (faster reload) or Pack-a-Punch (more
damage) can be plugged in later without touching this class."""
import pygame

from game import assets
from game.entities.bullet import Bullet
from game.utils import adjusted_mouse_position
from game.weapons.definitions import WEAPON_DEFS

vector = pygame.math.Vector2


class Weapon:
    def __init__(self, owner, def_name: str):
        self.owner = owner
        self.definition = WEAPON_DEFS[def_name]
        self.shoot_sound = assets.sound(self.definition.shoot_sound)
        self.reload_sound = assets.sound("reload_sound.mp3")
        self.current_ammo = self.definition.magazine_size
        self.is_reloading = False
        self.last_shot_time = 0
        self.reload_started_at = 0

    @property
    def name(self) -> str:
        return self.definition.name

    @property
    def magazine_size(self) -> int:
        return int(self.owner.modifiers.apply("magazine_size", self.definition.magazine_size))

    @property
    def fire_rate(self) -> float:
        return self.owner.modifiers.apply("fire_rate", self.definition.fire_rate)

    @property
    def reload_time(self) -> float:
        return self.owner.modifiers.apply("reload_time", self.definition.reload_time)

    @property
    def damage(self) -> int:
        return int(self.owner.modifiers.apply("damage", self.definition.damage))

    @property
    def penetration(self) -> int:
        return int(self.owner.modifiers.apply("penetration", self.definition.penetration))

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
        self.shoot_sound.play()
        for _ in range(self.definition.pellets_per_shot):
            self._fire_bullet()
        if self.current_ammo <= 0:
            self.reload()

    def reload(self):
        if self.is_reloading:
            return
        if self.current_ammo == self.magazine_size:
            return
        self.is_reloading = True
        self.reload_started_at = pygame.time.get_ticks()
        self.reload_sound.play()

    def update(self):
        if not self.is_reloading:
            return
        elapsed = pygame.time.get_ticks() - self.reload_started_at
        if elapsed >= self.reload_time * 1000:
            self.is_reloading = False
            self.current_ammo = self.magazine_size

    def _fire_bullet(self):
        scene = self.owner.scene
        cam = scene.camera.camera
        mx, my = adjusted_mouse_position(cam.x, cam.y)
        dx, dy = mx - self.owner.rect.centerx, my - self.owner.rect.centery
        if dx == 0 and dy == 0:
            return
        direction = vector(dx, dy).normalize()
        Bullet(
            scene,
            self.owner.rect.centerx,
            self.owner.rect.centery,
            direction,
            self.owner.angle,
            self.definition.bullet_spread,
            self.definition.bullet_speed,
        )
