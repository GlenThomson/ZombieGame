"""The actual game scene. Owns the entity sprite groups, camera, round
manager, and HUD. Doubles as the 'scene' object the entities reach into."""
import random
import pygame

from settings import (
    TILE_SIZE,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    WHITE,
    POINTS_PER_HIT,
    POINTS_PER_KILL,
    INTERACT_RANGE_PX,
    DOOR_DEFAULT_COST,
    WALL_BUY_DEFAULT_WEAPON,
    PERK_MACHINE_DEFAULT_PERK,
)
from game import assets
from game.camera import Camera
from game.states.base import State
from game.systems.round_manager import RoundManager
from game.systems.interaction import find_focused
from game.entities.player import Player
from game.entities.wall import Wall, BarbWire, ZombieSpawn
from game.entities.door import Door
from game.entities.wall_buy import WallBuy
from game.entities.window import Window
from game.entities.perk_machine import PerkMachine
from game.entities.mystery_box import MysteryBox
from game.entities.pack_a_punch import PackAPunch
from game.stats.perks import PerkSystem, PERKS
from game.world.tile import TileType
from game.ui.hud import HUD


class PlayState(State):
    def on_enter(self, *, grid, background=None, door_costs=None,
                 wall_buy_weapons=None, perk_machine_perks=None, **kwargs):
        # Sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.zombies = pygame.sprite.Group()
        self.walls = pygame.sprite.Group()
        self.barb_wire = pygame.sprite.Group()
        self.blood_splatters = pygame.sprite.Group()
        self.pickups = pygame.sprite.Group()
        self.grenades = pygame.sprite.Group()
        self.doors = pygame.sprite.Group()
        self.wall_buys = pygame.sprite.Group()
        self.windows = pygame.sprite.Group()
        self.perk_machines = pygame.sprite.Group()
        self.mystery_boxes = pygame.sprite.Group()
        self.pack_a_punch_machines = pygame.sprite.Group()
        self.zombie_spawns: list[ZombieSpawn] = []
        self.interactables: set = set()
        self.interaction_prompt: str | None = None
        self.focused_interactable = None

        self.grid = grid
        self.kill_count = 0
        self.door_costs = dict(door_costs or {})
        self.wall_buy_weapons = dict(wall_buy_weapons or {})
        self.perk_machine_perks = dict(perk_machine_perks or {})

        # Timed effects (e.g. Double Points). Each entry: name → (expire_ms, on_expire).
        self.timed_effects: dict[str, tuple[int, callable]] = {}
        self.points_multiplier = 1.0

        # Camera + map dimensions need to exist before Player so Player can
        # call camera-relative helpers in __init__.
        self.map_width = len(grid[0]) * TILE_SIZE
        self.map_height = len(grid) * TILE_SIZE
        self.camera = Camera(self.map_width, self.map_height)

        self.round_manager = RoundManager(self, starting_round=1)
        self.player = Player(self, 20 * TILE_SIZE, 20 * TILE_SIZE)
        self.perk_system = PerkSystem(self.player)

        self._populate_from_grid(grid)
        self._ensure_spawns_exist()
        self._auto_seed_tier1_tiles_if_missing()

        if background:
            self.background_image = pygame.image.load(background).convert()
        else:
            self.background_image = None

        self.hud = HUD()
        self.round_text_font = pygame.font.Font(None, 100)

    # ----- map population -----

    def _populate_from_grid(self, grid):
        player_spawn_set = False
        for row, tiles in enumerate(grid):
            for col, tile in enumerate(tiles):
                if tile == TileType.WALL:
                    Wall(self, col, row)
                elif tile == TileType.BARB_WIRE:
                    BarbWire(self, col, row)
                elif tile == TileType.ZOMBIE_SPAWN:
                    self.zombie_spawns.append(ZombieSpawn(col, row))
                elif tile == TileType.PLAYER_SPAWN:
                    self.player.pos.x = col * TILE_SIZE
                    self.player.pos.y = row * TILE_SIZE
                    player_spawn_set = True
                elif tile == TileType.DOOR_CLOSED:
                    cost = self.door_costs.get((col, row), DOOR_DEFAULT_COST)
                    door = Door(self, col, row, cost)
                    self.interactables.add(door)
                elif tile == TileType.DOOR_OPEN:
                    pass  # Already passable.
                elif tile == TileType.WALL_BUY:
                    weapon = self.wall_buy_weapons.get((col, row), WALL_BUY_DEFAULT_WEAPON)
                    wb = WallBuy(self, col, row, weapon)
                    self.interactables.add(wb)
                elif tile == TileType.WINDOW:
                    win = Window(self, col, row)
                    self.interactables.add(win)
                elif tile == TileType.PERK_MACHINE:
                    perk_name = self.perk_machine_perks.get((col, row), PERK_MACHINE_DEFAULT_PERK)
                    pm = PerkMachine(self, col, row, perk_name)
                    self.interactables.add(pm)
                elif tile == TileType.MYSTERY_BOX:
                    mb = MysteryBox(self, col, row)
                    self.interactables.add(mb)
                elif tile == TileType.PACK_A_PUNCH:
                    pap = PackAPunch(self, col, row)
                    self.interactables.add(pap)
        self._player_spawn_set = player_spawn_set

    def _ensure_spawns_exist(self):
        if not self._player_spawn_set:
            self._auto_place_player()
        if not self.zombie_spawns:
            self._auto_place_zombie_spawns()

    def _auto_place_player(self):
        rows = len(self.grid)
        cols = len(self.grid[0])
        cy, cx = rows // 2, cols // 2
        for radius in range(max(rows, cols)):
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if abs(dx) != radius and abs(dy) != radius:
                        continue
                    y, x = cy + dy, cx + dx
                    if 0 <= y < rows and 0 <= x < cols and self.grid[y][x] == TileType.EMPTY:
                        self.player.pos.x = x * TILE_SIZE
                        self.player.pos.y = y * TILE_SIZE
                        return

    def _auto_place_zombie_spawns(self):
        rows = len(self.grid)
        cols = len(self.grid[0])
        candidates = []
        for x in range(cols):
            for y in (0, rows - 1):
                if self.grid[y][x] == TileType.EMPTY:
                    candidates.append((x, y))
        for y in range(1, rows - 1):
            for x in (0, cols - 1):
                if self.grid[y][x] == TileType.EMPTY:
                    candidates.append((x, y))
        if not candidates:
            px = self.player.pos.x / TILE_SIZE
            py = self.player.pos.y / TILE_SIZE
            candidates = [
                (x, y)
                for y in range(rows)
                for x in range(cols)
                if self.grid[y][x] == TileType.EMPTY and (abs(x - px) + abs(y - py)) > 5
            ] or [
                (x, y)
                for y in range(rows)
                for x in range(cols)
                if self.grid[y][x] == TileType.EMPTY
            ]
        if not candidates:
            return
        if len(candidates) > 8:
            step = len(candidates) / 8
            candidates = [candidates[int(i * step)] for i in range(8)]
        for x, y in candidates:
            self.zombie_spawns.append(ZombieSpawn(x, y))

    def _first_empty_tile_far_from_player(self) -> tuple[int, int] | None:
        rows = len(self.grid)
        cols = len(self.grid[0])
        px = self.player.pos.x / TILE_SIZE
        py = self.player.pos.y / TILE_SIZE
        best = None
        best_d2 = 0
        for y in range(rows):
            for x in range(cols):
                if self.grid[y][x] != TileType.EMPTY:
                    continue
                d2 = (x - px) ** 2 + (y - py) ** 2
                if d2 > best_d2:
                    best_d2 = d2
                    best = (x, y)
        return best

    def _auto_seed_tier1_tiles_if_missing(self):
        """If the loaded map has no doors / wall buys / windows yet, drop one
        of each in plausible spots so Tier 1 mechanics can be tried out
        without needing the map maker. Runtime-only — doesn't modify the .pkl."""
        has_door = any(d for d in self.doors)
        has_wall_buy = any(w for w in self.wall_buys)
        has_window = any(w for w in self.windows)
        has_perk = any(w for w in self.perk_machines)
        has_box = any(w for w in self.mystery_boxes)
        has_pap = any(w for w in self.pack_a_punch_machines)
        if has_door and has_wall_buy and has_window and has_perk and has_box and has_pap:
            return

        # Find candidate tiles: walls adjacent to empty tiles work for doors
        # and wall buys; perimeter walls work for windows.
        rows = len(self.grid)
        cols = len(self.grid[0])
        wall_with_empty_neighbour = []
        for y in range(rows):
            for x in range(cols):
                if self.grid[y][x] != TileType.WALL:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < cols and 0 <= ny < rows and self.grid[ny][nx] == TileType.EMPTY:
                        wall_with_empty_neighbour.append((x, y))
                        break

        if not wall_with_empty_neighbour:
            return

        # Distance from player so seeded tiles aren't all in the same corner.
        px = self.player.pos.x / TILE_SIZE
        py = self.player.pos.y / TILE_SIZE
        wall_with_empty_neighbour.sort(
            key=lambda p: -((p[0] - px) ** 2 + (p[1] - py) ** 2) ** 0.5
        )

        def take_one() -> tuple[int, int] | None:
            if not wall_with_empty_neighbour:
                return None
            return wall_with_empty_neighbour.pop()

        if not has_door:
            spot = take_one()
            if spot:
                x, y = spot
                self.grid[y][x] = TileType.DOOR_CLOSED
                door = Door(self, x, y, DOOR_DEFAULT_COST)
                self.interactables.add(door)
        if not has_wall_buy:
            spot = take_one()
            if spot:
                x, y = spot
                self.grid[y][x] = TileType.WALL_BUY
                wb = WallBuy(self, x, y, WALL_BUY_DEFAULT_WEAPON)
                self.interactables.add(wb)
        if not has_window:
            spot = take_one()
            if spot is None:
                # Sparse maps may run out of wall-adjacent candidates. Windows
                # can sit on any empty tile — fall back to that.
                spot = self._first_empty_tile_far_from_player()
                if spot is not None:
                    self.grid[spot[1]][spot[0]] = TileType.WINDOW
                    win = Window(self, spot[0], spot[1])
                    self.interactables.add(win)
            else:
                x, y = spot
                self.grid[y][x] = TileType.WINDOW
                win = Window(self, x, y)
                self.interactables.add(win)
        if not has_perk:
            spot = take_one()
            if spot:
                x, y = spot
                self.grid[y][x] = TileType.PERK_MACHINE
                pm = PerkMachine(self, x, y, PERK_MACHINE_DEFAULT_PERK)
                self.interactables.add(pm)
        if not has_box:
            spot = take_one()
            if spot:
                x, y = spot
                self.grid[y][x] = TileType.MYSTERY_BOX
                mb = MysteryBox(self, x, y)
                self.interactables.add(mb)
        if not has_pap:
            spot = take_one()
            if spot:
                x, y = spot
                self.grid[y][x] = TileType.PACK_A_PUNCH
                pap = PackAPunch(self, x, y)
                self.interactables.add(pap)

    # ---- per-frame ----

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.app.switch("menu")
                return
            if event.key == pygame.K_g:
                self.player.throw_grenade()
            elif event.key == pygame.K_r:
                self.player.weapon.reload()
            elif event.key == pygame.K_f:
                self._fire_interaction()
            elif pygame.K_1 <= event.key <= pygame.K_4:
                self.player.inventory.equip(event.key - pygame.K_1)

    def _fire_interaction(self):
        if self.focused_interactable is None:
            return
        self.focused_interactable.interact(self.player)
        # The interactable may have removed itself; refresh on next frame anyway.

    def update(self):
        if self.player.is_dead():
            self.app.switch("game_over", final_round=self.round_manager.current_round,
                            final_kills=self.kill_count)
            return

        if pygame.mouse.get_pressed()[0]:
            self.player.shoot()

        dt_ms = self.app.clock.get_time()
        dt_s = dt_ms / 1000.0

        self.camera.update(self.player)
        self.bullets.update()
        self.pickups.update()
        self.zombies.update((self.player.pos.x, self.player.pos.y))
        self.player.update()
        self.blood_splatters.update()
        self.grenades.update()
        for window in list(self.windows):
            window.update_against_zombies()
        for box in list(self.mystery_boxes):
            box.update()

        self._sprite_interactions()
        self._update_interaction_focus()
        self._tick_timed_effects()
        self.round_manager.tick(dt_s)

    # ---- timed effects (Double Points etc.) ----

    def start_timed_effect(self, name: str, duration_ms: int,
                           on_apply=None, on_expire=None):
        existing = self.timed_effects.get(name)
        if existing is not None:
            # Already active — just push the expiry forward.
            self.timed_effects[name] = (
                pygame.time.get_ticks() + duration_ms, existing[1]
            )
            return
        if on_apply is not None:
            on_apply()
        self.timed_effects[name] = (
            pygame.time.get_ticks() + duration_ms,
            on_expire or (lambda: None),
        )

    def _tick_timed_effects(self):
        now = pygame.time.get_ticks()
        expired = [n for n, (t, _) in self.timed_effects.items() if now >= t]
        for n in expired:
            _, on_expire = self.timed_effects.pop(n)
            on_expire()

    def _update_interaction_focus(self):
        # Drop any dead interactables from the set first.
        self.interactables = {it for it in self.interactables if getattr(it, "alive", lambda: True)()}
        focused = find_focused(
            (self.player.rect.centerx, self.player.rect.centery),
            self.interactables,
            INTERACT_RANGE_PX,
        )
        self.focused_interactable = focused
        self.interaction_prompt = focused.get_prompt(self.player) if focused else None

    def _sprite_interactions(self):
        damage = self.player.weapon.damage if self.player.weapon else 1
        penetration = self.player.weapon.penetration if self.player.weapon else 1
        mult = self.points_multiplier
        for zombie in self.zombies:
            for bullet in self.bullets:
                if zombie.rect.colliderect(bullet.hit_box):
                    bullet.hit_count += 1
                    was_alive = zombie.health > 0
                    zombie.take_damage(damage)
                    if was_alive:
                        if zombie.health <= 0:
                            self.player.points += int(POINTS_PER_KILL * mult)
                        else:
                            self.player.points += int(POINTS_PER_HIT * mult)
                    if bullet.hit_count >= penetration:
                        bullet.kill()
            if zombie.hit_box.colliderect(self.player.hit_box):
                zombie.speed = zombie.speed_base * 0.1
                self.player.take_damage()
            else:
                zombie.speed = zombie.speed_base

    def draw(self):
        pygame.display.set_caption(f"{self.app.clock.get_fps():.2f}")
        self.surface.fill(WHITE)
        if self.background_image is not None:
            self.surface.blit(self.background_image, self.camera.camera.topleft)

        self.blood_splatters.draw(self.surface)

        # Visible interactable groups (Wall / BarbWire are invisible —
        # the world is the background image).
        visible_interactables = (
            self.doors, self.wall_buys, self.windows,
            self.perk_machines, self.mystery_boxes, self.pack_a_punch_machines,
        )
        for group in visible_interactables:
            for sprite in group:
                self.surface.blit(sprite.image, self.camera.apply(sprite))

        for sprite in self.all_sprites:
            if sprite in self.walls or sprite in self.barb_wire:
                continue
            if any(sprite in g for g in visible_interactables):
                continue
            self.surface.blit(sprite.image, self.camera.apply(sprite))
        for sprite in self.zombies:
            self.surface.blit(sprite.image, self.camera.apply(sprite))

        self.hud.draw(self.surface, self)

        if self.round_manager.round_text_countdown > 0:
            self._draw_round_text()

        pygame.display.flip()

    def _draw_round_text(self):
        self.round_manager.round_text_countdown -= 1
        text = self.round_text_font.render(
            f"Round {self.round_manager.current_round}", True, (255, 0, 0)
        )
        text.set_alpha(self.round_manager.round_text_countdown)
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.surface.blit(text, rect)
