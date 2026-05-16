"""Mystery Box: walk near, hold F, pay points, get a random weapon.

States:
- IDLE: shows the box closed, prompts to interact
- SPINNING: cycles through weapon names visually for a short while,
  then commits to one (or to TEDDY)
- READY: weapon name is settled, waiting for player to take it
- TEDDY: box rolled a teddy bear (1-in-7-ish), plays a sound for 2s
  and then relocates to a random eligible tile elsewhere on the map

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


TEDDY_CHANCE = 0.14            # CoD: roughly 1 in 7
TEDDY_DISPLAY_MS = 2000
FORCED_TEDDY_AFTER_USES = 5    # nth roll always teddies regardless of RNG


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
        self.state = "idle"           # "idle" | "spinning" | "ready" | "teddy"
        self.spin_started_at = 0
        self.last_label_swap_at = 0
        self.current_label = "?"
        self.committed_weapon: str | None = None
        self.teddy_until_ms = 0
        self._render()

    def _render(self):
        import os
        from game import assets
        png = f"mystery_box_{self.state}.png"
        path = os.path.join("assets", "images", png)
        if os.path.isfile(path):
            self.image = assets.image(png).copy()
            # When spinning / ready, overlay the current label so the player
            # sees the weapon name they're rolling.
            if self.state in ("spinning", "ready") and self.current_label:
                label_surf = self.font.render(self.current_label, True, (0, 0, 0))
                self.image.blit(
                    label_surf,
                    label_surf.get_rect(midbottom=(TILE_SIZE // 2, TILE_SIZE - 4)),
                )
        else:
            self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(self.image, (60, 30, 10), self.image.get_rect())
            pygame.draw.rect(self.image, (255, 215, 0), self.image.get_rect(), 2)

    def update(self):
        now = pygame.time.get_ticks()
        if self.state == "spinning":
            if now - self.last_label_swap_at >= MYSTERY_BOX_SPIN_FRAME_MS:
                self.last_label_swap_at = now
                self.current_label = random.choice(MYSTERY_BOX_POOL)[:5]
                self._render()
            if now - self.spin_started_at >= MYSTERY_BOX_SPIN_DURATION_MS:
                self._commit_roll()
        elif self.state == "teddy":
            if now >= self.teddy_until_ms:
                self._relocate()

    def _commit_roll(self):
        # Track per-scene mystery-box usage so the box reliably moves after
        # FORCED_TEDDY_AFTER_USES rolls — CoD-faithful "the box left" moment.
        scene = self.scene
        scene.mystery_box_uses = getattr(scene, "mystery_box_uses", 0) + 1
        forced = scene.mystery_box_uses >= FORCED_TEDDY_AFTER_USES
        if forced or random.random() < TEDDY_CHANCE:
            self.state = "teddy"
            self.teddy_until_ms = pygame.time.get_ticks() + TEDDY_DISPLAY_MS
            self.scene.announce_event("teddy", {"sound": "kaboom.mp3"})
            self._render()
            scene.mystery_box_uses = 0  # reset on relocation
            return
        weapon = random.choice(MYSTERY_BOX_POOL)
        self.committed_weapon = weapon
        self.current_label = weapon[:5]
        self.state = "ready"
        self._render()

    def _relocate(self):
        """Box vanishes from this tile and reappears at a random empty tile
        far from here. The grid + scene groups are updated so the new box
        can be interacted with normally."""
        from game.world.tile import TileType
        scene = self.scene
        old_x, old_y = self.x_tile, self.y_tile
        if 0 <= old_y < len(scene.grid) and 0 <= old_x < len(scene.grid[0]):
            scene.grid[old_y][old_x] = TileType.EMPTY
        scene.interactables.discard(self)
        self.kill()
        new_spot = _find_relocation_spot(scene, exclude=(old_x, old_y))
        if new_spot is None:
            return
        nx, ny = new_spot
        scene.grid[ny][nx] = TileType.MYSTERY_BOX
        new_box = MysteryBox(scene, nx, ny)
        scene.interactables.add(new_box)

    # --- Interactable ---

    def get_world_pos(self) -> tuple[float, float]:
        return (self.rect.centerx, self.rect.centery)

    def get_prompt(self, player) -> str | None:
        if self.state == "spinning":
            return "rolling..."
        if self.state == "teddy":
            return "the box is leaving..."
        if self.state == "ready":
            return f"[{INTERACT_KEY_LABEL}] Take {self.committed_weapon}"
        prefix = "" if player.points >= self.cost else "(need points) "
        return f"{prefix}[{INTERACT_KEY_LABEL}] Mystery Box  -  {self.cost}"

    def interact(self, player) -> None:
        if self.state in ("spinning", "teddy"):
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
        if not player.spend(self.cost):
            return
        self.state = "spinning"
        self.spin_started_at = pygame.time.get_ticks()
        self.last_label_swap_at = 0
        self.current_label = random.choice(MYSTERY_BOX_POOL)[:5]
        self._render()


def _find_relocation_spot(scene, exclude: tuple[int, int]) -> tuple[int, int] | None:
    from game.world.tile import TileType
    rows = len(scene.grid)
    cols = len(scene.grid[0])
    candidates = []
    for y in range(rows):
        for x in range(cols):
            if (x, y) == exclude:
                continue
            if scene.grid[y][x] != TileType.EMPTY:
                continue
            # Distance from the old position so the box actually moves.
            d2 = (x - exclude[0]) ** 2 + (y - exclude[1]) ** 2
            if d2 < 25:  # at least 5 tiles away
                continue
            candidates.append((x, y))
    if not candidates:
        return None
    return random.choice(candidates)
