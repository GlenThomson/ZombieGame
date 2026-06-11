"""Top-level application: pygame init, main loop, state machine.

The game renders at a FIXED logical resolution (settings.SCREEN_WIDTH x
SCREEN_HEIGHT) onto an off-screen canvas; the real OS window is freely
resizable (drag the edges, maximize, F11 fullscreen) and the canvas is
scaled up/down to fit each frame, letterboxed to preserve aspect. Mouse
coordinates are mapped back from window space to logical space so every
state keeps working unchanged.

Each frame: pump events, call active state's update + draw, present."""
import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS_LIMIT, SCREEN_TITLE
from game.utils import quit_application


class App:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.window = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        # Logical canvas — every state draws here via State.surface.
        self.display = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(SCREEN_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.fullscreen = False
        self._windowed_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
        # Presentation transform (recomputed when the window resizes).
        self._scale = 1.0
        self._offset = (0, 0)

        # Route EVERY pygame.mouse.get_pos() call (player aim, hover
        # effects, map maker painting...) through the window->logical
        # mapping so resizing never breaks input.
        real_get_pos = pygame.mouse.get_pos
        def logical_get_pos():
            return self.window_to_logical(real_get_pos())
        pygame.mouse.get_pos = logical_get_pos

        # State registry built lazily to avoid circular imports.
        from game.states.menu import MenuState
        from game.states.map_select import MapSelectState
        from game.states.play import PlayState
        from game.states.game_over import GameOverState
        from game.states.mapmaking import MapMakingState
        from game.states.map_maker_landing import MapMakerLandingState
        from game.states.multiplayer_menu import MultiplayerMenuState
        from game.states.host_lobby import HostLobbyState
        from game.states.join_lobby import JoinLobbyState
        from game.states.host_play import HostPlayState
        from game.states.client_play import ClientPlayState
        self._state_classes = {
            "menu": MenuState,
            "map_select": MapSelectState,
            "play": PlayState,
            "game_over": GameOverState,
            "mapmaking": MapMakingState,
            "map_maker_landing": MapMakerLandingState,
            "multiplayer_menu": MultiplayerMenuState,
            "host_lobby": HostLobbyState,
            "join_lobby": JoinLobbyState,
            "host_play": HostPlayState,
            "client_play": ClientPlayState,
        }
        self.state = None
        self.switch("menu")

    def switch(self, name: str, **kwargs):
        if self.state is not None:
            self.state.on_exit()
        cls = self._state_classes[name]
        self.state = cls(self)
        self.state.on_enter(**kwargs)

    def quit(self):
        quit_application()

    # ---- window <-> logical mapping ----

    def window_to_logical(self, pos) -> tuple[int, int]:
        x = (pos[0] - self._offset[0]) / max(1e-6, self._scale)
        y = (pos[1] - self._offset[1]) / max(1e-6, self._scale)
        return (int(max(0, min(SCREEN_WIDTH - 1, x))),
                int(max(0, min(SCREEN_HEIGHT - 1, y))))

    def _translate_event(self, event):
        """Return an equivalent event with .pos mapped into logical coords."""
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN,
                          pygame.MOUSEBUTTONUP) and hasattr(event, "pos"):
            attrs = dict(event.__dict__)
            attrs["pos"] = self.window_to_logical(event.pos)
            return pygame.event.Event(event.type, attrs)
        return event

    def _toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self._windowed_size = self.window.get_size()
            self.window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.window = pygame.display.set_mode(
                self._windowed_size, pygame.RESIZABLE)

    def _present(self):
        """Scale the logical canvas onto the real window, letterboxed."""
        win_w, win_h = self.window.get_size()
        if (win_w, win_h) == (SCREEN_WIDTH, SCREEN_HEIGHT):
            self._scale, self._offset = 1.0, (0, 0)
            self.window.blit(self.display, (0, 0))
        else:
            self._scale = min(win_w / SCREEN_WIDTH, win_h / SCREEN_HEIGHT)
            out_w = max(1, int(SCREEN_WIDTH * self._scale))
            out_h = max(1, int(SCREEN_HEIGHT * self._scale))
            self._offset = ((win_w - out_w) // 2, (win_h - out_h) // 2)
            self.window.fill((0, 0, 0))
            scaled = pygame.transform.smoothscale(self.display, (out_w, out_h))
            self.window.blit(scaled, self._offset)
        pygame.display.flip()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    self._toggle_fullscreen()
                    continue
                self.state.handle_event(self._translate_event(event))
            self.state.update()
            self.state.draw()
            self._present()
            self.clock.tick(FPS_LIMIT)
