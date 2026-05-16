"""One-shot art generator. Run this once to (re)create the entity sprites
and tileable map backgrounds in assets/images/. Idempotent."""
import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

OUT = "assets/images"
os.makedirs(OUT, exist_ok=True)

TILE = 40
SCREEN_W, SCREEN_H = 1000, 1000


def font(size: int) -> ImageFont.FreeTypeFont:
    # Try common Windows fonts first; fall back to PIL default.
    for path in (
        "C:/Windows/Fonts/impact.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ):
        if os.path.isfile(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


# ---------- vending machine bodies (perk machines) ----------

def perk_machine_sprite(initial: str, color: tuple[int, int, int]) -> Image.Image:
    img = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    body_dark = tuple(max(0, c - 50) for c in color) + (255,)
    # Outer black bezel
    d.rounded_rectangle((1, 1, TILE - 2, TILE - 2), radius=4, fill=(20, 20, 22, 255))
    # Inner vending machine front
    inner = (4, 5, TILE - 5, TILE - 6)
    d.rounded_rectangle(inner, radius=3, fill=color + (255,))
    # Top "Cola" stripe
    d.rectangle((4, 5, TILE - 5, 12), fill=body_dark)
    # Glass dispenser shadow
    d.rectangle((6, 14, TILE - 7, TILE - 14), fill=tuple(min(255, c + 30) for c in color) + (180,))
    # Dispense slot
    d.rectangle((8, TILE - 12, TILE - 9, TILE - 8), fill=(0, 0, 0, 255))
    # Big initial
    f = font(20)
    bbox = d.textbbox((0, 0), initial, font=f)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    d.text(
        ((TILE - tw) / 2 - bbox[0], (TILE - th) / 2 - bbox[1] + 1),
        initial, font=f, fill=(255, 255, 255, 255),
    )
    # Glow border
    d.rounded_rectangle((1, 1, TILE - 2, TILE - 2), radius=4, outline=(255, 215, 0, 255), width=1)
    return img


# ---------- mystery box ----------

def mystery_box_sprite(state: str = "idle") -> Image.Image:
    img = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if state == "idle":
        wood = (90, 50, 25)
        wood_dark = (55, 28, 12)
        accent = (255, 215, 0)
    elif state == "spinning":
        wood = (200, 80, 0)
        wood_dark = (120, 40, 0)
        accent = (255, 230, 50)
    elif state == "ready":
        wood = (255, 215, 0)
        wood_dark = (150, 100, 0)
        accent = (255, 255, 200)
    else:  # teddy
        wood = (220, 130, 80)
        wood_dark = (130, 70, 40)
        accent = (255, 220, 200)
    # Box body
    d.rounded_rectangle((2, 2, TILE - 3, TILE - 3), radius=3, fill=wood + (255,))
    # Top edge highlight
    d.line((4, 4, TILE - 5, 4), fill=tuple(min(255, c + 30) for c in wood) + (255,), width=1)
    # Wood grain
    for y in (12, 22, 32):
        d.line((4, y, TILE - 5, y), fill=wood_dark + (255,), width=1)
    # Iron corner brackets
    for cx, cy in ((3, 3), (TILE - 7, 3), (3, TILE - 7), (TILE - 7, TILE - 7)):
        d.rectangle((cx, cy, cx + 4, cy + 4), fill=(40, 30, 20, 255))
    # Question mark or label
    label = "?" if state == "idle" else ("!" if state == "ready" else ("*" if state == "spinning" else "T"))
    f = font(22)
    bbox = d.textbbox((0, 0), label, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(
        ((TILE - tw) / 2 - bbox[0], (TILE - th) / 2 - bbox[1]),
        label, font=f, fill=accent + (255,),
    )
    return img


# ---------- pack-a-punch machine ----------

def pap_sprite() -> Image.Image:
    img = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Black ornate frame
    d.rounded_rectangle((1, 1, TILE - 2, TILE - 2), radius=5, fill=(20, 18, 8, 255))
    # Gold inner
    d.rounded_rectangle((4, 5, TILE - 5, TILE - 6), radius=4, fill=(220, 170, 0, 255))
    # Highlight
    d.rounded_rectangle((6, 7, TILE - 7, 14), radius=2, fill=(255, 220, 80, 255))
    # PaP letters
    f = font(14)
    bbox = d.textbbox((0, 0), "PaP", font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(
        ((TILE - tw) / 2 - bbox[0], (TILE - th) / 2 - bbox[1] + 6),
        "PaP", font=f, fill=(20, 18, 8, 255),
    )
    # Outer glow
    d.rounded_rectangle((1, 1, TILE - 2, TILE - 2), radius=5, outline=(255, 220, 60, 255), width=2)
    return img


# ---------- power switch ----------

def power_switch_sprite(on: bool) -> Image.Image:
    img = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if on:
        body = (40, 80, 40)
        lever = (255, 220, 60)
    else:
        body = (50, 50, 60)
        lever = (180, 180, 180)
    d.rounded_rectangle((2, 2, TILE - 3, TILE - 3), radius=3, fill=body + (255,))
    d.rounded_rectangle((2, 2, TILE - 3, TILE - 3), radius=3, outline=(220, 220, 220, 255), width=2)
    cx = TILE // 2
    if on:
        d.line((cx, 8, cx, TILE - 14), fill=lever, width=5)
        d.ellipse((cx - 4, 4, cx + 4, 12), fill=lever)
        d.text((cx - 9, TILE - 14), "ON", font=font(11), fill=(255, 255, 255, 255))
    else:
        d.line((cx, 8, cx + 6, TILE - 14), fill=lever, width=5)
        d.ellipse((cx - 4, 4, cx + 4, 12), fill=lever)
        d.text((cx - 11, TILE - 14), "OFF", font=font(11), fill=(255, 255, 255, 255))
    return img


# ---------- door ----------

def door_sprite() -> Image.Image:
    img = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, TILE - 1, TILE - 1), fill=(110, 60, 20, 255))
    # Wood plank lines
    for y in (8, 16, 24, 32):
        d.line((1, y, TILE - 2, y), fill=(70, 35, 10, 255), width=1)
    # Vertical edge lines
    for x in (TILE // 3, 2 * TILE // 3):
        d.line((x, 1, x, TILE - 2), fill=(70, 35, 10, 255), width=1)
    # Iron handle
    d.ellipse((TILE - 12, TILE // 2 - 3, TILE - 6, TILE // 2 + 3), fill=(40, 40, 40, 255))
    d.rectangle((0, 0, TILE - 1, TILE - 1), outline=(255, 215, 0, 255), width=2)
    return img


# ---------- wall buy ----------

def wall_buy_sprite(weapon_name: str) -> Image.Image:
    img = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((1, 1, TILE - 2, TILE - 2), radius=2, fill=(40, 40, 50, 255))
    # Wall mount plate
    d.rectangle((6, TILE - 14, TILE - 7, TILE - 8), fill=(30, 30, 35, 255))
    # Drawn outline of a "rifle" — generic horizontal weapon shape
    d.rectangle((6, 14, TILE - 7, 18), fill=(160, 160, 170, 255))   # body
    d.rectangle((TILE - 14, 12, TILE - 8, 16), fill=(200, 200, 210, 255))  # barrel
    d.polygon([(6, 18), (12, 18), (12, 24), (6, 22)], fill=(80, 60, 30, 255))  # stock
    # Weapon label (first 5 chars)
    label = weapon_name[:5]
    f = font(10)
    bbox = d.textbbox((0, 0), label, font=f)
    tw = bbox[2] - bbox[0]
    d.text(((TILE - tw) / 2 - bbox[0], TILE - 12), label, font=f, fill=(255, 215, 0, 255))
    d.rounded_rectangle((1, 1, TILE - 2, TILE - 2), radius=2, outline=(255, 215, 0, 255), width=1)
    return img


# ---------- window ----------

def window_sprite(planks: int) -> Image.Image:
    img = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Frame
    d.rectangle((0, 0, TILE - 1, TILE - 1), fill=(60, 60, 80, 255))
    d.rectangle((0, 0, TILE - 1, TILE - 1), outline=(180, 180, 200, 255), width=2)
    # Gap inside (sky / dark)
    d.rectangle((4, 4, TILE - 5, TILE - 5), fill=(40, 50, 70, 255))
    # Planks (broken if planks < 4)
    slot_h = (TILE - 8) / 4
    for i in range(planks):
        y = int(4 + i * slot_h) + 1
        d.rectangle((3, y, TILE - 4, int(y + slot_h - 1)), fill=(160, 110, 50, 255))
        d.line((3, y, TILE - 4, y), fill=(90, 60, 25, 255), width=1)
        d.line((3, int(y + slot_h - 1)), fill=(60, 40, 18, 255), width=1)
        # Two nails
        d.ellipse((6, y + 2, 9, y + 5), fill=(50, 50, 50, 255))
        d.ellipse((TILE - 10, y + 2, TILE - 7, y + 5), fill=(50, 50, 50, 255))
    return img


# ---------- trap ----------

def trap_fire_sprite(active: bool) -> Image.Image:
    img = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if active:
        d.rectangle((0, 0, TILE - 1, TILE - 1), fill=(180, 60, 0, 255))
        # Flames
        for cx, h in ((TILE // 2, 30), (TILE // 4, 22), (3 * TILE // 4, 22)):
            d.polygon(
                [(cx - 6, TILE - 4), (cx, TILE - h), (cx + 6, TILE - 4)],
                fill=(255, 200, 0, 255),
            )
            d.polygon(
                [(cx - 3, TILE - 4), (cx, TILE - h + 6), (cx + 3, TILE - 4)],
                fill=(255, 100, 0, 255),
            )
    else:
        d.rectangle((0, 0, TILE - 1, TILE - 1), fill=(60, 30, 10, 255))
        # Cold grate
        for x in range(6, TILE - 4, 6):
            d.line((x, 6, x, TILE - 6), fill=(20, 10, 5, 255), width=1)
    d.rectangle((0, 0, TILE - 1, TILE - 1), outline=(255, 215, 0, 255), width=2)
    return img


def trap_flogger_sprite(active: bool, t: float = 0.0) -> Image.Image:
    img = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    body = (90, 90, 90) if active else (40, 40, 40)
    d.rectangle((0, 0, TILE - 1, TILE - 1), fill=body + (255,))
    cx = TILE // 2
    # Cross arms
    color = (220, 220, 220) if active else (110, 110, 110)
    for offset in (0, math.pi / 2):
        a = t + offset
        x2 = cx + int(math.cos(a) * (TILE // 2 - 4))
        y2 = cx + int(math.sin(a) * (TILE // 2 - 4))
        d.line((cx, cx, x2, y2), fill=color + (255,), width=4)
    # Hub
    d.ellipse((cx - 3, cx - 3, cx + 3, cx + 3), fill=(20, 20, 20, 255))
    d.rectangle((0, 0, TILE - 1, TILE - 1), outline=(255, 215, 0, 255), width=2)
    return img


# ---------- backgrounds ----------

def background_concrete(w: int, h: int) -> Image.Image:
    img = Image.new("RGB", (w, h), (60, 60, 65))
    px = img.load()
    rng = random.Random(42)
    # Speckle for concrete texture
    for y in range(h):
        for x in range(w):
            n = rng.randint(-12, 12)
            r, g, b = px[x, y]
            px[x, y] = (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)))
    # Dark concrete tile lines every TILE pixels
    d = ImageDraw.Draw(img)
    for x in range(0, w, TILE):
        d.line((x, 0, x, h), fill=(35, 35, 38), width=1)
    for y in range(0, h, TILE):
        d.line((0, y, w, y), fill=(35, 35, 38), width=1)
    # Cracks for atmosphere
    rng2 = random.Random(7)
    for _ in range(int(w * h / 5000)):
        x0 = rng2.randint(0, w - 1)
        y0 = rng2.randint(0, h - 1)
        for _ in range(rng2.randint(4, 12)):
            x1 = x0 + rng2.randint(-10, 10)
            y1 = y0 + rng2.randint(-10, 10)
            d.line((x0, y0, x1, y1), fill=(30, 30, 32), width=1)
            x0, y0 = x1, y1
    img = img.filter(ImageFilter.SMOOTH)
    return img


def background_brick(w: int, h: int) -> Image.Image:
    img = Image.new("RGB", (w, h), (90, 50, 38))
    d = ImageDraw.Draw(img)
    rng = random.Random(99)
    BRICK_W, BRICK_H = 50, 24
    for row in range(0, h, BRICK_H):
        offset = (BRICK_W // 2) if (row // BRICK_H) % 2 else 0
        for col in range(-BRICK_W, w + BRICK_W, BRICK_W):
            x = col + offset
            shade = rng.randint(-15, 15)
            base = (max(0, 130 + shade), max(0, 60 + shade), max(0, 45 + shade))
            d.rectangle((x + 1, row + 1, x + BRICK_W - 2, row + BRICK_H - 2), fill=base)
            # Mortar
            d.rectangle((x, row, x + 1, row + BRICK_H), fill=(40, 35, 30))
            d.rectangle((x, row, x + BRICK_W, row + 1), fill=(40, 35, 30))
    return img


def background_wood_floor(w: int, h: int) -> Image.Image:
    img = Image.new("RGB", (w, h), (110, 70, 35))
    d = ImageDraw.Draw(img)
    rng = random.Random(11)
    PLANK_H = 32
    for row in range(0, h, PLANK_H):
        shade = rng.randint(-15, 12)
        base = (
            max(0, min(255, 130 + shade)),
            max(0, min(255, 80 + shade)),
            max(0, min(255, 40 + shade)),
        )
        d.rectangle((0, row, w, row + PLANK_H - 1), fill=base)
        # Plank gap
        d.line((0, row + PLANK_H - 1, w, row + PLANK_H - 1), fill=(50, 30, 15), width=1)
        # Knots
        for _ in range(w // 200):
            kx = rng.randint(20, w - 20)
            ky = row + rng.randint(6, PLANK_H - 8)
            d.ellipse((kx - 3, ky - 3, kx + 3, ky + 3), fill=(80, 50, 25))
    return img


# ---------- main ----------

def main():
    print("generating perk machines...")
    perks = (
        ("Quick Revive", "Q", (180, 220, 255)),
        ("Juggernog",     "J", (200, 0, 0)),
        ("Speed Cola",    "S", (0, 200, 80)),
        ("Double Tap",    "D", (220, 220, 0)),
        ("Stamin-Up",     "U", (0, 200, 220)),
        ("Mule Kick",     "M", (220, 130, 0)),
    )
    for name, initial, color in perks:
        img = perk_machine_sprite(initial, color)
        slug = name.replace(" ", "_").lower()
        img.save(os.path.join(OUT, f"perk_{slug}.png"))

    print("mystery box variants...")
    for state in ("idle", "spinning", "ready", "teddy"):
        mystery_box_sprite(state).save(os.path.join(OUT, f"mystery_box_{state}.png"))

    print("pack-a-punch...")
    pap_sprite().save(os.path.join(OUT, "pack_a_punch.png"))

    print("power switch...")
    power_switch_sprite(False).save(os.path.join(OUT, "power_switch_off.png"))
    power_switch_sprite(True).save(os.path.join(OUT, "power_switch_on.png"))

    print("door...")
    door_sprite().save(os.path.join(OUT, "door_closed.png"))

    print("wall buy...")
    wall_buy_sprite("Shotgun").save(os.path.join(OUT, "wall_buy_generic.png"))

    print("window planks...")
    for n in range(0, 5):
        window_sprite(n).save(os.path.join(OUT, f"window_{n}.png"))

    print("traps...")
    trap_fire_sprite(False).save(os.path.join(OUT, "trap_fire_off.png"))
    trap_fire_sprite(True).save(os.path.join(OUT, "trap_fire_on.png"))
    trap_flogger_sprite(False).save(os.path.join(OUT, "trap_flogger_off.png"))
    trap_flogger_sprite(True).save(os.path.join(OUT, "trap_flogger_on.png"))

    print("backgrounds (this can take a few seconds)...")
    background_concrete(2000, 1320).save(os.path.join(OUT, "bg_concrete.png"))
    background_brick(2000, 1320).save(os.path.join(OUT, "bg_brick.png"))
    background_wood_floor(2000, 1320).save(os.path.join(OUT, "bg_wood.png"))

    print("done. total files:")
    print(sum(1 for _ in os.listdir(OUT)))


if __name__ == "__main__":
    main()
