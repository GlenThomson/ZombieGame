import random
import tkinter as tk
from tkinter import simpledialog

import colors
import pygame

from Game_settings import *
from Map import Camera
from Sprites import Zombie, Wall, Player, Bullet,Barb_wire,Pickup,Grenade
from Toolbar import Toolbar
from utility_functions import *

vector = pygame.math.Vector2
pygame.init()

class game_main():
    def __init__(self):
        self.clock = pygame.time.Clock()
        self.display = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        # set up the different mode variables
        self.mode = "MENU"
        # creates tool bar
        self.toolbar = Toolbar(self)
        self.map_maker_mode = MapMakerMode(self)
        self.map_width, self.map_height = 0, 0
        self.grid = []
        self.background_image= None
        self.current_round = 1
        self.zombies_to_spawn = 10  # Initial number of zombies
        self.spawn_timer = 0
        self.time_between_spawns = 30 / self.zombies_to_spawn  # Time in seconds between each spawn
        self.zombie_kills = 0
        self.font = pygame.font.Font(None, 36)
        self.gold_color = (255, 215, 0)
        self.end_round_sound = pygame.mixer.Sound('Sounds/end_round_sound.mp3')
        self.gun_sound = pygame.mixer.Sound('Sounds/machinegunloopwav-14862.mp3')
        self.bullet_casing_sound = pygame.mixer.Sound('Sounds/Gun Shell Fall2 Wood - QuickSounds.com.mp3')
        self.gun_sound_playing = False
        #initialize varialbes for round displayed each new round
        self.round_text_countdown =500
        self.display_round_text = False
        self.round_text_font = pygame.font.Font(None, 100)

        #
    # Main game loop
    def run_game(self):
        while True:
            if self.mode == "MENU":
                self.menu_events()
                self.draw_menu()
            elif self.mode == "GAME_OVER":
                self.draw_game_over()
            elif self.mode == "PLAY":
                if self.player.is_dead():
                    self.mode = "GAME_OVER"
                self.update()
                self.events()
                self.draw()
            elif self.mode == "MAPMAKING":
                self.map_maker_mode.events()
                self.map_maker_mode.draw()

            self.clock.tick(FPS_LIMIT)

    def update(self):
        self.camera.update(self.player)
        self.bullets.update()
        self.pick_ups.update()
        self.zombies.update((self.player.pos.x, self.player.pos.y))
        self.player.update()
        self.blood_splatters.update()
        self.grenades.update()
        self.sprite_interactions()
        self.manage_zombie_spawning()


    def initialize_game(self):
        # set up the different sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.zombies = pygame.sprite.Group()
        self.walls = pygame.sprite.Group()
        self.barb_wire = pygame.sprite.Group()
        self.blood_splatters = pygame.sprite.Group()
        self.pick_ups = pygame.sprite.Group()
        self.grenades = pygame.sprite.Group()
        self.player = Player(self, TILE_SIZE *20, TILE_SIZE*20)

        # creates all the walls
        for row, tiles in enumerate(self.grid):
            for col, tile in enumerate(tiles):
                if tile == 1:
                    Wall(self, col, row)
                elif tile == 2:
                    Barb_wire(self, col, row)
        # sets the map width and height
        self.map_width = len(self.grid[0]) * TILE_SIZE
        self.map_height = len(self.grid) * TILE_SIZE
        # creates the camera that will move around the map
        self.camera = Camera(self.map_width, self.map_height, self)

        if self.background_image_path:
            self.background_image = pygame.image.load(self.background_image_path).convert()
        else:
            self.background_image = None  # Fallback if no background image is set


    def draw(self):  # draws everything to the screen
        pygame.display.set_caption("{:.2f}".format(self.clock.get_fps()))
        self.display.fill(WHITE)
        self.display.blit(self.background_image, (0+self.camera.camera.x, 0+self.camera.camera.y))
        self.blood_splatters.draw(self.display)
        #self.draw_grid(self.display, self.grid)
        for sprite in self.all_sprites:
            if sprite not in self.walls and sprite not in self.barb_wire:
                self.display.blit(sprite.image, self.camera.apply(sprite))
        self.toolbar.draw()
        self.player.draw_health_bar()
        #for zombie in self.zombies:
            #zombie.draw_path()
        for sprite in self.zombies:
            self.display.blit(sprite.image, self.camera.apply(sprite))
        # Draw round number and kills
        round_text = self.font.render(f"Round: {self.current_round}", True, self.gold_color )
        kills_text = self.font.render(f"Kills: {self.zombie_kills}", True, self.gold_color)
        # Positioning the text on the screen
        self.display.blit(round_text, (10, SCREEN_HEIGHT-100))  # Position at top-left corner
        self.display.blit(kills_text, (10, SCREEN_WIDTH-50))  # Position below the round number        #self.draw_health_bar()
        #draws the new round number in the middle of the screen
        if self.round_text_countdown>0:
            self.draw_round_text()

        pygame.display.flip()

    def draw_grid(self, display, grid):  # draws the grid to the screen
        map_width = len(grid[0]) * TILE_SIZE
        map_height = len(grid) * TILE_SIZE
        for x_pos in range(0, map_width, TILE_SIZE):
            pygame.draw.line(display, BLACK, (x_pos, 0), (x_pos, map_height), 2)
        for y_pos in range(0, map_height, TILE_SIZE):
            pygame.draw.line(display, BLACK, (0, y_pos), (map_width, y_pos), 2)

    def draw_round_text(self):
        # Calculate the alpha based on the time elapsed
        self.round_text_countdown -= 1
        # Create the text surface
        text_surface = self.round_text_font.render(f"Round {self.current_round}", True, (255, 0, 0))
        text_surface.set_alpha(self.round_text_countdown)
        # Position the text
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        # Draw the text
        self.display.blit(text_surface, text_rect)


    def events(self):  # checks for any events e.g(quit or player move)
        for event in pygame.event.get():
            self.toolbar.handle_events(event)  # checks for tool bar events
            if event.type == pygame.QUIT:
                quit_application()
                # code for firing the gun
        mouse_state = pygame.mouse.get_pressed()
        if mouse_state[0]:
            # Getting the direction from the player to the mouse
            mx, my = get_adjusted_mouse_position(self.camera.camera.x,self.camera.camera.y)
            dx, dy = mx - self.player.rect.centerx, my - self.player.rect.centery
            # Calculating angle in degrees
            direction = pygame.math.Vector2(dx, dy).normalize()
            # Creating a new bullet and adding it to the bullets group
            new_bullet = Bullet(self, self.player.rect.centerx, self.player.rect.centery, direction, self.player.angle)
            self.bullets.add(new_bullet)

        if mouse_state[0] and self.gun_sound_playing==False:
            self.gun_sound.play()
            self.gun_sound_playing = True
        elif not mouse_state[0] and self.gun_sound_playing ==True:
            self.bullet_casing_sound.play()
            self.gun_sound.stop()
            self.gun_sound_playing = False
        #checkks for grenade throw and throws it if player has grenades
        keys = pygame.key.get_pressed()
        if keys[pygame.K_g]:
            direction = self.player.angle
            if self.player.grenade_count >0 and len(self.grenades) ==0 :
                grenade = Grenade(self.player.pos.x, self.player.pos.y, direction, self)
                self.player.grenade_count -=1

    def sprite_interactions(self):
        for zombie in self.zombies:
            for bullet in self.bullets:
                #checks if zombies get hit by a bullet
                if zombie.hit_box.colliderect(bullet.hit_box):
                    zombie.take_damage()
                    #if bullet has hit its max zombies it dissapears
                    if bullet.hit_count >= BULLET_PENATRATION:
                        bullet.kill()

            #slows down the zombie if touching player and takes health off the player
            if zombie.hit_box.colliderect(self.player.hit_box):
                zombie.speed = float(ZOMBIE_SPEED*0.1)
                self.player.take_damage()
            else:
                zombie.speed = ZOMBIE_SPEED

    def zombie_spawn(self):
        edge = random.choice(["top", "bottom", "left", "right"])

        if edge in ["top", "bottom"]:
            x = random.randint(2, self.map_width // TILE_SIZE - 3) * TILE_SIZE
            y = 2 * TILE_SIZE if edge == "top" else (self.map_height // TILE_SIZE - 3) * TILE_SIZE
        else:  # left or right
            y = random.randint(2, self.map_height // TILE_SIZE - 3) * TILE_SIZE
            x = 2 * TILE_SIZE if edge == "left" else (self.map_width // TILE_SIZE - 3) * TILE_SIZE
        self.zombies.add(Zombie(x, y, self))

    def manage_zombie_spawning(self):
        self.spawn_timer += self.clock.get_time() / 1000  # Convert milliseconds to seconds
        if self.spawn_timer >= self.time_between_spawns and self.zombies_to_spawn >0:
            self.spawn_timer = 0  # Reset timer
            self.zombie_spawn()
            self.zombies_to_spawn -= 1

        elif self.zombies_to_spawn == 0 and len(self.zombies) ==0 :
            self.new_round()

    def new_round(self):
        # Prepare for the next round
        self.current_round += 1
        self.player.grenade_count = 2
        self.round_text_countdown = 500
        self.end_round_sound.play()
        self.zombies_to_spawn = int(self.current_round* 10)  # Increase by 50%
        self.time_between_spawns = 30 / self.zombies_to_spawn


    def draw_game_over(self):
        self.display.fill((0, 0, 0))  # Black background for game over screen
        self.toolbar.draw()
        font = pygame.font.Font(None, 74)
        text = font.render('Game Over', True, (255, 0, 0))  # Red Game Over text
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.display.blit(text, text_rect)
        pygame.display.flip()
        for event in pygame.event.get():
            self.toolbar.handle_events(event)  # checks for tool bar events
            if event.type == pygame.QUIT:
                quit_application()

    # MENU CODE
    def draw_menu(self):
        # set up text and font
        game.display.fill(WHITE)
        font = pygame.font.Font(None, 74)
        title_text = font.render('My Game', True, BLACK)
        font = pygame.font.Font(None, 50)
        play_text = font.render('Play', True, BLACK)
        map_maker_text = font.render('Map Maker', True, BLACK)
        # Calculate positions
        title_pos = (SCREEN_WIDTH // 2 - title_text.get_width() // 2, SCREEN_HEIGHT // 4 - title_text.get_height() // 2)
        play_pos = (SCREEN_WIDTH // 2 - play_text.get_width() // 2, SCREEN_HEIGHT // 2 - play_text.get_height() // 2)
        map_maker_pos = (
        SCREEN_WIDTH // 2 - map_maker_text.get_width() // 2, SCREEN_HEIGHT // 2 + map_maker_text.get_height() + 100)

        # Draw text on screen at calculated positions
        game.display.blit(title_text, title_pos)
        game.display.blit(play_text, play_pos)
        game.display.blit(map_maker_text, map_maker_pos)

        # Creating rectangles for button collision
        self.play_rect = pygame.Rect(play_pos[0], play_pos[1], play_text.get_width(), play_text.get_height())
        self.map_maker_rect = pygame.Rect(map_maker_pos[0], map_maker_pos[1], map_maker_text.get_width(),
                                          map_maker_text.get_height())
        pygame.display.flip()

    # checks for players decision in the menu
    def menu_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit_application()
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                # Check if user clicks on one of the choices using the rectangles created in draw_menu
                if self.play_rect.collidepoint((x, y)):

                    map_data = load_map_from_file()  # This now returns a dictionary
                    if map_data:  # Check if map data was successfully loaded
                        self.grid = map_data['grid']  # Assign grid
                        self.background_image_path = map_data.get('background_image_path')  # Get background image path
                        self.mode = "PLAY"
                        self.initialize_game()

                        pass
                elif self.map_maker_rect.collidepoint((x, y)):
                    self.mode = "MAPMAKING"
                    self.map_maker_mode.get_map_size()
                    self.map_maker_mode.create_outer_wall()


"""Class Map making mode for player to make there own map designs, which will 
include choses map size adding walls zombie spawners pick ups ect
"""


class MapMakerMode:
    def __init__(self, game):
        self.game = game
        self.map_width = 0
        self.map_height = 0
        self.grid = []
        self.offset = vector(0, 0)  # Scrolling offset
        self.scroll_speed = 5  # Speed of scrolling
        self.background_image_path = None  # Path to the background image
        self.item_number = self.game.toolbar.pop_up_menu.item_number

    def select_background_image(self):
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        self.background_image_path = filedialog.askopenfilename(initialdir=os.getcwd(), title="Select Background Image", filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
        root.destroy()
        if self.background_image_path:  # Load the image if a file was selected
            self.background_image = pygame.image.load(self.background_image_path).convert()

    # asks the user the size of the map they wish to create
    def get_map_size(self):
        self.select_background_image()  # Call the function to select background image
        self.map_width = self.background_image.get_width()
        self.map_height = self.background_image.get_height()
        self.grid = [[0 for _ in range(self.map_width // TILE_SIZE)] for _ in range(self.map_height // TILE_SIZE)]


    # this creates walls on out side of the map
    def create_outer_wall(self):
        grid_height = len(self.grid)  # Number of rows
        grid_width = len(self.grid[0])  # Number of columns

        for y in range(grid_height):
            for x in range(grid_width):
                if x == 0 or y == 0 or x == grid_width - 1 or y == grid_height - 1:
                    self.grid[y][x] = 1  # Wall

    # draws everything to the display
    def draw(self):
        if self.background_image:
            self.game.display.blit(self.background_image, (0+self.offset.x, 0+self.offset.y))
        else:
            self.game.display.fill(WHITE)  # Fallback color if no image is selected
        self.game.draw_grid(self.game.display, self.grid)
        self.draw_items()
        self.game.toolbar.draw()
        pygame.display.flip()

    def screen_scrolling(self):
        # ... [rest of your event handling code]
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.offset.x = min(self.offset.x + self.scroll_speed, 0)  # Do not scroll past the left edge
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.offset.x = max(self.offset.x - self.scroll_speed,
                                -self.map_width + SCREEN_WIDTH)  # Do not scroll past the right edge
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.offset.y = min(self.offset.y + self.scroll_speed, 0)  # Do not scroll past the top edge
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.offset.y = max(self.offset.y - self.scroll_speed,
                                -self.map_height + SCREEN_HEIGHT)  # Do not scroll past the bottom edge

    def events(self):
        for event in pygame.event.get():
            game.toolbar.handle_events(event)  # checks for tool bar events
            if event.type == pygame.QUIT:
                quit_application()
            selected_option = self.game.toolbar.pop_up_menu.handle_event(event)
            #updates the item selected from the pop up menue to place on map
            if selected_option:
                self.item_number=self.game.toolbar.pop_up_menu.item_number
        # checks for screen scrolling
        self.screen_scrolling()
        # looks for mouse clicks on grid to add or delete walls
        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]:  # If left mouse button is pressed
            #gets mouse ajusted for screen scrolling
            x, y = get_adjusted_mouse_position(int(self.offset.x),int(self.offset.y))
            grid_x, grid_y = x // TILE_SIZE, y // TILE_SIZE
            self.grid[grid_y][grid_x] = self.item_number  # Set to wall
        elif mouse_pressed[2]:  # If right mouse button is pressed
            x, y = get_adjusted_mouse_position(int(self.offset.x),int(self.offset.y))
            grid_x, grid_y = x // TILE_SIZE, y // TILE_SIZE
            self.grid[grid_y][grid_x] = 0  # Set to empty


    def save_map(self):
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        map_name = simpledialog.askstring("Input", "Please enter the map name:")

        map_data = {
            'grid': self.grid,
            'background_image_path': self.background_image_path  # Save the path as a string
        }

        with open(f"maps/{map_name}.pkl", 'wb') as f:
            pickle.dump(map_data, f)

    # loops through the walls if the wall is a 1 then it draws a wall
    def draw_items(self):
        for y, row in enumerate(self.grid):
            for x, tile in enumerate(row):
                if tile == 1:
                    pygame.draw.rect(self.game.display, BLACK, (
                    (x * TILE_SIZE) + self.offset.x, (y * TILE_SIZE) + self.offset.y, TILE_SIZE, TILE_SIZE))
                elif tile == 2:
                    pygame.draw.rect(self.game.display, LIGHTGREY, (
                    (x * TILE_SIZE) + self.offset.x, (y * TILE_SIZE) + self.offset.y, TILE_SIZE, TILE_SIZE))
                elif tile == 3:
                    pygame.draw.rect(self.game.display, WHITE, (
                        (x * TILE_SIZE) + self.offset.x, (y * TILE_SIZE) + self.offset.y, TILE_SIZE, TILE_SIZE))

# Creates the game object and starts the programe
game = game_main()
game.run_game()
