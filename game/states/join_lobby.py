"""Join lobby: enter host IP, connect, wait for the game to start."""
import pygame

from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    MENU_TITLE,
    MENU_TEXT,
    MENU_TEXT_DIM,
    GOLD,
    DEFAULT_HOST_PORT,
)
from game.net import protocol
from game.net.client import NetClient
from game.net.discovery import DiscoveryListener
from game.states.base import State
from game.ui.menu_widgets import Button, draw_menu_background


class JoinLobbyState(State):
    def on_enter(self, **kwargs):
        self.title_font = pygame.font.Font(None, 80)
        self.body_font = pygame.font.Font(None, 32)
        self.btn_font = pygame.font.Font(None, 36)
        self.input_font = pygame.font.Font(None, 40)
        self.small_font = pygame.font.Font(None, 26)

        self.ip_text = "127.0.0.1"
        self.port_text = str(DEFAULT_HOST_PORT)
        self.editing_field = "ip"  # "ip" | "port"
        self.status: str = "Pick a game from the list, or type the host's IP."
        self.connect_button = Button(
            "Connect", (SCREEN_WIDTH // 2, 540), self.btn_font, width=200,
        )
        self.back_button = Button(
            "Back", (140, SCREEN_HEIGHT - 60), self.btn_font, width=160, height=44,
        )

        # LAN discovery — listens for host UDP broadcasts.
        self.discovery = DiscoveryListener()
        self.discovery.start()
        # Rects rebuilt per frame in draw() so we can hit-test clicks.
        self._discovery_row_rects: list[tuple[pygame.Rect, dict]] = []

        self.client: NetClient | None = None
        self.my_player_id: int | None = None
        self.lobby_state: dict | None = None

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.connect_button.update_hover(event.pos)
            self.back_button.update_hover(event.pos)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._cancel()
                return
            if event.key == pygame.K_TAB:
                self.editing_field = "port" if self.editing_field == "ip" else "ip"
                return
            if event.key == pygame.K_RETURN:
                self._try_connect()
                return
            if event.key == pygame.K_BACKSPACE:
                if self.editing_field == "ip":
                    self.ip_text = self.ip_text[:-1]
                else:
                    self.port_text = self.port_text[:-1]
                return
            ch = event.unicode
            if not ch:
                return
            if self.editing_field == "ip":
                if ch in "0123456789." and len(self.ip_text) < 21:
                    self.ip_text += ch
            else:
                if ch.isdigit() and len(self.port_text) < 5:
                    self.port_text += ch
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.back_button.clicked(event):
                self._cancel()
                return
            if self.connect_button.clicked(event):
                self._try_connect()
                return
            # Click on a discovered-game row: prefill IP+port and connect.
            for rect, entry in self._discovery_row_rects:
                if rect.collidepoint(event.pos):
                    self.ip_text = str(entry.get("ip", ""))
                    self.port_text = str(entry.get("port", DEFAULT_HOST_PORT))
                    self._try_connect()
                    return
            # Click on either input field to edit it.
            ip_rect = pygame.Rect(SCREEN_WIDTH // 2 - 250, 460, 360, 40)
            port_rect = pygame.Rect(SCREEN_WIDTH // 2 + 130, 460, 120, 40)
            if ip_rect.collidepoint(event.pos):
                self.editing_field = "ip"
            elif port_rect.collidepoint(event.pos):
                self.editing_field = "port"

    def _cancel(self):
        if self.client is not None:
            self.client.close()
        self.discovery.stop()
        self.app.switch("multiplayer_menu")

    def on_exit(self):
        # Make sure the UDP listener thread / socket is freed even when
        # we leave via S_START_GAME (which doesn't go through _cancel).
        try:
            self.discovery.stop()
        except Exception:
            pass

    def _try_connect(self):
        try:
            port = int(self.port_text)
        except ValueError:
            self.status = "Port must be a number."
            return
        if self.client is not None and self.client.connected:
            self.status = "Already connected. Waiting for host..."
            return
        self.status = f"Connecting to {self.ip_text}:{port}..."
        from game import config
        self.client = NetClient()
        ok = self.client.connect(self.ip_text, port=port,
                                 name=config.player_name(), timeout=4.0)
        if not ok:
            err = (self.client.last_error or "unknown").lower()
            if "timed out" in err or "10060" in err or "no route" in err:
                self.status = (
                    "Couldn't reach the host. They may be on a different network, "
                    "or their firewall is blocking the game. "
                    "(For internet play, both PCs need a VPN like Hamachi/Tailscale.)"
                )
            elif "refused" in err or "10061" in err:
                self.status = (
                    "Connection refused — the host isn't hosting a game on that port."
                )
            else:
                self.status = f"Couldn't connect: {self.client.last_error or 'unknown'}"
            self.client = None

    def update(self):
        if self.client is None:
            return
        for msg in self.client.drain_incoming():
            kind = msg.get("type")
            if kind == protocol.S_WELCOME:
                self.my_player_id = msg.get("player_id")
                self.status = f"Connected. You are Player {self.my_player_id + 1}. Waiting for host..."
            elif kind == protocol.S_REJECT:
                self.status = f"Rejected: {msg.get('reason', '')}"
                self.client.close()
                self.client = None
            elif kind == protocol.S_LOBBY:
                self.lobby_state = msg
            elif kind == protocol.S_START_GAME:
                self.app.switch(
                    "client_play",
                    net_client=self.client,
                    my_player_id=self.my_player_id,
                    grid=msg["grid"],
                    background=msg.get("background_image_path"),
                    floor_grid=msg.get("floor_grid"),
                    wall_style=msg.get("wall_style", "brick"),
                    decor=msg.get("decor", []),
                    background_bytes=msg.get("background_image_bytes"),
                )
                return
            elif kind == protocol.S_GOODBYE:
                self.status = "Host disconnected."
                self.client.close()
                self.client = None
        if self.client is not None and not self.client.connected:
            self.status = f"Disconnected: {self.client.last_error or 'connection closed'}"
            self.client = None

    def _in_lobby(self) -> bool:
        return (
            self.client is not None
            and self.client.connected
            and self.my_player_id is not None
        )

    def draw(self):
        draw_menu_background(self.surface, pygame.time.get_ticks())
        if self._in_lobby():
            self._draw_connected_view()
        else:
            self._draw_pre_connect_view()
        self.back_button.draw(self.surface)
        pygame.display.flip()

    # ---- view: not connected yet ----

    def _draw_pre_connect_view(self):
        title = self.title_font.render("JOIN", True, MENU_TITLE)
        self.surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 60))

        # Discovered games on the LAN
        list_label = self.body_font.render("Games on your network:", True, MENU_TEXT_DIM)
        self.surface.blit(list_label, (SCREEN_WIDTH // 2 - list_label.get_width() // 2, 150))

        self._discovery_row_rects = []
        entries = self.discovery.entries()
        list_x = SCREEN_WIDTH // 2 - 280
        list_w = 560
        row_h = 44
        list_top = 190
        max_rows = 4
        if not entries:
            empty = self.small_font.render(
                "  (scanning... no hosts found yet — start a game on another PC)",
                True, MENU_TEXT_DIM,
            )
            self.surface.blit(empty, (list_x + 10, list_top + 8))
        else:
            mouse_pos = pygame.mouse.get_pos()
            for i, entry in enumerate(entries[:max_rows]):
                rect = pygame.Rect(list_x, list_top + i * (row_h + 4), list_w, row_h)
                self._discovery_row_rects.append((rect, entry))
                hover = rect.collidepoint(mouse_pos)
                bg = (50, 50, 60) if hover else (28, 28, 32)
                pygame.draw.rect(self.surface, bg, rect, border_radius=4)
                pygame.draw.rect(
                    self.surface, GOLD if hover else (80, 80, 90), rect,
                    width=2, border_radius=4,
                )
                name = entry.get("host_name") or "Host"
                map_name = entry.get("map_name") or "—"
                status_txt = "IN GAME" if entry.get("in_game") else "lobby"
                players = entry.get("players", "?")
                max_p = entry.get("max_players", "?")
                line1 = self.body_font.render(
                    f"{name}  ({status_txt})", True, MENU_TEXT,
                )
                line2 = self.small_font.render(
                    f"map: {map_name}   players: {players}/{max_p}   {entry.get('ip','')}:{entry.get('port','')}",
                    True, MENU_TEXT_DIM,
                )
                self.surface.blit(line1, (rect.x + 12, rect.y + 4))
                self.surface.blit(line2, (rect.x + 12, rect.y + 24))

        # Manual IP entry below the list
        manual_label = self.body_font.render("Or type an IP : Port", True, MENU_TEXT_DIM)
        self.surface.blit(manual_label, (SCREEN_WIDTH // 2 - manual_label.get_width() // 2, 420))

        ip_rect = pygame.Rect(SCREEN_WIDTH // 2 - 250, 460, 360, 40)
        port_rect = pygame.Rect(SCREEN_WIDTH // 2 + 130, 460, 120, 40)
        for field, rect, value in (("ip", ip_rect, self.ip_text), ("port", port_rect, self.port_text)):
            border = GOLD if self.editing_field == field else (80, 80, 90)
            pygame.draw.rect(self.surface, (28, 28, 32), rect, border_radius=4)
            pygame.draw.rect(self.surface, border, rect, width=2, border_radius=4)
            text = self.input_font.render(value, True, MENU_TEXT)
            self.surface.blit(text, text.get_rect(midleft=(rect.x + 8, rect.centery)))

        # Status line — wrap long error text across two lines if needed.
        status_color = (220, 80, 80) if (
            "Couldn" in self.status or "Rejected" in self.status
            or "Disconnected" in self.status or "refused" in self.status
        ) else MENU_TEXT
        self._blit_wrapped(
            self.status, self.body_font, status_color,
            center_x=SCREEN_WIDTH // 2, top_y=545, max_width=SCREEN_WIDTH - 60,
        )

        self.connect_button.draw(self.surface)

    # ---- view: already in the lobby ----

    def _draw_connected_view(self):
        # Big green "IN LOBBY" badge so it's blindingly obvious that the
        # connect step succeeded and you're now waiting on the host.
        title = self.title_font.render("IN LOBBY", True, (90, 220, 90))
        self.surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 80))

        subtitle = self.body_font.render(
            f"You are Player {self.my_player_id + 1}.  Waiting for the host to start.",
            True, MENU_TEXT,
        )
        self.surface.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 180))

        # Roster panel
        roster_top = 250
        roster_x = SCREEN_WIDTH // 2 - 200
        roster_w = 400
        roster_h = 240
        pygame.draw.rect(self.surface, (28, 28, 32),
                         (roster_x, roster_top, roster_w, roster_h),
                         border_radius=6)
        pygame.draw.rect(self.surface, (80, 80, 90),
                         (roster_x, roster_top, roster_w, roster_h),
                         width=2, border_radius=6)
        ypos = roster_top + 12
        roster_label = self.body_font.render("Players in lobby:", True, MENU_TEXT_DIM)
        self.surface.blit(roster_label, (roster_x + 16, ypos))
        ypos += 36

        if self.lobby_state is not None:
            host_line = self.body_font.render(
                f"  • {self.lobby_state.get('hosting_name', 'Host')}  (host)",
                True, GOLD,
            )
            self.surface.blit(host_line, (roster_x + 16, ypos))
            ypos += 32
            for p in self.lobby_state.get("players", []):
                marker = "you" if p.get("id") == self.my_player_id else ""
                color = (90, 220, 90) if marker else MENU_TEXT
                line = self.body_font.render(
                    f"  • {p.get('name', 'Player')}  {marker}", True, color,
                )
                self.surface.blit(line, (roster_x + 16, ypos))
                ypos += 32
            map_line = self.small_font.render(
                f"Map: {self.lobby_state.get('map_name', '?')}",
                True, MENU_TEXT_DIM,
            )
            self.surface.blit(map_line, (roster_x + 16, roster_top + roster_h - 28))
        else:
            line = self.body_font.render(
                "  ...waiting for lobby info...", True, MENU_TEXT_DIM,
            )
            self.surface.blit(line, (roster_x + 16, ypos))

        # Hint
        hint = self.small_font.render(
            "Press ESC or click Back to leave the lobby.",
            True, MENU_TEXT_DIM,
        )
        self.surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 540))

    def _blit_wrapped(self, text: str, font, color, *,
                      center_x: int, top_y: int, max_width: int) -> None:
        """Naive word-wrap blitter for status messages that may now be
        sentence-long error hints."""
        words = text.split(" ")
        lines: list[str] = []
        current = ""
        for w in words:
            trial = (current + " " + w).strip()
            if font.size(trial)[0] <= max_width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = w
        if current:
            lines.append(current)
        for i, line in enumerate(lines):
            rendered = font.render(line, True, color)
            self.surface.blit(
                rendered,
                (center_x - rendered.get_width() // 2, top_y + i * (font.get_height() + 2)),
            )
