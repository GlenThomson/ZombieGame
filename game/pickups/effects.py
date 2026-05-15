"""Pickup effect registry. Add a new pickup by writing one function and tagging
it with @effect("name"). The Pickup class dispatches by name with no if/elif.

Each effect optionally registers an `icon=(label, fill_rgb)` so the Pickup can
synthesize a placeholder sprite when there's no matching .png in assets."""
from typing import Callable
from game import assets


_REGISTRY: dict[str, Callable] = {}
_WEIGHTS: dict[str, float] = {}
_ICONS: dict[str, tuple[str, tuple[int, int, int]]] = {}


def effect(name: str, *, weight: float = 1.0,
           icon: tuple[str, tuple[int, int, int]] | None = None):
    def decorator(fn: Callable):
        _REGISTRY[name] = fn
        _WEIGHTS[name] = weight
        if icon is not None:
            _ICONS[name] = icon
        return fn
    return decorator


def names() -> list[str]:
    return list(_REGISTRY.keys())


def weighted_names() -> tuple[list[str], list[float]]:
    return list(_REGISTRY.keys()), list(_WEIGHTS.values())


def icon_for(name: str) -> tuple[str, tuple[int, int, int]] | None:
    return _ICONS.get(name)


def apply(name: str, scene):
    handler = _REGISTRY.get(name)
    if handler is None:
        return
    handler(scene)


# ---------------- effect implementations ----------------

@effect("instant_kill", weight=1.0, icon=("IK", (220, 30, 30)))
def _instant_kill(scene):
    assets.sound("instant_kill.mp3").play()
    for zombie in scene.zombies:
        zombie.health = 1


@effect("nuke_pickup", weight=2.0, icon=("NK", (60, 60, 80)))
def _nuke(scene):
    assets.sound("kaboom.mp3").play()
    assets.sound("nuke_sound.mp3").play()
    for zombie in scene.zombies:
        zombie.kill()


@effect("max_ammo", weight=1.5, icon=("MA", (220, 200, 30)))
def _max_ammo(scene):
    assets.sound("end_round_sound.mp3").play()
    for slot in scene.player.inventory.slots:
        if slot is None:
            continue
        slot.current_ammo = slot.magazine_size
        slot.is_reloading = False


@effect("double_points", weight=1.0, icon=("2X", (30, 200, 30)))
def _double_points(scene):
    # Stamps a temporary modifier on the player; PlayState reads
    # POINTS_PER_HIT/KILL via this multiplier. The effect lasts 30 seconds —
    # set up via PlayState.timed_effects (see PlayState).
    scene.start_timed_effect("double_points", duration_ms=30_000,
                              on_apply=lambda: setattr(scene, "points_multiplier", 2.0),
                              on_expire=lambda: setattr(scene, "points_multiplier", 1.0))


@effect("carpenter", weight=1.0, icon=("CP", (140, 100, 50)))
def _carpenter(scene):
    from settings import WINDOW_PLANK_COUNT
    repaired_anything = False
    for window in list(scene.windows):
        if window.planks < WINDOW_PLANK_COUNT:
            window.planks = WINDOW_PLANK_COUNT
            window._render()
            repaired_anything = True
    if repaired_anything:
        scene.player.points += 200
