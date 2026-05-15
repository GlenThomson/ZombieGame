"""The player character. Owns a weapon inventory and a stat ModifierStack."""
import math
import pygame

from settings import (
    TILE_SIZE,
    PLAYER_SPEED,
    PLAYER_HEALTH,
    PLAYER_HIT_BOX_SIZE,
    BULLET_DAMAGE,
    STARTING_GRENADES,
    STARTING_POINTS,
)
from game import assets
from game.systems.collision import resolve_wall_collision
from game.utils import adjusted_mouse_position
from game.stats.modifiers import ModifierStack
from game.weapons.inventory import Inventory

vector = pygame.math.Vector2


class Player(pygame.sprite.Sprite):
    def __init__(self, scene, x: float, y: float):
        super().__init__(scene.all_sprites)
        self.scene = scene
        self.original_image = assets.image("player.png", scale=(TILE_SIZE, TILE_SIZE))
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.pos = vector(x, y)
        self.vel = vector(0, 0)
        self.angle = 0

        self.hit_box = pygame.Rect(0, 0, PLAYER_HIT_BOX_SIZE, PLAYER_HIT_BOX_SIZE)
        self.hit_box.center = self.rect.center

        self.modifiers = ModifierStack()
        self._base_health = PLAYER_HEALTH
        self.health = self.max_health
        self.grenade_count = STARTING_GRENADES
        self.points = STARTING_POINTS

        self.inventory = Inventory(self)
        self.inventory.add("Pistol")
        self.inventory.equip(0)

    @property
    def max_health(self) -> float:
        return self.modifiers.apply("max_health", self._base_health)

    @property
    def speed(self) -> float:
        return self.modifiers.apply("speed", PLAYER_SPEED)

    def tile_position(self):
        return self.pos // TILE_SIZE

    def update(self):
        self._movement()
        self._aim()
        self.weapon.update()

    @property
    def weapon(self):
        return self.inventory.equipped

    def _movement(self):
        keys = pygame.key.get_pressed()
        speed = self.speed
        if keys[pygame.K_a]:
            self.vel.x = -speed
        elif keys[pygame.K_d]:
            self.vel.x = speed
        else:
            self.vel.x = 0
        if keys[pygame.K_w]:
            self.vel.y = -speed
        elif keys[pygame.K_s]:
            self.vel.y = speed
        else:
            self.vel.y = 0

        if self.vel.y != 0 and self.vel.x != 0:
            length = math.hypot(self.vel.x, self.vel.y)
            self.vel.x = (self.vel.x / length) * speed
            self.vel.y = (self.vel.y / length) * speed

        self.pos += self.vel
        self.hit_box.centerx = self.pos.x
        resolve_wall_collision(self, self.scene.walls, "x")
        resolve_wall_collision(self, self.scene.barb_wire, "x")
        self.hit_box.centery = self.pos.y
        resolve_wall_collision(self, self.scene.walls, "y")
        resolve_wall_collision(self, self.scene.barb_wire, "y")
        self.rect.center = self.hit_box.center

    def _aim(self):
        cam_x, cam_y = self.scene.camera.camera.x, self.scene.camera.camera.y
        mx, my = adjusted_mouse_position(cam_x, cam_y)
        rel_x, rel_y = mx - self.pos.x, my - self.pos.y
        self.angle = (180 / math.pi) * -math.atan2(rel_y, rel_x)
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=self.pos)

    def take_damage(self, amount: float = BULLET_DAMAGE):
        self.health -= amount

    def heal_to_full(self):
        self.health = self.max_health

    def is_dead(self) -> bool:
        return self.health <= 0

    def shoot(self):
        self.weapon.shoot()

    def throw_grenade(self):
        if self.grenade_count <= 0:
            return False
        if len(self.scene.grenades) > 0:
            return False
        from game.entities.grenade import Grenade
        Grenade(self.scene, self.pos.x, self.pos.y, self.angle)
        self.grenade_count -= 1
        return True
