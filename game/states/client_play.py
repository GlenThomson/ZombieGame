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

    def on_enter(self, *, net_client, my_player_id: int, grid, background=None,
                 floor_grid: list | None = None, wall_style: str = "brick",
                 decor: list | None = None, background_bytes: bytes | None = None,
                 **kwargs):
        self.net_client = net_client
        self.my_player_id = my_player_id
        self.grid = grid
        self.wall_style = wall_style
        self.decor = decor or []
        from game.world.tile import FloorType
        self.floor_grid = floor_grid or [
            [int(FloorType.CONCRETE) for _ in row] for row in grid
        ]

        self.map_width = len(grid[0]) * TILE_SIZE
        self.map_height = len(grid) * TILE_SIZE
        self.camera = Camera(self.map_width, self.map_height)

        # Preferred path: host bundled the raw bg bytes in S_START_GAME, so
        # we always render the same view regardless of whether this PC has
        # the matching asset file. Fallback: resolve a local file path the
        # same way map_loader does for offline play.
        self.background_image = None
        if background_bytes:
            try:
                import io
                self.background_image = pygame.image.load(
                    io.BytesIO(background_bytes)
                ).convert()
            except (pygame.error, Exception):
                self.background_image = None
        if self.background_image is None:
            from game.world.map_loader import _resolve_bg_path
            resolved = _resolve_bg_path(background)
            if resolved:
                try:
                    self.background_image = pygame.image.load(resolved).convert()
                except pygame.error:
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
                # Double-tap ESC to leave — a single stray ESC shouldn't
                # yank you out of a co-op game.
                now = pygame.time.get_ticks()
                if now < getattr(self, "_leave_confirm_until", 0):
                    self.net_client.close()
                    self.app.switch("menu")
                else:
                    self._leave_confirm_until = now + 2500
                return
            if event.key == pygame.K_m:
                from game import assets, config
                if assets.master_volume() > 0:
                    assets.set_master_volume(0.0)
                    config.save(volume=0.0)
                else:
                    assets.set_master_volume(1.0)
                    config.save(volume=1.0)
                return
            mapping = {
                pygame.K_g: "grenade",
                pygame.K_t: "monkey",
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
            return
        if event.type == pygame.MOUSEWHEEL and event.y != 0:
            self.input_source.push_event(f"cycle:{1 if event.y > 0 else -1}")

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
                    player_stats=msg.get("player_stats") or [],
                    map_name=msg.get("map_name", ""),
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
        snap = self.latest_snapshot
        cam_x, cam_y = self.camera.camera.x, self.camera.camera.y

        # Floor tiles + walls (static — derived from grid + floor_grid + wall_style).
        self._draw_floor_grid(cam_x, cam_y)
        self._draw_walls(cam_x, cam_y)
        if self.background_image is not None and not any(any(r) for r in self.floor_grid):
            self.surface.blit(self.background_image, self.camera.camera.topleft)

        # Decor (sorted by bottom-y so taller items render correctly behind shorter)
        self._draw_decor(cam_x, cam_y)

        # Blood under everything
        for b in snap.get("blood", []):
            img = assets.image("bloodSplatter.png").copy()
            img.set_alpha(max(0, b.get("alpha", 200)))
            wx, wy = b["pos"]
            self.surface.blit(img, img.get_rect(center=(wx + cam_x, wy + cam_y)))

        # Mystery-box halo first so machines render on top of it.
        import math as _math
        glow_t = pygame.time.get_ticks() / 300.0
        for it in snap.get("interactables", []):
            if it.get("type") != "mystery_box":
                continue
            wx, wy = it["pos"]
            r = int(34 + 6 * _math.sin(glow_t))
            halo = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(halo, (255, 215, 0, 70), (r, r), r)
            pygame.draw.circle(halo, (255, 215, 0, 110), (r, r), int(r * 0.6))
            self.surface.blit(halo, halo.get_rect(
                center=(wx + cam_x + TILE_SIZE // 2, wy + cam_y + TILE_SIZE // 2)))

        # Interactables
        for it in snap.get("interactables", []):
            self._draw_interactable(it, cam_x, cam_y)

        # Pickups
        for p in snap.get("pickups", []):
            if not p.get("visible", True):
                continue
            self._draw_pickup(p, cam_x, cam_y)

        # Bullets — colour + size shifts when Pack-a-Punched.
        for b in snap.get("bullets", []):
            wx, wy = b["pos"]
            kind = b.get("kind", "normal")
            pap = bool(b.get("pap", False))
            if kind == "laser":
                color = (255, 100, 255) if pap else (120, 255, 160)
                w = 16 if pap else 14
                h = 5 if pap else 4
                base = pygame.Surface((w, h), pygame.SRCALPHA)
                pygame.draw.rect(base, color, base.get_rect(), border_radius=2)
                pygame.draw.line(base, (255, 255, 255), (1, h // 2), (w - 2, h // 2), 1)
                rotated = pygame.transform.rotate(base, b.get("angle", 0.0))
                rect = rotated.get_rect(center=(wx + cam_x, wy + cam_y))
                self.surface.blit(rotated, rect)
            elif kind == "blast" and b.get("r", 0) > 0:
                from game.entities.bullet import _blast_ring
                ring = _blast_ring(int(b["r"]), min(1.0, float(b.get("fade", 0))))
                self.surface.blit(ring, ring.get_rect(center=(wx + cam_x, wy + cam_y)))
            else:
                size = 4 if pap else 3
                if kind == "chain":
                    color = (200, 240, 255) if pap else (140, 200, 255)
                elif kind == "blast":
                    color = (255, 240, 80) if pap else (255, 140, 0)
                else:
                    color = (255, 80, 255) if pap else GOLD
                pygame.draw.rect(self.surface, color, (wx + cam_x - size // 2, wy + cam_y - size // 2, size, size))

        # Monkey bombs — same animated cymbal toy the host renders.
        from game.entities.grenade import explosion_frames as _expl_frames
        now_ms = pygame.time.get_ticks()
        for m in snap.get("monkey_bombs", []):
            wx, wy = m["pos"]
            if m.get("exploding"):
                frames = _expl_frames()
                idx = min(int(m.get("frame", 0)), len(frames) - 1)
                img = frames[idx]
            else:
                name = f"monkey_bomb_{(now_ms // 160) % 2}.png"
                if os.path.isfile(os.path.join("assets", "images", name)):
                    img = assets.image(name, scale=(30, 30))
                    wig = 10 if (now_ms // 160) % 2 else -10
                    img = pygame.transform.rotate(img, wig)
                    if m.get("flash") and (now_ms // 90) % 2 == 0:
                        img = img.copy()
                        img.fill((120, 120, 120), special_flags=pygame.BLEND_RGB_ADD)
                else:
                    img = pygame.Surface((24, 24), pygame.SRCALPHA)
                    pygame.draw.circle(img, (220, 100, 160), (12, 12), 12)
            self.surface.blit(img, img.get_rect(center=(wx + cam_x, wy + cam_y)))

        # Grenades — height-scaled while airborne, real explosion frames.
        for g in snap.get("grenades", []):
            wx, wy = g["pos"]
            if g.get("exploding"):
                frames = _expl_frames()
                idx = min(int(g.get("frame", 0)), len(frames) - 1)
                img = frames[idx]
            else:
                size = max(8, int(20 * float(g.get("scale", 1.0))))
                img = assets.image("grenade.png", scale=(size, size))
            self.surface.blit(img, img.get_rect(center=(wx + cam_x, wy + cam_y)))

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

        # Active power-up banner (same renderer the host uses).
        from game.ui.hud import draw_active_effects
        draw_active_effects(self.surface, [
            (e.get("name", ""), int(e.get("remaining_ms", 0)))
            for e in snap.get("active_effects", [])
        ], local_player_id=self.my_player_id)

        # Hit markers at the cursor (data ships in my player snapshot row).
        me = self._my_player()
        if me is not None:
            if me.get("kill_ago", 9999) < 250:
                self._draw_hit_marker((255, 60, 60), 9)
            elif me.get("hit_ago", 9999) < 150:
                self._draw_hit_marker((240, 240, 240), 7)

        # Leave-confirm banner (double-tap ESC).
        if pygame.time.get_ticks() < getattr(self, "_leave_confirm_until", 0):
            font = pygame.font.Font(None, 36)
            text = font.render("Press ESC again to leave the game", True, (255, 90, 90))
            bg = pygame.Surface((text.get_width() + 24, text.get_height() + 12), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 200))
            self.surface.blit(bg, bg.get_rect(center=(SCREEN_WIDTH // 2, 140)))
            self.surface.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, 140)))

        # Hold Tab: scoreboard from the latest snapshot.
        if pygame.key.get_pressed()[pygame.K_TAB]:
            from game.ui.hud import draw_scoreboard
            draw_scoreboard(self.surface, [
                {"id": p.get("id"), "name": p.get("name", "?"),
                 "points": p.get("points", 0), "kills": p.get("kills", 0),
                 "headshots": p.get("headshots", 0), "downs": p.get("downs", 0)}
                for p in snap.get("players", [])
            ], local_player_id=self.my_player_id)

        # Round overlay
        countdown = snap.get("round_text_countdown", 0)
        if countdown > 0:
            text = self.round_text_font.render(
                f"Round {snap.get('round', 1)}", True, (255, 0, 0)
            )
            text.set_alpha(min(255, max(0, countdown)))
            self.surface.blit(text, text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)))


    def _draw_hit_marker(self, color, size: int):
        mx, my = pygame.mouse.get_pos()
        for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            pygame.draw.line(self.surface, color,
                             (mx + dx * 4, my + dy * 4),
                             (mx + dx * size, my + dy * size), 3)

    def _draw_zombie(self, z: dict, cam_x, cam_y):
        kind = z.get("type", "Zombie")
        img = self._zombie_images.get(kind)
        if img is None:
            from game.entities.zombie_variants import (
                _tinted_sprite, _hellhound_sprite, Crawler, Runner, Hellhound,
            )
            if kind == "Crawler":
                img = _tinted_sprite(Crawler._TINT, Crawler._SCALE)
            elif kind == "Runner":
                img = _tinted_sprite(Runner._TINT)
            elif kind == "Hellhound":
                img = _hellhound_sprite(Hellhound._SCALE)
            else:
                img = assets.image("zombie.png", scale=(TILE_SIZE, TILE_SIZE))
            self._zombie_images[kind] = img
        rotated = pygame.transform.rotate(img, -z.get("angle", 0))
        rise = float(z.get("rise", 1.0))
        if rise < 1.0:
            rotated = rotated.copy()
            rotated.set_alpha(int(40 + 215 * rise))
        rect = rotated.get_rect(center=(z["pos"][0] + cam_x, z["pos"][1] + cam_y))
        self.surface.blit(rotated, rect)

    def _draw_player(self, p: dict, cam_x, cam_y):
        pid = p["id"]
        base = self._player_images.get(pid)
        if base is None:
            base = assets.image("player.png", scale=(TILE_SIZE, TILE_SIZE))
            tint = PLAYER_TINTS[pid % len(PLAYER_TINTS)] if pid > 0 else None
            if tint is not None:
                # Match Player.__init__: solid-coloured tint, near-full alpha.
                base = base.copy()
                overlay = pygame.Surface(base.get_size(), pygame.SRCALPHA)
                overlay.fill((*tint, 230))
                base.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            self._player_images[pid] = base
        if p.get("is_dead"):
            # Dead = a flat corpse: half-size, rotated to their last facing
            # and dimmed further so it visibly reads as a body, not a player.
            img = pygame.transform.scale(base, (TILE_SIZE // 2, TILE_SIZE // 2))
            img = pygame.transform.rotate(img, p.get("angle", 0))
            img.set_alpha(110)
        elif p.get("is_down"):
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

    def _draw_floor_grid(self, cam_x, cam_y):
        from game.world.tile import FLOOR_SPRITES
        rows = len(self.floor_grid)
        cols = len(self.floor_grid[0]) if rows else 0
        x0 = max(0, int(-cam_x) // TILE_SIZE)
        y0 = max(0, int(-cam_y) // TILE_SIZE)
        x1 = min(cols, x0 + SCREEN_WIDTH // TILE_SIZE + 2)
        y1 = min(rows, y0 + SCREEN_HEIGHT // TILE_SIZE + 2)
        for y in range(y0, y1):
            for x in range(x0, x1):
                png = FLOOR_SPRITES.get(int(self.floor_grid[y][x]))
                if png is None:
                    continue
                self.surface.blit(
                    assets.image(os.path.join("tiles", png)),
                    (x * TILE_SIZE + cam_x, y * TILE_SIZE + cam_y),
                )

    def _draw_decor(self, cam_x, cam_y):
        from game.world.tile import DECOR_SPRITES
        if not self.decor:
            return
        # Build list of (bottom_y, image, topleft) so we can sort.
        items = []
        for entry in self.decor:
            kind = entry.get("kind")
            pos = entry.get("pos")
            if not (kind and pos):
                continue
            png = DECOR_SPRITES.get(kind)
            if png is None:
                continue
            full = os.path.join("assets", "images", "decor", png)
            if not os.path.isfile(full):
                continue
            img = assets.image(os.path.join("decor", png))
            x_tile, y_tile = pos
            rect = img.get_rect(
                bottomleft=(x_tile * TILE_SIZE, (y_tile + 1) * TILE_SIZE),
            )
            items.append((rect.bottom, img, rect))
        for _b, img, rect in sorted(items, key=lambda t: t[0]):
            self.surface.blit(img, (rect.x + cam_x, rect.y + cam_y))

    def _draw_walls(self, cam_x, cam_y):
        from game.world.tile import TileType, WALL_STYLES
        wall_png = WALL_STYLES.get(self.wall_style, "wall_brick.png")
        path = os.path.join("assets", "images", "tiles", wall_png)
        if not os.path.isfile(path):
            return
        wall_img = assets.image(os.path.join("tiles", wall_png))
        rows = len(self.grid)
        cols = len(self.grid[0]) if rows else 0
        x0 = max(0, int(-cam_x) // TILE_SIZE)
        y0 = max(0, int(-cam_y) // TILE_SIZE)
        x1 = min(cols, x0 + SCREEN_WIDTH // TILE_SIZE + 2)
        y1 = min(rows, y0 + SCREEN_HEIGHT // TILE_SIZE + 2)
        for y in range(y0, y1):
            for x in range(x0, x1):
                if int(self.grid[y][x]) == int(TileType.WALL):
                    self.surface.blit(
                        wall_img, (x * TILE_SIZE + cam_x, y * TILE_SIZE + cam_y),
                    )

    def _sprite_for(self, kind: str, it: dict) -> str | None:
        """Map an interactable snapshot dict to its asset filename."""
        if kind == "door":
            return "door_closed.png"
        if kind == "wall_buy":
            return "wall_buy_generic.png"
        if kind == "window":
            planks = max(0, min(4, int(it.get("planks", 4))))
            return f"window_{planks}.png"
        if kind == "perk_machine":
            slug = str(it.get("perk", "")).replace(" ", "_").lower()
            return f"perk_{slug}.png"
        if kind == "mystery_box":
            return f"mystery_box_{it.get('state', 'idle')}.png"
        if kind == "pack_a_punch":
            return "pack_a_punch.png"
        if kind == "power_switch":
            return "power_switch_on.png" if it.get("on") else "power_switch_off.png"
        if kind == "trap":
            return f"trap_{it.get('kind', 'fire')}_{'on' if it.get('active') else 'off'}.png"
        return None

    def _draw_interactable(self, it: dict, cam_x, cam_y):
        wx, wy = it["pos"]
        rect = pygame.Rect(wx + cam_x, wy + cam_y, TILE_SIZE, TILE_SIZE)
        kind = it["type"]

        # Wall buys use the shared icon+plaque builder so the name is
        # readable on the client exactly like on the host.
        if kind == "wall_buy":
            from game.entities.wall_buy import build_wall_buy_image
            weapon = str(it.get("weapon", ""))
            cache_key = f"wall_buy::{weapon}"
            img = self._zombie_images.get(cache_key)
            if img is None:
                img = build_wall_buy_image(weapon)
                self._zombie_images[cache_key] = img
            self.surface.blit(img, img.get_rect(midtop=(rect.centerx, rect.top)))
            return

        png = self._sprite_for(kind, it)
        if png is not None and os.path.isfile(os.path.join("assets", "images", png)):
            img = assets.image(png)
            self.surface.blit(img, rect.topleft)
            # Overlays specific to certain types
            if kind == "mystery_box" and it.get("label"):
                font = pygame.font.Font(None, 14)
                label = font.render(str(it["label"]), True, (0, 0, 0))
                self.surface.blit(label, label.get_rect(midbottom=(rect.centerx, rect.bottom - 4)))
            return

        # Fallbacks (legacy colored rendering)
        if kind == "door":
            pygame.draw.rect(self.surface, (110, 60, 20), rect)
            pygame.draw.rect(self.surface, GOLD, rect, 2)
        elif kind == "wall_buy":
            pygame.draw.rect(self.surface, (40, 40, 50), rect)
            pygame.draw.rect(self.surface, GOLD, rect, 2)
        elif kind == "window":
            pygame.draw.rect(self.surface, (60, 60, 80), rect)
            pygame.draw.rect(self.surface, (180, 180, 200), rect, 2)
        elif kind == "perk_machine":
            color = tuple(it.get("color", (220, 0, 0)))
            pygame.draw.rect(self.surface, color, rect)
            pygame.draw.rect(self.surface, (220, 220, 220), rect, 2)
        elif kind == "mystery_box":
            pygame.draw.rect(self.surface, (60, 30, 10), rect)
            pygame.draw.rect(self.surface, (255, 215, 0), rect, 2)
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
        if me.get("monkey_bombs", 0) > 0:
            mk = self.weapon_font.render(
                f"Monkey: {me['monkey_bombs']}", True, (220, 100, 160))
            self.surface.blit(mk, (SCREEN_WIDTH - 100, 100))

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
