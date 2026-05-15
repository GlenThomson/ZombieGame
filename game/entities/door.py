"""Door tile entity.

Adjacent DOOR_CLOSED tiles are linked into a single logical DoorGroup so
that a 3-tile-wide door costs the same as a 1-tile door and opens with one
F press. Each tile is still its own sprite (so it lives in scene.walls
and blocks movement on its own); they share state via the group."""
import pygame

from settings import TILE_SIZE, INTERACT_KEY_LABEL, GOLD
from game.world.tile import TileType


class DoorGroup:
    """Shared state for a set of physically-adjacent door tiles."""

    def __init__(self, scene, cost: int):
        self.scene = scene
        self.cost = cost
        self.tiles: list["Door"] = []   # populated as Door instances register

    def open(self):
        for door in list(self.tiles):
            x, y = door.x_tile, door.y_tile
            if 0 <= y < len(self.scene.grid) and 0 <= x < len(self.scene.grid[0]):
                self.scene.grid[y][x] = TileType.DOOR_OPEN
            self.scene.interactables.discard(door)
            door.kill()
        self.tiles.clear()


class Door(pygame.sprite.Sprite):
    def __init__(self, scene, x_tile: int, y_tile: int, group: DoorGroup):
        super().__init__(scene.all_sprites, scene.walls, scene.doors)
        self.scene = scene
        self.x_tile = x_tile
        self.y_tile = y_tile
        self.group = group
        group.tiles.append(self)

        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill((110, 60, 20))
        for y in range(0, TILE_SIZE, 8):
            pygame.draw.line(self.image, (70, 35, 10), (0, y), (TILE_SIZE, y), 1)
        pygame.draw.rect(self.image, GOLD, self.image.get_rect(), 2)
        self.rect = self.image.get_rect(topleft=(x_tile * TILE_SIZE, y_tile * TILE_SIZE))

    @property
    def cost(self) -> int:
        return self.group.cost

    # --- Interactable protocol ---

    def get_world_pos(self) -> tuple[float, float]:
        return (self.rect.centerx, self.rect.centery)

    def get_prompt(self, player) -> str | None:
        affordable = player.points >= self.group.cost
        prefix = "" if affordable else "(need points) "
        return f"{prefix}[{INTERACT_KEY_LABEL}] Open Door  -  {self.group.cost}"

    def interact(self, player) -> None:
        if player.points < self.group.cost:
            return
        player.points -= self.group.cost
        self.group.open()
