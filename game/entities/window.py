"""Boardable window. Has WINDOW_PLANK_COUNT planks. Zombies adjacent to the
window break planks at intervals; once all planks are gone, the window is
removed entirely so zombies (and bullets) pass through. The player can
repair it from inside, earning points per plank rebuilt."""
import pygame

from settings import (
    TILE_SIZE,
    INTERACT_KEY_LABEL,
    WINDOW_PLANK_COUNT,
    WINDOW_REPAIR_POINTS_PER_PLANK,
    WINDOW_PLANK_BREAK_INTERVAL_MS,
    GOLD,
)


class Window(pygame.sprite.Sprite):
    def __init__(self, scene, x_tile: int, y_tile: int):
        # In scene.walls so it physically blocks zombies + bullets while planks remain.
        super().__init__(scene.all_sprites, scene.walls, scene.windows)
        self.scene = scene
        self.x_tile = x_tile
        self.y_tile = y_tile
        self.planks = WINDOW_PLANK_COUNT
        self.last_break_at = pygame.time.get_ticks()
        self.rect = pygame.Rect(
            x_tile * TILE_SIZE, y_tile * TILE_SIZE, TILE_SIZE, TILE_SIZE
        )
        self._render()

    def _render(self):
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        # Window frame
        pygame.draw.rect(self.image, (60, 60, 80), self.image.get_rect(), 0)
        pygame.draw.rect(self.image, (180, 180, 200), self.image.get_rect(), 2)
        # Plank stripes proportional to how many remain
        if self.planks > 0:
            slot_h = TILE_SIZE / WINDOW_PLANK_COUNT
            for i in range(self.planks):
                y = int(i * slot_h) + 2
                pygame.draw.rect(
                    self.image, (160, 110, 50),
                    (3, y, TILE_SIZE - 6, int(slot_h) - 2),
                )
                pygame.draw.line(
                    self.image, (90, 60, 25), (3, y), (TILE_SIZE - 4, y), 1,
                )

    def update_against_zombies(self):
        """Called by PlayState every frame. If any zombie is adjacent and the
        cooldown has elapsed, lose one plank."""
        if self.planks <= 0:
            self._collapse()
            return
        now = pygame.time.get_ticks()
        if now - self.last_break_at < WINDOW_PLANK_BREAK_INTERVAL_MS:
            return
        if self._has_adjacent_zombie():
            self.planks -= 1
            self.last_break_at = now
            self._render()
            if self.planks <= 0:
                self._collapse()

    def _has_adjacent_zombie(self) -> bool:
        # Slightly inflated rect so zombies "next to" the window count.
        check = self.rect.inflate(TILE_SIZE * 0.5, TILE_SIZE * 0.5)
        for zombie in self.scene.zombies:
            if check.colliderect(zombie.rect):
                return True
        return False

    def _collapse(self):
        # Window fully broken: remove from blocking groups so zombies pass.
        self.scene.interactables.discard(self)
        self.kill()

    # --- Interactable ---

    def get_world_pos(self) -> tuple[float, float]:
        return (self.rect.centerx, self.rect.centery)

    def get_prompt(self, player) -> str | None:
        if self.planks >= WINDOW_PLANK_COUNT:
            return None
        return f"[{INTERACT_KEY_LABEL}] Repair window  +{WINDOW_REPAIR_POINTS_PER_PLANK}"

    def interact(self, player) -> None:
        if self.planks >= WINDOW_PLANK_COUNT:
            return
        self.planks += 1
        player.points += WINDOW_REPAIR_POINTS_PER_PLANK
        self._render()
