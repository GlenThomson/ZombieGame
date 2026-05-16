"""Power switch. Sits on a wall like a perk machine. Free to interact;
flipping it sets scene.power_on = True (irreversible). Perks, Pack-a-Punch,
and traps refuse to operate until the power is on."""
import pygame

from settings import TILE_SIZE, INTERACT_KEY_LABEL


class PowerSwitch(pygame.sprite.Sprite):
    def __init__(self, scene, x_tile: int, y_tile: int):
        super().__init__(scene.all_sprites, scene.walls, scene.power_switches)
        self.scene = scene
        self.x_tile = x_tile
        self.y_tile = y_tile
        self.rect = pygame.Rect(
            x_tile * TILE_SIZE, y_tile * TILE_SIZE, TILE_SIZE, TILE_SIZE,
        )
        self._render()

    def _render(self):
        import os
        from game import assets
        png = "power_switch_on.png" if self.scene.power_on else "power_switch_off.png"
        if os.path.isfile(os.path.join("assets", "images", png)):
            self.image = assets.image(png).copy()
        else:
            self.image = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            body = (50, 50, 60) if not self.scene.power_on else (40, 70, 40)
            pygame.draw.rect(self.image, body, self.image.get_rect())
            pygame.draw.rect(self.image, (220, 220, 220), self.image.get_rect(), 2)

    def get_world_pos(self) -> tuple[float, float]:
        return (self.rect.centerx, self.rect.centery)

    def get_prompt(self, player) -> str | None:
        if self.scene.power_on:
            return None
        return f"[{INTERACT_KEY_LABEL}] Turn on the power"

    def interact(self, player) -> None:
        if self.scene.power_on:
            return
        self.scene.power_on = True
        self.scene.announce_event("power_on", {"sound": "kaboom.mp3"})
        self._render()
        # Re-render every other PowerSwitch so they look "on" too.
        for ps in self.scene.power_switches:
            if ps is not self:
                ps._render()
