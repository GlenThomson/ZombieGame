"""The player character. Owns a weapon inventory + a stat ModifierStack +
an InputSource (local pygame OR network-fed remote)."""
import math
import pygame

from settings import (
    TILE_SIZE,
    PLAYER_SPEED,
    PLAYER_HEALTH,
    PLAYER_HIT_BOX_SIZE,
    BULLET_DAMAGE,
    STARTING_GRENADES,
    STARTING_POINTS,
    STARTING_MONKEY_BOMBS,
)
from game import assets
from game.systems.collision import resolve_wall_collision
from game.systems.input import InputState, LocalInputSource
from game.stats.modifiers import ModifierStack
from game.weapons.inventory import Inventory

vector = pygame.math.Vector2


class Player(pygame.sprite.Sprite):
    def __init__(self, scene, x: float, y: float, *,
                 player_id: int = 0,
                 name: str = "Player1",
                 input_source=None,
                 image_name: str = "player.png",
                 tint: tuple[int, int, int] | None = None):
        super().__init__(scene.all_sprites)
        self.scene = scene
        self.player_id = player_id
        self.name = name
        self.input_source = input_source if input_source is not None else LocalInputSource()
        self._tint = tint

        base = assets.image(image_name, scale=(TILE_SIZE, TILE_SIZE))
        if tint is not None:
            base = base.copy()
            overlay = pygame.Surface(base.get_size(), pygame.SRCALPHA)
            overlay.fill((*tint, 110))
            base.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        self.original_image = base
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.pos = vector(x, y)
        self.vel = vector(0, 0)
        self.angle = 0

        self.hit_box = pygame.Rect(0, 0, PLAYER_HIT_BOX_SIZE, PLAYER_HIT_BOX_SIZE)
        self.hit_box.center = self.rect.center

        self.modifiers = ModifierStack()
        self._base_health = PLAYER_HEALTH
        self.health = self.max_health
        self.grenade_count = STARTING_GRENADES
        self.monkey_bomb_count = STARTING_MONKEY_BOMBS
        self.points = STARTING_POINTS

        self.inventory = Inventory(self)
        self.inventory.add("Pistol")
        self.inventory.equip(0)

        # Down + revive state. When down the player can't move but CAN
        # shoot a fixed last-stand pistol (M1911) while crawling.
        self.is_down: bool = False
        self.bleed_out_at_ms: int = 0
        self.revive_progress_ms: int = 0  # accumulated by reviver each frame
        self.auto_revive_at_ms: int = 0   # set by Quick Revive on go_down
        self.quick_revive_charges: int = 0
        from game.weapons.weapon import Weapon
        self.last_stand_weapon: Weapon = Weapon(self, "M1911")

    @property
    def max_health(self) -> float:
        return self.modifiers.apply("max_health", self._base_health)

    @property
    def speed(self) -> float:
        return self.modifiers.apply("speed", PLAYER_SPEED)

    def tile_position(self):
        return self.pos // TILE_SIZE

    def update(self, snap=None):
        """Caller can pass a pre-fetched InputState. If omitted, polls
        the input source. Scene passes the snapshot in so it can route
        scene-level events ("interact") elsewhere first."""
        if snap is None:
            snap = self.input_source.snapshot()
        if self.is_down:
            # Crawling: no movement, but you can still aim + shoot the
            # last-stand pistol (CoD authentic).
            self._update_down_state()
            self._aim(snap.mouse_pos)
            self.last_stand_weapon.update()
            if snap.buttons[0]:
                self.last_stand_weapon.shoot()
            return
        self._movement(snap)
        self._aim(snap.mouse_pos)
        weapon = self.weapon
        if weapon is not None:
            weapon.update()
        self._consume_input_events(snap)
        if snap.buttons[0]:
            self.shoot()

    def _update_down_state(self):
        now = pygame.time.get_ticks()
        # Quick Revive auto-revive comes due before bleed-out.
        if self.auto_revive_at_ms and now >= self.auto_revive_at_ms:
            self.quick_revive_charges -= 1
            self.auto_revive_at_ms = 0
            self.revive()
            return
        if now >= self.bleed_out_at_ms:
            self.is_down = False
            self.health = 0

    def go_down(self):
        from settings import PLAYER_BLEED_OUT_MS
        self.is_down = True
        self.bleed_out_at_ms = pygame.time.get_ticks() + PLAYER_BLEED_OUT_MS
        self.revive_progress_ms = 0
        self.health = 1  # don't quite kill them; PlayState reads is_down
        # Quick Revive: auto-revive in 5 seconds, consumes one charge.
        if self.quick_revive_charges > 0:
            self.auto_revive_at_ms = pygame.time.get_ticks() + 5000

    def revive(self):
        self.is_down = False
        self.bleed_out_at_ms = 0
        self.revive_progress_ms = 0
        self.health = self.max_health * 0.5  # revived at half health

    def _consume_input_events(self, snap: InputState):
        for ev in snap.events:
            if ev == "grenade":
                self.throw_grenade()
            elif ev == "monkey":
                self.throw_monkey_bomb()
            elif ev == "reload":
                if self.weapon is not None:
                    self.weapon.reload()
            elif ev.startswith("switch:"):
                try:
                    self.inventory.equip(int(ev.split(":", 1)[1]))
                except ValueError:
                    pass
            # "interact" is consumed at scene level — ignored here.

    @property
    def weapon(self):
        return self.inventory.equipped

    def _movement(self, snap: InputState):
        from game.systems.input import MOVEMENT_WASD, MOVEMENT_ARROWS
        # If the input includes movement from BOTH schemes, accept either.
        # Lets us run two local players (P1 WASD + P2 arrows) without a
        # per-player input scheme — the snapshot for P2 simply has the
        # arrow keys pressed when held.
        speed = self.speed
        left = snap.is_down(pygame.K_a) or snap.is_down(pygame.K_LEFT)
        right = snap.is_down(pygame.K_d) or snap.is_down(pygame.K_RIGHT)
        up = snap.is_down(pygame.K_w) or snap.is_down(pygame.K_UP)
        down = snap.is_down(pygame.K_s) or snap.is_down(pygame.K_DOWN)
        self.vel.x = (-speed if left else 0) + (speed if right else 0)
        self.vel.y = (-speed if up else 0) + (speed if down else 0)

        if self.vel.y != 0 and self.vel.x != 0:
            length = math.hypot(self.vel.x, self.vel.y)
            self.vel.x = (self.vel.x / length) * speed
            self.vel.y = (self.vel.y / length) * speed

        self.pos += self.vel
        self.hit_box.centerx = self.pos.x
        resolve_wall_collision(self, self.scene.walls, "x")
        resolve_wall_collision(self, self.scene.barb_wire, "x")
        self.hit_box.centery = self.pos.y
        resolve_wall_collision(self, self.scene.walls, "y")
        resolve_wall_collision(self, self.scene.barb_wire, "y")
        self.rect.center = self.hit_box.center

    def _aim(self, world_mouse: tuple[int, int]):
        wx, wy = world_mouse
        rel_x, rel_y = wx - self.pos.x, wy - self.pos.y
        if rel_x == 0 and rel_y == 0:
            return
        self.angle = (180 / math.pi) * -math.atan2(rel_y, rel_x)
        if self.vel.length_squared() > 0.1:
            bob = 4 * math.sin(pygame.time.get_ticks() / 80)
        else:
            bob = 0
        self.image = pygame.transform.rotate(self.original_image, self.angle + bob)
        self.rect = self.image.get_rect(center=self.pos)

    def take_damage(self, amount: float = BULLET_DAMAGE):
        if self.is_down:
            return
        self.health -= amount

    def heal_to_full(self):
        self.health = self.max_health

    def is_dead(self) -> bool:
        return (not self.is_down) and self.health <= 0

    def shoot(self):
        if self.is_down:
            return
        if self.weapon is not None:
            self.weapon.shoot()

    def throw_grenade(self):
        if self.is_down or self.grenade_count <= 0:
            return False
        # Limit grenades-in-flight per player, not globally.
        in_flight = sum(1 for g in self.scene.grenades if getattr(g, "thrower_id", None) == self.player_id)
        if in_flight > 0:
            return False
        from game.entities.grenade import Grenade
        grenade = Grenade(self.scene, self.pos.x, self.pos.y, self.angle)
        grenade.thrower_id = self.player_id
        self.grenade_count -= 1
        return True

    def throw_monkey_bomb(self):
        if self.is_down or self.monkey_bomb_count <= 0:
            return False
        from game.entities.monkey_bomb import MonkeyBomb
        # Place a few tiles in front of the player.
        import math
        rad = math.radians(self.angle)
        offset = 60
        x = self.pos.x + offset * math.cos(rad)
        y = self.pos.y + offset * -math.sin(rad)
        MonkeyBomb(self.scene, x, y, thrower_id=self.player_id)
        self.monkey_bomb_count -= 1
        return True
