"""State base class. The App owns a single active state and forwards
events / update / draw to it each frame."""


class State:
    def __init__(self, app):
        self.app = app

    @property
    def surface(self):
        return self.app.display

    def on_enter(self, **kwargs):
        """Called once when this state becomes active."""

    def on_exit(self):
        """Called once when this state is replaced by another."""

    def handle_event(self, event):
        pass

    def update(self):
        pass

    def draw(self):
        pass
