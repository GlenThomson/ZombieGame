"""Walking, pathing, biting zombie. Subclass for Dogs / SpecialZombies later."""
import math
import random
import pygame

from settings import (
    TILE_SIZE,
    ZOMBIE_SPEED_BASE,
    ZOMBIE_SPEED_RAMP_PER_ROUND,
    ZOMBIE_MAX_SPEED,
    ZOMBIE_HEALTH_BASE,
    ZOMBIE_HEALTH_RAMP_PER_ROUND,
    ZOMBIE_CHASE_DISTANCE,
    MAX_ROTATE_SPEED,
    PICKUP_DROP_CHANCE,
)
from game import assets
from game.systems.collision import resolve_wall_collision
from game.systems.pathfinding import find_path
from game.world.tile import TileType
from game.entities.effects import BloodSplatter

vector = pygame.math.Vector2


class Zombie(pygame.sprite.Sprite):
    image_name = "zombie.png"

    def __init__(self, scene, x: float, y: float):
        super().__init__(scene.all_sprites, scene.zombies)
        self.scene = scene
        self.original_image = assets.image(self.image_name, scale=(TILE_SIZE, TILE_SIZE))
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.pos = vector(x, y)
        self.vel = vector(0, 0)
        self.angle = 0

        self.hit_box = pygame.Rect(0, 0, self.rect.width * 0.7, self.rect.height * 0.7)
        self.hit_box.center = self.rect.center

        round_num = scene.round_manager.current_round
        # Speed ramps linearly and caps. Round 1 = base, +RAMP per round.
        self.speed_base = min(
            ZOMBIE_MAX_SPEED,
            ZOMBIE_SPEED_BASE + ZOMBIE_SPEED_RAMP_PER_ROUND * (round_num - 1),
        )
        self.speed = self.speed_base
        # Health compounds (doubles every ~4 rounds at 18%).
        self.health = ZOMBIE_HEALTH_BASE * ((1 + ZOMBIE_HEALTH_RAMP_PER_ROUND) ** (round_num - 1))

        self.colliding_with_wall = False
        self.is_chasing = False
        self.path = self._compute_path()
        self.path_index = 0

    def _compute_path(self):
        target = self.scene.nearest_player_to(self.pos)
        if target is None:
            return []
        return find_path(self.scene.grid, self.pos, target.tile_position())

    def tile_position(self):
        return self.pos // TILE_SIZE

    def update(self, scene_or_pos=None):
        if self.health <= 0:
            self.kill()
            return

        # Compatibility: zombie.update() may be called with a (x, y) tuple
        # (legacy path) or with the scene object (multi-player path).
        if hasattr(scene_or_pos, "nearest_player_to"):
            target = scene_or_pos.nearest_player_to(self.pos)
            player_pos = (target.pos.x, target.pos.y) if target is not None else (self.pos.x, self.pos.y)
        elif scene_or_pos is None:
            target = self.scene.nearest_player_to(self.pos)
            player_pos = (target.pos.x, target.pos.y) if target is not None else (self.pos.x, self.pos.y)
        else:
            player_pos = scene_or_pos

        if self._is_close_to_player() and self._has_line_of_sight(player_pos):
            if not self.is_chasing:
                self.is_chasing = True
            self._aim(player_pos)
        else:
            if self.is_chasing:
                self.is_chasing = False
                self.path = self._compute_path()
                self.path_index = 0
            self._follow_path()

    def _follow_path(self):
        if not self.path or self.path_index >= len(self.path):
            return
        next_tile = self.path[self.path_index]
        target = vector((next_tile.x + 0.5) * TILE_SIZE, (next_tile.y + 0.5) * TILE_SIZE)
        self._aim((target.x, target.y))

        tile_rect = pygame.Rect(
            next_tile.x * TILE_SIZE, next_tile.y * TILE_SIZE, TILE_SIZE, TILE_SIZE
        )
        if self.hit_box.colliderect(tile_rect):
            self.path_index += 1
            if self.path_index == len(self.path):
                self.path = self._compute_path()
                self.path_index = 0

    def _aim(self, target_pos):
        dx = target_pos[0] - self.pos.x
        dy = target_pos[1] - self.pos.y
        target_angle = math.degrees(math.atan2(dy, dx))
        diff = (target_angle - self.angle + 180) % 360 - 180
        diff = max(-MAX_ROTATE_SPEED, min(MAX_ROTATE_SPEED, diff))
        self.angle += diff

        self.image = pygame.transform.rotate(self.original_image, -self.angle)
        self.rect = self.image.get_rect(center=self.pos)
        self.vel.x = self.speed * math.cos(math.radians(self.angle))
        self.vel.y = self.speed * math.sin(math.radians(self.angle))
        self.pos += self.vel

        self.hit_box.centerx = self.pos.x
        collided_x = False
        collided_y = False
        if self._is_near_wall():
            collided_x = resolve_wall_collision(self, self.scene.walls, "x")
        self.hit_box.centery = self.pos.y
        if self._is_near_wall():
            collided_y = resolve_wall_collision(self, self.scene.walls, "y")
        self.rect.center = self.hit_box.center
        self.colliding_with_wall = collided_x or collided_y

    def _is_near_wall(self):
        grid_x = int(self.pos.x / TILE_SIZE)
        grid_y = int(self.pos.y / TILE_SIZE)
        rows = len(self.scene.grid)
        cols = len(self.scene.grid[0])
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                x, y = grid_x + dx, grid_y + dy
                if 0 <= x < cols and 0 <= y < rows and TileType.is_blocking(self.scene.grid[y][x]):
                    return True
        return False

    def _is_close_to_player(self) -> bool:
        target = self.scene.nearest_player_to(self.pos)
        if target is None:
            return False
        return self.pos.distance_to(target.pos) < ZOMBIE_CHASE_DISTANCE

    def _has_line_of_sight(self, target_pos) -> bool:
        start = self.pos
        end = target_pos if isinstance(target_pos, vector) else vector(*target_pos)
        if start == end:
            return True
        step = (end - start).normalize() * TILE_SIZE * 0.5
        cur = vector(start.x, start.y)
        rows = len(self.scene.grid)
        cols = len(self.scene.grid[0])
        while cur.distance_to(end) > TILE_SIZE * 0.5:
            cur += step
            gx, gy = int(cur.x / TILE_SIZE), int(cur.y / TILE_SIZE)
            if not (0 <= gx < cols and 0 <= gy < rows):
                return False
            if TileType.is_blocking(self.scene.grid[gy][gx]):
                return False
        # If we're wedged against a wall, fall back to A* instead of bee-lining.
        if self.colliding_with_wall:
            return False
        return True

    def take_damage(self, amount: int = 1):
        self.health -= amount
        BloodSplatter(self.scene, self.pos, duration_ms=10)
        if self.health <= 0 and self.alive():
            self.scene.kill_count += 1
            BloodSplatter(self.scene, self.pos, duration_ms=5000)
            if random.randint(1, PICKUP_DROP_CHANCE) == 1:
                from game.pickups.pickup import Pickup
                Pickup(self.scene, self.rect.x, self.rect.y)
            self.kill()
