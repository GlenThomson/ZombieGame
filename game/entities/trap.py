"""Map traps. Stand near, pay points, activates for 30s killing any zombie
that walks through the trap tile. Requires the map's power to be on.

Two visual variants — Flogger (rotating arms) and Fire trap (ground gout
of flame) — share the same kill-on-contact mechanic."""
import math
import pygame

from settings import TILE_SIZE, INTERACT_KEY_LABEL, GOLD


TRAP_COST = 1000
TRAP_DURATION_MS = 30_000
TRAP_KILL_POINTS = 50  # per zombie killed by the trap


class Trap(pygame.sprite.Sprite):
    def __init__(self, scene, x_tile: int, y_tile: int, kind: str):
        super().__init__(scene.all_sprites, scene.traps)
        self.scene = scene
        self.x_tile = x_tile
        self.y_tile = y_tile
        self.kind = kind  # "flogger" | "fire"
        self.cost = TRAP_COST
        self.active_until_ms = 0
        self.activator_id: int | None = None
        self.rect = pygame.Rect(x_tile * TILE_SIZE, y_tile * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        self._render()

    @property
    def is_active(self) -> bool:
        return pygame.time.get_ticks() < self.active_until_ms

    def _render(self):
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        if self.kind == "fire":
            base = (180, 60, 0) if self.is_active else (60, 30, 10)
            pygame.draw.rect(self.image, base, self.image.get_rect())
            if self.is_active:
                # crude flame layers
                pygame.draw.polygon(
                    self.image, (255, 200, 0),
                    [(8, TILE_SIZE - 4), (TILE_SIZE // 2, 4), (TILE_SIZE - 8, TILE_SIZE - 4)],
                )
                pygame.draw.polygon(
                    self.image, (255, 100, 0),
                    [(12, TILE_SIZE - 4), (TILE_SIZE // 2, 12), (TILE_SIZE - 12, TILE_SIZE - 4)],
                )
        else:  # flogger
            base = (90, 90, 90) if self.is_active else (40, 40, 40)
            pygame.draw.rect(self.image, base, self.image.get_rect())
            cx = TILE_SIZE // 2
            if self.is_active:
                # rotating arms approximation (static cross — animation later)
                t = pygame.time.get_ticks() / 100.0
                for offset in (0, math.pi / 2):
                    a = t + offset
                    x2 = cx + int(math.cos(a) * (TILE_SIZE // 2 - 4))
                    y2 = cx + int(math.sin(a) * (TILE_SIZE // 2 - 4))
                    pygame.draw.line(self.image, (220, 220, 220), (cx, cx), (x2, y2), 4)
        pygame.draw.rect(self.image, GOLD, self.image.get_rect(), 2)

    def update_kills(self):
        """Called each frame by PlayState. Damages zombies on/over this tile
        while the trap is active. Returns the player who activated it (if
        still in scene) so points can be credited."""
        if not self.is_active:
            return
        # Refresh visual (flogger arms rotate).
        if self.kind == "flogger":
            self._render()
        for zombie in list(self.scene.zombies):
            if self.rect.colliderect(zombie.rect) and zombie.health > 0:
                zombie.take_damage(99999)
                activator = self.scene._player_by_id(self.activator_id) if self.activator_id is not None else None
                if activator is not None:
                    activator.points += TRAP_KILL_POINTS

    # --- Interactable ---

    def get_world_pos(self) -> tuple[float, float]:
        return (self.rect.centerx, self.rect.centery)

    def get_prompt(self, player) -> str | None:
        if self.is_active:
            return None
        if not getattr(self.scene, "power_on", True):
            return "Trap (power off)"
        affordable = player.points >= self.cost
        prefix = "" if affordable else "(need points) "
        label = "Fire Trap" if self.kind == "fire" else "Flogger"
        return f"{prefix}[{INTERACT_KEY_LABEL}] {label}  -  {self.cost}"

    def interact(self, player) -> None:
        if self.is_active:
            return
        if not getattr(self.scene, "power_on", True):
            return
        if player.points < self.cost:
            return
        player.points -= self.cost
        self.active_until_ms = pygame.time.get_ticks() + TRAP_DURATION_MS
        self.activator_id = player.player_id
        self.scene.announce_event("trap_on", {"sound": "kaboom.mp3"})
        self._render()
