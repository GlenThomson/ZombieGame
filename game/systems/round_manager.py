"""Round + spawn pacing. Owns the round counter, decides when to spawn each
zombie this round, and decides when the round is over.

Round 5 / 10 / 15 / ... are special "hellhound rounds" — fewer total enemies
but all of them are Hellhounds (CoD: dogs round)."""
import random

from settings import (
    ROUND_SPAWN_WINDOW_SECONDS,
    ZOMBIES_PER_ROUND_MULTIPLIER,
    STARTING_GRENADES,
)
from game import assets
from game.entities.zombie import Zombie
from game.entities.zombie_variants import Crawler, Runner, Hellhound


HELLHOUND_ROUND_INTERVAL = 5  # every 5th round is a dogs round


class RoundManager:
    def __init__(self, scene, starting_round: int = 1, player_count: int = 1):
        self.scene = scene
        self.player_count = max(1, player_count)
        self.current_round = starting_round
        self.spawn_window_seconds = ROUND_SPAWN_WINDOW_SECONDS
        self.zombies_to_spawn = self._target_zombie_count(starting_round)
        self.time_between_spawns = self.spawn_window_seconds / max(1, self.zombies_to_spawn)
        self.spawn_timer = 0.0
        self.end_round_sound = assets.sound("end_round_sound.mp3")
        self.round_text_countdown = 0  # ms; >0 means show "Round N" overlay

    def is_hellhound_round(self, round_num: int | None = None) -> bool:
        r = self.current_round if round_num is None else round_num
        return r > 0 and r % HELLHOUND_ROUND_INTERVAL == 0

    def _target_zombie_count(self, round_num: int) -> int:
        # CoD scales zombie count up by player count, roughly +50% per extra.
        scale = 1.0 + 0.5 * (self.player_count - 1)
        if self.is_hellhound_round(round_num):
            return max(6, int(round_num * 2 * scale))
        return int(ZOMBIES_PER_ROUND_MULTIPLIER * round_num * scale)

    def tick(self, dt_seconds: float):
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
        cls = self._choose_zombie_class()
        cls(self.scene, spawn.x, spawn.y)

    def _choose_zombie_class(self):
        r = self.current_round
        if self.is_hellhound_round():
            return Hellhound
        roll = random.random()
        if r >= 5 and roll < 0.20:
            return Runner
        if r >= 3 and roll < 0.30:
            return Crawler
        return Zombie

    def _begin_next_round(self):
        self.current_round += 1
        self.scene.player.grenade_count = STARTING_GRENADES
        self.round_text_countdown = 500
        self.end_round_sound.play()
        self.zombies_to_spawn = self._target_zombie_count(self.current_round)
        self.time_between_spawns = self.spawn_window_seconds / max(1, self.zombies_to_spawn)
