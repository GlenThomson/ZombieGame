"""Generate assets/images/hellhound.png — a top-down hellhound in a
RUNNING pose: tapered two-part body (chest + hips), legs extended in a
sprint stride, swept-back ears, straight tail, glowing eyes.

Drawn at 4x then smoothscale'd. Run once:
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

# Dark demonic dog: near-black body, warm brown highlights, ember eyes.
OUTLINE = (8, 5, 4)
FUR = (52, 32, 22)
FUR_DARK = (30, 18, 12)
FUR_LIGHT = (96, 62, 40)
FUR_SPINE = (130, 88, 56)
EAR_INNER = (110, 45, 35)
NOSE = (12, 8, 8)
MOUTH = (120, 20, 20)
TEETH = (235, 228, 198)
EYE_GLOW = (255, 100, 25)
EYE_HOT = (255, 235, 190)


def ellipse(surf, cx, cy, w, h, color):
    surf_rect = pygame.Rect(int(cx - w / 2), int(cy - h / 2), int(w), int(h))
    pygame.draw.ellipse(surf, color, surf_rect)


def capsule(surf, p1, p2, width, color):
    pygame.draw.line(surf, color, p1, p2, width)
    pygame.draw.circle(surf, color, p1, width // 2)
    pygame.draw.circle(surf, color, p2, width // 2)


def leg(surf, hip, knee, paw, thickness):
    """Two-segment leg with outline + fill + paw."""
    for pts, w, col in (
        ((hip, knee), thickness + 8, OUTLINE),
        ((knee, paw), thickness + 6, OUTLINE),
        ((hip, knee), thickness, FUR),
        ((knee, paw), thickness - 2, FUR_DARK),
    ):
        capsule(surf, pts[0], pts[1], w, col)
    pygame.draw.circle(surf, OUTLINE, paw, thickness // 2 + 4)
    pygame.draw.circle(surf, FUR_DARK, paw, thickness // 2 + 1)


def main():
    s = pygame.Surface((RENDER, RENDER), pygame.SRCALPHA)
    cy = RENDER // 2
    R = RENDER

    hips = (int(R * 0.30), cy)
    chest = (int(R * 0.56), cy)
    head = (int(R * 0.76), cy)

    # ---------- tail: straight back with a slight upward kink ----------
    tail_pts = [
        (hips[0], cy),
        (int(R * 0.16), cy - int(R * 0.03)),
        (int(R * 0.05), cy - int(R * 0.09)),
    ]
    for w, col in ((26, OUTLINE), (16, FUR), (8, FUR_LIGHT)):
        pygame.draw.lines(s, col, False, tail_pts, w)

    # ---------- legs (under/behind body, sprint stride) ----------
    th = 22
    # hind legs: extended BACK (top one pushed off, bottom mid-stride)
    leg(s, (hips[0] + 8, cy - int(R * 0.10)),
        (hips[0] - int(R * 0.12), cy - int(R * 0.16)),
        (hips[0] - int(R * 0.22), cy - int(R * 0.13)), th)
    leg(s, (hips[0] + 8, cy + int(R * 0.10)),
        (hips[0] - int(R * 0.10), cy + int(R * 0.17)),
        (hips[0] - int(R * 0.20), cy + int(R * 0.15)), th)
    # front legs: reaching FORWARD
    leg(s, (chest[0] - 6, cy - int(R * 0.10)),
        (chest[0] + int(R * 0.10), cy - int(R * 0.17)),
        (chest[0] + int(R * 0.20), cy - int(R * 0.14)), th)
    leg(s, (chest[0] - 6, cy + int(R * 0.10)),
        (chest[0] + int(R * 0.12), cy + int(R * 0.16)),
        (chest[0] + int(R * 0.22), cy + int(R * 0.13)), th)

    # ---------- body: hips smaller, chest bigger, blended ----------
    # outline pass
    ellipse(s, hips[0], cy, R * 0.30 + 12, R * 0.26 + 12, OUTLINE)
    ellipse(s, chest[0], cy, R * 0.34 + 12, R * 0.30 + 12, OUTLINE)
    pygame.draw.polygon(s, OUTLINE, [
        (hips[0], cy - int(R * 0.13) - 6), (chest[0], cy - int(R * 0.15) - 6),
        (chest[0], cy + int(R * 0.15) + 6), (hips[0], cy + int(R * 0.13) + 6),
    ])
    # fur fill
    ellipse(s, hips[0], cy, R * 0.30, R * 0.26, FUR)
    ellipse(s, chest[0], cy, R * 0.34, R * 0.30, FUR)
    pygame.draw.polygon(s, FUR, [
        (hips[0], cy - int(R * 0.13)), (chest[0], cy - int(R * 0.15)),
        (chest[0], cy + int(R * 0.15)), (hips[0], cy + int(R * 0.13)),
    ])
    # flank shading (darker lower flank = light from top-left)
    ellipse(s, hips[0] + 10, cy + int(R * 0.07), R * 0.26, R * 0.10, FUR_DARK)
    # spine highlight strip
    spine_pts = [(hips[0] - int(R * 0.10), cy - 4),
                 (hips[0] + 20, cy - int(R * 0.06)),
                 (chest[0], cy - int(R * 0.07)),
                 (chest[0] + int(R * 0.10), cy - 4)]
    pygame.draw.lines(s, FUR_LIGHT, False, spine_pts, 18)
    pygame.draw.lines(s, FUR_SPINE, False, spine_pts, 8)
    # raised hackles along the spine (spiky fur)
    for i, (px, py) in enumerate(spine_pts[:-1]):
        nx, ny = spine_pts[i + 1]
        for t in (0.25, 0.65):
            bx, by = px + (nx - px) * t, py + (ny - py) * t
            pygame.draw.polygon(s, FUR_DARK, [
                (bx - 7, by + 2), (bx + 1, by - 14), (bx + 9, by + 2)])

    # ---------- head + snout ----------
    ellipse(s, head[0], cy, R * 0.24 + 10, R * 0.24 + 10, OUTLINE)
    ellipse(s, head[0], cy, R * 0.24, R * 0.24, FUR)
    ellipse(s, head[0] - 4, cy - int(R * 0.05), R * 0.16, R * 0.10, FUR_LIGHT)
    # snout wedge
    snout_tip = (int(R * 0.95), cy + 2)
    snout = [
        (head[0] + int(R * 0.05), cy - int(R * 0.085)),
        snout_tip,
        (head[0] + int(R * 0.05), cy + int(R * 0.10)),
    ]
    pygame.draw.polygon(s, OUTLINE, [
        (snout[0][0] - 4, snout[0][1] - 5), (snout_tip[0] + 5, snout_tip[1]),
        (snout[2][0] - 4, snout[2][1] + 5)])
    pygame.draw.polygon(s, FUR, snout)
    # open jaw
    pygame.draw.polygon(s, MOUTH, [
        (head[0] + int(R * 0.10), cy + 1),
        (snout_tip[0] - 10, cy + 1),
        (head[0] + int(R * 0.11), cy + int(R * 0.07)),
    ])
    for i in range(3):
        tx = head[0] + int(R * 0.12) + i * 14
        pygame.draw.polygon(s, TEETH, [
            (tx, cy + 1), (tx + 5, cy + 7), (tx + 10, cy + 1)])
    pygame.draw.circle(s, OUTLINE, (snout_tip[0] - 4, snout_tip[1] - 3), 10)
    pygame.draw.circle(s, NOSE, (snout_tip[0] - 4, snout_tip[1] - 3), 7)

    # ---------- ears: swept back along the head ----------
    for side in (-1, 1):
        base = (head[0] - int(R * 0.02), cy + side * int(R * 0.10))
        tip = (head[0] - int(R * 0.16), cy + side * int(R * 0.20))
        wide = (head[0] + int(R * 0.05), cy + side * int(R * 0.13))
        pygame.draw.polygon(s, OUTLINE, [
            (base[0] - 4, base[1]), (tip[0] - 6, tip[1] + side * 4),
            (wide[0] + 4, wide[1] + side * 4)])
        pygame.draw.polygon(s, FUR_DARK, [base, tip, wide])
        pygame.draw.polygon(s, EAR_INNER, [
            (base[0] - 2, base[1] + side * 2),
            (tip[0] + 6, tip[1]),
            (wide[0] - 4, wide[1])])

    # ---------- glowing eyes ----------
    for side in (-1, 1):
        ex = head[0] + int(R * 0.045)
        ey = cy + side * int(R * 0.065)
        halo = pygame.Surface((56, 56), pygame.SRCALPHA)
        for r, a in ((26, 45), (17, 110), (10, 190), (5, 255)):
            pygame.draw.circle(halo, (*EYE_GLOW, a), (28, 28), r)
        s.blit(halo, (ex - 28, ey - 28))
        pygame.draw.circle(s, EYE_HOT, (ex, ey), 4)

    out = pygame.transform.smoothscale(s, (OUT_SIZE, OUT_SIZE))
    os.makedirs(os.path.join("assets", "images"), exist_ok=True)
    out_path = os.path.join("assets", "images", "hellhound.png")
    pygame.image.save(out, out_path)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
