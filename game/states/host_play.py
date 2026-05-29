"""Host-side PlayState: runs the full game (like SP), but each frame it
also pulls remote-client inputs into their RemoteInputSources and
broadcasts a snapshot of the current scene to all connected clients.

Supports mid-game join: any client that connects to the running server
during play is auto-handed an S_START_GAME and a freshly-spawned Player."""
import pygame

from settings import MAX_PLAYERS, PLAYER_TINTS, TILE_SIZE
from game.net import protocol
from game.systems.input import RemoteInputSource
from game.states.play import PlayState
from game.states.snapshot import build_snapshot
from game.entities.player import Player
from game.stats.perks import PerkSystem


class HostPlayState(PlayState):
    def on_enter(self, *, server, lobby_clients: list, grid, background=None,
                 door_costs=None, wall_buy_weapons=None, perk_machine_perks=None,
                 floor_grid: list | None = None,
                 wall_style: str = "brick",
                 decor: list | None = None,
                 map_name: str = "",
                 announcer=None,
                 host_name: str = "Host", **kwargs):
        # Server holds the connected client list. We need a RemoteInputSource
        # for each client and we must give them stable player_ids matching
        # what each client thinks it is (the player_id sent in S_WELCOME).
        self.server = server
        self.announcer = announcer  # may be None if launched without lobby
        self.client_id_to_input: dict[int, RemoteInputSource] = {}

        # Build the explicit player roster. The host is always pid=0; each
        # lobby client keeps the pid the server already told them about (so
        # the snapshot they receive includes a player with their pid and the
        # client's camera can find itself).
        def _world_mouse_host():
            mx, my = pygame.mouse.get_pos()
            return (mx - self.camera.camera.x, my - self.camera.camera.y)

        from game.systems.input import LocalInputSource as _LocalInput
        players_spec: list[tuple[int, str, object]] = [
            (0, host_name, _LocalInput(world_mouse_provider=_world_mouse_host)),
        ]
        for client in lobby_clients:
            src = RemoteInputSource()
            self.client_id_to_input[client.player_id] = src
            players_spec.append((client.player_id, client.name, src))

        # Stash the original map blob so late joiners can be re-handed
        # S_START_GAME without us having to track each field separately.
        # Send only the basename so clients on other machines resolve via
        # their local assets/images/ fallback; also bundle the raw bytes
        # so clients that don't have the asset locally still match the host.
        import os as _os
        bg_for_wire = _os.path.basename(background) if background else None
        from game.states.host_lobby import _read_bg_bytes
        bg_bytes = _read_bg_bytes(background)
        self._start_game_payload = {
            "type": protocol.S_START_GAME,
            "map_name": map_name,
            "grid": grid,
            "background_image_path": bg_for_wire,
            "background_image_bytes": bg_bytes,
            "door_costs": door_costs or {},
            "wall_buy_weapons": wall_buy_weapons or {},
            "perk_machine_perks": perk_machine_perks or {},
            "floor_grid": floor_grid,
            "wall_style": wall_style,
            "decor": decor or [],
        }
        super().on_enter(
            grid=grid,
            background=background,
            door_costs=door_costs,
            wall_buy_weapons=wall_buy_weapons,
            perk_machine_perks=perk_machine_perks,
            floor_grid=floor_grid,
            wall_style=wall_style,
            decor=decor or [],
            local_player_id=0,
            players_spec=players_spec,
        )

    # ---- mid-game join ----

    def _check_for_late_joiners(self):
        """Promote any newly-connected client into a real Player + InputSource
        and hand them S_START_GAME so their JoinLobbyState bounces straight
        into ClientPlayState."""
        # Cap the table at MAX_PLAYERS so we don't over-spawn.
        if len(self.players) >= MAX_PLAYERS:
            return
        for client in self.server.connected_clients():
            if client.player_id in self.client_id_to_input:
                continue  # already a player
            if len(self.players) >= MAX_PLAYERS:
                # Tell the late joiner the game is full so they don't hang.
                try:
                    client.send({"type": protocol.S_REJECT, "reason": "game full"})
                except Exception:
                    pass
                continue
            try:
                self._add_late_joiner(client)
            except Exception as e:
                # If we crash mid-promotion, the joiner would otherwise sit
                # in their join screen forever. Tell them what happened so
                # they can retry, and roll back the half-built Player.
                print(f"[host] late-join failed for client {client.player_id}: "
                      f"{type(e).__name__}: {e}")
                self.client_id_to_input.pop(client.player_id, None)
                self.perk_system_by_player.pop(client.player_id, None)
                self.players = [p for p in self.players if p.player_id != client.player_id]
                try:
                    client.send({"type": protocol.S_REJECT,
                                 "reason": "host failed to add you to the game"})
                except Exception:
                    pass

    def _add_late_joiner(self, client):
        # Spawn near the host so the new player isn't dropped in a sealed-off
        # back room they haven't paid the doors to reach.
        host = self.players[0]
        spawn_x = host.rect.centerx + 20
        spawn_y = host.rect.centery + 20

        src = RemoteInputSource()
        self.client_id_to_input[client.player_id] = src
        tint = PLAYER_TINTS[client.player_id % len(PLAYER_TINTS)] if client.player_id > 0 else None
        new_player = Player(
            self, spawn_x, spawn_y,
            player_id=client.player_id,
            name=client.name,
            input_source=src,
            tint=tint,
        )
        self.players.append(new_player)
        self.perk_system_by_player[client.player_id] = PerkSystem(new_player)

        # Send the map payload directly to the new client. Their JoinLobbyState
        # already handles S_START_GAME and switches to ClientPlayState.
        try:
            client.send(self._start_game_payload)
        except Exception:
            pass

    def update(self):
        # Refresh LAN announcement player count so mid-game joiners see
        # accurate state.
        if self.announcer is not None:
            self.announcer.update(player_count=len(self.players), in_game=True)

        # Promote any new TCP connections into players + ship them the map.
        self._check_for_late_joiners()

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
        if self.announcer is not None:
            self.announcer.stop()
