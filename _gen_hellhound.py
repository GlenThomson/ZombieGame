"""Generate assets/images/hellhound.png — a top-down flaming hellhound.

Inspired by the reference: a fiery orange-red dog silhouette with flame
wisps streaming off the back, top-down view, facing east.

Drawn at 4x then smoothscale'd. Run once:
    python _gen_hellhound.py
"""
import math
import os
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
pygame.init()
pygame.display.set_mode((100, 100))

OUT_SIZE = 64
SCALE = 4
RENDER = OUT_SIZE * SCALE   # 256

# Flame palette — outer cool red, hot yellow core. Built with transparency
# so the flame wisps blend instead of looking like solid orange blobs.
FLAME_OUTER = (110, 20, 10, 255)        # dark red rim
FLAME_RED   = (200, 50, 20, 255)        # red-orange
FLAME_ORANGE = (250, 130, 30, 255)      # bright orange
FLAME_YELLOW = (255, 220, 110, 255)     # hot yellow core
FLAME_WHITE  = (255, 245, 200, 255)
EYE_HOT      = (255, 255, 200, 255)
EYE_RING     = (255, 90, 30, 255)
SHADOW       = (40, 8, 4, 220)


def _flame_blob(surf, cx, cy, w, h, alpha_mul=1.0):
    """Layered ellipses to build a soft flame-like fill: dark outer, red
    middle, orange near the core, yellow hot spot."""
    layers = [
        (1.00, FLAME_OUTER),
        (0.90, FLAME_RED),
        (0.70, FLAME_ORANGE),
        (0.45, FLAME_YELLOW),
        (0.22, FLAME_WHITE),
    ]
    for shrink, color in layers:
        r, g, b, a = color
        a2 = max(0, min(255, int(a * alpha_mul)))
        sw = max(2, int(w * shrink))
        sh = max(2, int(h * shrink))
        rect = pygame.Rect(cx - sw // 2, cy - sh // 2, sw, sh)
        layer = pygame.Surface((sw + 4, sh + 4), pygame.SRCALPHA)
        pygame.draw.ellipse(layer, (r, g, b, a2), pygame.Rect(2, 2, sw, sh))
        surf.blit(layer, (rect.x - 2, rect.y - 2))


def main():
    random.seed(7)
    surf = pygame.Surface((RENDER, RENDER), pygame.SRCALPHA)
    cy = RENDER // 2

    # ---- Trailing flame tendrils (behind body) ----
    # Multiple curved wisps streaming off the back-left.
    tail_origin_x = int(RENDER * 0.32)
    for streak in range(7):
        # Each streak has a slight vertical offset + random curl
        base_y = cy + random.randint(-int(RENDER * 0.10), int(RENDER * 0.10))
        length = int(RENDER * (0.30 + random.random() * 0.18))
        curl = random.uniform(-0.15, 0.15)
        n_blobs = 12
        for i in range(n_blobs):
            t = i / (n_blobs - 1)
            x = tail_origin_x - int(t * length)
            y = base_y + int(math.sin(t * math.pi + curl * 3) * RENDER * 0.05)
            # Shrink + fade as they trail away
            size = int((1 - t) * RENDER * 0.10) + 4
            alpha = 1.0 - t * 0.7
            _flame_blob(surf, x, y, size, size, alpha_mul=alpha)

    # ---- Body — elongated flame-blob ----
    body_cx = int(RENDER * 0.52)
    body_w = int(RENDER * 0.66)
    body_h = int(RENDER * 0.46)
    _flame_blob(surf, body_cx, cy, body_w, body_h)

    # ---- Hind legs — small flame puffs sticking out the back-bottom of body ----
    for sign in (-1, 1):
        lx = int(RENDER * 0.36)
        ly = cy + sign * int(RENDER * 0.26)
        _flame_blob(surf, lx, ly, int(RENDER * 0.22), int(RENDER * 0.30))
        # Paw — small hot dot at the tip
        pygame.draw.circle(surf, FLAME_YELLOW, (lx, ly + sign * int(RENDER * 0.10)), 6)

    # ---- Front legs — same idea, front-bottom of body ----
    for sign in (-1, 1):
        lx = int(RENDER * 0.62)
        ly = cy + sign * int(RENDER * 0.26)
        _flame_blob(surf, lx, ly, int(RENDER * 0.22), int(RENDER * 0.30))
        pygame.draw.circle(surf, FLAME_YELLOW, (lx, ly + sign * int(RENDER * 0.10)), 6)

    # ---- Spine / mane — extra hot streak along the top of the body ----
    mane_pts = [
        (int(RENDER * 0.34), cy - int(RENDER * 0.10)),
        (int(RENDER * 0.50), cy - int(RENDER * 0.18)),
        (int(RENDER * 0.70), cy - int(RENDER * 0.12)),
        (int(RENDER * 0.78), cy - int(RENDER * 0.06)),
    ]
    for px, py in mane_pts:
        _flame_blob(surf, px, py, int(RENDER * 0.18), int(RENDER * 0.18), alpha_mul=0.9)
    # Hot core stripe
    for px, py in mane_pts:
        pygame.draw.circle(surf, FLAME_YELLOW, (px, py + 4), 8)
        pygame.draw.circle(surf, FLAME_WHITE, (px, py + 4), 4)

    # ---- Head — distinct hotter blob at the front-right ----
    head_cx = int(RENDER * 0.78)
    head_w = int(RENDER * 0.30)
    head_h = int(RENDER * 0.34)
    _flame_blob(surf, head_cx, cy + 4, head_w, head_h)

    # ---- Ears — two pointed flame tongues on top of head ----
    for side in (-1, 1):
        base = (head_cx - int(RENDER * 0.04),
                cy + side * int(RENDER * 0.14))
        tip = (head_cx + int(RENDER * 0.02),
               cy + side * int(RENDER * 0.26))
        # Ear flame puff
        _flame_blob(surf, (base[0] + tip[0]) // 2, (base[1] + tip[1]) // 2,
                    int(RENDER * 0.10), int(RENDER * 0.14))
        pygame.draw.circle(surf, FLAME_YELLOW, tip, 5)

    # ---- Snout — narrow flame-tongue pointing east ----
    snout_x = int(RENDER * 0.92)
    snout_y = cy + 2
    _flame_blob(surf, int(RENDER * 0.86), snout_y, int(RENDER * 0.18), int(RENDER * 0.16))
    # Hot tip
    pygame.draw.circle(surf, FLAME_YELLOW, (snout_x, snout_y), 8)
    pygame.draw.circle(surf, FLAME_WHITE, (snout_x, snout_y), 4)

    # ---- Glowing yellow-white eyes — two bright dots on the head ----
    for side in (-1, 1):
        ex = head_cx + int(RENDER * 0.02)
        ey = cy + side * int(RENDER * 0.06)
        # Soft hot halo
        halo = pygame.Surface((48, 48), pygame.SRCALPHA)
        for r, a in ((22, 60), (14, 150), (8, 220), (4, 255)):
            pygame.draw.circle(halo, (255, 220, 100, a), (24, 24), r)
        surf.blit(halo, (ex - 24, ey - 24))
        pygame.draw.circle(surf, EYE_HOT, (ex, ey), 4)
        pygame.draw.circle(surf, EYE_RING, (ex, ey), 4, 1)

    # ---- Inner spine highlight — extra-bright slash along centre of body ----
    for i in range(8):
        x = int(RENDER * 0.42 + i * RENDER * 0.04)
        pygame.draw.circle(surf, FLAME_YELLOW, (x, cy - 6 + (i % 2) * 4), 5)
        pygame.draw.circle(surf, FLAME_WHITE, (x, cy - 6 + (i % 2) * 4), 2)

    # Smoothscale down
    out = pygame.transform.smoothscale(surf, (OUT_SIZE, OUT_SIZE))
    os.makedirs(os.path.join("assets", "images"), exist_ok=True)
    out_path = os.path.join("assets", "images", "hellhound.png")
    pygame.image.save(out, out_path)
    print(f"wrote {out_path} ({OUT_SIZE}x{OUT_SIZE} from {RENDER}x{RENDER} master)")


if __name__ == "__main__":
    main()
