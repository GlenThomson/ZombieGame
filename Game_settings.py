import pygame

vector = pygame.math.Vector2
# screen settings
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 1000
FPS_LIMIT = 60
SCREEN_TITLE = "Zombie"
# grid settings
TILE_SIZE = 40
GRID_WIDTH = SCREEN_WIDTH // TILE_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // TILE_SIZE

# player settings
PLAYER_SPEED = 5
PLAYER_HIT_BOX = pygame.Rect(0, 0, TILE_SIZE * 0.8, TILE_SIZE * 0.8)
BARREL_OFFSET = vector(12, 12)
PLAYER_HEALTH = 100

# zombie settings
ZOMBIE_SPEED = 1.6
ZOMBIE_IMAGE = "images/zombie.png"
MAX_ROTATE_SPEED = 5
ZOMBIE_HEALTH = 10
ZOMBIE_CHASE_DISTANCE =300
ZOMBIE_MAX_SPEED = 2.8
MAX_ZOMBIES = 100

# Color constants
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARKGREY = (40, 40, 40)
LIGHTGREY = (100, 100, 100)
Red = (255, 51, 51)
Purple = (153, 51, 255)

# Gun 1 settings
Pistol_BULLET_SPEED = 25
Pistol_BULLET_SPREAD = 2
Pistol_BULLET_FIRE_RATE = 1
Pistol_BULLET_DAMAGE = 1
Pistol_BULLET_PENATRATION = 3
Pistol_MAGAZINE_SIZE =10
Pistol_RELOAD_TIME = 3

# Gun 2 settings
BULLET_SPEED = 25
BULLET_SPREAD = 10
BULLET_FIRE_RATE = 5
BULLET_DAMAGE = 1
BULLET_PENATRATION = 3
MAGAZINE_SIZE =30
RELOAD_TIME = 3

#greade settings
GRENADE_SPEED = 7  # Adjust as necessary
GRENADE_DURATION = 2000  # Milliseconds until explosion

#Sounds