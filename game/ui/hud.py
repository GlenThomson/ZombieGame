"""In-game HUD: round, kills, points, health bar, current weapon + ammo,
and the interaction prompt for whatever's nearest the player."""
import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, GOLD, MENU_TEXT, MENU_TEXT_DIM


class HUD:
    def __init__(self):
        self.label_font = pygame.font.Font(None, 36)
        self.weapon_font = pygame.font.Font(None, 28)
        self.points_font = pygame.font.Font(None, 44)
        self.prompt_font = pygame.font.Font(None, 32)

    def draw(self, surface, scene):
        # Round + kills (bottom-left)
        round_text = self.label_font.render(
            f"Round: {scene.round_manager.current_round}", True, GOLD
        )
        kills_text = self.label_font.render(f"Kills: {scene.kill_count}", True, GOLD)
        surface.blit(round_text, (10, SCREEN_HEIGHT - 110))
        surface.blit(kills_text, (10, SCREEN_HEIGHT - 75))

        points_text = self.points_font.render(
            f"{scene.player.points}", True, GOLD
        )
        surface.blit(points_text, (10, SCREEN_HEIGHT - 45))

        self._draw_health_bar(surface, scene.player)
        self._draw_weapon_panel(surface, scene.player)
        self._draw_grenade_count(surface, scene.player)
        self._draw_perks(surface, scene.player)
        self._draw_interaction_prompt(surface, scene)

    def _draw_health_bar(self, surface, player):
        bar_w_max = 150
        bar_h = 20
        x = SCREEN_WIDTH - 200
        y = 10
        max_hp = max(1, player.max_health)
        ratio = max(0.0, player.health / max_hp)
        pygame.draw.rect(surface, (255, 0, 0), (x, y, bar_w_max, bar_h))
        pygame.draw.rect(surface, (0, 255, 0), (x, y, int(bar_w_max * ratio), bar_h))
        pygame.draw.rect(surface, MENU_TEXT, (x, y, bar_w_max, bar_h), 2)

    def _draw_weapon_panel(self, surface, player):
        weapon = player.weapon
        if weapon is None:
            return
        text = f"{weapon.name}  {weapon.current_ammo}/{weapon.magazine_size}"
        if weapon.is_reloading:
            text += "  (reloading)"
        rendered = self.weapon_font.render(text, True, MENU_TEXT)
        surface.blit(rendered, (SCREEN_WIDTH - 220, 40))

        slot_x = SCREEN_WIDTH - 220
        for i, slot in enumerate(player.inventory.slots):
            label = "-" if slot is None else slot.name[:1]
            color = GOLD if i == player.inventory.equipped_index else MENU_TEXT_DIM
            rendered = self.weapon_font.render(f"{i+1}:{label}", True, color)
            surface.blit(rendered, (slot_x + i * 50, 70))

    def _draw_grenade_count(self, surface, player):
        rendered = self.weapon_font.render(f"Grenades: {player.grenade_count}", True, MENU_TEXT)
        surface.blit(rendered, (SCREEN_WIDTH - 220, 100))

    def _draw_perks(self, surface, player):
        perk_system = getattr(player.scene, "perk_system", None)
        if perk_system is None:
            return
        x = SCREEN_WIDTH - 220
        y = 130
        for perk in perk_system.owned():
            text = self.weapon_font.render(perk.name, True, perk.icon_color)
            surface.blit(text, (x, y))
            y += 24

    def _draw_interaction_prompt(self, surface, scene):
        prompt = getattr(scene, "interaction_prompt", None)
        if not prompt:
            return
        rendered = self.prompt_font.render(prompt, True, GOLD)
        bg = pygame.Surface((rendered.get_width() + 24, rendered.get_height() + 12), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 200))
        cx = SCREEN_WIDTH // 2
        bg_rect = bg.get_rect(midbottom=(cx, SCREEN_HEIGHT - 130))
        surface.blit(bg, bg_rect)
        surface.blit(rendered, rendered.get_rect(midbottom=(cx, SCREEN_HEIGHT - 138)))
