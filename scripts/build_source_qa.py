#!/usr/bin/env python3
"""Build a labelled source-master contact sheet for visual QA."""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "prototypes.json"
TARGET = ROOT / "assets" / "previews" / "production-set-source-qa.png"


def crop_to_alpha(image: Image.Image, padding: int = 8) -> Image.Image:
    rgba = image.convert("RGBA")
    bbox = rgba.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("master contains no visible pixels")
    left, top, right, bottom = bbox
    return rgba.crop((max(0, left - padding), max(0, top - padding), min(rgba.width, right + padding), min(rgba.height, bottom + padding)))


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    vehicles = sorted(manifest["vehicles"], key=lambda item: int(item.get("missionchief_slot", 9999)))

    columns = 3
    tile_width, tile_height = 600, 335
    rows = math.ceil(len(vehicles) / columns)
    canvas = Image.new("RGB", (columns * tile_width, rows * tile_height + 56), "#182029")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=18)
    title_font = ImageFont.load_default(size=24)
    draw.text((24, 16), f"TKB UK Emergency Fleet - source-master QA ({len(vehicles)} assets)", font=title_font, fill="white")

    for index, vehicle in enumerate(vehicles):
        row, column = divmod(index, columns)
        left = column * tile_width + 14
        top = 56 + row * tile_height + 14
        panel = (left, top, left + tile_width - 28, top + tile_height - 28)
        draw.rounded_rectangle(panel, 12, fill="#f2f4f6")

        master = crop_to_alpha(Image.open(ROOT / vehicle["source"]))
        max_width, max_height = tile_width - 70, tile_height - 100
        scale = min(max_width / master.width, max_height / master.height)
        size = (max(1, round(master.width * scale)), max(1, round(master.height * scale)))
        thumb = master.resize(size, Image.Resampling.LANCZOS)
        x = left + (tile_width - 28 - thumb.width) // 2
        y = top + 20 + (max_height - thumb.height) // 2
        panel_rgba = canvas.convert("RGBA")
        panel_rgba.alpha_composite(thumb, (x, y))
        canvas.paste(panel_rgba.convert("RGB"))

        label = f"{vehicle['missionchief_slot']:03d}  {vehicle['display_name']}"
        draw = ImageDraw.Draw(canvas)
        draw.rounded_rectangle((left + 18, top + tile_height - 76, left + tile_width - 48, top + tile_height - 42), 7, fill="#141b22")
        draw.text((left + 30, top + tile_height - 69), label, font=font, fill="white")

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(TARGET, format="PNG", compress_level=6)
    print(TARGET)


if __name__ == "__main__":
    main()
