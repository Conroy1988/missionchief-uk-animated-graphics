#!/usr/bin/env python3
"""Render an actual-pixel map-scale comparison for representative v2 vehicles."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from v2_profile import EXPORT_CANVAS, MASTER_DIR, PREVIEW_DIR, RELEASE, ROOT, STATIC_DIR


SLOTS = json.loads((ROOT / "data/vehicle-slots.json").read_text())["slots"]
SLOTS_BY_ASSET = {slot["asset_id"]: slot for slot in SLOTS}
COMMAND_DIR = ROOT / "assets/exports/command/static"
PREVIEW = PREVIEW_DIR / "compact-map-scale-calibration.png"

REPRESENTATIVE_IDS = (
    "fire-rescue-pump",
    "fire-officer",
    "frontline-ambulance",
    "rapid-response-vehicle",
    "police-helicopter",
    "ambulance-control-unit",
    "inland-rescue-boat-trailer",
    "alb",
    "medical-cycle-responder",
    "hgv-recovery-vehicle",
)

THEMES = (
    ((230, 232, 229), (192, 196, 192), (198, 56, 48), (65, 69, 71)),
    ((94, 110, 86), (132, 146, 120), (255, 118, 72), (245, 247, 240)),
    ((34, 41, 48), (71, 80, 87), (235, 76, 69), (235, 239, 242)),
)


def occupied_size(image: Image.Image) -> tuple[int, int]:
    bbox = image.getchannel("A").getbbox()
    return (0, 0) if bbox is None else (bbox[2] - bbox[0], bbox[3] - bbox[1])


def tile_background(
    size: tuple[int, int], theme_index: int
) -> tuple[Image.Image, tuple[int, int, int]]:
    background, road, route, foreground = THEMES[theme_index % len(THEMES)]
    tile = Image.new("RGB", size, background)
    draw = ImageDraw.Draw(tile)
    draw.line((0, size[1] * 0.70, size[0], size[1] * 0.43), fill=road, width=8)
    draw.line((0, size[1] * 0.78, size[0], size[1] * 0.51), fill=(244, 244, 241), width=2)
    draw.line((0, size[1] * 0.86, size[0], size[1] * 0.58), fill=route, width=3)
    draw.text(
        (7, 7), "Busy-map actual pixels", fill=foreground, font=ImageFont.load_default()
    )
    return tile, foreground


def paste_actual(tile: Image.Image, sprite: Image.Image) -> None:
    left = (tile.width - sprite.width) // 2
    top = tile.height - sprite.height - 5
    tile.paste(sprite, (left, top), sprite)


def render_preview() -> None:
    columns = (
        ("v1.4.14 command baseline", COMMAND_DIR),
        ("v2.0.0 oversized master", MASTER_DIR),
        (f"{RELEASE} compact {EXPORT_CANVAS[0]}×{EXPORT_CANVAS[1]}", STATIC_DIR),
    )
    groups_per_row = 2
    tile_width, tile_height = 220, 184
    header_height = 92
    rows = (len(REPRESENTATIVE_IDS) + groups_per_row - 1) // groups_per_row
    sheet = Image.new(
        "RGB",
        (
            tile_width * len(columns) * groups_per_row,
            header_height + tile_height * rows,
        ),
        (13, 19, 25),
    )
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text(
        (18, 16),
        f"{RELEASE} compact fleet — map-scale calibration",
        fill=(255, 255, 255),
        font=font,
    )
    draw.text(
        (18, 36),
        "All sprites are pasted at native pixels. The compact export preserves the raised perspective while removing map dominance.",
        fill=(172, 184, 194),
        font=font,
    )
    for group_column in range(groups_per_row):
        group_x = group_column * len(columns) * tile_width
        for column, (label, _directory) in enumerate(columns):
            draw.text(
                (group_x + column * tile_width + 8, 70),
                label,
                fill=(236, 240, 244),
                font=font,
            )

    for index, asset_id in enumerate(REPRESENTATIVE_IDS):
        row = index // groups_per_row
        group_column = index % groups_per_row
        group_x = group_column * len(columns) * tile_width
        slot = SLOTS_BY_ASSET[asset_id]
        y = header_height + row * tile_height
        for column, (_label, directory) in enumerate(columns):
            sprite = Image.open(directory / f"{asset_id}.png").convert("RGBA")
            tile, foreground = tile_background((tile_width, tile_height), row)
            paste_actual(tile, sprite)
            width, height = occupied_size(sprite)
            tile_draw = ImageDraw.Draw(tile)
            tile_draw.text(
                (7, tile_height - 29),
                f"{slot['slot']:03d} {slot['label']}",
                fill=foreground,
                font=font,
            )
            tile_draw.text(
                (7, tile_height - 15),
                f"canvas {sprite.width}×{sprite.height} · visible {width}×{height}",
                fill=foreground,
                font=font,
            )
            x = group_x + column * tile_width
            sheet.paste(tile, (x, y))
            draw.rectangle(
                (
                    x,
                    y,
                    x + tile_width - 1,
                    y + tile_height - 1,
                ),
                outline=(76, 89, 99),
            )

    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=f"{PREVIEW.stem}-", suffix=".png", delete=False) as handle:
        temporary = Path(handle.name)
    try:
        sheet.save(temporary, compress_level=6)
        with Image.open(temporary) as verification:
            verification.load()
        shutil.copyfile(temporary, PREVIEW)
        with Image.open(PREVIEW) as verification:
            verification.load()
    finally:
        temporary.unlink(missing_ok=True)


def main() -> None:
    missing = [
        f"{directory}/{asset_id}.png"
        for asset_id in REPRESENTATIVE_IDS
        for directory in (COMMAND_DIR, MASTER_DIR, STATIC_DIR)
        if not (directory / f"{asset_id}.png").exists()
    ]
    if missing:
        raise FileNotFoundError("Missing calibration assets: " + ", ".join(missing))
    render_preview()
    print(f"preview={PREVIEW.relative_to(ROOT)}")
    print(f"representative_assets={len(REPRESENTATIVE_IDS)}")


if __name__ == "__main__":
    main()
