"""Small standalone helpers."""
import sys
import pygame


def quit_application():
    pygame.quit()
    sys.exit()


def adjusted_mouse_position(offset_x=0, offset_y=0):
    mx, my = pygame.mouse.get_pos()
    return mx - offset_x, my - offset_y
