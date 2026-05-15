"""Mystery Box: walk near, hold F, pay points, get a random weapon.

The box has two states:
- IDLE: shows the box closed, prompts to interact
- SPINNING: cycles through weapon names visually for a short while,
  then commits to one and adds it to the player's inventory

A simple visual placeholder is used until proper art lands."""
import random
import pygame

from settings import (
    TILE_SIZE,
    INTERACT_KEY_LABEL,
    MYSTERY_BOX_COST,
    MYSTERY_BOX_SPIN_DURATION_MS,
    MYSTERY_BOX_SPIN_FRAME_MS,
)
from game.weapons.definitions import MYSTERY_BOX_POOL


class MysteryBox(pygame.sprite.Sprite):
    def __init__(self, scene, x_tile: int, y_tile: int):
        super().__init__(scene.all_sprites, scene.walls, scene.mystery_boxes)
        self.scene = scene
        self.x_tile = x_tile
        self.y_tile = y_tile
        self.cost = MYSTERY_BOX_COST
        self.rect = pygame.Rect(
            x_tile * TILE_SIZE, y_tile * TILE_SIZE, TILE_SIZE, TILE_SIZE
        )
        self.font = pygame.font.Font(None, 14)
        self.state = "idle"           # "idle" | "spinning" | "ready"
        self.spin_started_at = 0
        self.last_label_swap_at = 0
        self.current_label = "?"
        self.committed_weapon: str | None = None
        self._render()

    def _render(self):
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        # Box body
        if self.state == "spinning":
            body = (200, 60, 0)
        elif self.state == "ready":
            body = (255, 215, 0)
        else:
            body = (60, 30, 10)
        pygame.draw.rect(self.image, body, self.image.get_rect())
        pygame.draw.rect(self.image, (255, 215, 0), self.image.get_rect(), 2)
        text = self.font.render(self.current_label, True, (255, 255, 255))
        self.image.blit(text, text.get_rect(center=(TILE_SIZE // 2, TILE_SIZE // 2)))

    def update(self):
        """Driven by PlayState each frame so the spin animation advances."""
        if self.state != "spinning":
            return
        now = pygame.time.get_ticks()
        if now - self.last_label_swap_at >= MYSTERY_BOX_SPIN_FRAME_MS:
            self.last_label_swap_at = now
            self.current_label = random.choice(MYSTERY_BOX_POOL)[:5]
            self._render()
        if now - self.spin_started_at >= MYSTERY_BOX_SPIN_DURATION_MS:
            self._commit_roll()

    def _commit_roll(self):
        weapon = random.choice(MYSTERY_BOX_POOL)
        self.committed_weapon = weapon
        self.current_label = weapon[:5]
        self.state = "ready"
        self._render()

    # --- Interactable ---

    def get_world_pos(self) -> tuple[float, float]:
        return (self.rect.centerx, self.rect.centery)

    def get_prompt(self, player) -> str | None:
        if self.state == "spinning":
            return "rolling..."
        if self.state == "ready":
            return f"[{INTERACT_KEY_LABEL}] Take {self.committed_weapon}"
        # idle
        prefix = "" if player.points >= self.cost else "(need points) "
        return f"{prefix}[{INTERACT_KEY_LABEL}] Mystery Box  -  {self.cost}"

    def interact(self, player) -> None:
        if self.state == "spinning":
            return
        if self.state == "ready":
            if self.committed_weapon is None:
                return
            added = player.inventory.add(self.committed_weapon)
            if not added:
                player.inventory.replace_equipped(self.committed_weapon)
            # Mystery box hands you a fully-loaded weapon (mag + reserve).
            for slot in player.inventory.slots:
                if slot is not None and slot.definition.name == self.committed_weapon:
                    slot.current_ammo = slot.magazine_size
                    slot.reserve_ammo = slot.reserve_max
                    slot.is_reloading = False
                    break
            self.state = "idle"
            self.current_label = "?"
            self.committed_weapon = None
            self._render()
            return
        # idle → start a spin
        if player.points < self.cost:
            return
        player.points -= self.cost
        self.state = "spinning"
        self.spin_started_at = pygame.time.get_ticks()
        self.last_label_swap_at = 0
        self.current_label = random.choice(MYSTERY_BOX_POOL)[:5]
        self._render()
