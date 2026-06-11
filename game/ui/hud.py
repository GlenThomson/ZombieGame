"""In-game HUD: round, kills, points, health bar, current weapon + ammo,
and the interaction prompt for whatever's nearest the player."""
import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, GOLD, MENU_TEXT, MENU_TEXT_DIM


# Display names + colours for active timed power-ups.
EFFECT_BANNERS = {
    "instant_kill":  ("INSTA-KILL",    (255, 60, 60)),
    "double_points": ("DOUBLE POINTS", (80, 255, 80)),
    "fire_sale":     ("FIRE SALE",     (255, 100, 240)),
}


def draw_active_effects(surface, effects: list[tuple[str, int]],
                        local_player_id: int | None = None):
    """Top-centre banner for each active power-up: name + seconds left.
    `effects` is a list of (effect_name, remaining_ms). Per-player effects
    (keys like "death_machine_2") only show on that player's screen."""
    if not effects:
        return
    font = pygame.font.Font(None, 34)
    y = 12
    for name, remaining_ms in sorted(effects):
        if name.startswith("death_machine_"):
            if local_player_id is not None and not name.endswith(f"_{local_player_id}"):
                continue
            label, color = "DEATH MACHINE", (255, 80, 80)
        else:
            label, color = EFFECT_BANNERS.get(name, (name.upper(), (220, 220, 220)))
        secs = max(0, remaining_ms) // 1000
        text = font.render(f"{label}  {secs}s", True, color)
        bg = pygame.Surface((text.get_width() + 20, text.get_height() + 8), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 150))
        cx = SCREEN_WIDTH // 2
        surface.blit(bg, bg.get_rect(midtop=(cx, y)))
        surface.blit(text, text.get_rect(midtop=(cx, y + 4)))
        y += text.get_height() + 14


def draw_scoreboard(surface, rows: list[dict], local_player_id: int | None = None):
    """Hold-Tab scoreboard. `rows`: dicts with name/points/kills/headshots/
    downs (+ id). Sorted by points, local player highlighted."""
    rows = sorted(rows, key=lambda r: -int(r.get("points", 0)))
    font_h = pygame.font.Font(None, 30)
    font_r = pygame.font.Font(None, 32)
    cols = [("PLAYER", 220), ("POINTS", 110), ("KILLS", 90),
            ("HEADSHOTS", 130), ("DOWNS", 90)]
    width = sum(w for _, w in cols) + 40
    height = 70 + 40 * len(rows)
    panel = pygame.Rect(0, 0, width, height)
    panel.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    bg = pygame.Surface(panel.size, pygame.SRCALPHA)
    bg.fill((10, 10, 14, 225))
    surface.blit(bg, panel.topleft)
    pygame.draw.rect(surface, (120, 100, 30), panel, width=2, border_radius=4)

    x = panel.x + 20
    for title, w in cols:
        surface.blit(font_h.render(title, True, (150, 150, 150)), (x, panel.y + 16))
        x += w
    y = panel.y + 56
    for r in rows:
        is_me = local_player_id is not None and r.get("id") == local_player_id
        color = GOLD if is_me else (220, 220, 220)
        x = panel.x + 20
        vals = [str(r.get("name", "?"))[:14], str(r.get("points", 0)),
                str(r.get("kills", 0)), str(r.get("headshots", 0)),
                str(r.get("downs", 0))]
        for (_, w), val in zip(cols, vals):
            surface.blit(font_r.render(val, True, color), (x, y))
            x += w
        y += 40


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
        # Active power-up banner (Double Points / Insta-Kill / Fire Sale).
        now = pygame.time.get_ticks()
        draw_active_effects(surface, [
            (name, expiry - now)
            for name, (expiry, _) in scene.timed_effects.items()
        ], local_player_id=scene.local_player.player_id)

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

        # Weapon name along the top-right — GOLD once Pack-a-Punched.
        name_color = GOLD if getattr(weapon, "is_packed", False) else MENU_TEXT
        rendered = self.weapon_font.render(weapon.name, True, name_color)
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
        max_slots = getattr(player.inventory, "max_slots", 2)
        for i in range(max_slots):
            slot = player.inventory.slots[i]
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
        from game.ui.perk_icons import perk_icon
        x = SCREEN_WIDTH - 220
        y = 130
        for perk in perk_system.owned():
            icon = perk_icon(perk.name, perk.icon_color, height=36)
            surface.blit(icon, (x, y))
            x += icon.get_width() + 8

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
