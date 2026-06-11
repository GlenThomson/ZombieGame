"""Input abstraction.

Two implementations:
- LocalInputSource: reads pygame.key/mouse directly. Used for the local
  player on host AND on client.
- RemoteInputSource: holds the most recent InputState received over the
  network. Used on the host to drive remotely-controlled players.

A Player asks its `input_source` for the current state once per frame; it
never touches pygame.* directly anymore."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

import pygame


@dataclass
class InputState:
    keys: frozenset[int] = field(default_factory=frozenset)
    mouse_pos: tuple[int, int] = (0, 0)
    buttons: tuple[bool, bool, bool] = (False, False, False)
    # Discrete one-shot events raised this frame (key DOWN edges):
    # e.g. ("interact", "grenade", "reload", "switch:1", "switch:2", ...)
    events: tuple[str, ...] = ()

    def is_down(self, key: int) -> bool:
        return key in self.keys

    def to_wire(self, frame: int) -> dict:
        return {
            "type": "input",
            "frame": frame,
            "keys": sorted(self.keys),
            "mouse_pos": list(self.mouse_pos),
            "buttons": list(self.buttons),
            "events": list(self.events),
        }

    @classmethod
    def from_wire(cls, msg: dict) -> "InputState":
        return cls(
            keys=frozenset(int(k) for k in msg.get("keys", ())),
            mouse_pos=tuple(int(v) for v in msg.get("mouse_pos", (0, 0))[:2]),
            buttons=tuple(bool(b) for b in msg.get("buttons", (False, False, False))[:3]),
            events=tuple(msg.get("events", ())),
        )


class InputSource:
    """Override either snapshot() or push events into self._events."""

    def snapshot(self) -> InputState:
        raise NotImplementedError


class LocalInputSource(InputSource):
    """Polls pygame each frame. Discrete events come from the event-queue
    feed in PlayState.handle_event so we don't double-fire on key-repeat."""

    def __init__(self, world_mouse_provider=None):
        """`world_mouse_provider` is an optional callable that returns the
        mouse position in WORLD coords (after subtracting the camera). When
        omitted, snapshot() returns the raw screen mouse position."""
        self._pending_events: list[str] = []
        self._world_mouse_provider = world_mouse_provider
        self.latest = InputState()

    def push_event(self, name: str):
        self._pending_events.append(name)

    def snapshot(self) -> InputState:
        keys = pygame.key.get_pressed()
        held = []
        for k in (
            pygame.K_w, pygame.K_a, pygame.K_s, pygame.K_d,
            pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT,
            pygame.K_f, pygame.K_g, pygame.K_r, pygame.K_t,
            pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
            pygame.K_LSHIFT, pygame.K_RSHIFT,   # sprint
        ):
            if keys[k]:
                held.append(k)
        events = tuple(self._pending_events)
        self._pending_events.clear()
        if self._world_mouse_provider is not None:
            mouse_pos = self._world_mouse_provider()
        else:
            mouse_pos = pygame.mouse.get_pos()
        state = InputState(
            keys=frozenset(held),
            mouse_pos=mouse_pos,
            buttons=pygame.mouse.get_pressed(),
            events=events,
        )
        self.latest = state
        return state


class RemoteInputSource(InputSource):
    """Driven from the network: caller assigns latest InputState whenever a
    new packet arrives."""

    def __init__(self):
        self.latest = InputState()

    def feed_wire(self, msg: dict):
        self.latest = InputState.from_wire(msg)

    def snapshot(self) -> InputState:
        # Each snapshot consumes one batch of discrete events so they don't
        # re-fire on subsequent frames before the next packet arrives.
        s = self.latest
        if s.events:
            self.latest = InputState(
                keys=s.keys,
                mouse_pos=s.mouse_pos,
                buttons=s.buttons,
                events=(),
            )
        return s


# --- mapping for which keys are "movement" per scheme ---

MOVEMENT_WASD = {
    "left": pygame.K_a, "right": pygame.K_d,
    "up": pygame.K_w, "down": pygame.K_s,
}
MOVEMENT_ARROWS = {
    "left": pygame.K_LEFT, "right": pygame.K_RIGHT,
    "up": pygame.K_UP, "down": pygame.K_DOWN,
}
