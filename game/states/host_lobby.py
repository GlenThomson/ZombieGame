"""Host lobby: shows our LAN IP, lists connected players, lets us pick a
map and start the game."""
import os
import socket
import pygame

from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    MENU_TITLE,
    MENU_TEXT,
    MENU_TEXT_DIM,
    GOLD,
    DEFAULT_HOST_PORT,
    MAX_PLAYERS,
)
from game.net.host import HostServer
from game.states.base import State
from game.ui.menu_widgets import Button, draw_menu_background
from game.world import map_loader


def _read_bg_bytes(bg_path: str | None) -> bytes | None:
    """Return the raw bytes of the background image, or None if there's no
    file. We hunt at the exact path first, then fall back to
    assets/images/<basename> so a map saved with a path like
    C:/.../zombiemap..png still finds its companion asset that lives in the
    repo. Bundled into S_START_GAME so clients don't need a local copy."""
    if not bg_path:
        return None
    candidates = [bg_path]
    base = os.path.basename(bg_path)
    if base:
        candidates.append(os.path.join("assets", "images", base))
    for path in candidates:
        if os.path.isfile(path):
            try:
                with open(path, "rb") as f:
                    return f.read()
            except OSError:
                return None
    return None


def get_local_ip() -> str:
    """Best-effort local LAN IP. Falls back to 127.0.0.1 if no network."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Doesn't actually send anything; just picks the right interface.
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return "127.0.0.1"


class HostLobbyState(State):
    def on_enter(self, **kwargs):
        self.title_font = pygame.font.Font(None, 80)
        self.body_font = pygame.font.Font(None, 32)
        self.btn_font = pygame.font.Font(None, 36)

        self.server = HostServer(port=DEFAULT_HOST_PORT, max_clients=MAX_PLAYERS - 1)
        self.server.start()
        # Cleared when we hand the server off to HostPlayState; until then,
        # on_exit() will shutdown the server so we don't leak listeners.
        self._server_handed_off = False

        # UDP discovery so clients see this game in their join list. Lives
        # for the duration of the lobby; HostPlayState reuses it via the
        # `announcer` kwarg on switch.
        from game import config
        from game.net.discovery import DiscoveryAnnouncer
        self.host_name = config.player_name()
        self.announcer = DiscoveryAnnouncer(
            host_name=self.host_name, game_port=DEFAULT_HOST_PORT,
        )
        self.announcer.max_players = MAX_PLAYERS
        self.announcer.start()

        self.local_ip = get_local_ip()
        self.maps = map_loader.list_maps()
        self.selected_map_idx = 0 if self.maps else -1

        cx = SCREEN_WIDTH // 2
        self.start_button = Button("Start Game", (cx, SCREEN_HEIGHT - 120), self.btn_font, width=240)
        self.back_button = Button("Cancel", (140, SCREEN_HEIGHT - 60), self.btn_font, width=200, height=44)
        self.next_map_btn = Button(">", (cx + 200, 480), self.btn_font, width=48, height=44)
        self.prev_map_btn = Button("<", (cx - 200, 480), self.btn_font, width=48, height=44)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            for b in (self.start_button, self.back_button, self.next_map_btn, self.prev_map_btn):
                b.update_hover(event.pos)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._cancel()
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_button.clicked(event):
                self._cancel()
                return
            if self.start_button.clicked(event):
                self._start_game()
                return
            if self.maps:
                if self.next_map_btn.clicked(event):
                    self.selected_map_idx = (self.selected_map_idx + 1) % len(self.maps)
                elif self.prev_map_btn.clicked(event):
                    self.selected_map_idx = (self.selected_map_idx - 1) % len(self.maps)

    def _cancel(self):
        self.server.shutdown()
        self.app.switch("multiplayer_menu")

    def _start_game(self):
        if self.selected_map_idx < 0:
            return
        from game.net import protocol
        fname = self.maps[self.selected_map_idx]
        data = map_loader.load(f"maps/{fname}")
        clients = self.server.connected_clients()
        # Ship only the basename of the bg path: an absolute Windows path
        # that resolves on the host won't resolve on a client's machine.
        # _resolve_bg_path on the receiving side falls back to
        # assets/images/<basename>, which is checked into the repo.
        bg_path = data["background_image_path"]
        bg_for_wire = os.path.basename(bg_path) if bg_path else None
        # Also bundle the raw bg image bytes so clients without a
        # matching asset file still render the same view as the host.
        bg_bytes = _read_bg_bytes(bg_path)
        self.server.broadcast({
            "type": protocol.S_START_GAME,
            "map_name": fname,
            "grid": data["grid"],
            "background_image_path": bg_for_wire,
            "background_image_bytes": bg_bytes,
            "door_costs": data["door_costs"],
            "wall_buy_weapons": data["wall_buy_weapons"],
            "perk_machine_perks": data["perk_machine_perks"],
            "floor_grid": data.get("floor_grid"),
            "wall_style": data.get("wall_style", "brick"),
            "decor": data.get("decor", []),
        })
        self._server_handed_off = True
        # Mark the announcer as in-game and hand it off; HostPlayState
        # owns its lifetime from here so the game stays discoverable.
        self.announcer.update(map_name=fname, in_game=True,
                              player_count=1 + len(clients))
        announcer = self.announcer
        self.announcer = None  # don't double-stop in on_exit
        self.app.switch(
            "host_play",
            server=self.server,
            lobby_clients=clients,
            announcer=announcer,
            host_name=self.host_name,
            map_name=fname,
            grid=data["grid"],
            background=data["background_image_path"],
            door_costs=data["door_costs"],
            wall_buy_weapons=data["wall_buy_weapons"],
            perk_machine_perks=data["perk_machine_perks"],
            floor_grid=data.get("floor_grid"),
            wall_style=data.get("wall_style", "brick"),
            decor=data.get("decor", []),
        )

    def on_exit(self):
        # Shut the server down unless we're handing it off to host_play.
        # Without this, every navigation (Cancel / ESC / back to menu) leaks
        # a HostServer that keeps listening on port 50515 — and Windows'
        # SO_REUSEADDR semantics let new connections land on the zombie
        # server whose UI is no longer being drawn.
        if not self._server_handed_off:
            self.server.shutdown()
        # Stop announcing only if we still own it (i.e. we didn't hand it
        # off to HostPlayState above).
        if self.announcer is not None:
            self.announcer.stop()

    def update(self):
        # Push lobby state to clients so they see who else has joined.
        from game.net import protocol
        clients = self.server.connected_clients()
        self.server.broadcast({
            "type": protocol.S_LOBBY,
            "players": [{"id": c.player_id, "name": c.name} for c in clients],
            "hosting_name": self.host_name,
            "map_name": self.maps[self.selected_map_idx] if self.selected_map_idx >= 0 else "",
        })
        # Keep the LAN announcement fresh — map selection and player
        # count change as people join / the host cycles maps.
        if self.announcer is not None:
            self.announcer.update(
                map_name=self.maps[self.selected_map_idx] if self.selected_map_idx >= 0 else "",
                player_count=1 + len(clients),
                in_game=False,
            )

    def draw(self):
        draw_menu_background(self.surface, pygame.time.get_ticks())

        title = self.title_font.render("HOSTING", True, MENU_TITLE)
        self.surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 60))

        ip_line = self.body_font.render(
            f"Tell friends to join: {self.local_ip}:{DEFAULT_HOST_PORT}", True, GOLD,
        )
        self.surface.blit(ip_line, (SCREEN_WIDTH // 2 - ip_line.get_width() // 2, 160))

        # Connected players
        clients = self.server.connected_clients()
        players_label = self.body_font.render(
            f"Players in lobby: {1 + len(clients)} / {MAX_PLAYERS}", True, MENU_TEXT,
        )
        self.surface.blit(players_label, (SCREEN_WIDTH // 2 - players_label.get_width() // 2, 220))
        ypos = 270
        host_line = self.body_font.render(f"- {self.host_name} (you)", True, MENU_TEXT)
        self.surface.blit(host_line, (SCREEN_WIDTH // 2 - 120, ypos))
        ypos += 30
        for c in clients:
            line = self.body_font.render(f"- {c.name}", True, MENU_TEXT)
            self.surface.blit(line, (SCREEN_WIDTH // 2 - 120, ypos))
            ypos += 30

        # Map picker
        map_label = self.body_font.render("Map:", True, MENU_TEXT_DIM)
        self.surface.blit(map_label, (SCREEN_WIDTH // 2 - 50, 440))
        map_name = self.maps[self.selected_map_idx] if self.maps else "(no maps)"
        map_text = self.body_font.render(map_name, True, GOLD)
        self.surface.blit(map_text, (SCREEN_WIDTH // 2 - map_text.get_width() // 2, 480))
        if self.maps:
            self.next_map_btn.draw(self.surface)
            self.prev_map_btn.draw(self.surface)

        self.start_button.draw(self.surface)
        self.back_button.draw(self.surface)

        # Network hint near the bottom — covers the two issues people hit
        # most: Windows Firewall blocking the .exe, and friends on a
        # different network unable to reach the LAN IP.
        hint_font = pygame.font.Font(None, 22)
        for i, line in enumerate([
            "On the same wifi? Friends will see this game in their JOIN list automatically.",
            "Not connecting? Allow Zombies through Windows Firewall when prompted.",
            "Different network? You need a VPN like Hamachi / Tailscale on both PCs.",
        ]):
            rendered = hint_font.render(line, True, MENU_TEXT_DIM)
            self.surface.blit(
                rendered,
                (SCREEN_WIDTH // 2 - rendered.get_width() // 2,
                 SCREEN_HEIGHT - 180 + i * 22),
            )

