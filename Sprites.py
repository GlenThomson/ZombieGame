import pygame
import random
import math
from Game_settings import *
vector = pygame.math.Vector2

def collide_hit_box(sprite1,sprite2):
    return sprite1.hit_box.colliderect(sprite2.rect)

def collide_wall(sprite,direction):
    if direction == 'x':

        hits = pygame.sprite.spritecollide(sprite, sprite.game.walls, False,collide_hit_box)
        if hits:
            print("hhhhhhh")
            if sprite.vel.x > 0:
                sprite.pos.x = hits[0].rect.left - sprite.hit_box.width/2.0
            if sprite.vel.x < 0:
                sprite.pos.x = hits[0].rect.right + sprite.hit_box.width/2.0
            sprite.vel.x = 0
            sprite.hit_box.centerx = sprite.pos.x
    if direction == 'y':
        hits = pygame.sprite.spritecollide(sprite, sprite.game.walls, False,collide_hit_box)
        if hits:
            print("pppp")
            if sprite.vel.y > 0:
                sprite.pos.y = hits[0].rect.top - sprite.hit_box.height/2.0
            if sprite.vel.y < 0:
                sprite.pos.y = hits[0].rect.bottom + sprite.hit_box.height/2.0
            sprite.vel.y = 0
            sprite.hit_box.centery = sprite.pos.y

class Zombie(pygame.sprite.Sprite):
    def __init__(self, x, y,game):
        self.groups = game.all_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        #load in the image
        self.image = pygame.image.load("images/zombie.png")
        self.image = pygame.transform.scale(self.image,(TILE_SIZE,TILE_SIZE))
        self.original_image = self.image.copy()
        #set the cooridiantes
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = ZOMBIE_SPEED
        #need to keep seperate float position as rect only takes ints
        self.vel = vector(0,0)
        self.pos = vector(x,y)
        self.hit_box = ZOMBIE_HIT_BOX
        self.hit_box.center = self.rect.center

    #update
    def update(self, player_pos):
        #set zombie position
        self.aim(player_pos)


    #change the zombies direction to face were it is going
    def aim(self, player_pos,):
        # Calculate the direction of movement and find the angle
        dx = player_pos[0] - self.pos.x
        dy = player_pos[1] - self.pos.y
        #calculate the angle based of the player position
        self.angle = math.degrees(math.atan2(dy, dx))
        self.image = pygame.transform.rotate(self.original_image, -self.angle)  # Rotate the image
        self.vel.x = self.speed * math.cos(math.radians(self.angle))
        self.vel.y = self.speed * math.sin(math.radians(self.angle))
        # move the zombie in the direction it is facing
        self.pos += (self.vel.x,self.vel.y)
        self.hit_box.centerx = self.pos.x
        collide_wall(self,'x')
        self.hit_box.centery = self.pos.y
        collide_wall(self,'y')
        self.rect.center = self.hit_box.center



class Player(pygame.sprite.Sprite):
    def __init__(self,game,x,y):
        self.groups = game.all_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.angle = 0
        self.groups = game.bullets
        self.game = game
        self.image = pygame.image.load("images/player.png")
        self.image = pygame.transform.scale(self.image,(TILE_SIZE,TILE_SIZE))
        self.original_image = self.image.copy()
        self.rect = self.image.get_rect(topleft=(x, y))
        self.hit_box = PLAYER_HIT_BOX
        self.hit_box.center = self.rect.center
        print(self.hit_box.center)
        #Coordiantes and velocity of player
        self.vel = vector(0,0)
        self.pos = vector(x,y)


    def update(self):
        #update the position of player
        self.aim()

        self.movement()


    def movement(self):
        #gets the keys pressed
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

        #keeps diagonal movement same speed as vertical and sideways
        if self.vel.y!=0 and self.vel.x!=0 :
            length = math.sqrt(self.vel.x**2 + self.vel.y**2)
            self.vel.x = (self.vel.x / length) * PLAYER_SPEED
            self.vel.y = (self.vel.y / length) * PLAYER_SPEED

        #update postions
        self.pos += self.vel
        print("hel")
        print(self.hit_box.center)
        self.hit_box.centerx = self.pos.x
        collide_wall(self,'x')
        self.hit_box.centery = self.pos.y
        collide_wall(self,'y')
        self.rect.center = self.hit_box.center

    def aim(self):
        self.angle = 0
        # Get the mouse position and calculate the angle to the mouse
        self.mx, self.my = pygame.mouse.get_pos()
        self.rel_x, self.rel_y = self.mx - self.pos.x - self.rect.width // 2, self.my - self.pos.y - self.rect.height // 2
        self. angle = (180 / math.pi) * -math.atan2(self.rel_y, self.rel_x)
        # Rotate the image and set the new rect
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect()
        self.rect.center = self.pos


class Wall(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.walls
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill((222,111,222))
        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = x * TILE_SIZE
        self.rect.y = y * TILE_SIZE


class Bullet(pygame.sprite.Sprite):
    def __init__(self,game, x, y,direction, angle):
        self.groups = game.all_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.image = pygame.Surface((10, 10))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = 1
        self.angle = math.radians(angle)
        #calculate the speed in x and y direction
        self.vel = vector(direction.x * self.speed,direction.y * self.speed)
        #need to keep seperate float position as rect only takes ints
        self.pos = vector(x,y)


    def update(self):
        #add the speed to the x and y postion
        self.pos += self.vel
        #update the rect position
        self.rect.x = int(self.pos.x)
        self.rect.y = int(self.pos.y)
