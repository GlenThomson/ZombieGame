"""Procedural perk icons: little soda-bottle vials in each perk's colour
with its initial on the label — replaces the plain coloured-text list on
the HUD. Drawn once per (perk, size) and cached."""
import pygame

_cache: dict[tuple[str, int], pygame.Surface] = {}

# Bottle proportions are defined at this design height and scaled.
_H = 64


def perk_icon(name: str, color: tuple[int, int, int],
              height: int = 34) -> pygame.Surface:
    key = (name, height)
    cached = _cache.get(key)
    if cached is not None:
        return cached

    w, h = int(_H * 0.56), _H
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    cx = w // 2

    dark = tuple(max(0, c - 70) for c in color)
    light = tuple(min(255, c + 80) for c in color)

    # Cap
    pygame.draw.rect(surf, (190, 190, 195),
                     (cx - 7, 0, 14, 7), border_radius=2)
    # Neck
    pygame.draw.rect(surf, dark, (cx - 5, 6, 10, 9))
    # Body (rounded bottle)
    body = pygame.Rect(3, 14, w - 6, h - 17)
    pygame.draw.rect(surf, dark, body.inflate(2, 2), border_radius=8)
    pygame.draw.rect(surf, color, body, border_radius=8)
    # Liquid shine
    pygame.draw.rect(surf, light,
                     (body.x + 3, body.y + 4, 5, body.height - 10),
                     border_radius=3)
    # Label band with the perk's initial
    label = pygame.Rect(body.x + 2, body.y + body.height // 3,
                        body.width - 4, body.height // 3)
    pygame.draw.rect(surf, (18, 18, 22), label, border_radius=4)
    font = pygame.font.Font(None, int(h * 0.34))
    initial = "".join(word[0] for word in name.split()[:2]).upper()
    text = font.render(initial, True, (240, 240, 240))
    surf.blit(text, text.get_rect(center=label.center))

    out_w = max(8, int(w * height / h))
    scaled = pygame.transform.smoothscale(surf, (out_w, height))
    _cache[key] = scaled
    return scaled
