"""Pickup effect registry. Add a new pickup by writing one function and tagging
it with @effect("name"). The Pickup class dispatches by name with no if/elif."""
from typing import Callable
from game import assets


_REGISTRY: dict[str, Callable] = {}
_WEIGHTS: dict[str, float] = {}


def effect(name: str, *, weight: float = 1.0):
    """Register a pickup effect. `weight` controls how often it spawns
    relative to other pickups."""
    def decorator(fn: Callable):
        _REGISTRY[name] = fn
        _WEIGHTS[name] = weight
        return fn
    return decorator


def names() -> list[str]:
    return list(_REGISTRY.keys())


def weighted_names() -> tuple[list[str], list[float]]:
    return list(_REGISTRY.keys()), list(_WEIGHTS.values())


def apply(name: str, scene):
    handler = _REGISTRY.get(name)
    if handler is None:
        return
    handler(scene)


# ---------------- effect implementations ----------------

@effect("instant_kill", weight=1.0)
def _instant_kill(scene):
    assets.sound("instant_kill.mp3").play()
    for zombie in scene.zombies:
        zombie.health = 1


@effect("nuke_pickup", weight=2.0)
def _nuke(scene):
    assets.sound("kaboom.mp3").play()
    assets.sound("nuke_sound.mp3").play()
    for zombie in scene.zombies:
        zombie.kill()
