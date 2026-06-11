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


def apply(name: str, scene, collector=None):
    handler = _REGISTRY.get(name)
    if handler is None:
        return
    handler(scene, collector)


# ---------------- effect implementations ----------------

@effect("instant_kill", weight=1.0, icon=("IK", (220, 30, 30)))
def _instant_kill(scene, collector=None):
    """BO1: 30 seconds where EVERY zombie (including new spawns) dies to a
    single hit. Implemented as a scene flag the damage code checks."""
    scene.announce_event("instant_kill", {"sound": "instant_kill.mp3"})
    scene.start_timed_effect(
        "instant_kill", duration_ms=30_000,
        on_apply=lambda: setattr(scene, "instant_kill_active", True),
        on_expire=lambda: setattr(scene, "instant_kill_active", False),
    )


@effect("nuke_pickup", weight=2.0, icon=("NK", (60, 60, 80)))
def _nuke(scene, collector=None):
    from settings import NUKE_POINTS
    from game.entities.effects import FloatingText
    scene.announce_event("nuke", {"sound": "kaboom.mp3"})
    scene.announce_event("nuke", {"sound": "nuke_sound.mp3"})
    for zombie in scene.zombies:
        zombie.kill()
    # BO1: everyone gets a flat 400 points.
    for player in scene.players:
        if not player.is_dead():
            player.points += NUKE_POINTS
    FloatingText(scene, scene.local_player.pos, f"+{NUKE_POINTS}",
                 color=(120, 255, 120))


@effect("max_ammo", weight=1.5, icon=("MA", (220, 200, 30)))
def _max_ammo(scene, collector=None):
    from settings import STARTING_GRENADES
    scene.announce_event("max_ammo", {"sound": "end_round_sound.mp3"})
    # All players' weapons get a full mag + full reserve, and grenades
    # are restocked (CoD: max-ammo helps the whole team).
    for player in scene.players:
        player.grenade_count = max(player.grenade_count, STARTING_GRENADES)
        for slot in player.inventory.slots:
            if slot is None:
                continue
            slot.current_ammo = slot.magazine_size
            slot.reserve_ammo = slot.reserve_max
            slot.is_reloading = False


@effect("double_points", weight=1.0, icon=("2X", (30, 200, 30)))
def _double_points(scene, collector=None):
    scene.start_timed_effect(
        "double_points", duration_ms=30_000,
        on_apply=lambda: setattr(scene, "points_multiplier", 2.0),
        on_expire=lambda: setattr(scene, "points_multiplier", 1.0),
    )


@effect("carpenter", weight=1.0, icon=("CP", (140, 100, 50)))
def _carpenter(scene, collector=None):
    from settings import WINDOW_PLANK_COUNT
    repaired_anything = False
    for window in list(scene.windows):
        if window.planks < WINDOW_PLANK_COUNT:
            window.planks = WINDOW_PLANK_COUNT
            window._render()
            repaired_anything = True
    if repaired_anything and collector is not None:
        collector.points += 200


@effect("monkey_bombs", weight=0.6, icon=("MB", (220, 100, 160)))
def _monkey_bombs(scene, collector=None):
    """Grants 4 monkey bombs to the collecting player."""
    scene.announce_event("monkey_pickup", {"sound": "instant_kill.mp3"})
    if collector is not None:
        collector.monkey_bomb_count = min(4, collector.monkey_bomb_count + 4)


@effect("fire_sale", weight=0.6, icon=("FS", (220, 60, 200)))
def _fire_sale(scene, collector=None):
    """Mystery boxes drop to 10 points for 30 seconds."""
    from settings import MYSTERY_BOX_COST

    def _start():
        for box in scene.mystery_boxes:
            box.cost = 10

    def _end():
        for box in scene.mystery_boxes:
            box.cost = MYSTERY_BOX_COST

    scene.announce_event("fire_sale", {"sound": "kaboom.mp3"})
    scene.start_timed_effect(
        "fire_sale", duration_ms=30_000, on_apply=_start, on_expire=_end,
    )
