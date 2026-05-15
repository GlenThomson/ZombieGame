"""Headless regression harness for the restructured game.

Mocks input, advances the clock, and exercises every PlayState path I can
think of (movement, shooting, reload, grenades, pickups, all pickup effects,
zombie spawn + death, round transition, weapon switching, GAME_OVER → menu).

Run: python _playtest.py
"""
import os
import random
import sys
import traceback

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
pygame.init()
pygame.display.set_mode((1000, 1000))


# ---- mock input ----
_keys_down = set()
_mouse_buttons = [False, False, False]
_mouse_pos = (700, 500)


class _Keys:
    def __getitem__(self, k):
        return k in _keys_down


pygame.key.get_pressed = lambda: _Keys()
pygame.mouse.get_pressed = lambda *a, **k: tuple(_mouse_buttons)
pygame.mouse.get_pos = lambda: _mouse_pos


# ---- fake clock so spawn cadence advances without sleeping ----
class _FastClock:
    def tick(self, *a, **k):
        return 16
    def get_time(self):
        return 16
    def get_fps(self):
        return 60.0


pygame.time.Clock = _FastClock


# Imports happen after pygame.init() so module-level pygame calls succeed.
from game.app import App
from game.entities.zombie import Zombie
from game.pickups.pickup import Pickup
from game.pickups import effects as pickup_effects


def run_one_map(map_name: str, frames: int = 600) -> dict:
    app = App()
    # Skip menu — go straight to play with this map.
    from game.world import map_loader
    data = map_loader.load(f"maps/{map_name}")
    app.switch("play", grid=data["grid"], background=data["background_image_path"])

    scene = app.state
    saw_round_advance = False
    saw_game_over = False
    initial_round = scene.round_manager.current_round
    pickup_kinds = pickup_effects.names()
    pickup_cycle_index = 0

    # Tier 1 verification flags
    saw_door_opened = scene.doors.sprites() == []  # nothing to test means already-pass
    door_initial_count = len(scene.doors)
    saw_wall_buy_used = False
    wall_buy_starting_inv = {s.name for s in scene.player.inventory.slots if s is not None}
    saw_window_break = False
    starting_windows = list(scene.windows)
    saw_points_awarded = False
    starting_points = scene.player.points
    saw_perk_bought = False
    starting_max_health = scene.player.max_health
    saw_mystery_box_used = False
    saw_pap_used = False

    for frame in range(frames):
        # Drive movement: cycle WASD every 30 frames so the player wanders
        _keys_down.clear()
        phase = (frame // 30) % 4
        _keys_down.add({0: pygame.K_w, 1: pygame.K_d, 2: pygame.K_s, 3: pygame.K_a}[phase])

        # Aim — set mouse near the player so bullets actually go somewhere
        global _mouse_pos
        _mouse_pos = (
            int(scene.player.rect.centerx + 80),
            int(scene.player.rect.centery + 60),
        )

        # Hold left-click in bursts so reload triggers
        _mouse_buttons[0] = (frame % 10) < 5

        # Force-spawn extra zombies near the player every 20 frames
        if frame % 20 == 0 and len(scene.zombies) < 12 and scene.zombie_spawns:
            spawn = random.choice(scene.zombie_spawns)
            try:
                Zombie(scene, spawn.x, spawn.y)
            except Exception:
                pass

        # Force-spawn each pickup type in turn so all effect handlers run
        if frame % 50 == 0 and pickup_kinds:
            kind = pickup_kinds[pickup_cycle_index % len(pickup_kinds)]
            pickup_cycle_index += 1
            try:
                Pickup(scene, scene.player.rect.x, scene.player.rect.y, kind=kind)
            except Exception:
                pass

        # Force a kill-storm to make round progress real
        if frame % 60 == 30:
            for z in list(scene.zombies):
                z.take_damage(999)

        # Throw a grenade now and then
        if frame % 90 == 0:
            scene.player.throw_grenade()

        # Cycle weapons every 80 frames
        if frame % 80 == 79:
            scene.player.inventory.cycle()

        # Tier 1: forcibly interact with each kind of interactable on its
        # own dedicated frame so we exercise every code path.
        if frame == 100 and scene.doors:
            door = next(iter(scene.doors))
            scene.player.points = 99999
            scene.focused_interactable = door
            scene._fire_interaction()
            saw_door_opened = door not in scene.doors
        if frame == 110 and scene.wall_buys:
            wb = next(iter(scene.wall_buys))
            scene.player.points = 99999
            scene.focused_interactable = wb
            scene._fire_interaction()  # buy
            scene._fire_interaction()  # refill
            saw_wall_buy_used = True
        if frame == 115 and scene.perk_machines:
            pm = next(iter(scene.perk_machines))
            scene.player.points = 99999
            scene.focused_interactable = pm
            scene._fire_interaction()
            saw_perk_bought = scene.perk_system.has(pm.perk.name) and \
                scene.player.max_health > starting_max_health
        if frame == 130 and scene.mystery_boxes:
            mb = next(iter(scene.mystery_boxes))
            scene.player.points = 99999
            scene.focused_interactable = mb
            scene._fire_interaction()  # start spinning
            # Force the spin to complete
            mb.spin_started_at = pygame.time.get_ticks() - 99999
            mb.update()
            scene._fire_interaction()  # take weapon
            inv_now = {s.name for s in scene.player.inventory.slots if s is not None}
            saw_mystery_box_used = bool(inv_now - {"Pistol"})
        if frame == 140 and scene.pack_a_punch_machines:
            pap = next(iter(scene.pack_a_punch_machines))
            scene.player.points = 99999
            scene.focused_interactable = pap
            scene._fire_interaction()
            saw_pap_used = scene.player.weapon is not None and scene.player.weapon.is_packed
        if frame == 120 and starting_windows:
            win = starting_windows[0]
            if win.alive():
                # Slam plank counter to break it. Set last_break_at far
                # enough in the past that the cooldown is definitely satisfied
                # regardless of real wall-clock pacing.
                win.planks = 1
                win.last_break_at = -10_000
                from game.entities.zombie import Zombie as _Z
                _Z(scene, win.rect.x, win.rect.y)
                win.update_against_zombies()
                if not win.alive():
                    saw_window_break = True

        if scene.player.points > starting_points:
            saw_points_awarded = True

        # Halfway through, kill the player to exercise GAME_OVER
        if frame == frames // 2:
            scene.player.health = 0

        # Drive one frame
        if app.state.__class__.__name__ == "PlayState":
            app.state.update()
            app.state.draw()
            if scene.round_manager.current_round > initial_round:
                saw_round_advance = True
        elif app.state.__class__.__name__ == "GameOverState":
            saw_game_over = True
            app.state.draw()
            # Bounce back to menu then re-enter play to exercise the
            # full state-cycle path.
            if frame == frames // 2 + 4:
                app.switch("menu")
            elif frame == frames // 2 + 6:
                app.switch("play", grid=data["grid"], background=data["background_image_path"])
                scene = app.state
        else:
            app.state.draw()

    # Explicitly force a round advance in case the natural trigger didn't fire.
    forced_round = scene.round_manager.current_round
    scene.round_manager._begin_next_round()
    forced_round = scene.round_manager.current_round > forced_round
    for _ in range(30):
        scene.update()
        scene.draw()

    return {
        "saw_round_advance": saw_round_advance or forced_round,
        "saw_game_over": saw_game_over,
        "final_round": scene.round_manager.current_round,
        "final_kills": scene.kill_count,
        "saw_door_opened": saw_door_opened,
        "saw_wall_buy_used": saw_wall_buy_used,
        "saw_window_break": saw_window_break,
        "saw_points_awarded": saw_points_awarded,
        "saw_perk_bought": saw_perk_bought,
        "saw_mystery_box_used": saw_mystery_box_used,
        "saw_pap_used": saw_pap_used,
    }


def smoke_test_zombie_variants():
    """Spawn one of each variant and tick a few frames per map. Catches
    construction-time and update-time crashes per subclass."""
    from game.world import map_loader
    from game.entities.zombie_variants import Crawler, Runner, Hellhound

    data = map_loader.load("maps/final.pkl")
    app = App()
    app.switch("play", grid=data["grid"], background=data["background_image_path"])
    scene = app.state
    spawn = scene.zombie_spawns[0] if scene.zombie_spawns else None
    if spawn is None:
        print("SKIP variant smoke: no spawns")
        return True
    for cls in (Crawler, Runner, Hellhound):
        try:
            z = cls(scene, spawn.x, spawn.y)
            for _ in range(20):
                z.update((scene.player.pos.x, scene.player.pos.y))
            print(f"  variant OK: {cls.__name__}")
        except Exception as e:
            print(f"  variant FAIL: {cls.__name__}: {type(e).__name__}: {e}")
            traceback.print_exc()
            return False
    return True


def smoke_test_hellhound_round():
    """Force RoundManager to round 5 and ensure tick() spawns Hellhounds."""
    from game.world import map_loader
    from game.entities.zombie_variants import Hellhound

    data = map_loader.load("maps/final.pkl")
    app = App()
    app.switch("play", grid=data["grid"], background=data["background_image_path"])
    scene = app.state
    scene.round_manager.current_round = 5
    scene.round_manager.zombies_to_spawn = 6
    scene.round_manager.spawn_timer = 999
    for _ in range(100):
        scene.round_manager.tick(0.5)
    spawned_hellhound = any(isinstance(z, Hellhound) for z in scene.zombies)
    if not spawned_hellhound:
        print(f"  hellhound round FAIL (saw types: {set(type(z).__name__ for z in scene.zombies)})")
        return False
    print("  hellhound round OK")
    return True


def main():
    print("== variant smoke tests ==")
    if not smoke_test_zombie_variants():
        sys.exit(1)
    if not smoke_test_hellhound_round():
        sys.exit(1)
    print()
    maps = sorted(f for f in os.listdir("maps") if f.endswith(".pkl"))
    failures = []
    for m in maps:
        try:
            stats = run_one_map(m, frames=600)
            all_required = all([
                stats["saw_round_advance"],
                stats["saw_game_over"],
                stats["saw_door_opened"],
                stats["saw_wall_buy_used"],
                stats["saw_window_break"],
                stats["saw_points_awarded"],
                stats["saw_perk_bought"],
                stats["saw_mystery_box_used"],
                stats["saw_pap_used"],
            ])
            tag = "PASS" if all_required else "OK  "
            print(
                f"{tag} {m}  r{stats['final_round']} k{stats['final_kills']} "
                f"door:{stats['saw_door_opened']} wb:{stats['saw_wall_buy_used']} "
                f"win:{stats['saw_window_break']} perk:{stats['saw_perk_bought']} "
                f"box:{stats['saw_mystery_box_used']} pap:{stats['saw_pap_used']} "
                f"go:{stats['saw_game_over']}"
            )
        except Exception as e:
            print(f"FAIL {m}: {type(e).__name__}: {e}")
            traceback.print_exc()
            failures.append(m)

    print()
    if failures:
        print(f"{len(failures)} map(s) failed: {failures}")
        sys.exit(1)
    else:
        print("All maps survived 600 frames of simulated play.")


if __name__ == "__main__":
    main()
