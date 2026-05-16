"""The actual game scene. Owns the entity sprite groups, camera, round
manager, and HUD. Doubles as the 'scene' object the entities reach into.

Multi-player ready: holds a list of Player instances. The "local" player
(the one whose camera + HUD we render) is identified by `local_player_id`.
On a single-player game there's just one player and `local_player_id == 0`.
"""
import math
import os
import random
import pygame

from settings import (
    TILE_SIZE,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    WHITE,
    POINTS_PER_HIT,
    POINTS_PER_KILL,
    POINTS_PER_HEADSHOT_HIT,
    HEADSHOT_DAMAGE_MULT,
    INTERACT_RANGE_PX,
    DOOR_DEFAULT_COST,
    WALL_BUY_DEFAULT_WEAPON,
    PERK_MACHINE_DEFAULT_PERK,
    MAX_PLAYERS,
    PLAYER_TINTS,
    REVIVE_HOLD_MS,
    REVIVE_RANGE_PX,
)
from game import assets
from game.camera import Camera
from game.states.base import State
from game.systems.round_manager import RoundManager
from game.systems.interaction import find_focused
from game.systems.input import LocalInputSource, RemoteInputSource
from game.entities.player import Player
from game.entities.wall import Wall, BarbWire, ZombieSpawn
from game.entities.door import Door, DoorGroup
from game.entities.wall_buy import WallBuy
from game.entities.window import Window
from game.entities.perk_machine import PerkMachine
from game.entities.mystery_box import MysteryBox
from game.entities.pack_a_punch import PackAPunch
from game.entities.power_switch import PowerSwitch
from game.entities.trap import Trap
from game.stats.perks import PerkSystem, PERKS
from game.world.tile import TileType
from game.ui.hud import HUD


class PlayState(State):
    def on_enter(self, *, grid, background=None, door_costs=None,
                 wall_buy_weapons=None, perk_machine_perks=None,
                 floor_grid: list | None = None,
                 wall_style: str = "brick",
                 player_count: int = 1,
                 local_player_id: int = 0,
                 remote_input_sources: dict | None = None,
                 player_names: list[str] | None = None,
                 **kwargs):
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
        self.power_switches = pygame.sprite.Group()
        self.traps = pygame.sprite.Group()
        self.monkey_bombs = pygame.sprite.Group()
        self.muzzle_flashes = pygame.sprite.Group()
        self.floating_texts = pygame.sprite.Group()
        self.power_on: bool = False
        # Things zombies should target instead of the player while active
        # (e.g. live monkey bombs). Highest-priority first.
        self.zombie_attractors: list = []
        self.lightning_arcs: list = []
        self.mystery_box_uses: int = 0
        self.zombie_spawns: list[ZombieSpawn] = []
        self.interactables: set = set()
        self.interaction_prompt: str | None = None
        self.focused_interactable = None

        self.grid = grid
        self.kill_count = 0
        self.door_costs = dict(door_costs or {})
        self.wall_buy_weapons = dict(wall_buy_weapons or {})
        self.perk_machine_perks = dict(perk_machine_perks or {})
        # Wall style is read by the Wall entity in its __init__, so set it
        # BEFORE _populate_from_grid below.
        self.wall_style = wall_style
        # Floor grid: same shape as the object grid. If not provided
        # (legacy map), default to all CONCRETE.
        from game.world.tile import FloorType
        if floor_grid is None:
            floor_grid = [
                [int(FloorType.CONCRETE) for _ in row] for row in grid
            ]
        self.floor_grid = floor_grid

        self.timed_effects: dict[str, tuple[int, callable]] = {}
        self.points_multiplier = 1.0
        self.damage_flash_alpha = 0
        self.paused = False           # P key toggles in SP only

        # Map dimensions + camera (camera follows the local player or midpoint).
        self.map_width = len(grid[0]) * TILE_SIZE
        self.map_height = len(grid) * TILE_SIZE
        self.camera = Camera(self.map_width, self.map_height)

        # ---- Players ----
        player_count = max(1, min(MAX_PLAYERS, player_count))
        self.local_player_id = local_player_id
        names = player_names or [f"Player{i + 1}" for i in range(player_count)]
        self.players: list[Player] = []
        remote_input_sources = remote_input_sources or {}

        def _world_mouse():
            mx, my = pygame.mouse.get_pos()
            return (mx - self.camera.camera.x, my - self.camera.camera.y)

        for i in range(player_count):
            input_source = remote_input_sources.get(i)
            if input_source is None and i == local_player_id:
                input_source = LocalInputSource(world_mouse_provider=_world_mouse)
            elif input_source is None:
                input_source = RemoteInputSource()
            tint = PLAYER_TINTS[i % len(PLAYER_TINTS)] if i > 0 else None
            p = Player(
                self, 20 * TILE_SIZE, 20 * TILE_SIZE,
                player_id=i,
                name=names[i] if i < len(names) else f"Player{i + 1}",
                input_source=input_source,
                tint=tint,
            )
            self.players.append(p)

        self.perk_system_by_player = {p.player_id: PerkSystem(p) for p in self.players}

        # Round manager spawn-scaling depends on player count.
        self.round_manager = RoundManager(self, starting_round=1, player_count=player_count)

        self._populate_from_grid(grid)
        self._ensure_spawns_exist()
        self._auto_seed_tier1_tiles_if_missing()
        # Maps without a power switch default to "power on" so existing
        # maps don't suddenly lock out perks/PaP.
        if not any(self.power_switches):
            self.power_on = True

        # Spread spawn positions slightly so multiple players don't sit on
        # the same tile if the map only has one player_spawn.
        self._spread_initial_player_positions()

        if background:
            self.background_image = pygame.image.load(background).convert()
        else:
            self.background_image = None

        self.hud = HUD()
        self.round_text_font = pygame.font.Font(None, 180)

    # ---- backwards-compat alias for code that pre-dates multi-player ----

    @property
    def player(self) -> Player:
        return self.local_player

    @property
    def local_player(self) -> Player:
        for p in self.players:
            if p.player_id == self.local_player_id:
                return p
        return self.players[0]

    @property
    def perk_system(self) -> PerkSystem:
        # HUD reads scene.perk_system for the local player.
        return self.perk_system_by_player[self.local_player.player_id]

    def alive_players(self) -> list[Player]:
        return [p for p in self.players if not p.is_dead()]

    def standing_players(self) -> list[Player]:
        return [p for p in self.alive_players() if not p.is_down]

    def nearest_player_to(self, pos) -> Player | None:
        targets = self.standing_players() or self.alive_players()
        if not targets:
            return None
        ax, ay = (pos.x, pos.y) if hasattr(pos, "x") else pos[:2]
        return min(targets, key=lambda p: (p.pos.x - ax) ** 2 + (p.pos.y - ay) ** 2)

    def nearest_zombie_target(self, pos):
        """Returns the position vector zombies should aim at: a live monkey
        bomb if there is one, else the nearest standing player."""
        if self.zombie_attractors:
            attractor = self.zombie_attractors[0]
            apos = attractor.pos
            return type(apos)(apos.x, apos.y)
        target = self.nearest_player_to(pos)
        return target.pos if target is not None else None

    # ----- map population -----

    def _populate_from_grid(self, grid):
        player_spawn_set = False
        door_tile_set: set[tuple[int, int]] = set()
        for row, tiles in enumerate(grid):
            for col, tile in enumerate(tiles):
                if tile == TileType.WALL:
                    Wall(self, col, row)
                elif tile == TileType.BARB_WIRE:
                    BarbWire(self, col, row)
                elif tile == TileType.ZOMBIE_SPAWN:
                    self.zombie_spawns.append(ZombieSpawn(col, row))
                elif tile == TileType.PLAYER_SPAWN:
                    for p in self.players:
                        p.pos.x = col * TILE_SIZE
                        p.pos.y = row * TILE_SIZE
                    player_spawn_set = True
                elif tile == TileType.DOOR_CLOSED:
                    door_tile_set.add((col, row))
                elif tile == TileType.DOOR_OPEN:
                    pass
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
                elif tile == TileType.POWER_SWITCH:
                    sw = PowerSwitch(self, col, row)
                    self.interactables.add(sw)
                elif tile == TileType.TRAP_FLOGGER:
                    t = Trap(self, col, row, "flogger")
                    self.interactables.add(t)
                elif tile == TileType.TRAP_FIRE:
                    t = Trap(self, col, row, "fire")
                    self.interactables.add(t)
        # Adjacent DOOR_CLOSED tiles form one logical door.
        self._build_door_groups(door_tile_set)
        self._player_spawn_set = player_spawn_set

    def _build_door_groups(self, door_tiles: set[tuple[int, int]]):
        visited: set[tuple[int, int]] = set()
        for tile in door_tiles:
            if tile in visited:
                continue
            # BFS to find all 4-connected door tiles.
            component: list[tuple[int, int]] = []
            queue = [tile]
            while queue:
                t = queue.pop()
                if t in visited:
                    continue
                visited.add(t)
                component.append(t)
                tx, ty = t
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    n = (tx + dx, ty + dy)
                    if n in door_tiles and n not in visited:
                        queue.append(n)
            cost = max(
                (self.door_costs.get(t, DOOR_DEFAULT_COST) for t in component),
                default=DOOR_DEFAULT_COST,
            )
            group = DoorGroup(self, cost)
            for x, y in component:
                door = Door(self, x, y, group)
                self.interactables.add(door)

    def _spread_initial_player_positions(self):
        """When multiple players share a player_spawn tile, fan them out."""
        if len(self.players) <= 1:
            return
        cx, cy = self.players[0].pos.x, self.players[0].pos.y
        spread = TILE_SIZE * 1.2
        for i, p in enumerate(self.players[1:], start=1):
            angle = (i / max(1, len(self.players) - 1)) * 2 * math.pi
            p.pos.x = cx + math.cos(angle) * spread
            p.pos.y = cy + math.sin(angle) * spread

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
                        for p in self.players:
                            p.pos.x = x * TILE_SIZE
                            p.pos.y = y * TILE_SIZE
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
            px = self.local_player.pos.x / TILE_SIZE
            py = self.local_player.pos.y / TILE_SIZE
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
        px = self.local_player.pos.x / TILE_SIZE
        py = self.local_player.pos.y / TILE_SIZE
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
        has_door = any(d for d in self.doors)
        has_wall_buy = any(w for w in self.wall_buys)
        has_window = any(w for w in self.windows)
        has_perk = any(w for w in self.perk_machines)
        has_box = any(w for w in self.mystery_boxes)
        has_pap = any(w for w in self.pack_a_punch_machines)
        if has_door and has_wall_buy and has_window and has_perk and has_box and has_pap:
            return

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

        px = self.local_player.pos.x / TILE_SIZE
        py = self.local_player.pos.y / TILE_SIZE
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
                group = DoorGroup(self, DOOR_DEFAULT_COST)
                door = Door(self, x, y, group)
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
            if event.key == pygame.K_p and len(self.players) == 1:
                # Single-player only — pause is meaningless in MP.
                self.paused = not self.paused
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
            if ev_name is None:
                return
            src = self.local_player.input_source
            if hasattr(src, "push_event"):
                src.push_event(ev_name)

    def _fire_interaction_for(self, player: Player):
        focused = self._find_focused_for(player)
        if focused is None:
            return
        focused.interact(player)

    def _find_focused_for(self, player: Player):
        return find_focused(
            (player.rect.centerx, player.rect.centery),
            self.interactables,
            INTERACT_RANGE_PX,
        )

    def update(self):
        if self.paused:
            return
        # End-of-game: all players dead.
        if not self.alive_players():
            self.app.switch(
                "game_over",
                final_round=self.round_manager.current_round,
                final_kills=self.kill_count,
                player_stats=[
                    {
                        "name": p.name,
                        "kills": p.kills,
                        "headshots": p.headshot_kills,
                        "points_spent": p.points_spent,
                        "perks": [pk.name for pk in self.perk_system_by_player[p.player_id].owned()],
                    }
                    for p in self.players
                ],
            )
            return

        dt_ms = self.app.clock.get_time()
        dt_s = dt_ms / 1000.0

        # Camera follows midpoint of standing players (or alive if all down).
        followed = self.standing_players() or self.alive_players() or [self.local_player]
        avg_x = sum(p.pos.x for p in followed) / len(followed)
        avg_y = sum(p.pos.y for p in followed) / len(followed)

        class _CamTarget:
            rect = pygame.Rect(int(avg_x), int(avg_y), 1, 1)
        self.camera.update(_CamTarget)

        self.bullets.update()
        self.pickups.update()
        self.zombies.update(self)
        for p in self.players:
            snap = p.input_source.snapshot()
            # Scene-level routing of interact (Player ignores "interact").
            for ev in snap.events:
                if ev == "interact":
                    self._fire_interaction_for(p)
            p.update(snap)
        self.blood_splatters.update()
        self.grenades.update()
        self.muzzle_flashes.update()
        self.floating_texts.update()
        self.monkey_bombs.update()
        for window in list(self.windows):
            window.update_against_zombies()
        for box in list(self.mystery_boxes):
            box.update()
        for trap in list(self.traps):
            trap.update_kills()

        if self.damage_flash_alpha > 0:
            self.damage_flash_alpha = max(0, self.damage_flash_alpha - 14)

        self._sprite_interactions()
        self._handle_revives()
        self._update_interaction_focus_for_local()
        self._tick_timed_effects()
        self.round_manager.tick(dt_s)

    def _handle_revives(self):
        # Any standing player adjacent to a downed player who's holding F
        # contributes time toward that player's revive_progress_ms.
        if len(self.players) <= 1:
            return
        downed = [p for p in self.players if p.is_down]
        if not downed:
            return
        dt = self.app.clock.get_time()
        for downed_p in downed:
            advanced = False
            for reviver in self.players:
                if reviver is downed_p or reviver.is_down or reviver.is_dead():
                    continue
                d2 = (downed_p.pos.x - reviver.pos.x) ** 2 + (downed_p.pos.y - reviver.pos.y) ** 2
                if d2 > REVIVE_RANGE_PX ** 2:
                    continue
                # Was F held in the most recent input snapshot? Both Local and
                # Remote sources keep `latest` (Remote) or repopulate via
                # snapshot() — this is checked once per frame for the reviver.
                src = reviver.input_source
                latest = getattr(src, "latest", None)
                if latest is not None:
                    holding = pygame.K_f in latest.keys
                else:
                    # Local: peek at the held keys without disturbing events.
                    holding = pygame.key.get_pressed()[pygame.K_f]
                if holding:
                    # Quick Revive doubles your revive speed on teammates.
                    reviver_perks = self.perk_system_by_player.get(reviver.player_id)
                    mult = 2.0 if reviver_perks and reviver_perks.has("Quick Revive") else 1.0
                    downed_p.revive_progress_ms += int(dt * mult)
                    advanced = True
                    break
            if not advanced and downed_p.revive_progress_ms > 0:
                # Decay if no one is helping (avoids resuming a stale revive).
                downed_p.revive_progress_ms = max(0, downed_p.revive_progress_ms - dt // 2)
            if downed_p.revive_progress_ms >= REVIVE_HOLD_MS:
                downed_p.revive()

    def _update_interaction_focus_for_local(self):
        self.interactables = {it for it in self.interactables if getattr(it, "alive", lambda: True)()}
        focused = self._find_focused_for(self.local_player)
        self.focused_interactable = focused
        self.interaction_prompt = focused.get_prompt(self.local_player) if focused else None

    def _sprite_interactions(self):
        from game.entities.effects import FloatingText, LightningArc
        mult = self.points_multiplier
        for zombie in self.zombies:
            for bullet in self.bullets:
                if not zombie.rect.colliderect(bullet.hit_box):
                    continue
                bullet.hit_count += 1
                is_headshot = bullet.hit_box.centery < zombie.rect.top + zombie.rect.height * 0.25
                damage = bullet.damage * (HEADSHOT_DAMAGE_MULT if is_headshot else 1.0)
                was_alive = zombie.health > 0
                zombie.take_damage(damage)
                shooter = self._player_by_id(bullet.shooter_id)
                if was_alive and shooter is not None:
                    if zombie.health <= 0:
                        pts = int(POINTS_PER_KILL * mult)
                        shooter.points += pts
                        shooter.kills += 1
                        if is_headshot:
                            shooter.headshot_kills += 1
                        color = (255, 90, 90) if is_headshot else (255, 215, 0)
                        label = f"+{pts}!" if is_headshot else f"+{pts}"
                        FloatingText(self, zombie.pos, label, color=color)
                    else:
                        base = POINTS_PER_HIT + (POINTS_PER_HEADSHOT_HIT if is_headshot else 0)
                        pts = int(base * mult)
                        shooter.points += pts
                if bullet.effect_kind == "chain":
                    self._chain_lightning_from(zombie, damage, shooter, mult)
                elif bullet.effect_kind == "blast":
                    self._blast_knockback(zombie)
                if bullet.hit_count >= bullet.penetration:
                    bullet.kill()

            # Each player can take damage from any zombie touching them.
            for player in self.players:
                if player.is_down or player.is_dead():
                    continue
                if zombie.hit_box.colliderect(player.hit_box):
                    zombie.speed = zombie.speed_base * 0.1
                    player.take_damage()
                    if player is self.local_player:
                        self.damage_flash_alpha = min(180, self.damage_flash_alpha + 60)
                    if player.health <= 0 and not player.is_down:
                        any_standing_others = any(
                            p is not player and not p.is_down and not p.is_dead()
                            for p in self.players
                        )
                        if any_standing_others:
                            player.go_down()
                else:
                    zombie.speed = zombie.speed_base
        # decay lightning arcs
        self.lightning_arcs = [a for a in self.lightning_arcs if a.alive()]

    def _chain_lightning_from(self, origin_zombie, damage: float, shooter, mult: float):
        """Wunderwaffe: chain to up to 4 more zombies within 180px."""
        from game.entities.effects import FloatingText, LightningArc
        chained: set = {id(origin_zombie)}
        prev = origin_zombie
        for _ in range(4):
            best = None
            best_d2 = 180 * 180
            for z in self.zombies:
                if id(z) in chained or z.health <= 0:
                    continue
                d2 = (z.pos.x - prev.pos.x) ** 2 + (z.pos.y - prev.pos.y) ** 2
                if d2 < best_d2:
                    best_d2 = d2
                    best = z
            if best is None:
                break
            chained.add(id(best))
            self.lightning_arcs.append(LightningArc(
                (prev.pos.x, prev.pos.y), (best.pos.x, best.pos.y),
            ))
            was_alive = best.health > 0
            best.take_damage(damage)
            if was_alive and shooter is not None and best.health <= 0:
                pts = int(POINTS_PER_KILL * mult)
                shooter.points += pts
                shooter.kills += 1
                FloatingText(self, best.pos, f"+{pts}", color=(140, 200, 255))
            prev = best

    def _blast_knockback(self, zombie):
        """Thundergun: shove the zombie away from the local player."""
        anchor = self.local_player.pos
        dx = zombie.pos.x - anchor.x
        dy = zombie.pos.y - anchor.y
        length = (dx * dx + dy * dy) ** 0.5
        if length < 0.1:
            return
        push = 60.0
        zombie.pos.x += dx / length * push
        zombie.pos.y += dy / length * push
        zombie.rect.center = zombie.pos
        zombie.hit_box.center = zombie.pos

    def _player_by_id(self, player_id: int | None) -> Player | None:
        if player_id is None:
            return None
        for p in self.players:
            if p.player_id == player_id:
                return p
        return None

    # ---- timed effects (Double Points etc.) ----

    def start_timed_effect(self, name: str, duration_ms: int,
                           on_apply=None, on_expire=None):
        existing = self.timed_effects.get(name)
        if existing is not None:
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

    # ---- audio events ----

    def announce_event(self, name: str, data: dict | None = None):
        """Play a sound locally. HostPlayState overrides to also broadcast
        the event to connected clients so they hear it too."""
        sound_name = (data or {}).get("sound")
        if sound_name:
            from game import assets
            assets.sound(sound_name).play()

    # ---- draw ----

    def draw(self):
        pygame.display.set_caption(f"{self.app.clock.get_fps():.2f}")
        self.surface.fill(WHITE)
        # Draw the floor tile grid (every cell). Background image is now a
        # legacy fallback only used if floor_grid was empty for some reason.
        self._draw_floor_grid()
        if self.background_image is not None and not any(any(r) for r in self.floor_grid):
            self.surface.blit(self.background_image, self.camera.camera.topleft)

        self.blood_splatters.draw(self.surface)

        visible_interactables = (
            self.doors, self.wall_buys, self.windows,
            self.perk_machines, self.mystery_boxes, self.pack_a_punch_machines,
            self.power_switches, self.traps,
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

        # Floating points + muzzle flashes
        for sprite in self.muzzle_flashes:
            self.surface.blit(sprite.image, self.camera.apply(sprite))
        for sprite in self.floating_texts:
            self.surface.blit(sprite.image, sprite.rect)

        # Lightning arcs (Wunderwaffe chain effect)
        cam_x, cam_y = self.camera.camera.x, self.camera.camera.y
        for arc in self.lightning_arcs:
            x1 = int(arc.p1[0] + cam_x); y1 = int(arc.p1[1] + cam_y)
            x2 = int(arc.p2[0] + cam_x); y2 = int(arc.p2[1] + cam_y)
            color = (140, 200, 255)
            pygame.draw.line(self.surface, color, (x1, y1), (x2, y2), 3)
            mx = (x1 + x2) // 2 + ((y1 - y2) // 8)
            my = (y1 + y2) // 2 + ((x2 - x1) // 8)
            pygame.draw.line(self.surface, (240, 240, 255), (x1, y1), (mx, my), 1)
            pygame.draw.line(self.surface, (240, 240, 255), (mx, my), (x2, y2), 1)

        self._draw_low_health_overlay()
        self._draw_damage_flash()
        self._draw_player_labels()

        self.hud.draw(self.surface, self)

        if self.round_manager.round_text_countdown > 0:
            self._draw_round_text()

        if self.paused:
            self._draw_pause_overlay()

        pygame.display.flip()

    def _draw_floor_grid(self):
        """Blit the floor tile beneath each cell. Only draws cells in the
        camera's viewport so big maps stay fast."""
        from game.world.tile import FLOOR_SPRITES
        from game import assets
        cam_x, cam_y = self.camera.camera.x, self.camera.camera.y
        # Visible tile range — clamp to grid bounds.
        rows = len(self.floor_grid)
        cols = len(self.floor_grid[0]) if rows else 0
        x0 = max(0, int(-cam_x) // TILE_SIZE)
        y0 = max(0, int(-cam_y) // TILE_SIZE)
        x1 = min(cols, x0 + SCREEN_WIDTH // TILE_SIZE + 2)
        y1 = min(rows, y0 + SCREEN_HEIGHT // TILE_SIZE + 2)
        for y in range(y0, y1):
            for x in range(x0, x1):
                ftype = self.floor_grid[y][x]
                png = FLOOR_SPRITES.get(int(ftype))
                if png is None:
                    continue
                img = assets.image(os.path.join("tiles", png))
                self.surface.blit(img, (x * TILE_SIZE + cam_x, y * TILE_SIZE + cam_y))

    def _draw_pause_overlay(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.surface.blit(overlay, (0, 0))
        font_big = pygame.font.Font(None, 110)
        font_sm = pygame.font.Font(None, 32)
        title = font_big.render("PAUSED", True, (220, 220, 220))
        self.surface.blit(
            title, title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20)),
        )
        sub = font_sm.render("Press P to resume", True, (180, 180, 180))
        self.surface.blit(
            sub, sub.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)),
        )

    def _draw_player_labels(self):
        if len(self.players) <= 1:
            return
        font = pygame.font.Font(None, 18)
        for p in self.players:
            label_color = PLAYER_TINTS[p.player_id % len(PLAYER_TINTS)] or (220, 220, 220)
            text = font.render(p.name, True, label_color)
            screen_pos = (
                p.rect.centerx + self.camera.camera.x - text.get_width() // 2,
                p.rect.top + self.camera.camera.y - 16,
            )
            self.surface.blit(text, screen_pos)
            if p.is_down:
                # show a revive bar
                pct = min(1.0, p.revive_progress_ms / REVIVE_HOLD_MS)
                bar = pygame.Rect(0, 0, 36, 5)
                bar.midbottom = (
                    p.rect.centerx + self.camera.camera.x,
                    p.rect.top + self.camera.camera.y - 2,
                )
                pygame.draw.rect(self.surface, (60, 60, 60), bar)
                pygame.draw.rect(self.surface, (0, 220, 0),
                                  (bar.x, bar.y, int(bar.w * pct), bar.h))

    def _draw_low_health_overlay(self):
        ratio = self.local_player.health / max(1, self.local_player.max_health)
        if ratio >= 0.3:
            return
        intensity = max(0.0, min(1.0, (0.3 - ratio) / 0.3))
        pulse = (math.sin(pygame.time.get_ticks() / 200) + 1) / 2
        alpha = int(70 + 120 * intensity * (0.5 + 0.5 * pulse))
        alpha = max(0, min(255, alpha))
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for i in range(120):
            a = max(0, alpha - i * 2)
            pygame.draw.rect(
                overlay, (200, 0, 0, a),
                (i, i, SCREEN_WIDTH - 2 * i, SCREEN_HEIGHT - 2 * i), 2,
            )
        self.surface.blit(overlay, (0, 0))

    def _draw_damage_flash(self):
        if self.damage_flash_alpha <= 0:
            return
        flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        flash.fill((220, 0, 0, self.damage_flash_alpha))
        self.surface.blit(flash, (0, 0))

    def _draw_round_text(self):
        # Decay slower so the announcement lingers; cap alpha at 255.
        self.round_manager.round_text_countdown -= 1
        alpha = min(255, max(0, self.round_manager.round_text_countdown // 2))
        msg = f"Round {self.round_manager.current_round}"
        # Drop shadow underneath for legibility against the background.
        shadow = self.round_text_font.render(msg, True, (0, 0, 0))
        shadow.set_alpha(alpha)
        srect = shadow.get_rect(center=(SCREEN_WIDTH // 2 + 4, SCREEN_HEIGHT // 2 + 4))
        self.surface.blit(shadow, srect)
        text = self.round_text_font.render(msg, True, (190, 0, 0))
        text.set_alpha(alpha)
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.surface.blit(text, rect)
