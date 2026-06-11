"""Generate the monkey bomb assets:
  assets/images/monkey_bomb_0.png   cymbals apart
  assets/images/monkey_bomb_1.png   cymbals together (clash)
  assets/sounds/monkey_jingle.wav   wind-up toy music-box loop (~4.5s)

Run once: python _gen_monkey.py
"""
import math
import os
import struct
import wave

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
pygame.init()
pygame.display.set_mode((100, 100))

OUT = 64
R = OUT * 4  # 256 master

FUR = (110, 72, 40)
FUR_DARK = (74, 46, 24)
FUR_LIGHT = (150, 104, 62)
FACE = (224, 190, 150)
BELLY = (205, 172, 132)
EYE = (24, 16, 10)
FEZ = (190, 40, 40)
FEZ_DARK = (130, 24, 24)
CYMBAL = (235, 195, 60)
CYMBAL_EDGE = (160, 120, 20)
CYMBAL_SHINE = (255, 240, 170)
OUTLINE = (20, 12, 8)


def _ellipse(s, cx, cy, w, h, color):
    pygame.draw.ellipse(s, color, pygame.Rect(int(cx - w/2), int(cy - h/2), int(w), int(h)))


def draw_monkey(clash: bool) -> pygame.Surface:
    """Top-down-ish cymbal monkey facing 'up' the screen: round body,
    head with ears + fez, arms out to the sides holding cymbals."""
    s = pygame.Surface((R, R), pygame.SRCALPHA)
    cx, cy = R // 2, R // 2

    # arms + cymbals FIRST (under the body edges)
    # cymbal distance from body: apart vs together (clash = near front)
    if clash:
        cym_dx, cym_dy = int(R * 0.16), -int(R * 0.16)
    else:
        cym_dx, cym_dy = int(R * 0.30), -int(R * 0.04)
    for side in (-1, 1):
        arm_start = (cx + side * int(R * 0.14), cy - int(R * 0.02))
        cym = (cx + side * cym_dx, cy + cym_dy)
        pygame.draw.line(s, OUTLINE, arm_start, cym, 30)
        pygame.draw.line(s, FUR_DARK, arm_start, cym, 22)
        # cymbal disc
        _ellipse(s, cym[0], cym[1], R * 0.20 + 8, R * 0.20 + 8, OUTLINE)
        _ellipse(s, cym[0], cym[1], R * 0.20, R * 0.20, CYMBAL)
        _ellipse(s, cym[0], cym[1], R * 0.20, R * 0.20, CYMBAL)
        pygame.draw.circle(s, CYMBAL_EDGE, cym, int(R * 0.10), 3)
        _ellipse(s, cym[0] - R * 0.03, cym[1] - R * 0.03, R * 0.06, R * 0.04, CYMBAL_SHINE)
        pygame.draw.circle(s, CYMBAL_EDGE, cym, 6)

    # clash spark between cymbals
    if clash:
        spark_y = cy + cym_dy
        for ang in range(0, 360, 45):
            a = math.radians(ang)
            x2 = cx + math.cos(a) * R * 0.10
            y2 = spark_y + math.sin(a) * R * 0.10
            pygame.draw.line(s, (255, 255, 200), (cx, spark_y), (x2, y2), 5)

    # legs (small stubs at the bottom)
    for side in (-1, 1):
        _ellipse(s, cx + side * int(R * 0.12), cy + int(R * 0.26),
                 R * 0.13, R * 0.10, OUTLINE)
        _ellipse(s, cx + side * int(R * 0.12), cy + int(R * 0.26),
                 R * 0.10, R * 0.075, FUR_DARK)

    # body
    _ellipse(s, cx, cy + int(R * 0.08), R * 0.34 + 10, R * 0.38 + 10, OUTLINE)
    _ellipse(s, cx, cy + int(R * 0.08), R * 0.34, R * 0.38, FUR)
    _ellipse(s, cx, cy + int(R * 0.12), R * 0.20, R * 0.24, BELLY)

    # tail curling from behind
    tail = [(cx + int(R * 0.10), cy + int(R * 0.26)),
            (cx + int(R * 0.28), cy + int(R * 0.32)),
            (cx + int(R * 0.34), cy + int(R * 0.22))]
    pygame.draw.lines(s, OUTLINE, False, tail, 16)
    pygame.draw.lines(s, FUR, False, tail, 9)

    # head
    head_y = cy - int(R * 0.20)
    # ears
    for side in (-1, 1):
        _ellipse(s, cx + side * int(R * 0.20), head_y, R * 0.14 + 6, R * 0.14 + 6, OUTLINE)
        _ellipse(s, cx + side * int(R * 0.20), head_y, R * 0.14, R * 0.14, FUR)
        _ellipse(s, cx + side * int(R * 0.20), head_y, R * 0.07, R * 0.07, FACE)
    _ellipse(s, cx, head_y, R * 0.27 + 8, R * 0.25 + 8, OUTLINE)
    _ellipse(s, cx, head_y, R * 0.27, R * 0.25, FUR)
    _ellipse(s, cx, head_y - int(R * 0.04), R * 0.16, R * 0.10, FUR_LIGHT)
    # face
    _ellipse(s, cx, head_y + int(R * 0.03), R * 0.18, R * 0.15, FACE)
    # eyes (wide crazy toy eyes)
    for side in (-1, 1):
        pygame.draw.circle(s, (250, 250, 245),
                           (cx + side * int(R * 0.055), head_y), int(R * 0.035))
        pygame.draw.circle(s, EYE,
                           (cx + side * int(R * 0.055), head_y + 2), int(R * 0.018))
    # grin
    pygame.draw.arc(s, EYE, pygame.Rect(cx - int(R * 0.07), head_y + int(R * 0.015),
                                        int(R * 0.14), int(R * 0.09)),
                    math.pi + 0.4, 2 * math.pi - 0.4, 4)
    # fez hat
    fez_y = head_y - int(R * 0.14)
    pygame.draw.polygon(s, OUTLINE, [
        (cx - int(R * 0.10) - 4, fez_y + 6),
        (cx + int(R * 0.10) + 4, fez_y + 6),
        (cx + int(R * 0.07) + 4, fez_y - int(R * 0.10) - 4),
        (cx - int(R * 0.07) - 4, fez_y - int(R * 0.10) - 4)])
    pygame.draw.polygon(s, FEZ, [
        (cx - int(R * 0.10), fez_y + 4),
        (cx + int(R * 0.10), fez_y + 4),
        (cx + int(R * 0.07), fez_y - int(R * 0.10)),
        (cx - int(R * 0.07), fez_y - int(R * 0.10))])
    pygame.draw.line(s, FEZ_DARK, (cx - int(R * 0.08), fez_y),
                     (cx + int(R * 0.08), fez_y), 4)
    pygame.draw.circle(s, (255, 220, 90), (cx, fez_y - int(R * 0.10)), 7)

    return pygame.transform.smoothscale(s, (OUT, OUT))


def gen_jingle():
    """Wind-up music-box loop: plinky sine notes with decay, ~4.4s."""
    sr = 22050
    # A cheerful toy melody (frequencies, beats) — roughly "pop goes the weasel" feel
    notes = [
        (523, .5), (659, .5), (784, .5), (659, .5),
        (523, .5), (784, .5), (1047, 1.0),
        (880, .5), (784, .5), (659, .5), (784, .5),
        (523, 1.0), (392, .5), (523, 1.0),
    ]
    tempo = 0.32  # seconds per beat
    samples = []
    for freq, beats in notes:
        n = int(sr * beats * tempo)
        for i in range(n):
            t = i / sr
            env = math.exp(-t * 7.0)
            # bell-ish: fundamental + faint 3rd harmonic
            v = (math.sin(2 * math.pi * freq * t) * 0.7
                 + math.sin(2 * math.pi * freq * 3 * t) * 0.15) * env * 0.5
            samples.append(int(max(-1, min(1, v)) * 28000))
    with wave.open(os.path.join("assets", "sounds", "monkey_jingle.wav"), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes(struct.pack("<" + "h" * len(samples), *samples))
    print(f"wrote monkey_jingle.wav ({len(samples)/sr:.1f}s)")


if __name__ == "__main__":
    for i, clash in enumerate((False, True)):
        img = draw_monkey(clash)
        path = os.path.join("assets", "images", f"monkey_bomb_{i}.png")
        pygame.image.save(img, path)
        print(f"wrote {path}")
    gen_jingle()
