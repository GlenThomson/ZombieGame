"""Centralized input snapshot. Built once per frame so multiple systems can
read the same state without re-polling pygame."""
import pygame
from dataclasses import dataclass


@dataclass
class InputSnapshot:
    keys: pygame.key.ScancodeWrapper
    mouse_buttons: tuple[bool, ...]
    mouse_pos: tuple[int, int]


def snapshot() -> InputSnapshot:
    return InputSnapshot(
        keys=pygame.key.get_pressed(),
        mouse_buttons=pygame.mouse.get_pressed(),
        mouse_pos=pygame.mouse.get_pos(),
    )
