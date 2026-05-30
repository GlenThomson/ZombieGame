"""Generate assets/images/hellhound.png — a top-down hellhound sprite.

Stylised brown dog version, with the legs tucked under the body instead
of sticking straight out the sides (the previous version's "legs poking
out" silhouette looked off when rotated in game).

Drawn at 4x then smoothscale'd down. Run once:
    python _gen_hellhound.py
"""
import math
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
pygame.init()
pygame.display.set_mode((100, 100))

OUT_SIZE = 64
SCALE = 4
RENDER = OUT_SIZE * SCALE   # 256

# ---- Style: stylised cartoony, very bold outlines ----
# The dog FACES +X (east), so head/snout point right.
# Bold colours + outlines so the silhouette stays readable at the
# ~32 px size the game renders it at.

OUTLINE = (12, 8, 6)                # near-black
FUR = (98, 50, 28)                  # rich warm brown
FUR_DARK = (54, 26, 14)
FUR_LIGHT = (148, 84, 46)
BELLY = (74, 38, 22)
EAR_INNER = (180, 70, 60)           # pinkish hellhound ear
NOSE = (16, 8, 8)
TEETH = (245, 235, 200)
MOUTH = (130, 22, 22)
TONGUE = (210, 60, 80)
EYE_GLOW = (255, 110, 30)
EYE_HOT = (255, 240, 200)


def ellipse_o(surf, cx, cy, w, h, fill, outline_width=10):
    """Filled ellipse with a fat outline."""
    rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
    pygame.draw.ellipse(surf, OUTLINE, rect.inflate(outline_width, outline_width))
    pygame.draw.ellipse(surf, fill, rect)


def main():
    surf = pygame.Surface((RENDER, RENDER), pygame.SRCALPHA)
    cy = RENDER // 2

    # -------- Tail (drawn first so the body covers its base) --------
    tail_pts = []
    for i in range(0, 22):
        t = i / 21
        x = int(RENDER * (0.30 - t * 0.28))
        y = int(cy - math.sin(t * math.pi * 0.9) * RENDER * 0.20
                   - t * RENDER * 0.06)
        tail_pts.append((x, y))
    for layer_w, color in ((18, OUTLINE), (14, FUR_DARK), (10, FUR), (6, FUR_LIGHT)):
        for i in range(len(tail_pts) - 1):
            taper = max(1, int(layer_w * (1 - i / len(tail_pts))))
            pygame.draw.line(surf, color, tail_pts[i], tail_pts[i + 1], taper + 2)

    # -------- Body (slightly wider/taller now that there are no legs
    #          poking out — keeps the overall sprite footprint similar) --
    body_cx = int(RENDER * 0.50)
    body_w = int(RENDER * 0.56)
    body_h = int(RENDER * 0.48)
    ellipse_o(surf, body_cx, cy, body_w, body_h, FUR, outline_width=14)
    # Spine highlight along the top of the back
    pygame.draw.ellipse(
        surf, FUR_LIGHT,
        pygame.Rect(body_cx - int(body_w * 0.38), cy - int(body_h * 0.30),
                    int(body_w * 0.72), int(body_h * 0.34)),
    )
    # Belly shadow underneath
    pygame.draw.ellipse(
        surf, BELLY,
        pygame.Rect(body_cx - int(body_w * 0.32), cy + int(body_h * 0.04),
                    int(body_w * 0.64), int(body_h * 0.30)),
    )

    # -------- Paws: only small darker bumps that just kiss the body
    #          edge so it reads as a four-legged creature without the
    #          legs sticking out as stilts. Two hind + two front. --------
    paw_w = int(RENDER * 0.10)
    paw_h = int(RENDER * 0.08)
    for sign in (-1, 1):
        # Hind paws — just inside the back-quarter of the body
        hpx = int(RENDER * 0.36)
        hpy = cy + sign * int(body_h * 0.46)
        pygame.draw.ellipse(
            surf, FUR_DARK,
            pygame.Rect(hpx - paw_w // 2, hpy - paw_h // 2, paw_w, paw_h),
        )
        # Front paws — just inside the front-quarter of the body
        fpx = int(RENDER * 0.60)
        fpy = cy + sign * int(body_h * 0.46)
        pygame.draw.ellipse(
            surf, FUR_DARK,
            pygame.Rect(fpx - paw_w // 2, fpy - paw_h // 2, paw_w, paw_h),
        )

    # -------- Head — sits clearly to the right of the body --------
    head_cx = int(RENDER * 0.74)
    head_w = int(RENDER * 0.38)
    head_h = int(RENDER * 0.40)
    ellipse_o(surf, head_cx, cy + 4, head_w, head_h, FUR, outline_width=14)
    # Forehead shine
    pygame.draw.ellipse(
        surf, FUR_LIGHT,
        pygame.Rect(head_cx - int(head_w * 0.30), cy - int(head_h * 0.28),
                    int(head_w * 0.60), int(head_h * 0.32)),
    )

    # -------- Ears — bold pointy triangles atop the head, going up & out --
    for side in (-1, 1):
        base_a = (head_cx - int(head_w * 0.16),
                  cy + side * int(head_h * 0.38))
        base_b = (head_cx + int(head_w * 0.08),
                  cy + side * int(head_h * 0.30))
        tip = (head_cx - int(head_w * 0.22),
               cy + side * int(head_h * 0.78))
        outline = [(p[0], p[1]) for p in (base_a, tip, base_b)]
        for d in range(-6, 7, 2):
            shifted = [(p[0] + d, p[1] + side * d) for p in outline]
            pygame.draw.polygon(surf, OUTLINE, shifted)
        pygame.draw.polygon(surf, FUR_DARK, outline)
        inner = [
            ((base_a[0] + base_b[0]) // 2, (base_a[1] + base_b[1]) // 2),
            (tip[0] + 8, tip[1] - side * 4),
            (base_b[0] - 8, base_b[1] + side * 6),
        ]
        pygame.draw.polygon(surf, EAR_INNER, inner)

    # -------- Snout & teeth --------
    snout_back_x = head_cx + int(head_w * 0.22)
    snout_tip_x = int(RENDER * 0.96)
    snout_back_y_top = cy - int(head_h * 0.20)
    snout_back_y_bot = cy + int(head_h * 0.28)
    snout_pts = [
        (snout_back_x, snout_back_y_top),
        (snout_tip_x - 12, cy + 2),
        (snout_back_x, snout_back_y_bot),
    ]
    for d in range(-6, 7, 2):
        pygame.draw.polygon(surf, OUTLINE,
                            [(p[0], p[1] + d) for p in snout_pts])
    pygame.draw.polygon(surf, FUR, snout_pts)
    mouth_y = cy + 6
    pygame.draw.polygon(surf, MOUTH, [
        (snout_back_x + 20, mouth_y - 18),
        (snout_tip_x - 24, mouth_y - 2),
        (snout_back_x + 20, mouth_y + 14),
    ])
    pygame.draw.ellipse(surf, TONGUE,
                        pygame.Rect(snout_back_x + 30, mouth_y - 4, 36, 18))
    for i in range(3):
        tx = snout_back_x + 32 + i * 22
        pygame.draw.polygon(surf, TEETH, [
            (tx, mouth_y - 18),
            (tx + 10, mouth_y - 4),
            (tx - 6, mouth_y - 6),
        ])
    for i in range(2):
        tx = snout_back_x + 42 + i * 24
        pygame.draw.polygon(surf, TEETH, [
            (tx, mouth_y + 14),
            (tx + 10, mouth_y + 2),
            (tx - 6, mouth_y + 4),
        ])
    pygame.draw.circle(surf, OUTLINE, (snout_tip_x - 8, cy - 2), 14)
    pygame.draw.circle(surf, NOSE, (snout_tip_x - 8, cy - 2), 11)
    pygame.draw.circle(surf, (90, 50, 50), (snout_tip_x - 12, cy - 4), 3)

    # -------- Glowing red eyes --------
    for side in (-1, 1):
        ex = head_cx + int(head_w * 0.05)
        ey = cy + side * int(head_h * 0.20)
        ellipse_o(surf, ex, ey, 30, 22, FUR_DARK, outline_width=4)
        halo = pygame.Surface((80, 80), pygame.SRCALPHA)
        for r, a in ((36, 50), (24, 110), (14, 200), (7, 250)):
            pygame.draw.circle(halo, (*EYE_GLOW, a), (40, 40), r)
        surf.blit(halo, (ex - 40, ey - 40))
        pygame.draw.circle(surf, EYE_HOT, (ex, ey), 5)
        pygame.draw.circle(surf, OUTLINE, (ex, ey), 5, 2)

    out = pygame.transform.smoothscale(surf, (OUT_SIZE, OUT_SIZE))
    os.makedirs(os.path.join("assets", "images"), exist_ok=True)
    out_path = os.path.join("assets", "images", "hellhound.png")
    pygame.image.save(out, out_path)
    print(f"wrote {out_path} ({OUT_SIZE}x{OUT_SIZE} from {RENDER}x{RENDER} master)")


if __name__ == "__main__":
    main()
