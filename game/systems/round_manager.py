"""Round + spawn pacing. Owns the round counter, decides when to spawn each
zombie this round, and decides when the round is over."""
import random
import pygame

from settings import (
    ROUND_SPAWN_WINDOW_SECONDS,
    ZOMBIES_PER_ROUND_MULTIPLIER,
    STARTING_GRENADES,
)
from game import assets
from game.entities.zombie import Zombie


class RoundManager:
    def __init__(self, scene, starting_round: int = 1):
        self.scene = scene
        self.current_round = starting_round
        self.zombies_to_spawn = ZOMBIES_PER_ROUND_MULTIPLIER * starting_round
        self.spawn_window_seconds = ROUND_SPAWN_WINDOW_SECONDS
        self.time_between_spawns = self.spawn_window_seconds / max(1, self.zombies_to_spawn)
        self.spawn_timer = 0.0
        self.end_round_sound = assets.sound("end_round_sound.mp3")
        self.round_text_countdown = 0  # ms; >0 means show "Round N" overlay

    def tick(self, dt_seconds: float):
        # Spawn zombies on cadence.
        if self.zombies_to_spawn > 0:
            self.spawn_timer += dt_seconds
            if self.spawn_timer >= self.time_between_spawns:
                self.spawn_timer = 0
                self._spawn_one_zombie()
                self.zombies_to_spawn -= 1
        elif len(self.scene.zombies) == 0:
            self._begin_next_round()

    def _spawn_one_zombie(self):
        if not self.scene.zombie_spawns:
            return
        spawn = random.choice(self.scene.zombie_spawns)
        Zombie(self.scene, spawn.x, spawn.y)

    def _begin_next_round(self):
        self.current_round += 1
        self.scene.player.grenade_count = STARTING_GRENADES
        self.round_text_countdown = 500
        self.end_round_sound.play()
        self.zombies_to_spawn = self.current_round * ZOMBIES_PER_ROUND_MULTIPLIER
        self.time_between_spawns = self.spawn_window_seconds / self.zombies_to_spawn
