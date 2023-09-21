import pygame
import random
import math
from Game_settings import *

class Zombie(pygame.sprite.Sprite):
    def __init__(self, x, y,game):
        super().__init__()
        self.game= game
        #load in the image
        self.image = pygame.image.load("images/zombie.png")
        self.image = pygame.transform.scale(self.image,(TILE_SIZE,TILE_SIZE))
        self.original_image = self.image.copy()
        #set the cooridiantes
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.speed = ZOMBIE_SPEED
        #need to keep seperate float position as rect only takes ints
        self.x = float(x)
        self.y = float(y)
        self.count = 0
        self.vel_x = 0
        self.vel_y = 0

    #Might need speeding up code may be inefficient
    def collide_wall(self,direction):
        if direction == 'x':
            hits = pygame.sprite.spritecollide(self, self.game.walls, False)
            if hits:
                if self.vel_x > 0:
                    self.x = hits[0].rect.left - self.rect.width
                if self.vel_x < 0:
                    self.x = hits[0].rect.right
                self.vel_x = 0
                self.rect.x = self.x
        if direction == 'y':
            hits = pygame.sprite.spritecollide(self, self.game.walls, False)
            if hits:
                if self.vel_y > 0:
                    self.y = hits[0].rect.top - self.rect.height
                if self.vel_y < 0:
                    self.y = hits[0].rect.bottom
                self.vel_y = 0
                self.rect.y = self.y

    #update
    def update(self, player_pos):
        #set zombie position
        self.aim(player_pos)


    #change the zombies direction to face were it is going
    def aim(self, player_pos,):
        # Calculate the direction of movement and find the angle
        dx = player_pos[0] - self.x
        dy = player_pos[1] - self.y
        #calculate the angle based of the player position
        self.angle = math.degrees(math.atan2(dy, dx))
        self.image = pygame.transform.rotate(self.original_image, -self.angle)  # Rotate the image
        self.vel_x = self.speed * math.cos(math.radians(self.angle))
        self.vel_y = self.speed * math.sin(math.radians(self.angle))
        # move the zombie in the direction it is facing
        self.x += self.vel_x
        self.y += self.vel_y
        self.rect.x = self.x
        self.collide_wall('x')
        self.rect.y = self.y
        self.collide_wall('y')


class Player(pygame.sprite.Sprite):
    def __init__(self,game,x,y):
        self.groups = game.bullets
        self.game = game
        self.image = pygame.image.load("images/player.png")
        self.image = pygame.transform.scale(self.image,(TILE_SIZE,TILE_SIZE))
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill((255, 55, 55))
        self.original_image = self.image.copy()
        self.rect = self.image.get_rect(topleft=(x, y))
        #Coordiantes and velocity of player
        self.x = x
        self.y = y
        self.rect.x = x
        self.rect.y = y
        self.vel_x = 0
        self.vel_y = 0

    def update(self):
        #update the position of player
        self.movement()
        #self.aim()

    def movement(self):
        #gets the keys pressed
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.vel_x = -PLAYER_SPEED
        elif keys[pygame.K_RIGHT]:
            self.vel_x = PLAYER_SPEED
        else:
            self.vel_x = 0

        if keys[pygame.K_UP]:
            self.vel_y = -PLAYER_SPEED
        elif keys[pygame.K_DOWN]:
            self.vel_y = PLAYER_SPEED
        else:
            self.vel_y = 0

        #keeps diagonal movement same speed as vertical and sideways
        if self.vel_y!=0 and self.vel_x!=0 :
            length = math.sqrt(self.vel_x**2 + self.vel_y**2)
            self.vel_x = (self.vel_x / length) * PLAYER_SPEED
            self.vel_y = (self.vel_y / length) * PLAYER_SPEED

        #update postions
        self.x += self.vel_x
        self.y += self.vel_y
        self.rect.x = self.x
        self.collide_wall('x')
        self.rect.y = self.y
        self.collide_wall('y')


    def aim(self):
        self.angle = 0
        # Get the mouse position and calculate the angle to the mouse
        self.mx, self.my = pygame.mouse.get_pos()
        self.rel_x, self.rel_y = self.mx - self.x - self.rect.width // 2, self.my - self.y - self.rect.height // 2
        self. angle = (180 / math.pi) * -math.atan2(self.rel_y, self.rel_x)
        # Rotate the image and set the new rect
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=(self.x, self.y))

    #Might need speeding up code may be inefficient
    def collide_wall(self,direction):
        if direction == 'x':
            hits = pygame.sprite.spritecollide(self, self.game.walls, False)
            if hits:
                if self.vel_x > 0:
                    self.x = hits[0].rect.left - self.rect.width
                if self.vel_x < 0:
                    self.x = hits[0].rect.right
                self.vel_x = 0
                self.rect.x = self.x
        if direction == 'y':
            hits = pygame.sprite.spritecollide(self, self.game.walls, False)
            if hits:
                if self.vel_y > 0:
                    self.y = hits[0].rect.top - self.rect.height
                if self.vel_y < 0:
                    self.y = hits[0].rect.bottom
                self.vel_y = 0
                self.rect.y = self.y


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