#!/usr/bin/env python3
"""Validate and render the v2.0.3 driven-appliance cab correction."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

from v2_profile import (
    EXPORT_CANVAS,
    MASTER_DIR,
    MASTER_OVERRIDE_DIR,
    PREVIEW_DIR,
    RELEASE,
    RELEASE_CANDIDATE,
    ROOT,
    STATIC_DIR,
    compact_export,
    master_path,
)


CAB_IDS = ("f-wrc", "wrl-cafs", "rp-cafs")
LABELS = {
    "f-wrc": "F/WrC",
    "wrl-cafs": "WrL CAFS",
    "rp-cafs": "RP CAFS",
}
MASTER_FRONT_REGION = (120, 80, 195, 180)
MIN_MASTER_DARK_PIXELS = 1400
MIN_MASTER_GLAZING_PIXELS = 250
REPORT = ROOT / f"data/{RELEASE}-cab-legibility-report.json"
BEFORE_AFTER = PREVIEW_DIR / "cab-legibility-before-after.png"
LIVE_SCALE = PREVIEW_DIR / "cab-legibility-live-map.png"


def region_metrics(image: Image.Image, region: tuple[int, int, int, int]) -> dict:
    pixels = image.convert("RGBA").crop(region).get_flattened_data()
    opaque = 0
    dark = 0
    glazing = 0
    for red, green, blue, alpha in pixels:
        if alpha < 160:
            continue
        opaque += 1
        if red < 90 and green < 110 and blue < 120:
            dark += 1
        if red < 80 and 25 < green < 120 and 25 < blue < 135 and blue >= red:
            glazing += 1
    return {
        "region": list(region),
        "opaque_pixels": opaque,
        "dark_cab_pixels": dark,
        "glazing_pixels": glazing,
        "dark_share": round(dark / opaque, 4) if opaque else 0.0,
    }


def render_before_after() -> None:
    tile_width, tile_height = 290, 236
    sheet = Image.new("RGB", (tile_width * 2, 52 + tile_height * len(CAB_IDS)), (45, 50, 55))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text((12, 9), f"{RELEASE} driven-appliance cab correction", fill=(255, 255, 255), font=font)
    draw.text(
        (12, 28),
        "The front cab must remain immediately recognisable at native map scale.",
        fill=(186, 196, 204),
        font=font,
    )

    for row, asset_id in enumerate(CAB_IDS):
        before = Image.open(MASTER_DIR / f"{asset_id}.png").convert("RGBA")
        after = Image.open(master_path(asset_id)).convert("RGBA")
        for column, (caption, sprite) in enumerate((("BEFORE · rear/module only", before), ("CORRECTED · complete cab", after))):
            x = column * tile_width
            y = 52 + row * tile_height
            tile = Image.new("RGB", (tile_width, tile_height), (58, 64, 70))
            tile_draw = ImageDraw.Draw(tile)
            tile_draw.line((0, 178, tile_width, 139), fill=(98, 104, 108), width=8)
            tile_draw.line((0, 187, tile_width, 148), fill=(214, 62, 53), width=3)
            tile.paste(sprite, ((tile_width - sprite.width) // 2, 20), sprite)
            tile_draw.text((9, 6), LABELS[asset_id], fill=(255, 255, 255), font=font)
            tile_draw.text((9, 214), caption, fill=(235, 239, 242), font=font)
            if column == 1:
                tile_draw.text((180, 6), "FRONT: lower-right", fill=(255, 222, 89), font=font)
            sheet.paste(tile, (x, y))
            draw.rectangle((x, y, x + tile_width - 1, y + tile_height - 1), outline=(105, 116, 124))

    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    sheet.save(BEFORE_AFTER, compress_level=6)


def render_live_scale() -> None:
    themes = (
        ("LIGHT MAP", (231, 234, 231), (189, 194, 190), (214, 57, 50), (34, 39, 43)),
        ("SATELLITE MAP", (86, 105, 77), (126, 141, 114), (255, 112, 67), (250, 252, 247)),
        ("DARK GALLERY", (65, 65, 65), (90, 90, 90), (188, 53, 49), (255, 255, 255)),
    )
    tile_width, tile_height = 190, 150
    sheet = Image.new("RGB", (tile_width * len(themes), 48 + tile_height * len(CAB_IDS)), (18, 23, 28))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text((12, 9), f"{RELEASE} actual 110×110 cab-legibility audit", fill=(255, 255, 255), font=font)
    draw.text((12, 27), "No sprite is enlarged inside the map tiles.", fill=(172, 184, 194), font=font)

    for row, asset_id in enumerate(CAB_IDS):
        sprite = Image.open(STATIC_DIR / f"{asset_id}.png").convert("RGBA")
        if sprite.size != EXPORT_CANVAS:
            raise ValueError(f"Unexpected export canvas for {asset_id}: {sprite.size}")
        for column, (theme, background, road, route, foreground) in enumerate(themes):
            x = column * tile_width
            y = 48 + row * tile_height
            tile = Image.new("RGB", (tile_width, tile_height), background)
            tile_draw = ImageDraw.Draw(tile)
            tile_draw.line((0, 112, tile_width, 75), fill=road, width=9)
            tile_draw.line((0, 121, tile_width, 84), fill=route, width=3)
            tile.paste(sprite, ((tile_width - sprite.width) // 2, 24), sprite)
            tile_draw.text((7, 6), f"{LABELS[asset_id]} · {theme}", fill=foreground, font=font)
            tile_draw.text((7, 135), "native 110px canvas", fill=foreground, font=font)
            sheet.paste(tile, (x, y))
            draw.rectangle((x, y, x + tile_width - 1, y + tile_height - 1), outline=(98, 108, 116))

    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    sheet.save(LIVE_SCALE, compress_level=6)


def main() -> None:
    entries: list[dict] = []
    errors: list[str] = []

    for asset_id in CAB_IDS:
        source_path = master_path(asset_id)
        override_path = MASTER_OVERRIDE_DIR / f"{asset_id}.png"
        export_path = STATIC_DIR / f"{asset_id}.png"
        entry = {
            "asset_id": asset_id,
            "label": LABELS[asset_id],
            "master": source_path.relative_to(ROOT).as_posix(),
            "export": export_path.relative_to(ROOT).as_posix(),
        }
        local_errors: list[str] = []
        if source_path != override_path or not override_path.exists():
            local_errors.append("missing-release-master-override")
        if not export_path.exists():
            local_errors.append("missing-static-export")
            entries.append({**entry, "passed": False, "errors": local_errors})
            errors.extend(f"{asset_id}/{error}" for error in local_errors)
            continue

        master = Image.open(source_path).convert("RGBA")
        export = Image.open(export_path).convert("RGBA")
        metrics = region_metrics(master, MASTER_FRONT_REGION)
        if metrics["dark_cab_pixels"] < MIN_MASTER_DARK_PIXELS:
            local_errors.append(f"insufficient-dark-cab={metrics['dark_cab_pixels']}")
        if metrics["glazing_pixels"] < MIN_MASTER_GLAZING_PIXELS:
            local_errors.append(f"insufficient-glazing={metrics['glazing_pixels']}")
        if ImageChops.difference(export, compact_export(master)).getbbox() is not None:
            local_errors.append("static-export-master-drift")

        old_master = Image.open(MASTER_DIR / f"{asset_id}.png").convert("RGBA")
        entry.update(
            {
                "before": region_metrics(old_master, MASTER_FRONT_REGION),
                "after": metrics,
                "passed": not local_errors,
                "errors": local_errors,
            }
        )
        entries.append(entry)
        errors.extend(f"{asset_id}/{error}" for error in local_errors)

    render_before_after()
    render_live_scale()
    result = {
        "release": RELEASE_CANDIDATE,
        "scope": list(CAB_IDS),
        "front_region": list(MASTER_FRONT_REGION),
        "minimum_dark_cab_pixels": MIN_MASTER_DARK_PIXELS,
        "minimum_glazing_pixels": MIN_MASTER_GLAZING_PIXELS,
        "previews": [
            BEFORE_AFTER.relative_to(ROOT).as_posix(),
            LIVE_SCALE.relative_to(ROOT).as_posix(),
        ],
        "all_passed": not errors,
        "errors": errors,
        "entries": entries,
    }
    REPORT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("release", "scope", "all_passed", "errors")}, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
