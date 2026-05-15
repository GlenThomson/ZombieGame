"""Top-level application: pygame init, main loop, state machine.

Each frame: pump events, call active state's update + draw, tick the clock."""
import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS_LIMIT, SCREEN_TITLE
from game.utils import quit_application


class App:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.display = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(SCREEN_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

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

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                self.state.handle_event(event)
            self.state.update()
            self.state.draw()
            self.clock.tick(FPS_LIMIT)
