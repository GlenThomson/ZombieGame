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
from game.states.base import State
from game.ui.menu_widgets import Button, draw_menu_background


class JoinLobbyState(State):
    def on_enter(self, **kwargs):
        self.title_font = pygame.font.Font(None, 80)
        self.body_font = pygame.font.Font(None, 32)
        self.btn_font = pygame.font.Font(None, 36)
        self.input_font = pygame.font.Font(None, 40)

        self.ip_text = "127.0.0.1"
        self.port_text = str(DEFAULT_HOST_PORT)
        self.editing_field = "ip"  # "ip" | "port"
        self.status: str = "Enter the host's IP, then click Connect."
        self.connect_button = Button(
            "Connect", (SCREEN_WIDTH // 2, 440), self.btn_font, width=200,
        )
        self.back_button = Button(
            "Back", (140, SCREEN_HEIGHT - 60), self.btn_font, width=160, height=44,
        )

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
            # Click on either input field to edit it.
            ip_rect = pygame.Rect(SCREEN_WIDTH // 2 - 250, 270, 360, 40)
            port_rect = pygame.Rect(SCREEN_WIDTH // 2 + 130, 270, 120, 40)
            if ip_rect.collidepoint(event.pos):
                self.editing_field = "ip"
            elif port_rect.collidepoint(event.pos):
                self.editing_field = "port"

    def _cancel(self):
        if self.client is not None:
            self.client.close()
        self.app.switch("multiplayer_menu")

    def _try_connect(self):
        try:
            port = int(self.port_text)
        except ValueError:
            self.status = "Port must be a number."
            return
        if self.client is not None and self.client.connected:
            self.status = "Already connected. Waiting for host..."
            return
        self.client = NetClient()
        ok = self.client.connect(self.ip_text, port=port, name="Player", timeout=4.0)
        if not ok:
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

    def draw(self):
        draw_menu_background(self.surface, pygame.time.get_ticks())
        title = self.title_font.render("JOIN", True, MENU_TITLE)
        self.surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 80))

        # Host IP + Port input fields.
        label = self.body_font.render("Host IP : Port", True, MENU_TEXT_DIM)
        self.surface.blit(label, (SCREEN_WIDTH // 2 - label.get_width() // 2, 220))

        ip_rect = pygame.Rect(SCREEN_WIDTH // 2 - 250, 270, 360, 40)
        port_rect = pygame.Rect(SCREEN_WIDTH // 2 + 130, 270, 120, 40)
        for field, rect, value in (("ip", ip_rect, self.ip_text), ("port", port_rect, self.port_text)):
            border = GOLD if self.editing_field == field else (80, 80, 90)
            pygame.draw.rect(self.surface, (28, 28, 32), rect, border_radius=4)
            pygame.draw.rect(self.surface, border, rect, width=2, border_radius=4)
            text = self.input_font.render(value, True, MENU_TEXT)
            self.surface.blit(text, text.get_rect(midleft=(rect.x + 8, rect.centery)))

        # Status line.
        status_color = MENU_TEXT if "Couldn" not in self.status else (220, 80, 80)
        status = self.body_font.render(self.status, True, status_color)
        self.surface.blit(status, (SCREEN_WIDTH // 2 - status.get_width() // 2, 360))

        # Lobby roster (if we got one)
        if self.lobby_state is not None:
            ypos = 510
            roster_label = self.body_font.render("In lobby:", True, MENU_TEXT_DIM)
            self.surface.blit(roster_label, (SCREEN_WIDTH // 2 - 100, ypos))
            ypos += 30
            host_line = self.body_font.render(f"- {self.lobby_state.get('hosting_name', 'Host')} (host)", True, MENU_TEXT)
            self.surface.blit(host_line, (SCREEN_WIDTH // 2 - 100, ypos))
            ypos += 30
            for p in self.lobby_state.get("players", []):
                line = self.body_font.render(f"- {p.get('name', 'Player')}", True, MENU_TEXT)
                self.surface.blit(line, (SCREEN_WIDTH // 2 - 100, ypos))
                ypos += 30

        self.connect_button.draw(self.surface)
        self.back_button.draw(self.surface)
        pygame.display.flip()
