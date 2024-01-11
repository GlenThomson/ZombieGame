import random
import math
from Game_settings import *
import math
import random
from utility_functions import *

from Game_settings import *

vector = pygame.math.Vector2

def load_explosion_sprites():
    sprite_sheet = pygame.image.load('images/grenade_explosion.png').convert_alpha()
    explosion_frames = []
    for row in range(4):  # 4 rows
        for column in range(4):  # 4 columns
            frame = sprite_sheet.subsurface((column * 64, row * 64, 64, 64))
            frame = pygame.transform.scale(frame, (100, 100))
            explosion_frames.append(frame)
    return explosion_frames


def collide_hit_box(sprite1, sprite2):
    return sprite1.hit_box.colliderect(sprite2.rect)


def wall_collision(sprite, sprite_group, direction):
    collision_boolean = False
    if direction == 'x':
        hits = pygame.sprite.spritecollide(sprite, sprite_group, False, collide_hit_box)
        if hits:
            collision_boolean = True
            if hits[0].rect.centerx > sprite.hit_box.centerx:
                sprite.pos.x = hits[0].rect.left - sprite.hit_box.width / 2.0
            if hits[0].rect.centerx < sprite.hit_box.centerx:
                sprite.pos.x = hits[0].rect.right + sprite.hit_box.width / 2.0
            sprite.vel.x = 0
            sprite.hit_box.centerx = sprite.pos.x
    if direction == 'y':
        hits = pygame.sprite.spritecollide(sprite, sprite_group, False, collide_hit_box)
        if hits:
            collision_boolean = True
            if hits[0].rect.centery > sprite.hit_box.centery:
                sprite.pos.y = hits[0].rect.top - sprite.hit_box.height / 2.0
            if hits[0].rect.centery < sprite.hit_box.centery:
                sprite.pos.y = hits[0].rect.bottom + sprite.hit_box.height / 2.0
            sprite.vel.y = 0
            sprite.hit_box.centery = sprite.pos.y
    return collision_boolean


class Path_node():
    def __init__(self, x, y, player_tile_pos, zombie_tile_pos, G_cost=0):
        # define pathfinding variables
        self.previous_node = None
        self.player_tile_pos = player_tile_pos
        self.zombie_tile_pos = zombie_tile_pos
        self.pos = vector(x, y)
        self.G_cost = G_cost
        self.H_cost = self.calculate_h_cost(player_tile_pos)
        self.F_cost = self.G_cost + self.H_cost

    def set_previous(self, node):
        self.previous_node = node

    def calculate_h_cost(self, target_pos):
        dx = abs(target_pos.x - self.pos.x)
        dy = abs(target_pos.y - self.pos.y)
        return dx + dy

    def __repr__(self):
        return f"({self.F_cost}, {self.pos})"

class Path_Finding():
    def __init__(self, player_tile_pos, zombie_tile_pos, game):
        self.player_tile_pos = player_tile_pos
        self.zombie_tile_pos = zombie_tile_pos
        self.game = game
        self.path = []
        self.current_node = Path_node(zombie_tile_pos.x//TILE_SIZE, zombie_tile_pos.y//TILE_SIZE, player_tile_pos, zombie_tile_pos)
        self.nodes = [self.current_node]
        self.closed_nodes = []  # New list to keep track of evaluated nodes
        self.explored = []  # To store the explored nodes

        self.path_finding()

    def check_next_nodes(self, node):
        detection_range = 1
        frontier_nodes = []
        for x_offset in range(-detection_range, detection_range + 1):
            for y_offset in range(-detection_range, detection_range + 1):
                x = node.pos.x + x_offset
                y = node.pos.y + y_offset
                new_g_cost = node.G_cost + 1

                if x_offset != 0 and y_offset != 0:  # Diagonal movement
                    # Checks for diagonal shortcuts through walls
                    if (x_offset, y_offset) == (-1, -1) and (self.game.grid[int(y)][int(x + 1)] == 1 or self.game.grid[int(y + 1)][int(x)] == 1):
                        continue
                    if (x_offset, y_offset) == (-1, 1) and (self.game.grid[int(y)][int(x + 1)] == 1 or self.game.grid[int(y - 1)][int(x)] == 1):
                        continue
                    if (x_offset, y_offset) == (1, -1) and (self.game.grid[int(y)][int(x - 1)] == 1 or self.game.grid[int(y + 1)][int(x)] == 1):
                        continue
                    if (x_offset, y_offset) == (1, 1) and (self.game.grid[int(y)][int(x - 1)] == 1 or self.game.grid[int(y - 1)][int(x)] == 1):
                        continue

                newnode = Path_node(x, y, node.player_tile_pos, node.zombie_tile_pos, new_g_cost)

                # Checks
                within_bounds = (0 <= x < len(self.game.grid[0])) and (0 <= y < len(self.game.grid))
                not_blocked = self.game.grid[int(y)][int(x)] != 1
                not_visited = not any(existing_node.pos.x == x and existing_node.pos.y == y for existing_node in self.nodes + self.closed_nodes)

                if within_bounds and not_blocked and not_visited:
                    #frontier_nodes.append(newnode)
                    newnode.set_previous(node)
                    self.nodes.append(newnode)
                    self.explored.append(newnode)


    def path_finding(self):
        while self.nodes:
            self.nodes.sort(key=lambda node: node.F_cost)
            current_node = self.nodes.pop(0)  # Take the node with the lowest F_cost
            self.closed_nodes.append(current_node)  # Add the current node to closed nodes
            if current_node.pos == self.player_tile_pos:
                # Reconstruct the path
                temp = current_node
                while temp:
                    self.path.insert(0, temp)
                    temp = temp.previous_node
                return  # Exit the function

            self.check_next_nodes(current_node)

class Zombie(pygame.sprite.Sprite):
    def __init__(self, x, y, game):
        self.groups = game.all_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        # load in the image
        self.image = pygame.image.load(ZOMBIE_IMAGE).convert_alpha()
        self.image = pygame.transform.scale(self.image, (TILE_SIZE, TILE_SIZE))
        self.original_image = self.image.copy()
        # set the cooridiantes
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel = vector(0, 0)
        self.pos = vector(x, y)
        self.angle = 0
        # create the hit box
        self.hit_box = pygame.Rect(0, 0, self.rect.width * 0.7, self.rect.height * 0.7)
        self.hit_box.center = self.rect.center
        self.path_index = 0  # index to traverse the A* path
        self.path = self.update_path()
        self.is_chasing = False  # New flag for chase mode

        # Adjustments based on the current round
        self.round_multiplier = 1 + 0.1 * game.current_round  # increase per round
        self.speed = (ZOMBIE_SPEED + ZOMBIE_SPEED * self.round_multiplier)
        self.health = ZOMBIE_HEALTH * self.round_multiplier

    def update_path(self):
        self.path_obj = Path_Finding(self.game.player.get_tile_location(), self.pos, self.game)
        return self.path_obj.path

    def follow_path(self):
        if self.path and self.path_index < len(self.path):
            next_tile = self.path[self.path_index].pos
            next_node_center = vector((next_tile.x + 0.5) * TILE_SIZE, (next_tile.y + 0.5) * TILE_SIZE)

            # Aim for the center of the tile
            self.aim((next_node_center.x, next_node_center.y))

            # Tile rectangle
            tile_rect = pygame.Rect(next_tile.x * TILE_SIZE, next_tile.y * TILE_SIZE, TILE_SIZE, TILE_SIZE)

            # Check if any part of the zombie is inside the tile rectangle
            if self.hit_box.colliderect(tile_rect):
                self.path_index += 1

                # If zombie reaches the end of its path (close to player), update path again
                if self.path_index == len(self.path):
                    self.path = self.update_path()
                    self.path_index = 0

    # Update method modification
    def update(self, player_pos):
        if self.health<=0:
            self.kill()
        #self.follow_path()  # Now we use follow_path instead of directly aiming at the player
        # Check the distance to the player
        if self.is_close_to_player() and self.has_line_of_sight(player_pos):
            # If close enough, chase the player directly
            if not self.is_chasing:
                self.is_chasing = True
            self.aim(player_pos)
        else:
            # If not close, follow the path
            if self.is_chasing:
                # If just stopped chasing, recalculate the path
                self.is_chasing = False
                self.path = self.update_path()
                self.path_index = 0
            self.follow_path()

    def draw_path(self):
        # Drawing explored nodes in, say, a light red color
        for node in self.path_obj.explored:
            screen_x = node.pos.x * TILE_SIZE + self.game.camera.camera.x
            screen_y = node.pos.y * TILE_SIZE + self.game.camera.camera.y
            pygame.draw.rect(self.game.display, (77, 77, 255), (screen_x, screen_y, TILE_SIZE, TILE_SIZE))

        for node in self.path:
            # Translate world coordinates to screen coordinates
            screen_x = node.pos.x * TILE_SIZE + self.game.camera.camera.x
            screen_y = node.pos.y * TILE_SIZE + self.game.camera.camera.y
            pygame.draw.rect(self.game.display, (0, 0, 255), (screen_x, screen_y, TILE_SIZE, TILE_SIZE))

    def get_tile_location(self):
        return self.pos//TILE_SIZE

    # change the zombies direction to face were it is going
    def aim(self, player_pos, ):
        # Calculate the direction of movement and find the angle
        dx = player_pos[0] - self.pos.x
        dy = player_pos[1] - self.pos.y

        target_angle = math.degrees(math.atan2(dy, dx))

        angle_diff = target_angle - self.angle
        # Adjust for the fact that angles wrap around
        angle_diff = (angle_diff + 180) % 360 - 180

        # Limit the rotation
        if angle_diff > MAX_ROTATE_SPEED:
            angle_diff = MAX_ROTATE_SPEED
        elif angle_diff < -MAX_ROTATE_SPEED:
            angle_diff = -MAX_ROTATE_SPEED

        self.angle += angle_diff
        # calculate the angle based of the player position

        # Rotate the image
        self.image = pygame.transform.rotate(self.original_image, -self.angle)
        self.rect = self.image.get_rect()
        self.rect.center = self.pos
        self.vel.x = self.speed * math.cos(math.radians(self.angle))
        self.vel.y = self.speed * math.sin(math.radians(self.angle))
        self.pos += self.vel
        self.hit_box.centerx = self.pos.x


        if self.is_near_wall():
            wall_collision(self, self.game.walls, 'x')
        self.hit_box.centery = self.pos.y
        if self.is_near_wall():
            wall_collision(self, self.game.walls, 'y')
        self.rect.center = self.hit_box.center
        # Get the grid coordinates of the zombie

    # the purpose of this code is to reduce the computational load of checking for wall collisions, by only checking when near a wall
    def is_near_wall(self):
        # Define a range within which the zombie should check for walls (in grid coordinates)
        detection_range = 1  # Adjust this value as needed

        # Get the grid coordinates of the zombie
        grid_x = int(self.pos.x / TILE_SIZE)
        grid_y = int(self.pos.y / TILE_SIZE)

        # Iterate over neighboring grid cells to check for walls
        for x_offset in range(-detection_range, detection_range + 1):
            for y_offset in range(-detection_range, detection_range + 1):
                x = grid_x + x_offset
                y = grid_y + y_offset

                # Check if the grid cell is within the game grid boundaries
                if 0 <= x < len(self.game.grid[0]) and 0 <= y < len(self.game.grid):
                    # Check if the grid cell contains a wall (with a value of 1)
                    if self.game.grid[y][x] == 1:
                        return True

    def take_damage(self):
        self.health -= 1
        self.game.blood_splatters.add(BloodSplatter(self.game, self.pos, duration=10))
        if self.health <= 0:
            self.game.zombie_kills +=1
            self.game.blood_splatters.add(BloodSplatter(self.game, self.pos, duration=5000))  # Longer effect when dead

                # Determine if a pickup should drop
            if random.randint(1, 2) == 1:  # 1 in 50 chance
                Pickup(self.game, self.rect.x, self.rect.y)

    def is_close_to_player(self):
        distance = self.pos.distance_to(self.game.player.pos)
        return distance < ZOMBIE_CHASE_DISTANCE

    def has_line_of_sight(self, target_pos):
        """Check if there is a direct line of sight to the target position (e.g., the player)."""
        # Define the start and end points
        start = self.pos
        end = target_pos

        # Calculate the step vector for iteration
        step = (end - start).normalize() * TILE_SIZE * 0.5

        # Iterate from start to end, stepping by half a tile each time
        current_pos = vector(start.x, start.y)
        while current_pos.distance_to(end) > TILE_SIZE * 0.5:
            current_pos += step
            # Check if current position is inside a wall
            grid_x, grid_y = int(current_pos.x / TILE_SIZE), int(current_pos.y / TILE_SIZE)
            if self.game.grid[grid_y][grid_x] == 1:  # Assuming 1 represents a wall
                return False  # Line of sight is blocked by a wall
        return True  # No obstruction found

class Player(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.angle = 0
        self.groups = game.bullets
        self.game = game
        self.image = pygame.image.load("images/player.png")
        self.image = pygame.transform.scale(self.image, (TILE_SIZE, TILE_SIZE))
        self.original_image = self.image.copy()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.hit_box = PLAYER_HIT_BOX
        self.hit_box.center = self.rect.center
        # Coordiantes and velocity of player
        self.vel = vector(0, 0)
        self.pos = vector(x, y)
        self.health = PLAYER_HEALTH
        self.grenade_count = 10

    def update(self):
        # update the position of player
        self.movement()
        self.aim()

    def get_tile_location(self):
        return self.pos//TILE_SIZE

    def movement(self):
        # gets the keys pressed
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.vel.x = -PLAYER_SPEED
        elif keys[pygame.K_d]:
            self.vel.x = PLAYER_SPEED
        else:
            self.vel.x = 0

        if keys[pygame.K_w]:
            self.vel.y = -PLAYER_SPEED
        elif keys[pygame.K_s]:
            self.vel.y = PLAYER_SPEED
        else:
            self.vel.y = 0

        # keeps diagonal movement same speed as vertical and sideways
        if self.vel.y != 0 and self.vel.x != 0:
            length = math.sqrt(self.vel.x ** 2 + self.vel.y ** 2)
            self.vel.x = (self.vel.x / length) * PLAYER_SPEED
            self.vel.y = (self.vel.y / length) * PLAYER_SPEED

        # update postions
        self.pos += self.vel
        self.hit_box.centerx = self.pos.x
        wall_collision(self, self.game.walls, 'x')
        wall_collision(self, self.game.barb_wire, 'x')
        self.hit_box.centery = self.pos.y
        wall_collision(self, self.game.walls, 'y')
        wall_collision(self, self.game.barb_wire, 'y')
        self.rect.center = self.hit_box.center


    def aim(self):
        self.angle = 0
        # Get the mouse position and calculate the angle to the mouse
        self.mx, self.my = get_adjusted_mouse_position(self.game.camera.camera.x,self.game.camera.camera.y)
        self.rel_x, self.rel_y = self.mx - self.pos.x , self.my - self.pos.y
        self.angle = (180 / math.pi) * -math.atan2(self.rel_y, self.rel_x)
        # Rotate the image and set the new rect
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect()
        self.rect.center = self.pos

    def take_damage(self):
        self.health -= BULLET_DAMAGE

    # Function to draw the health bar
    def draw_health_bar(self):
        # Calculate the width of the health bar based on the current health
        bar_width = int(150 * (self.health / PLAYER_HEALTH))
        bar_height = 20
        x = SCREEN_WIDTH -200
        y = 10

        # Draw the background of the health bar
        pygame.draw.rect(self.game.display, (255, 0, 0), (x, y, 150, bar_height))  # Red background

        # Draw the actual health bar on top of the background
        pygame.draw.rect(self.game.display, (0, 255, 0), (x, y, bar_width, bar_height))  # Green health

    def is_dead(self):
        return self.health <= 0


class Wall(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.walls
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = x * TILE_SIZE
        self.rect.y = y * TILE_SIZE

class Barb_wire(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.barb_wire
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = x * TILE_SIZE
        self.rect.y = y * TILE_SIZE

class Bullet(pygame.sprite.Sprite):
    def __init__(self, game, x, y, direction, angle):
        self.groups = game.all_sprites
        self.game = game
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.image = pygame.Surface((3, 3))
        self.image.fill((255, 215, 0))
        self.rect = self.image.get_rect()
        # self.rect.center = (x, y)
        self.speed = BULLET_SPEED
        self.angle = math.radians(angle)
        self.spread = random.uniform(-BULLET_SPREAD, BULLET_SPREAD)
        self.hit_count = 0
        # calculate the speed in x and y direction
        self.vel = vector(direction.x * self.speed, direction.y * self.speed).rotate(self.spread)

        # need to keep seperate float position as rect only takes ints, also ads bullet spread
        self.pos = vector(x, y) + BARREL_OFFSET.rotate(-math.degrees(self.angle))
        # sets up the hitbox of the bullet
        self.hit_box = pygame.Rect(0, 0, self.rect.width, self.rect.height)
        self.hit_box.center = self.rect.center

    def update(self):
        # add the speed to the x and y postion
        self.pos += self.vel
        # updte the rect position and check for collisions
        self.hit_box.centerx = self.pos.x
        self.hit_box.centery = self.pos.y
        self.rect.center = self.hit_box.center
        if pygame.sprite.spritecollideany(self, self.game.walls):
            self.kill()



class BloodSplatter(pygame.sprite.Sprite):
    def __init__(self, game, pos, duration=500):
        self.groups = game.blood_splatters
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pygame.image.load('images/bloodSplatter.png').convert_alpha()
        self.original_pos = pos
        self.rect = self.image.get_rect(center=self.original_pos +self.game.camera.pos)
        self.spawn_time = pygame.time.get_ticks()
        self.duration = duration
        self.trancparancy = 200

    def update(self):
        self.trancparancy -=1
        self.rect.center= self.original_pos + self.game.camera.pos
        current_time = pygame.time.get_ticks()
        self.image.set_alpha(max(self.trancparancy, 0))  # Ensure alpha doesn't go below 0
        if current_time - self.spawn_time > self.duration:
            self.kill()


class Pickup(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.pick_ups
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.pickup_type = random.choice(["instant_kill", "nuke_pickup", "nuke_pickup"])
        self.game = game
        self.image = pygame.image.load("images/"+self.pickup_type+".png")
        self.image = pygame.transform.scale(self.image, (TILE_SIZE, TILE_SIZE))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.spawn_time = pygame.time.get_ticks()
        self.duration = 8000  # Duration before disappearing
        self.flicker_frequency = 1000  # Flicker every second initially
        self.next_flicker_time = self.spawn_time + self.flicker_frequency
        self.visible = True


    def update(self):
        current_time = pygame.time.get_ticks()
        time_left = self.duration - (current_time - self.spawn_time)

        # Increase flickering frequency as time runs out
        if time_left < 8000:  # Start increasing flicker frequency halfway through
            self.flicker_frequency = max(100, self.flicker_frequency - 3)  # Increase frequency, minimum 100ms

        #makes it so its not invisible to long
        if self.visible == False:
            self.next_flicker_time *= 0.9

        # Toggle visibility for flicker effect
        if current_time >= self.next_flicker_time:
            self.visible = not self.visible
            self.next_flicker_time = current_time + self.flicker_frequency
            self.image.set_alpha(255 if self.visible else 0)

        # Check for expiration
        if current_time - self.spawn_time > self.duration:
            self.kill()

        # Check for collision with the player
        if pygame.sprite.collide_rect(self, self.game.player):
            self.picked_up()
            self.kill()

    def picked_up(self):
        # Implement effect based on pickup type
        if self.pickup_type == "instant_kill":
            self.instant_kill = pygame.mixer.Sound('Sounds/instant_kill.mp3')
            self.instant_kill.play()
            for zombie in self.game.zombies:
                zombie.health = 1

        elif self.pickup_type == "nuke_pickup":
            self.kaboom_sound = pygame.mixer.Sound('Sounds/kaboom.mp3')
            self.nuke_sound = pygame.mixer.Sound('Sounds/nuke_sound.mp3')
            self.kaboom_sound.play()
            self.nuke_sound.play()
            for zombie in self.game.zombies:
                zombie.kill()

        elif self.pickup_type == "ray_gun":
            for zombie in self.game.zombies:
                zombie.kill()

class Grenade(pygame.sprite.Sprite):
    def __init__(self, x, y, direction, game):
        self.groups = game.all_sprites, game.grenades
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pygame.image.load('images/grenade.png').convert_alpha()  # Load your grenade image
        self.image = pygame.transform.scale(self.image, (20, 20))  # Scale to appropriate size
        self.rect = self.image.get_rect()
        self.pos = vector(x, y)
        self.rect.center = self.pos
        self.vel = vector(GRENADE_SPEED, 0).rotate(-direction)
        self.spawn_time = pygame.time.get_ticks()
        self.delay = 0
        self.damping = 0.6  # Damping factor (80% of velocity retained after bounce)
        self.time_between_ground_bounce = 30
        self.time_before_next_bounce = self.time_between_ground_bounce
        self.grenade_bounce_sound = pygame.mixer.Sound('Sounds/Grenade Bounce.mp3')
        self.grenade_explosion_sound = pygame.mixer.Sound('Sounds/grenade_explosion.mp3')
        self.explosion_frames = load_explosion_sprites()
        self.exploding = False
        self.explosion_radius = 100
        self.frame = 0
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 50

    def update(self):
        if self.exploding:
            now = pygame.time.get_ticks()
            if now - self.last_update > self.frame_rate:
                self.last_update = now
                self.frame += 1
                print(self.frame)
                if self.frame >= len(self.explosion_frames):
                    self.kill()  # End the explosion by removing the sprite
                    return
                center = self.rect.center
                self.image = self.explosion_frames[self.frame]
                self.rect = self.image.get_rect()
                self.rect.center = center

        self.delay -=1
        self.pos += self.vel
        self.rect.center = self.pos
        if self.vel.length() < 1:  # If velocity is very low, stop the grenade
            self.vel = pygame.math.Vector2(0, 0)
        else:
            self.check_collision()
            self.time_before_next_bounce -=1

        current_time = pygame.time.get_ticks()

        if current_time - self.spawn_time > GRENADE_DURATION and self.exploding == False:
            self.explode()

        # Slow down grenade over time on the ground
        if self.vel != (0,0) and self.time_before_next_bounce<=0:
            self.grenade_bounce_sound.play()
            self.time_between_ground_bounce *= 0.6
            self.time_before_next_bounce = self.time_between_ground_bounce
            self.vel *= self.damping

    #checks for collisions with walls to bounce of
    def check_collision(self):
        for wall in self.game.walls:
            if self.rect.colliderect(wall.rect):
                self.bounce(wall)

    #bounce of the walls
    def bounce(self, wall):
        self.grenade_bounce_sound.play()
        if self.delay <= 0: # slight delay to prevent grenades getting stuck in the wall
            self.delay =2
            # Check collision direction and reverse velocity accordingly
            if abs(self.rect.left - wall.rect.right) < 20 or abs(self.rect.right - wall.rect.left) < 20:
                self.vel.x *= -1
            if abs(self.rect.top - wall.rect.bottom) < 20 or abs(self.rect.bottom - wall.rect.top) < 20:
                self.vel.y *= -1
            # Apply damping factor after collision
            self.vel *= self.damping

    def explode(self):
        # Define the size of the explosion area (e.g., twice the size of the grenade)
        explosion_size = 6 * self.rect.width  # You can adjust this size as needed

        # Create a new rect for the explosion centered on the grenade's current position
        explosion_rect = pygame.Rect(0, 0, explosion_size, explosion_size)
        explosion_rect.center = self.rect.center
        # Handle explosion effect here
        self.grenade_explosion_sound.play()
        self.exploding = True

        for zombie in self.game.zombies:
            if explosion_rect.colliderect(zombie.rect):
                zombie.health -=100
