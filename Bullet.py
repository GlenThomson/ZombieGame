import pygame
import math

#  Bullet Class
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y,direction, angle):
        super().__init__()
        self.image = pygame.Surface((10, 10))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.speed = 1
        self.angle = math.radians(angle)
        #calculate the speed in x and y direction
        self.vx = direction.x * self.speed
        self.vy = direction.y * self.speed
        #need to keep seperate float position as rect only takes ints
        self.pos_x = float(x)
        self.pos_y = float(y)


    def update(self):
        #add the speed to the x and y postion
        self.pos_x += self.vx
        self.pos_y += self.vy
        #update the rect position
        self.rect.x = int(self.pos_x)
        self.rect.y = int(self.pos_y)


    # Step 6: Checking Bullet Collisions (you would do this in your main game loop or in a dedicated method for handling collisions)

    # Step 7: Drawing Bullets (Bullets will automatically be drawn in your existing draw method since they are added to all_sprites group)

