"""Generate 40x40 floor + visible-wall tiles. Each tile is mostly seamless
so it can be repeated across a grid without ugly seams."""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter

TILE = 40
OUT = "assets/images/tiles"
os.makedirs(OUT, exist_ok=True)


def add_noise(img: Image.Image, intensity: int = 12, seed: int = 0) -> Image.Image:
    rng = random.Random(seed)
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            n = rng.randint(-intensity, intensity)
            r, g, b = px[x, y][:3]
            px[x, y] = (
                max(0, min(255, r + n)),
                max(0, min(255, g + n)),
                max(0, min(255, b + n)),
            )
    return img


# ---------------- FLOORS ----------------

def floor_concrete() -> Image.Image:
    img = Image.new("RGB", (TILE, TILE), (95, 95, 100))
    add_noise(img, intensity=15, seed=1)
    d = ImageDraw.Draw(img)
    # A few subtle cracks
    rng = random.Random(2)
    for _ in range(2):
        x0, y0 = rng.randint(2, TILE - 2), rng.randint(2, TILE - 2)
        for _ in range(rng.randint(3, 6)):
            x1 = max(0, min(TILE - 1, x0 + rng.randint(-5, 5)))
            y1 = max(0, min(TILE - 1, y0 + rng.randint(-5, 5)))
            d.line((x0, y0, x1, y1), fill=(60, 60, 65), width=1)
            x0, y0 = x1, y1
    return img


def floor_concrete_bloodied() -> Image.Image:
    """Darker variant with a blood smear — used as accent tile."""
    img = floor_concrete()
    d = ImageDraw.Draw(img)
    cx = random.Random(3).randint(10, 30)
    cy = random.Random(4).randint(10, 30)
    for r, alpha in ((10, 70), (6, 90), (3, 110)):
        # Pillow doesn't blend RGB with alpha directly; emulate with a darker red.
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(110 - alpha // 4, 25, 25))
    return img


def floor_wood() -> Image.Image:
    img = Image.new("RGB", (TILE, TILE), (115, 75, 38))
    d = ImageDraw.Draw(img)
    plank_h = TILE // 4  # 10px planks
    rng = random.Random(11)
    for i in range(4):
        y = i * plank_h
        shade = rng.randint(-12, 12)
        color = (
            max(0, min(255, 130 + shade)),
            max(0, min(255, 80 + shade)),
            max(0, min(255, 42 + shade)),
        )
        d.rectangle((0, y, TILE, y + plank_h - 1), fill=color)
        d.line((0, y + plank_h - 1, TILE, y + plank_h - 1), fill=(50, 30, 12))
        # Knot
        if rng.random() < 0.4:
            kx = rng.randint(4, TILE - 5)
            ky = y + rng.randint(2, plank_h - 3)
            d.ellipse((kx - 2, ky - 2, kx + 2, ky + 2), fill=(70, 40, 18))
    add_noise(img, intensity=8, seed=12)
    return img


def floor_brick() -> Image.Image:
    img = Image.new("RGB", (TILE, TILE), (100, 50, 38))
    d = ImageDraw.Draw(img)
    rng = random.Random(20)
    BW, BH = 20, 10  # 2 wide, 4 tall — fits exactly in 40x40
    for row_idx in range(0, 4):
        y = row_idx * BH
        offset = (BW // 2) if row_idx % 2 else 0
        for col_idx in range(-1, 3):  # extra to cover edges
            x = col_idx * BW + offset
            shade = rng.randint(-15, 15)
            color = (
                max(0, min(255, 130 + shade)),
                max(0, min(255, 60 + shade)),
                max(0, min(255, 45 + shade)),
            )
            d.rectangle((x + 1, y + 1, x + BW - 2, y + BH - 2), fill=color)
            # Mortar
            d.rectangle((x, y, x, y + BH), fill=(40, 30, 20))
            d.rectangle((x, y, x + BW, y), fill=(40, 30, 20))
    return img


def floor_metal() -> Image.Image:
    """Diamond plate metal grating."""
    img = Image.new("RGB", (TILE, TILE), (75, 75, 80))
    d = ImageDraw.Draw(img)
    # Diamond bumps in a grid
    for row in range(0, TILE + 8, 8):
        for col in range(0, TILE + 8, 8):
            cx = col + (4 if (row // 8) % 2 else 0)
            d.polygon(
                [(cx, row - 2), (cx + 3, row + 1), (cx, row + 4), (cx - 3, row + 1)],
                fill=(110, 110, 115), outline=(40, 40, 45),
            )
    add_noise(img, intensity=6, seed=30)
    return img


def floor_dirt() -> Image.Image:
    img = Image.new("RGB", (TILE, TILE), (100, 75, 50))
    add_noise(img, intensity=18, seed=40)
    d = ImageDraw.Draw(img)
    rng = random.Random(41)
    # Pebbles
    for _ in range(8):
        x = rng.randint(2, TILE - 3)
        y = rng.randint(2, TILE - 3)
        c = rng.randint(60, 90)
        d.ellipse((x, y, x + 2, y + 2), fill=(c, c - 10, c - 20))
    return img


def floor_asphalt() -> Image.Image:
    img = Image.new("RGB", (TILE, TILE), (45, 45, 50))
    add_noise(img, intensity=12, seed=50)
    d = ImageDraw.Draw(img)
    rng = random.Random(51)
    # A few fine cracks
    for _ in range(2):
        x0, y0 = rng.randint(0, TILE - 1), rng.randint(0, TILE - 1)
        for _ in range(rng.randint(3, 5)):
            x1 = max(0, min(TILE - 1, x0 + rng.randint(-6, 6)))
            y1 = max(0, min(TILE - 1, y0 + rng.randint(-6, 6)))
            d.line((x0, y0, x1, y1), fill=(20, 20, 25), width=1)
            x0, y0 = x1, y1
    return img


def floor_carpet() -> Image.Image:
    img = Image.new("RGB", (TILE, TILE), (95, 25, 30))
    add_noise(img, intensity=9, seed=60)
    d = ImageDraw.Draw(img)
    # Thin weave lines
    for y in range(0, TILE, 2):
        d.line((0, y, TILE, y), fill=(70, 18, 22), width=1)
    return img


def floor_grass() -> Image.Image:
    img = Image.new("RGB", (TILE, TILE), (40, 65, 30))
    rng = random.Random(70)
    px = img.load()
    for y in range(TILE):
        for x in range(TILE):
            n = rng.randint(-12, 12)
            r, g, b = px[x, y]
            px[x, y] = (max(0, r + n), max(0, g + n), max(0, b + n))
    d = ImageDraw.Draw(img)
    for _ in range(20):
        x = rng.randint(0, TILE - 1)
        y = rng.randint(0, TILE - 1)
        d.line((x, y, x, y - 2), fill=(60, 100, 40), width=1)
    return img


# ---------------- WALLS ----------------

def wall_brick() -> Image.Image:
    img = Image.new("RGB", (TILE, TILE), (120, 60, 40))
    d = ImageDraw.Draw(img)
    rng = random.Random(80)
    BW, BH = 20, 10
    for row_idx in range(0, 4):
        y = row_idx * BH
        offset = (BW // 2) if row_idx % 2 else 0
        for col_idx in range(-1, 3):
            x = col_idx * BW + offset
            shade = rng.randint(-15, 15)
            color = (
                max(0, min(255, 160 + shade)),
                max(0, min(255, 80 + shade)),
                max(0, min(255, 55 + shade)),
            )
            d.rectangle((x + 1, y + 1, x + BW - 2, y + BH - 2), fill=color)
            d.rectangle((x, y, x, y + BH), fill=(50, 30, 20))
            d.rectangle((x, y, x + BW, y), fill=(50, 30, 20))
    # darker top edge for depth
    d.rectangle((0, 0, TILE, 2), fill=(20, 10, 5))
    return img


def wall_concrete() -> Image.Image:
    img = Image.new("RGB", (TILE, TILE), (130, 130, 135))
    add_noise(img, intensity=10, seed=90)
    d = ImageDraw.Draw(img)
    # Block lines
    BH = 13
    for y in (BH, 2 * BH):
        d.line((0, y, TILE, y), fill=(60, 60, 65))
    for col in (0, TILE // 2):
        for offset in (0, BH):
            d.line((col + offset, offset, col + offset, offset + BH), fill=(60, 60, 65))
    d.rectangle((0, 0, TILE, 2), fill=(30, 30, 35))
    return img


def wall_wood() -> Image.Image:
    img = Image.new("RGB", (TILE, TILE), (150, 100, 55))
    d = ImageDraw.Draw(img)
    rng = random.Random(100)
    # Vertical planks
    for px in range(0, TILE, 8):
        shade = rng.randint(-15, 15)
        color = (
            max(0, min(255, 165 + shade)),
            max(0, min(255, 105 + shade)),
            max(0, min(255, 55 + shade)),
        )
        d.rectangle((px, 0, px + 7, TILE), fill=color)
        d.line((px + 7, 0, px + 7, TILE), fill=(70, 45, 20))
    add_noise(img, intensity=6, seed=101)
    d.rectangle((0, 0, TILE, 2), fill=(40, 25, 10))
    return img


def wall_metal() -> Image.Image:
    img = Image.new("RGB", (TILE, TILE), (90, 90, 95))
    d = ImageDraw.Draw(img)
    # Vertical corrugations
    for x in range(0, TILE, 6):
        d.rectangle((x, 0, x + 3, TILE), fill=(115, 115, 120))
        d.rectangle((x + 3, 0, x + 6, TILE), fill=(80, 80, 85))
    # Bolts at corners
    for cx, cy in ((4, 4), (TILE - 5, 4), (4, TILE - 5), (TILE - 5, TILE - 5)):
        d.ellipse((cx - 2, cy - 2, cx + 2, cy + 2), fill=(50, 50, 55))
    add_noise(img, intensity=5, seed=110)
    return img


# ---------------- MAIN ----------------

def main():
    floors = {
        "floor_concrete":          floor_concrete,
        "floor_concrete_bloodied": floor_concrete_bloodied,
        "floor_wood":              floor_wood,
        "floor_brick":             floor_brick,
        "floor_metal":             floor_metal,
        "floor_dirt":              floor_dirt,
        "floor_asphalt":           floor_asphalt,
        "floor_carpet":            floor_carpet,
        "floor_grass":             floor_grass,
    }
    walls = {
        "wall_brick":    wall_brick,
        "wall_concrete": wall_concrete,
        "wall_wood":     wall_wood,
        "wall_metal":    wall_metal,
    }
    for name, fn in {**floors, **walls}.items():
        img = fn()
        img.save(os.path.join(OUT, f"{name}.png"))
        print(f"  {name}.png")


if __name__ == "__main__":
    main()
