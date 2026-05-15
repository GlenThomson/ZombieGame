"""Game-wide constants. Pure data, no pygame state."""
import pygame

vector = pygame.math.Vector2

# Screen
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 1000
FPS_LIMIT = 60
SCREEN_TITLE = "Zombies"

# Grid
TILE_SIZE = 40
GRID_WIDTH = SCREEN_WIDTH // TILE_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // TILE_SIZE

# Player
PLAYER_SPEED = 5
PLAYER_HEALTH = 100
PLAYER_HIT_BOX_SIZE = TILE_SIZE * 0.8
BARREL_OFFSET = vector(12, 12)
STARTING_GRENADES = 4

# Zombie
# Round 1 should be a slow stroll (clearly slower than the player) so the
# player has time to learn the controls. Speed ramps linearly per round
# until it caps; health ramps multiplicatively so late rounds are tough.
ZOMBIE_SPEED_BASE = 1.2           # round 1 walking speed (player runs at 5)
ZOMBIE_SPEED_RAMP_PER_ROUND = 0.15
ZOMBIE_MAX_SPEED = 3.5            # speed cap
ZOMBIE_HEALTH_BASE = 5            # 5 pistol shots to kill on round 1
ZOMBIE_HEALTH_RAMP_PER_ROUND = 0.18  # 18% compounding per round
# Legacy names kept so variant subclasses keep working without churn.
ZOMBIE_SPEED = ZOMBIE_SPEED_BASE
ZOMBIE_HEALTH = ZOMBIE_HEALTH_BASE
ZOMBIE_CHASE_DISTANCE = 300
MAX_ROTATE_SPEED = 5
MAX_ZOMBIES = 100

# Combat
BULLET_DEFAULT_SPEED = 25
BULLET_DAMAGE = 1

# Grenade
GRENADE_SPEED = 7
GRENADE_DURATION = 2000  # ms until explosion
GRENADE_EXPLOSION_RADIUS_TILES = 6  # in player-rect-widths
GRENADE_DAMAGE = 100

# Pickups
PICKUP_DURATION_MS = 8000
PICKUP_DROP_CHANCE = 100  # 1 in N

# Points (CoD economy)
STARTING_POINTS = 500
POINTS_PER_HIT = 10
POINTS_PER_KILL = 50
POINTS_PER_HEADSHOT_HIT = 25     # bonus points on top of POINTS_PER_HIT
HEADSHOT_DAMAGE_MULT = 1.5

# Interaction
INTERACT_KEY_LABEL = "F"
INTERACT_RANGE_PX = 50  # how close player must be to read a prompt

# Doors / wall buys / windows defaults
DOOR_DEFAULT_COST = 750
WALL_BUY_DEFAULT_WEAPON = "Shotgun"
WALL_BUY_BUY_COST = 1500
WALL_BUY_AMMO_COST = 60
WINDOW_PLANK_COUNT = 4
WINDOW_REPAIR_POINTS_PER_PLANK = 10
WINDOW_PLANK_BREAK_INTERVAL_MS = 800  # zombie smashes one plank every N ms

# Perks
PERK_MACHINE_DEFAULT_PERK = "Juggernog"
PERK_MACHINE_BUY_COOLDOWN_MS = 1000  # debounce repeated F presses

# Mystery Box
MYSTERY_BOX_COST = 950
MYSTERY_BOX_SPIN_DURATION_MS = 1500
MYSTERY_BOX_SPIN_FRAME_MS = 90  # weapon name swaps every N ms while spinning

# Pack-a-Punch
PACK_A_PUNCH_COST = 5000
PACK_A_PUNCH_DAMAGE_MULT = 2.5
PACK_A_PUNCH_FIRE_RATE_MULT = 1.2
PACK_A_PUNCH_MAG_MULT = 2.0

# Multiplayer / down + revive
MAX_PLAYERS = 4
PLAYER_BLEED_OUT_MS = 30_000
REVIVE_HOLD_MS = 3_000        # how long teammate must hold F to revive
REVIVE_RANGE_PX = 60
PLAYER_TINTS = (
    None,            # P1: original sprite
    (60, 160, 255),  # P2: blue tint
    (80, 220, 80),   # P3: green tint
    (255, 200, 60),  # P4: yellow tint
)
DEFAULT_HOST_PORT = 50515

# Round
ROUND_SPAWN_WINDOW_SECONDS = 30
ROUND_HEALTH_RAMP_PER_ROUND = 0.1
ZOMBIES_PER_ROUND_MULTIPLIER = 10

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARKGREY = (40, 40, 40)
LIGHTGREY = (100, 100, 100)
RED = (255, 51, 51)
PURPLE = (153, 51, 255)
GOLD = (255, 215, 0)

# Menu palette
MENU_BG = (15, 15, 18)
MENU_BG_ACCENT = (30, 8, 8)
MENU_TITLE = (200, 30, 30)
MENU_TEXT = (220, 220, 220)
MENU_TEXT_DIM = (140, 140, 140)
MENU_HOVER = (255, 90, 50)
