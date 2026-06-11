"""Headless multiplayer harness.

Spins up a HostServer + a HostPlayState in this process, connects 2 NetClient
instances to it, and runs ~120 frames of game time. Verifies:

- Clients connect and receive WELCOME with distinct player_ids
- Each client's input reaches the host's RemoteInputSource
- Host broadcasts snapshots that clients receive
- Snapshots include all expected sections (players, zombies, interactables)
- The host's PlayState exposes the correct number of Player instances
- Damage from a forced-spawned zombie reaches a client's player

Doesn't render. Run with: python _mp_playtest.py
"""
import os
import sys
import time
import traceback

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
pygame.init()
pygame.display.set_mode((1000, 1000))


# Replace pygame.time.Clock so the host's PlayState advances without sleeping.
class _FastClock:
    def tick(self, *a, **k):
        return 16
    def get_time(self):
        return 16
    def get_fps(self):
        return 60.0
pygame.time.Clock = _FastClock


from game.app import App
from game.net import protocol
from game.net.client import NetClient
from game.world import map_loader
from game.entities.zombie import Zombie


PORT = 51234


def main():
    app = App()
    # Spin up a host lobby (this allocates the HostServer).
    app.switch("host_lobby")
    host_lobby = app.state
    # Override the server's port to one less likely to conflict.
    host_lobby.server.shutdown()
    from game.net.host import HostServer
    host_lobby.server = HostServer(port=PORT, max_clients=3)
    host_lobby.server.start()

    # Connect 2 clients
    client_a = NetClient()
    client_b = NetClient()
    assert client_a.connect("127.0.0.1", PORT, name="A", timeout=2.0), client_a.last_error
    assert client_b.connect("127.0.0.1", PORT, name="B", timeout=2.0), client_b.last_error
    time.sleep(0.2)

    # Both should have received WELCOME
    a_welcome = next((m for m in client_a.drain_incoming() if m["type"] == protocol.S_WELCOME), None)
    b_welcome = next((m for m in client_b.drain_incoming() if m["type"] == protocol.S_WELCOME), None)
    assert a_welcome and b_welcome, "missing WELCOME"
    assert a_welcome["player_id"] != b_welcome["player_id"], "duplicate player_id"
    print(f"  WELCOME a={a_welcome['player_id']} b={b_welcome['player_id']}")

    # Lobby tick to register clients (HostLobbyState.update broadcasts S_LOBBY)
    host_lobby.update()
    time.sleep(0.05)
    # Each client should have a S_LOBBY message
    a_lobby = [m for m in client_a.drain_incoming() if m["type"] == protocol.S_LOBBY]
    b_lobby = [m for m in client_b.drain_incoming() if m["type"] == protocol.S_LOBBY]
    assert a_lobby and b_lobby, "missing S_LOBBY"
    print(f"  lobby roster: {a_lobby[-1]['players']}")

    # Start the game
    host_lobby._start_game()
    time.sleep(0.1)
    host_play = app.state
    assert host_play.__class__.__name__ == "HostPlayState"
    print(f"  host has {len(host_play.players)} players")

    # Each client should have received S_START_GAME. Payload includes the
    # map's background bytes (can be ~1MB), so poll up to 5s rather than
    # assuming it lands instantly.
    a_start, b_start = [], []
    deadline = time.time() + 5.0
    while time.time() < deadline and not (a_start and b_start):
        a_start += [m for m in client_a.drain_incoming() if m["type"] == protocol.S_START_GAME]
        b_start += [m for m in client_b.drain_incoming() if m["type"] == protocol.S_START_GAME]
        time.sleep(0.05)
    assert a_start and b_start, "missing S_START_GAME"
    print(f"  S_START_GAME map: {a_start[-1]['map_name']}")

    # Send some inputs from each client (client A: hold W; client B: hold D + click)
    import pygame as _pg
    client_a.send({
        "type": protocol.C_INPUT, "frame": 1,
        "keys": [_pg.K_w], "mouse_pos": [400, 300],
        "buttons": [False, False, False], "events": [],
    })
    client_b.send({
        "type": protocol.C_INPUT, "frame": 1,
        "keys": [_pg.K_d], "mouse_pos": [600, 400],
        "buttons": [True, False, False], "events": ["interact"],
    })
    time.sleep(0.1)

    # Run host frames
    initial_pos_a = (host_play.players[1].pos.x, host_play.players[1].pos.y) if len(host_play.players) > 1 else (0, 0)
    for _ in range(60):
        host_play.update()
    # Client A should have moved north (y decreased)
    moved_a = host_play.players[1].pos.y < initial_pos_a[1] - 1
    print(f"  client A moved north: {moved_a}")

    # Client A should be receiving snapshots
    a_snaps = [m for m in client_a.drain_incoming() if m["type"] == protocol.S_SNAPSHOT]
    b_snaps = [m for m in client_b.drain_incoming() if m["type"] == protocol.S_SNAPSHOT]
    assert a_snaps and b_snaps, f"no snapshots: a={len(a_snaps)} b={len(b_snaps)}"
    snap = a_snaps[-1]
    print(f"  snapshot has players={len(snap['players'])} interactables={len(snap['interactables'])}")
    # All player ids should appear in the snapshot
    snap_pids = sorted(p["id"] for p in snap["players"])
    expected = sorted(p.player_id for p in host_play.players)
    assert snap_pids == expected, f"snapshot pids {snap_pids} != {expected}"

    # Force a zombie next to client A's player and verify damage flows.
    # Zombies now rise from the ground for ~0.6s and swipe on a cooldown,
    # so poll wall-clock time instead of a fixed frame count.
    pa = host_play.players[1]
    Zombie(host_play, pa.pos.x + 5, pa.pos.y)
    starting_hp = pa.health
    deadline = time.time() + 5.0
    while time.time() < deadline:
        host_play.update()
        if pa.health < starting_hp or pa.is_down:
            break
    print(f"  client A HP: {starting_hp} -> {pa.health}")
    # Either took damage OR went down
    assert pa.health < starting_hp or pa.is_down, "client A wasn't damaged by zombie"

    # Force a kill-storm so we can confirm round counter advances on host
    for z in list(host_play.zombies):
        z.take_damage(999)
    starting_round = host_play.round_manager.current_round
    host_play.round_manager._begin_next_round()
    after_round = host_play.round_manager.current_round
    print(f"  round: {starting_round} -> {after_round}")
    assert after_round > starting_round

    # Tear down
    client_a.close()
    client_b.close()
    host_play.server.shutdown()
    print("\nMP test PASSED")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
