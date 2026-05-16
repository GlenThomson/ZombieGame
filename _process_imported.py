"""Process the imported sprite library into proper 40x40 floor + wall tiles
and rename furniture into a decor folder. Idempotent."""
import os

from PIL import Image

SRC = "assets/images/imported"
TILES = "assets/images/tiles"
DECOR = "assets/images/decor"
TILE = 40

os.makedirs(TILES, exist_ok=True)
os.makedirs(DECOR, exist_ok=True)


def to_tile(im: Image.Image) -> Image.Image:
    """Resize / crop an arbitrary sprite to 40x40 RGBA, preserving aspect by
    cropping the centre after scaling."""
    im = im.convert("RGBA")
    w, h = im.size
    # Trim transparent / near-black borders first.
    bbox = im.getbbox()
    if bbox is not None:
        im = im.crop(bbox)
        w, h = im.size
    # Scale so the smaller side hits TILE, then centre-crop.
    scale = TILE / min(w, h)
    new = im.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    nw, nh = new.size
    left = (nw - TILE) // 2
    top = (nh - TILE) // 2
    return new.crop((left, top, left + TILE, top + TILE))


def keep_natural(im: Image.Image) -> Image.Image:
    """For decor, keep the natural sprite size (after trimming transparent
    edges) so we can place couches that are 80x37 etc. without distortion."""
    im = im.convert("RGBA")
    bbox = im.getbbox()
    if bbox is not None:
        im = im.crop(bbox)
    return im


def main():
    # ---- FLOORS ----
    for src_name, out_name in (
        ("floor.png",      "floor_wood_dark.png"),
        ("floorwood.png",  "floor_wood_natural.png"),
    ):
        src = os.path.join(SRC, src_name)
        if not os.path.isfile(src):
            print(f"  skip {src_name} (missing)")
            continue
        to_tile(Image.open(src)).save(os.path.join(TILES, out_name))
        print(f"  tile  -> {out_name}")

    # ---- WALLS ----
    for src_name, out_name in (
        ("wall.png",                "wall_wood_user.png"),
        ("walls_0048_Layer-49.png", "wall_planks_h.png"),
        ("walls_0051_Layer-0.png",  "wall_panel.png"),
    ):
        src = os.path.join(SRC, src_name)
        if not os.path.isfile(src):
            continue
        to_tile(Image.open(src)).save(os.path.join(TILES, out_name))
        print(f"  wall  -> {out_name}")

    # ---- BARRIER (barb wire) ----
    bar = os.path.join(SRC, "barrier.png")
    if os.path.isfile(bar):
        to_tile(Image.open(bar)).save(os.path.join(TILES, "barbwire_user.png"))
        print("  wall  -> barbwire_user.png")

    # ---- BACKGROUND.JPG -> grass tile ----
    bg = os.path.join(SRC, "Background.jpg")
    if os.path.isfile(bg):
        # Crop a tileable 200x200 patch from the centre then scale to 40x40
        im = Image.open(bg).convert("RGBA")
        cx, cy = im.size[0] // 2, im.size[1] // 2
        patch = im.crop((cx - 100, cy - 100, cx + 100, cy + 100))
        patch.resize((TILE, TILE), Image.LANCZOS).save(os.path.join(TILES, "floor_grass_real.png"))
        print("  tile  -> floor_grass_real.png (grass photo)")

    # ---- DECOR (furniture) ----
    decor_map = {
        "objects_house_0000_Layer-1.png":   "couch.png",
        "objects_house_0001_Layer-2.png":   "sink.png",
        "objects_house_0010_Layer-11.png":  "chest.png",
        "objects_house_0015_Layer-16.png":  "tv.png",
        "objects_house_0020_Layer-21.png":  "keyboard.png",
        "objects_house_0027_Layer-28.png":  "chair.png",
        "objects_house_0033_Layer-34.png":  "bed.png",
        "objects_house_0039_Layer-40.png":  "wood_plank.png",
        "objects_house_0049_Layer-50.png":  "gold_box.png",
        "objects_house_0055_Layer-56.png":  "plant_small.png",
        "objects_house_0056_Layer-57.png":  "plant_large.png",
    }
    for src_name, out_name in decor_map.items():
        src = os.path.join(SRC, src_name)
        if not os.path.isfile(src):
            continue
        keep_natural(Image.open(src)).save(os.path.join(DECOR, out_name))
        print(f"  decor -> {out_name}")


if __name__ == "__main__":
    main()
