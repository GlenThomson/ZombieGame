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
        self.ammo_big_font = pygame.font.Font(None, 56)
        self.ammo_reserve_font = pygame.font.Font(None, 28)

    def draw_minimap(self, surface, scene):
        """Top-right corner mini-map. Walls dark, machines coloured, players
        gold, zombies red. Whole map fits in a 160x140 square."""
        from game.world.tile import TileType
        rows = len(scene.grid)
        cols = len(scene.grid[0])
        if rows == 0 or cols == 0:
            return
        max_w, max_h = 180, 140
        scale = min(max_w / cols, max_h / rows)
        if scale < 1:
            scale = max(1, scale)
        tx = int(cols * scale)
        ty = int(rows * scale)
        x0 = SCREEN_WIDTH - tx - 10
        y0 = SCREEN_HEIGHT - ty - 200
        # Background
        bg = pygame.Surface((tx + 8, ty + 8), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 160))
        surface.blit(bg, (x0 - 4, y0 - 4))
        # Tile colors
        TILE_COLORS = {
            int(TileType.WALL):         (60, 60, 60),
            int(TileType.DOOR_CLOSED):  (110, 60, 20),
            int(TileType.DOOR_OPEN):    (35, 25, 15),
            int(TileType.WINDOW):       (140, 100, 50),
            int(TileType.WALL_BUY):     (120, 120, 80),
            int(TileType.PERK_MACHINE): (200, 60, 60),
            int(TileType.MYSTERY_BOX):  (255, 215, 0),
            int(TileType.PACK_A_PUNCH): (255, 230, 80),
            int(TileType.POWER_SWITCH): (180, 220, 60),
            int(TileType.TRAP_FIRE):    (255, 90, 30),
            int(TileType.TRAP_FLOGGER): (180, 180, 180),
            int(TileType.ZOMBIE_SPAWN): (140, 0, 0),
        }
        for y, row in enumerate(scene.grid):
            for x, t in enumerate(row):
                color = TILE_COLORS.get(int(t))
                if color is None:
                    continue
                pygame.draw.rect(
                    surface, color,
                    (x0 + int(x * scale), y0 + int(y * scale),
                     max(1, int(scale)), max(1, int(scale))),
                )
        # Players + zombies on top
        from settings import TILE_SIZE
        for p in scene.players:
            px = x0 + int((p.pos.x / TILE_SIZE) * scale)
            py = y0 + int((p.pos.y / TILE_SIZE) * scale)
            pygame.draw.circle(surface, GOLD if p is scene.local_player else (60, 160, 255),
                               (px, py), 3)
        for z in scene.zombies:
            zx = x0 + int((z.pos.x / TILE_SIZE) * scale)
            zy = y0 + int((z.pos.y / TILE_SIZE) * scale)
            pygame.draw.circle(surface, (255, 50, 50), (zx, zy), 2)

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
        self.draw_minimap(surface, scene)

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
        # Big ammo readout near bottom-right (CoD-style).
        ammo_text = f"{weapon.current_ammo}"
        ammo_surf = self.ammo_big_font.render(ammo_text, True, GOLD)
        ammo_rect = ammo_surf.get_rect(bottomright=(SCREEN_WIDTH - 30, SCREEN_HEIGHT - 40))
        surface.blit(ammo_surf, ammo_rect)
        # Magazine size + reserve underneath in smaller text.
        if weapon.reserve_max > 0:
            sub = f"/{weapon.magazine_size}   {weapon.reserve_ammo}"
        else:
            sub = f"/{weapon.magazine_size}"
        sub_surf = self.ammo_reserve_font.render(sub, True, MENU_TEXT_DIM)
        sub_rect = sub_surf.get_rect(bottomright=(SCREEN_WIDTH - 30, SCREEN_HEIGHT - 12))
        surface.blit(sub_surf, sub_rect)

        # Weapon name along the top-right.
        rendered = self.weapon_font.render(weapon.name, True, MENU_TEXT)
        surface.blit(rendered, (SCREEN_WIDTH - 220, 40))

        # Reload progress bar — visible only when reloading.
        if weapon.is_reloading:
            now = pygame.time.get_ticks()
            elapsed = now - weapon.reload_started_at
            total = max(1, weapon.reload_time * 1000)
            progress = max(0.0, min(1.0, elapsed / total))
            bw = 220
            bh = 8
            bx = SCREEN_WIDTH - 30 - bw
            by = SCREEN_HEIGHT - 90
            pygame.draw.rect(surface, (40, 40, 40), (bx, by, bw, bh))
            pygame.draw.rect(surface, GOLD, (bx, by, int(bw * progress), bh))
            pygame.draw.rect(surface, MENU_TEXT, (bx, by, bw, bh), 1)

        slot_x = SCREEN_WIDTH - 220
        for i, slot in enumerate(player.inventory.slots):
            label = "-" if slot is None else slot.name[:1]
            color = GOLD if i == player.inventory.equipped_index else MENU_TEXT_DIM
            rendered = self.weapon_font.render(f"{i+1}:{label}", True, color)
            surface.blit(rendered, (slot_x + i * 50, 70))

    def _draw_grenade_count(self, surface, player):
        rendered = self.weapon_font.render(f"Grenades: {player.grenade_count}", True, MENU_TEXT)
        surface.blit(rendered, (SCREEN_WIDTH - 220, 100))
        if player.monkey_bomb_count > 0:
            r = self.weapon_font.render(
                f"Monkey: {player.monkey_bomb_count}", True, (220, 100, 160),
            )
            surface.blit(r, (SCREEN_WIDTH - 220, 124))

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
