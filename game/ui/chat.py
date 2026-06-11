"""Shared chat widget: a fading message log + an Enter-to-type input line.

Used by the host lobby, join lobby, host play, and client play states so
chat looks and behaves identically everywhere. The owner state is
responsible for transport (sending the committed line over the network and
feeding received lines back in via add())."""
import pygame

MESSAGE_TTL_MS = 9000       # in-game: messages fade out after this
MAX_MESSAGES = 8
MAX_LEN = 120


class ChatBox:
    def __init__(self):
        self.messages: list[tuple[int, str, str]] = []   # (ts_ms, name, text)
        self.active = False          # typing mode
        self.input_text = ""
        self.font = pygame.font.Font(None, 26)

    # ---- data ----

    def add(self, name: str, text: str):
        self.messages.append((pygame.time.get_ticks(), str(name), str(text)))
        if len(self.messages) > MAX_MESSAGES:
            self.messages = self.messages[-MAX_MESSAGES:]

    # ---- input. Returns the committed line when Enter is pressed with
    #      text, else None. Caller checks `chat.active` to know whether to
    #      swallow other game keys. ----

    def handle_key(self, event) -> str | None:
        if not self.active:
            if event.key == pygame.K_RETURN:
                self.active = True
                self.input_text = ""
            return None
        if event.key == pygame.K_ESCAPE:
            self.active = False
            self.input_text = ""
            return None
        if event.key == pygame.K_RETURN:
            line = self.input_text.strip()[:MAX_LEN]
            self.active = False
            self.input_text = ""
            return line or None
        if event.key == pygame.K_BACKSPACE:
            self.input_text = self.input_text[:-1]
            return None
        ch = event.unicode
        if ch and ch.isprintable() and len(self.input_text) < MAX_LEN:
            self.input_text += ch
        return None

    # ---- draw ----

    def draw(self, surface, *, x: int, bottom: int, fade: bool = True):
        """Render log (oldest at top) ending at `bottom`, plus the input
        line when typing. `fade=False` keeps messages forever (lobby)."""
        now = pygame.time.get_ticks()
        y = bottom
        if self.active:
            cursor = "|" if now % 1000 < 500 else ""
            line = self.font.render(f"say: {self.input_text}{cursor}", True, (255, 255, 255))
            bg = pygame.Surface((max(220, line.get_width() + 16), line.get_height() + 8),
                                pygame.SRCALPHA)
            bg.fill((0, 0, 0, 190))
            surface.blit(bg, (x - 6, y - line.get_height() - 4))
            surface.blit(line, (x, y - line.get_height()))
            y -= line.get_height() + 14
        else:
            hint = self.font.render("Enter = chat", True, (130, 130, 130))
            surface.blit(hint, (x, y - hint.get_height()))
            y -= hint.get_height() + 10

        for ts, name, text in reversed(self.messages):
            age = now - ts
            if fade and age > MESSAGE_TTL_MS:
                continue
            alpha = 255
            if fade and age > MESSAGE_TTL_MS - 2000:
                alpha = max(0, int(255 * (MESSAGE_TTL_MS - age) / 2000))
            line = self.font.render(f"{name}: {text}", True, (235, 235, 235))
            bg = pygame.Surface((line.get_width() + 12, line.get_height() + 4),
                                pygame.SRCALPHA)
            bg.fill((0, 0, 0, min(150, alpha)))
            line.set_alpha(alpha)
            surface.blit(bg, (x - 6, y - line.get_height() - 2))
            surface.blit(line, (x, y - line.get_height()))
            y -= line.get_height() + 8
