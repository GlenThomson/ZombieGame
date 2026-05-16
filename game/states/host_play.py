"""Host-side PlayState: runs the full game (like SP), but each frame it
also pulls remote-client inputs into their RemoteInputSources and
broadcasts a snapshot of the current scene to all connected clients."""
import pygame

from game.net import protocol
from game.systems.input import RemoteInputSource
from game.states.play import PlayState
from game.states.snapshot import build_snapshot


class HostPlayState(PlayState):
    def on_enter(self, *, server, lobby_clients: list, grid, background=None,
                 door_costs=None, wall_buy_weapons=None, perk_machine_perks=None,
                 floor_grid: list | None = None,
                 wall_style: str = "brick",
                 decor: list | None = None,
                 host_name: str = "Host", **kwargs):
        # Server holds the connected client list. We need a RemoteInputSource
        # for each client and we must give them stable player_ids matching
        # what each client thinks it is (the player_id sent in S_WELCOME).
        self.server = server
        self.client_id_to_input: dict[int, RemoteInputSource] = {}
        remote_input_sources = {}
        names = [host_name]
        for client in lobby_clients:
            src = RemoteInputSource()
            self.client_id_to_input[client.player_id] = src
            remote_input_sources[client.player_id] = src
            names.append(client.name)

        player_count = 1 + len(lobby_clients)
        super().on_enter(
            grid=grid,
            background=background,
            door_costs=door_costs,
            wall_buy_weapons=wall_buy_weapons,
            perk_machine_perks=perk_machine_perks,
            floor_grid=floor_grid,
            wall_style=wall_style,
            decor=decor or [],
            player_count=player_count,
            local_player_id=0,
            remote_input_sources=remote_input_sources,
            player_names=names,
        )

    def update(self):
        # Pull latest input from each client and feed its RemoteInputSource.
        for client in self.server.connected_clients():
            src = self.client_id_to_input.get(client.player_id)
            if src is None:
                continue
            wire = client.latest_input
            # Translate dict from net.host into wire format expected by InputState.
            src.feed_wire({
                "keys": list(wire.get("keys", ())),
                "mouse_pos": list(wire.get("mouse_pos", (0, 0))),
                "buttons": list(wire.get("buttons", (False, False, False))),
                "events": list(wire.get("events", ())),
            })

        # Run normal game tick (super does everything: movement, AI, etc.).
        super().update()

        # On game over the parent already switched state — bail.
        if self.app.state is not self:
            self._send_game_over()
            return

        # Broadcast snapshot to all clients.
        try:
            snap = build_snapshot(self)
            self.server.broadcast(snap)
        except Exception as e:
            print(f"[host] snapshot broadcast failed: {type(e).__name__}: {e}")

    def _send_game_over(self):
        try:
            self.server.broadcast({
                "type": protocol.S_GAME_OVER,
                "final_round": self.round_manager.current_round,
                "final_kills": self.kill_count,
            })
        except Exception:
            pass

    def announce_event(self, name: str, data: dict | None = None):
        # Play locally (host hears it) AND broadcast so clients hear it too.
        super().announce_event(name, data)
        try:
            self.server.broadcast({
                "type": protocol.S_EVENT,
                "event": name,
                "data": data or {},
            })
        except Exception:
            pass

    def on_exit(self):
        # Tell clients we're done so they fall back to the menu instead of
        # waiting on snapshots that will never come.
        try:
            self.server.broadcast({"type": protocol.S_GOODBYE})
        except Exception:
            pass
        # Drop the listener so the port isn't held by a zombie server next
        # time the player tries to host.
        try:
            self.server.shutdown()
        except Exception:
            pass
