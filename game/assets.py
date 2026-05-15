"""Centralized asset cache. Loads images and sounds once, hands out the
shared instance on subsequent requests. Cuts disk hits per shot/explosion to 1."""
import os
import pygame


_IMAGE_DIR = os.path.join("assets", "images")
_SOUND_DIR = os.path.join("assets", "sounds")

_image_cache: dict[str, pygame.Surface] = {}
_sound_cache: dict[str, pygame.mixer.Sound] = {}


def image(name: str, scale: tuple[int, int] | None = None) -> pygame.Surface:
    """Load an image by filename (relative to assets/images). Cached.

    Pass `scale=(w, h)` to get a pre-scaled copy (also cached separately)."""
    key = name if scale is None else f"{name}@{scale[0]}x{scale[1]}"
    cached = _image_cache.get(key)
    if cached is not None:
        return cached
    path = os.path.join(_IMAGE_DIR, name)
    surf = pygame.image.load(path).convert_alpha()
    if scale is not None:
        surf = pygame.transform.scale(surf, scale)
    _image_cache[key] = surf
    return surf


def sound(name: str) -> pygame.mixer.Sound:
    cached = _sound_cache.get(name)
    if cached is not None:
        return cached
    path = os.path.join(_SOUND_DIR, name)
    snd = pygame.mixer.Sound(path)
    _sound_cache[name] = snd
    return snd
