"""Resize and compress cookie photos before they go on the site.

Phone photos are typically 3-5 MB each, which makes the catalogue slow on mobile
and bloats the deployment. This squares them off, scales them down and writes
web-sized JPEGs into the folder the app actually serves from.

    python scripts/optimize_images.py

Drop originals in  images_raw/  ->  they land in  static/images/cookies/
The output filename (minus extension) is what you put in data/cookies.json.
"""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Pillow is not installed. Run:  pip install -r requirements.txt")

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "images_raw"
OUT_DIR = BASE_DIR / "static" / "images" / "cookies"

MAX_EDGE = 900          # px — plenty for a 420px-wide detail photo on a retina screen
QUALITY = 82            # visually lossless for photos, roughly 10x smaller than source
SOURCE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".bmp", ".tif", ".tiff"}


def optimize(src: Path, dest: Path) -> tuple[int, int]:
    """Square-crop, downscale and save. Returns (bytes_in, bytes_out)."""
    with Image.open(src) as img:
        # Honour the EXIF orientation flag, otherwise phone shots come out sideways.
        img = ImageOps.exif_transpose(img)
        img = ImageOps.fit(img.convert("RGB"), (MAX_EDGE, MAX_EDGE), Image.LANCZOS)
        dest.parent.mkdir(parents=True, exist_ok=True)
        img.save(dest, "JPEG", quality=QUALITY, optimize=True, progressive=True)

    return src.stat().st_size, dest.stat().st_size


def main() -> int:
    if not RAW_DIR.is_dir():
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Created {RAW_DIR.relative_to(BASE_DIR)}/ - drop your cookie photos in there.")
        return 0

    sources = sorted(p for p in RAW_DIR.iterdir() if p.suffix.lower() in SOURCE_SUFFIXES)
    if not sources:
        print(f"No images found in {RAW_DIR.relative_to(BASE_DIR)}/")
        return 0

    total_in = total_out = 0
    for src in sources:
        dest = OUT_DIR / f"{src.stem.lower().replace(' ', '-')}.jpg"
        try:
            size_in, size_out = optimize(src, dest)
        except OSError as exc:
            print(f"  skipped {src.name}: {exc}")
            continue

        total_in += size_in
        total_out += size_out
        print(f"  {src.name}  {size_in / 1024:,.0f} KB -> {dest.name}  {size_out / 1024:,.0f} KB")

    if total_in:
        print(
            f"\n{len(sources)} image(s): "
            f"{total_in / 1_048_576:.1f} MB -> {total_out / 1_048_576:.1f} MB "
            f"({100 - total_out / total_in * 100:.0f}% smaller)"
        )
        print(f"Output: {OUT_DIR.relative_to(BASE_DIR)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
