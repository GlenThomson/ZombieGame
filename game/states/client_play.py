"""Client-side PlayState: no game logic, only renders the latest snapshot
received from the host and forwards local input back."""
import math
import os
import pygame

from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    TILE_SIZE,
    WHITE,
    GOLD,
    MENU_TEXT,
    MENU_TEXT_DIM,
    PLAYER_TINTS,
    REVIVE_HOLD_MS,
)
from game import assets
from game.camera import Camera
from game.states.base import State
from game.systems.input import LocalInputSource
from game.net import protocol


class ClientPlayState(State):
    """Active when the user joined a host. The host sends snapshots; this
    state only renders + forwards input."""

    def on_enter(self, *, net_client, my_player_id: int, grid, background=None, **kwargs):
        self.net_client = net_client
        self.my_player_id = my_player_id
        self.grid = grid

        self.map_width = len(grid[0]) * TILE_SIZE
        self.map_height = len(grid) * TILE_SIZE
        self.camera = Camera(self.map_width, self.map_height)

        # Background path may be a path that exists on the host but not on
        # this PC. Fall back to assets/images/<basename> the same way the
        # map_loader does for offline loads.
        from game.world.map_loader import _resolve_bg_path
        resolved = _resolve_bg_path(background)
        if resolved:
            self.background_image = pygame.image.load(resolved).convert()
        else:
            self.background_image = None

        # World-mouse provider for our local input source so aim coords are
        # in the same frame the host expects.
        def _world_mouse():
            mx, my = pygame.mouse.get_pos()
            return (mx - self.camera.camera.x, my - self.camera.camera.y)

        self.input_source = LocalInputSource(world_mouse_provider=_world_mouse)

        self.latest_snapshot: dict = _empty_snapshot()
        self.frame_id = 0
        self.connection_lost = False

        # Caches for rendering
        self._zombie_images: dict[str, pygame.Surface] = {}
        self._player_images: dict[int, pygame.Surface] = {}
        self.label_font = pygame.font.Font(None, 36)
        self.weapon_font = pygame.font.Font(None, 28)
        self.points_font = pygame.font.Font(None, 44)
        self.prompt_font = pygame.font.Font(None, 32)
        self.round_text_font = pygame.font.Font(None, 100)
        self.player_label_font = pygame.font.Font(None, 18)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.net_client.close()
                self.app.switch("menu")
                return
            mapping = {
                pygame.K_g: "grenade",
                pygame.K_r: "reload",
                pygame.K_f: "interact",
                pygame.K_1: "switch:0",
                pygame.K_2: "switch:1",
                pygame.K_3: "switch:2",
                pygame.K_4: "switch:3",
            }
            ev_name = mapping.get(event.key)
            if ev_name is not None:
                self.input_source.push_event(ev_name)

    def update(self):
        # Drain incoming server messages
        for msg in self.net_client.drain_incoming():
            kind = msg.get("type")
            if kind == protocol.S_SNAPSHOT:
                self.latest_snapshot = msg
            elif kind == protocol.S_EVENT:
                data = msg.get("data") or {}
                sound_name = data.get("sound")
                if sound_name:
                    try:
                        assets.sound(sound_name).play()
                    except Exception:
                        pass
            elif kind == protocol.S_GAME_OVER:
                self.app.switch(
                    "game_over",
                    final_round=msg.get("final_round", 1),
                    final_kills=msg.get("final_kills", 0),
                )
                return
            elif kind in (protocol.S_GOODBYE, protocol.S_REJECT):
                self.connection_lost = True
                self.app.switch("menu")
                return

        if not self.net_client.connected:
            self.connection_lost = True
            self.app.switch("menu")
            return

        # Send our local input each frame
        snap = self.input_source.snapshot()
        self.frame_id += 1
        wire = snap.to_wire(self.frame_id)
        wire["type"] = protocol.C_INPUT
        self.net_client.send(wire)

        # Update camera to follow my player from latest snapshot
        me = self._my_player()
        if me is not None:
            class _T:
                rect = pygame.Rect(int(me["pos"][0]), int(me["pos"][1]), 1, 1)
            self.camera.update(_T)

    def _my_player(self) -> dict | None:
        for p in self.latest_snapshot.get("players", []):
            if p.get("id") == self.my_player_id:
                return p
        return None

    def draw(self):
        self.surface.fill(WHITE)
        if self.background_image is not None:
            self.surface.blit(self.background_image, self.camera.camera.topleft)

        snap = self.latest_snapshot
        cam_x, cam_y = self.camera.camera.x, self.camera.camera.y

        # Blood under everything
        for b in snap.get("blood", []):
            img = assets.image("bloodSplatter.png").copy()
            img.set_alpha(max(0, b.get("alpha", 200)))
            wx, wy = b["pos"]
            self.surface.blit(img, img.get_rect(center=(wx + cam_x, wy + cam_y)))

        # Interactables
        for it in snap.get("interactables", []):
            self._draw_interactable(it, cam_x, cam_y)

        # Pickups
        for p in snap.get("pickups", []):
            if not p.get("visible", True):
                continue
            self._draw_pickup(p, cam_x, cam_y)

        # Bullets
        for b in snap.get("bullets", []):
            wx, wy = b["pos"]
            pygame.draw.rect(self.surface, GOLD, (wx + cam_x - 1, wy + cam_y - 1, 3, 3))

        # Monkey bombs
        for m in snap.get("monkey_bombs", []):
            wx, wy = m["pos"]
            surf = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.circle(surf, (220, 100, 160), (12, 12), 12)
            pygame.draw.circle(surf, (60, 30, 50), (12, 12), 12, 2)
            self.surface.blit(surf, surf.get_rect(center=(wx + cam_x, wy + cam_y)))

        # Grenades
        for g in snap.get("grenades", []):
            wx, wy = g["pos"]
            if g.get("exploding"):
                # Crude fading orange burst (proper anim lives on host)
                radius = 24 + g.get("frame", 0) * 4
                surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (255, 140, 30, 200 - g.get("frame", 0) * 12),
                                   (radius, radius), radius)
                self.surface.blit(surf, (wx + cam_x - radius, wy + cam_y - radius))
            else:
                grenade_img = assets.image("grenade.png", scale=(20, 20))
                self.surface.blit(grenade_img, grenade_img.get_rect(center=(wx + cam_x, wy + cam_y)))

        # Zombies
        for z in snap.get("zombies", []):
            self._draw_zombie(z, cam_x, cam_y)

        # Players
        for p in snap.get("players", []):
            self._draw_player(p, cam_x, cam_y)

        # Muzzle flashes
        for m in snap.get("muzzle", []):
            mx, my = m["pos"]
            surf = pygame.Surface((18, 18), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 240, 120), (9, 9), 9)
            pygame.draw.circle(surf, (255, 180, 40), (9, 9), 6)
            pygame.draw.circle(surf, (255, 240, 200), (9, 9), 3)
            self.surface.blit(surf, surf.get_rect(center=(mx + cam_x, my + cam_y)))

        # Floating texts
        for f in snap.get("floats", []):
            font = pygame.font.Font(None, 22)
            text = font.render(f.get("text", ""), True, tuple(f.get("color", (255, 215, 0))))
            wx, wy = f["pos"]
            self.surface.blit(text, text.get_rect(center=(wx + cam_x, wy + cam_y)))

        # HUD for my player
        self._draw_hud()

        # Round overlay
        countdown = snap.get("round_text_countdown", 0)
        if countdown > 0:
            text = self.round_text_font.render(
                f"Round {snap.get('round', 1)}", True, (255, 0, 0)
            )
            text.set_alpha(min(255, max(0, countdown)))
            self.surface.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))

        pygame.display.flip()

    def _draw_zombie(self, z: dict, cam_x, cam_y):
        kind = z.get("type", "Zombie")
        img = self._zombie_images.get(kind)
        if img is None:
            from game.entities.zombie_variants import _tinted_sprite, Crawler, Runner, Hellhound
            if kind == "Crawler":
                img = _tinted_sprite(Crawler._TINT, Crawler._SCALE)
            elif kind == "Runner":
                img = _tinted_sprite(Runner._TINT)
            elif kind == "Hellhound":
                img = _tinted_sprite(Hellhound._TINT, Hellhound._SCALE)
            else:
                img = assets.image("zombie.png", scale=(TILE_SIZE, TILE_SIZE))
            self._zombie_images[kind] = img
        rotated = pygame.transform.rotate(img, -z.get("angle", 0))
        rect = rotated.get_rect(center=(z["pos"][0] + cam_x, z["pos"][1] + cam_y))
        self.surface.blit(rotated, rect)

    def _draw_player(self, p: dict, cam_x, cam_y):
        pid = p["id"]
        base = self._player_images.get(pid)
        if base is None:
            base = assets.image("player.png", scale=(TILE_SIZE, TILE_SIZE))
            tint = PLAYER_TINTS[pid % len(PLAYER_TINTS)] if pid > 0 else None
            if tint is not None:
                base = base.copy()
                overlay = pygame.Surface(base.get_size(), pygame.SRCALPHA)
                overlay.fill((*tint, 110))
                base.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            self._player_images[pid] = base
        if p.get("is_down"):
            # Greyscale-ish indicator: tint toward grey + ~half size
            img = pygame.transform.scale(base, (TILE_SIZE * 2 // 3, TILE_SIZE * 2 // 3))
            img.set_alpha(170)
        else:
            img = pygame.transform.rotate(base, p.get("angle", 0))
        rect = img.get_rect(center=(p["pos"][0] + cam_x, p["pos"][1] + cam_y))
        self.surface.blit(img, rect)
        # Player label above
        label_color = PLAYER_TINTS[pid % len(PLAYER_TINTS)] or (220, 220, 220)
        label = self.player_label_font.render(p.get("name", ""), True, label_color)
        self.surface.blit(label, label.get_rect(midbottom=(rect.centerx, rect.top - 4)))
        # Revive bar
        if p.get("is_down"):
            pct = min(1.0, p.get("revive_progress_ms", 0) / REVIVE_HOLD_MS)
            bar = pygame.Rect(0, 0, 36, 5)
            bar.midbottom = (rect.centerx, rect.top - 18)
            pygame.draw.rect(self.surface, (60, 60, 60), bar)
            pygame.draw.rect(self.surface, (0, 220, 0),
                             (bar.x, bar.y, int(bar.w * pct), bar.h))

    def _draw_pickup(self, p: dict, cam_x, cam_y):
        kind = p["kind"]
        png_path = os.path.join("assets", "images", f"{kind}.png")
        if os.path.isfile(png_path):
            img = assets.image(f"{kind}.png", scale=(TILE_SIZE, TILE_SIZE))
        else:
            from game.pickups import effects
            label, color = effects.icon_for(kind) or (kind[:2].upper(), (180, 180, 180))
            img = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            pygame.draw.rect(img, color, img.get_rect())
            pygame.draw.rect(img, (255, 255, 255), img.get_rect(), 2)
            font = pygame.font.Font(None, 22)
            text = font.render(label, True, (255, 255, 255))
            img.blit(text, text.get_rect(center=(TILE_SIZE // 2, TILE_SIZE // 2)))
        wx, wy = p["pos"]
        self.surface.blit(img, (wx + cam_x, wy + cam_y))

    def _draw_interactable(self, it: dict, cam_x, cam_y):
        # Draw as a colored box matching the host's renderer.
        wx, wy = it["pos"]
        rect = pygame.Rect(wx + cam_x, wy + cam_y, TILE_SIZE, TILE_SIZE)
        kind = it["type"]
        if kind == "door":
            pygame.draw.rect(self.surface, (110, 60, 20), rect)
            pygame.draw.rect(self.surface, GOLD, rect, 2)
        elif kind == "wall_buy":
            pygame.draw.rect(self.surface, (40, 40, 50), rect)
            pygame.draw.rect(self.surface, GOLD, rect, 2)
            font = pygame.font.Font(None, 16)
            txt = font.render(str(it.get("weapon", ""))[:6], True, GOLD)
            self.surface.blit(txt, (rect.x + 4, rect.centery - 6))
        elif kind == "window":
            pygame.draw.rect(self.surface, (60, 60, 80), rect)
            pygame.draw.rect(self.surface, (180, 180, 200), rect, 2)
            planks = it.get("planks", 4)
            slot_h = TILE_SIZE / 4
            for i in range(planks):
                pygame.draw.rect(
                    self.surface, (160, 110, 50),
                    (rect.x + 3, rect.y + int(i * slot_h) + 2,
                     TILE_SIZE - 6, int(slot_h) - 2),
                )
        elif kind == "perk_machine":
            color = tuple(it.get("color", (220, 0, 0)))
            pygame.draw.rect(self.surface, (20, 20, 28), rect)
            inner = rect.inflate(-8, -8)
            pygame.draw.rect(self.surface, color, inner)
            pygame.draw.rect(self.surface, (220, 220, 220), rect, 2)
            font = pygame.font.Font(None, 28)
            txt = font.render(it.get("perk", "P")[:1], True, (0, 0, 0))
            self.surface.blit(txt, txt.get_rect(center=rect.center))
        elif kind == "mystery_box":
            state = it.get("state", "idle")
            body = (200, 60, 0) if state == "spinning" else \
                   (255, 215, 0) if state == "ready" else (60, 30, 10)
            pygame.draw.rect(self.surface, body, rect)
            pygame.draw.rect(self.surface, (255, 215, 0), rect, 2)
            font = pygame.font.Font(None, 14)
            txt = font.render(str(it.get("label", "?")), True, (255, 255, 255))
            self.surface.blit(txt, txt.get_rect(center=rect.center))
        elif kind == "pack_a_punch":
            pygame.draw.rect(self.surface, (20, 18, 8), rect)
            pygame.draw.rect(self.surface, (200, 160, 0), rect.inflate(-8, -8))
            pygame.draw.rect(self.surface, (255, 230, 80), rect, 3)
            font = pygame.font.Font(None, 18)
            txt = font.render("PaP", True, (20, 18, 8))
            self.surface.blit(txt, txt.get_rect(center=rect.center))
        elif kind == "trap":
            active = it.get("active", False)
            tkind = it.get("kind", "fire")
            if tkind == "fire":
                base = (180, 60, 0) if active else (60, 30, 10)
                pygame.draw.rect(self.surface, base, rect)
                if active:
                    pygame.draw.polygon(self.surface, (255, 200, 0),
                                        [(rect.x + 8, rect.bottom - 4),
                                         (rect.centerx, rect.y + 4),
                                         (rect.right - 8, rect.bottom - 4)])
            else:
                base = (90, 90, 90) if active else (40, 40, 40)
                pygame.draw.rect(self.surface, base, rect)
                if active:
                    cx, cy = rect.center
                    import math as _m
                    t = pygame.time.get_ticks() / 100.0
                    for offset in (0, _m.pi / 2):
                        a = t + offset
                        x2 = cx + int(_m.cos(a) * (rect.width // 2 - 4))
                        y2 = cy + int(_m.sin(a) * (rect.height // 2 - 4))
                        pygame.draw.line(self.surface, (220, 220, 220), (cx, cy), (x2, y2), 4)
            pygame.draw.rect(self.surface, GOLD, rect, 2)
        elif kind == "power_switch":
            on = it.get("on", False)
            body = (40, 70, 40) if on else (50, 50, 60)
            pygame.draw.rect(self.surface, body, rect)
            pygame.draw.rect(self.surface, (220, 220, 220), rect, 2)
            lever = (255, 220, 80) if on else (180, 180, 180)
            cx = rect.centerx
            if on:
                pygame.draw.line(self.surface, lever, (cx, rect.y + 8), (cx, rect.bottom - 8), 4)
            else:
                pygame.draw.line(self.surface, lever, (cx, rect.y + 8), (cx + 6, rect.bottom - 8), 4)
            font = pygame.font.Font(None, 18)
            self.surface.blit(font.render("PWR", True, (255, 255, 255)),
                              (rect.x + 8, rect.bottom - 18))

    def _draw_hud(self):
        snap = self.latest_snapshot
        me = self._my_player()
        # Round + kills
        rt = self.label_font.render(f"Round: {snap.get('round', 1)}", True, GOLD)
        kt = self.label_font.render(f"Kills: {snap.get('kill_count', 0)}", True, GOLD)
        self.surface.blit(rt, (10, SCREEN_HEIGHT - 110))
        self.surface.blit(kt, (10, SCREEN_HEIGHT - 75))
        if me is None:
            return
        pt = self.points_font.render(f"{me['points']}", True, GOLD)
        self.surface.blit(pt, (10, SCREEN_HEIGHT - 45))

        # Health bar
        bar_w_max = 150
        bar_h = 20
        x = SCREEN_WIDTH - 200
        y = 10
        ratio = max(0.0, me["health"] / max(1, me["max_health"]))
        pygame.draw.rect(self.surface, (255, 0, 0), (x, y, bar_w_max, bar_h))
        pygame.draw.rect(self.surface, (0, 255, 0), (x, y, int(bar_w_max * ratio), bar_h))
        pygame.draw.rect(self.surface, MENU_TEXT, (x, y, bar_w_max, bar_h), 2)

        # Big ammo readout (bottom-right)
        big_font = pygame.font.Font(None, 56)
        small_font = pygame.font.Font(None, 28)
        ammo_surf = big_font.render(str(me["ammo"]), True, GOLD)
        ammo_rect = ammo_surf.get_rect(bottomright=(SCREEN_WIDTH - 30, SCREEN_HEIGHT - 40))
        self.surface.blit(ammo_surf, ammo_rect)
        reserve = me.get("reserve", 0)
        reserve_max = me.get("reserve_max", 0)
        sub = f"/{me['mag']}   {reserve}" if reserve_max > 0 else f"/{me['mag']}"
        sub_surf = small_font.render(sub, True, MENU_TEXT_DIM)
        sub_rect = sub_surf.get_rect(bottomright=(SCREEN_WIDTH - 30, SCREEN_HEIGHT - 12))
        self.surface.blit(sub_surf, sub_rect)

        weapon_text = me.get("weapon") or "-"
        if me.get("is_reloading"):
            weapon_text += "  (reloading)"
        rendered = self.weapon_font.render(weapon_text, True, MENU_TEXT)
        self.surface.blit(rendered, (SCREEN_WIDTH - 220, 40))
        slot_x = SCREEN_WIDTH - 220
        for i, slot in enumerate(me.get("inventory", [])):
            label = "-" if slot is None else slot[:1]
            color = GOLD if i == me.get("inventory_equipped", 0) else MENU_TEXT_DIM
            r = self.weapon_font.render(f"{i+1}:{label}", True, color)
            self.surface.blit(r, (slot_x + i * 50, 70))
        gren = self.weapon_font.render(f"Grenades: {me['grenades']}", True, MENU_TEXT)
        self.surface.blit(gren, (SCREEN_WIDTH - 220, 100))

        # Perks
        ypos = 130
        for name, color in me.get("perks", []):
            r = self.weapon_font.render(name, True, tuple(color))
            self.surface.blit(r, (SCREEN_WIDTH - 220, ypos))
            ypos += 24

        # Interaction prompt
        prompts = snap.get("interaction_prompts", {}) or {}
        prompt = prompts.get(self.my_player_id)
        if prompt:
            r = self.prompt_font.render(prompt, True, GOLD)
            bg = pygame.Surface((r.get_width() + 24, r.get_height() + 12), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 200))
            cx = SCREEN_WIDTH // 2
            self.surface.blit(bg, bg.get_rect(midbottom=(cx, SCREEN_HEIGHT - 130)))
            self.surface.blit(r, r.get_rect(midbottom=(cx, SCREEN_HEIGHT - 138)))


def _empty_snapshot() -> dict:
    return {
        "players": [], "zombies": [], "bullets": [], "pickups": [],
        "grenades": [], "blood": [], "muzzle": [], "floats": [],
        "interactables": [], "interaction_prompts": {},
        "round": 1, "kill_count": 0, "round_text_countdown": 0,
        "damage_flash_alpha": 0, "points_multiplier": 1.0,
    }
