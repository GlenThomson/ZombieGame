"""Shown when the player(s) all die."""
import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, MENU_TEXT, MENU_TEXT_DIM, GOLD
from game.states.base import State
from game.ui.menu_widgets import Button, draw_menu_background


class GameOverState(State):
    def on_enter(self, *, final_round: int = 1, final_kills: int = 0,
                 player_stats: list | None = None, **kwargs):
        title_font = pygame.font.Font(None, 110)
        sub_font = pygame.font.Font(None, 36)
        body_font = pygame.font.Font(None, 28)
        button_font = pygame.font.Font(None, 40)

        self.title_surf = title_font.render("YOU DIED", True, (200, 30, 30))
        self.title_pos = (SCREEN_WIDTH // 2 - self.title_surf.get_width() // 2, 100)

        self.sub_surfs = [
            sub_font.render(f"Survived to round {final_round}", True, MENU_TEXT),
            sub_font.render(f"Total team kills: {final_kills}", True, MENU_TEXT_DIM),
        ]

        # Scoreboard rows
        self.body_font = body_font
        self.player_stats = player_stats or []

        cx = SCREEN_WIDTH // 2
        self.retry_button = Button("Back to Menu", (cx, SCREEN_HEIGHT - 80), button_font)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.retry_button.update_hover(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and self.retry_button.clicked(event):
            self.app.switch("menu")
        elif event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
            self.app.switch("menu")

    def draw(self):
        draw_menu_background(self.surface, pygame.time.get_ticks())
        self.surface.blit(self.title_surf, self.title_pos)
        y = 230
        for surf in self.sub_surfs:
            self.surface.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, y))
            y += 42

        # Per-player scoreboard
        y += 20
        if self.player_stats:
            header = self.body_font.render(
                f"{'Player':<14}{'Kills':>8}{'Heads':>8}{'Spent':>10}", True, GOLD,
            )
            self.surface.blit(header, header.get_rect(midtop=(SCREEN_WIDTH // 2, y)))
            y += 36
            for stats in self.player_stats:
                name = stats["name"][:13]
                row = (
                    f"{name:<14}{stats['kills']:>8}{stats['headshots']:>8}"
                    f"{stats['points_spent']:>10}"
                )
                row_surf = self.body_font.render(row, True, MENU_TEXT)
                self.surface.blit(row_surf, row_surf.get_rect(midtop=(SCREEN_WIDTH // 2, y)))
                y += 30
                if stats.get("perks"):
                    perks_surf = self.body_font.render(
                        "  perks: " + ", ".join(stats["perks"]),
                        True, MENU_TEXT_DIM,
                    )
                    self.surface.blit(perks_surf, perks_surf.get_rect(midtop=(SCREEN_WIDTH // 2, y)))
                    y += 30

        self.retry_button.draw(self.surface)
        pygame.display.flip()
