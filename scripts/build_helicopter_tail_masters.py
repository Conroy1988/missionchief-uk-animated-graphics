#!/usr/bin/env python3
"""Build deterministic full-tail helicopter masters from the retained source previews."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import deque
from io import BytesIO
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
TARGET_DIR = ROOT / "assets" / "masters" / "v1.2.4"
BACKGROUND = (242, 244, 246)
SOURCES = {
    "hems": ROOT / "assets" / "previews" / "hems-white.png",
    "police-helicopter": ROOT / "assets" / "previews" / "police-helicopter-white.png",
}
MASTER_WIDTH = 600


def near_background(pixel: tuple[int, int, int], tolerance: int) -> bool:
    return max(abs(pixel[index] - BACKGROUND[index]) for index in range(3)) <= tolerance


def extract_subject(source: Image.Image) -> Image.Image:
    rgb = source.convert("RGB")
    width, height = rgb.size
    pixels = rgb.load()
    exterior = bytearray(width * height)
    queue: deque[tuple[int, int]] = deque()

    def enqueue(x: int, y: int) -> None:
        index = y * width + x
        if exterior[index] or not near_background(pixels[x, y], 28):
            return
        exterior[index] = 1
        queue.append((x, y))

    for x in range(width):
        enqueue(x, 0)
        enqueue(x, height - 1)
    for y in range(height):
        enqueue(0, y)
        enqueue(width - 1, y)

    while queue:
        x, y = queue.popleft()
        if x:
            enqueue(x - 1, y)
        if x + 1 < width:
            enqueue(x + 1, y)
        if y:
            enqueue(x, y - 1)
        if y + 1 < height:
            enqueue(x, y + 1)

    output = rgb.convert("RGBA")
    out = output.load()
    for y in range(height):
        for x in range(width):
            # Exact source-background pixels also occur inside the enclosed
            # fenestron. Clear them globally while preserving white livery.
            if exterior[y * width + x] or near_background(pixels[x, y], 2):
                out[x, y] = (0, 0, 0, 0)

    bbox = output.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("helicopter source extraction produced an empty image")
    cropped = output.crop(bbox)
    target_height = max(1, round(cropped.height * MASTER_WIDTH / cropped.width))
    return cropped.resize((MASTER_WIDTH, target_height), Image.Resampling.LANCZOS)


def png_bytes(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def target_path(asset_id: str) -> Path:
    return TARGET_DIR / f"{asset_id}-full-tail.png"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify every committed master is the exact deterministic output",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = []
    for asset_id, source_path in SOURCES.items():
        with Image.open(source_path) as source:
            source.load()
            master = extract_subject(source)
        rendered = png_bytes(master)
        target = target_path(asset_id)
        if args.check:
            if not target.is_file():
                raise FileNotFoundError(target)
            if target.read_bytes() != rendered:
                raise ValueError(f"committed {asset_id} full-tail master is stale")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(rendered)

        if master.getchannel("A").getbbox() != (0, 0, *master.size):
            raise ValueError(f"{asset_id}: full-tail master contains unexpected outer padding")
        results.append(
            {
                "id": asset_id,
                "target": str(target.relative_to(ROOT)),
                "dimensions": list(master.size),
                "sha256": hashlib.sha256(rendered).hexdigest(),
            }
        )

    print(json.dumps({"status": "Verified" if args.check else "Built", "full_tail_masters": results}, indent=2))


if __name__ == "__main__":
    main()
