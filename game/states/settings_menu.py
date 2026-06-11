"""Settings screen: master volume slider, FPS cap, fullscreen toggle.
All persisted to the user config (~/.zombies_game.json)."""
import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, MENU_TITLE, MENU_TEXT, MENU_TEXT_DIM, GOLD
from game import assets, config
from game.states.base import State
from game.ui.menu_widgets import Button, draw_menu_background

FPS_CHOICES = [30, 60, 120, 144, 240]


class SettingsState(State):
    def on_enter(self, **kwargs):
        self.title_font = pygame.font.Font(None, 80)
        self.body_font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 26)
        btn_font = pygame.font.Font(None, 40)

        cx = SCREEN_WIDTH // 2
        self.slider_rect = pygame.Rect(cx - 180, 270, 360, 14)
        self.dragging_volume = False

        self.fps_button = Button("", (cx, 400), btn_font, width=300)
        self.fullscreen_button = Button("", (cx, 480), btn_font, width=300)
        self.back_button = Button("Back", (cx, SCREEN_HEIGHT - 90), btn_font, width=200)
        self._refresh_labels()

    def _refresh_labels(self):
        self.fps_button.set_label(f"FPS cap: {self.app.fps_limit}")
        self.fullscreen_button.set_label(
            f"Fullscreen: {'ON' if self.app.fullscreen else 'OFF'}")

    def _set_volume_from_mouse(self, mx: int):
        frac = (mx - self.slider_rect.x) / self.slider_rect.width
        frac = max(0.0, min(1.0, frac))
        assets.set_master_volume(frac)
        config.save(volume=frac)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.switch("menu")
            return
        if event.type == pygame.MOUSEMOTION:
            for b in (self.fps_button, self.fullscreen_button, self.back_button):
                b.update_hover(event.pos)
            if self.dragging_volume:
                self._set_volume_from_mouse(event.pos[0])
        if event.type == pygame.MOUSEBUTTONUP:
            self.dragging_volume = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.slider_rect.inflate(16, 26).collidepoint(event.pos):
                self.dragging_volume = True
                self._set_volume_from_mouse(event.pos[0])
                return
            if self.fps_button.clicked(event):
                cur = self.app.fps_limit
                idx = FPS_CHOICES.index(cur) if cur in FPS_CHOICES else 1
                self.app.fps_limit = FPS_CHOICES[(idx + 1) % len(FPS_CHOICES)]
                config.save(fps_cap=self.app.fps_limit)
                self._refresh_labels()
                return
            if self.fullscreen_button.clicked(event):
                self.app._toggle_fullscreen()
                self._refresh_labels()
                return
            if self.back_button.clicked(event):
                self.app.switch("menu")
                return

    def draw(self):
        draw_menu_background(self.surface, pygame.time.get_ticks())
        title = self.title_font.render("SETTINGS", True, MENU_TITLE)
        self.surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 90))

        # Volume slider
        vol = assets.master_volume()
        label = self.body_font.render(f"Volume: {int(vol * 100)}%", True, MENU_TEXT)
        self.surface.blit(label, (self.slider_rect.x, self.slider_rect.y - 44))
        pygame.draw.rect(self.surface, (50, 50, 58), self.slider_rect, border_radius=7)
        fill = self.slider_rect.copy()
        fill.width = max(4, int(self.slider_rect.width * vol))
        pygame.draw.rect(self.surface, GOLD, fill, border_radius=7)
        knob_x = self.slider_rect.x + int(self.slider_rect.width * vol)
        pygame.draw.circle(self.surface, (240, 240, 240),
                           (knob_x, self.slider_rect.centery), 12)
        hint = self.small_font.render("(M in-game toggles mute)", True, MENU_TEXT_DIM)
        self.surface.blit(hint, (self.slider_rect.x, self.slider_rect.y + 24))

        self.fps_button.draw(self.surface)
        self.fullscreen_button.draw(self.surface)
        self.back_button.draw(self.surface)
