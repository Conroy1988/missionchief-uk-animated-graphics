#!/usr/bin/env python3
"""Validate and render the v2.0.4 complete mounted-carrier correction."""

from __future__ import annotations

import json

from PIL import Image, ImageChops, ImageDraw, ImageFont

from v2_profile import (
    EXPORT_CANVAS,
    MASTER_DIR,
    MASTER_OVERRIDE_DIR,
    MOUNTED_CARRIER_IDS,
    PREVIEW_DIR,
    RELEASE,
    RELEASE_CANDIDATE,
    ROOT,
    STATIC_DIR,
    compact_export,
    master_path,
)


SLOTS = json.loads((ROOT / "data/vehicle-slots.json").read_text())["slots"]
LABELS = {slot["asset_id"]: slot["label"] for slot in SLOTS}
PRIME_MOVER = MASTER_DIR / "pm.png"
FRONT_REGION = (135, 90, 200, 195)
CAB_METRIC_REGION = (98, 90, 195, 190)
REAR_ROLE_REGION = (0, 50, 135, 165)
MIN_MASTER_WIDTH = 170
MIN_EXPORT_WIDTH = 94
MIN_DARK_CAB_PIXELS = 2000
MIN_GLAZING_PIXELS = 700
MIN_ROLE_CHANGE_PIXELS = 1800
REPORT = ROOT / f"data/{RELEASE}-mounted-carrier-report.json"
BEFORE_AFTER = PREVIEW_DIR / "mounted-carrier-before-after.png"
LIVE_SCALE = PREVIEW_DIR / "mounted-carrier-live-map.png"


def region_metrics(image: Image.Image, region: tuple[int, int, int, int]) -> dict:
    opaque = 0
    dark = 0
    glazing = 0
    for red, green, blue, alpha in image.convert("RGBA").crop(region).get_flattened_data():
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
    }


def changed_pixels(left: Image.Image, right: Image.Image, region: tuple[int, int, int, int]) -> int:
    difference = ImageChops.difference(left.crop(region), right.crop(region)).convert("RGBA")
    return sum(max(pixel) >= 12 for pixel in difference.get_flattened_data())


def render_before_after() -> None:
    columns = 5
    tile_width, tile_height = 400, 238
    rows = (len(MOUNTED_CARRIER_IDS) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * tile_width, rows * tile_height + 48), (13, 20, 28))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text((14, 10), f"{RELEASE} mounted specialist-carrier correction", fill=(255, 255, 255), font=font)
    draw.text(
        (14, 28),
        "Every transported module now travels on the complete direction-neutral PM cab and three-axle chassis.",
        fill=(172, 184, 194),
        font=font,
    )

    for index, asset_id in enumerate(MOUNTED_CARRIER_IDS):
        column, row = index % columns, index // columns
        x, y = column * tile_width, 48 + row * tile_height
        tile = Image.new("RGB", (tile_width, tile_height), (31, 43, 53))
        tile_draw = ImageDraw.Draw(tile)
        tile_draw.line((0, 188, tile_width, 126), fill=(72, 84, 92), width=10)
        tile_draw.line((0, 196, tile_width, 134), fill=(218, 67, 55), width=3)
        before = Image.open(MASTER_DIR / f"{asset_id}.png").convert("RGBA")
        after = Image.open(master_path(asset_id)).convert("RGBA")
        before = before.resize((180, 180), Image.Resampling.LANCZOS)
        after = after.resize((180, 180), Image.Resampling.LANCZOS)
        tile.paste(before, (10, 34), before)
        tile.paste(after, (210, 34), after)
        tile_draw.text((10, 8), LABELS[asset_id], fill=(255, 255, 255), font=font)
        tile_draw.text((10, 218), "BEFORE · module only", fill=(255, 174, 154), font=font)
        tile_draw.text((210, 218), "CORRECTED · loaded PM", fill=(113, 223, 176), font=font)
        sheet.paste(tile, (x, y))
        draw.rectangle((x, y, x + tile_width - 1, y + tile_height - 1), outline=(67, 86, 100))

    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    sheet.save(BEFORE_AFTER, compress_level=6)


def render_live_scale() -> None:
    themes = (
        ("LIGHT", (231, 234, 231), (189, 194, 190), (214, 57, 50), (34, 39, 43)),
        ("SATELLITE", (86, 105, 77), (126, 141, 114), (255, 112, 67), (250, 252, 247)),
        ("DARK", (35, 42, 49), (76, 84, 91), (218, 67, 55), (255, 255, 255)),
    )
    columns = 5
    tile_width, tile_height = 390, 166
    rows = (len(MOUNTED_CARRIER_IDS) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * tile_width, rows * tile_height + 48), (13, 20, 28))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text((14, 10), f"{RELEASE} actual 110×110 mounted-carrier audit", fill=(255, 255, 255), font=font)
    draw.text((14, 28), "Sprites are pasted at native pixels with no enlargement.", fill=(172, 184, 194), font=font)

    for index, asset_id in enumerate(MOUNTED_CARRIER_IDS):
        column, row = index % columns, index // columns
        x, y = column * tile_width, 48 + row * tile_height
        sprite = Image.open(STATIC_DIR / f"{asset_id}.png").convert("RGBA")
        for theme_index, (name, background, road, route, foreground) in enumerate(themes):
            sub_x = x + theme_index * 130
            tile = Image.new("RGB", (130, tile_height), background)
            tile_draw = ImageDraw.Draw(tile)
            tile_draw.line((0, 121, 130, 85), fill=road, width=9)
            tile_draw.line((0, 129, 130, 93), fill=route, width=3)
            tile.paste(sprite, (10, 30), sprite)
            tile_draw.text((5, 5), name, fill=foreground, font=font)
            tile_draw.text((5, 151), LABELS[asset_id], fill=foreground, font=font)
            sheet.paste(tile, (sub_x, y))
            draw.rectangle((sub_x, y, sub_x + 129, y + tile_height - 1), outline=(67, 86, 100))

    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    sheet.save(LIVE_SCALE, compress_level=6)


def main() -> None:
    prime_mover = Image.open(PRIME_MOVER).convert("RGBA")
    entries: list[dict] = []
    errors: list[str] = []

    for asset_id in MOUNTED_CARRIER_IDS:
        source_path = master_path(asset_id)
        override_path = MASTER_OVERRIDE_DIR / f"{asset_id}.png"
        export_path = STATIC_DIR / f"{asset_id}.png"
        local_errors: list[str] = []
        if source_path != override_path or not override_path.exists():
            local_errors.append("missing-release-master-override")
        if not export_path.exists():
            local_errors.append("missing-static-export")
            entries.append({"asset_id": asset_id, "passed": False, "errors": local_errors})
            errors.extend(f"{asset_id}/{error}" for error in local_errors)
            continue

        master = Image.open(source_path).convert("RGBA")
        export = Image.open(export_path).convert("RGBA")
        master_bbox = master.getchannel("A").getbbox()
        export_bbox = export.getchannel("A").getbbox()
        metrics = region_metrics(master, CAB_METRIC_REGION)
        role_change_pixels = changed_pixels(master, prime_mover, REAR_ROLE_REGION)

        if master_bbox is None or master_bbox[2] - master_bbox[0] < MIN_MASTER_WIDTH:
            local_errors.append(f"short-master={master_bbox}")
        if export_bbox is None or export_bbox[2] - export_bbox[0] < MIN_EXPORT_WIDTH:
            local_errors.append(f"short-export={export_bbox}")
        if ImageChops.difference(
            master.crop(FRONT_REGION), prime_mover.crop(FRONT_REGION)
        ).getbbox() is not None:
            local_errors.append("prime-mover-front-changed")
        if metrics["dark_cab_pixels"] < MIN_DARK_CAB_PIXELS:
            local_errors.append(f"insufficient-dark-cab={metrics['dark_cab_pixels']}")
        if metrics["glazing_pixels"] < MIN_GLAZING_PIXELS:
            local_errors.append(f"insufficient-glazing={metrics['glazing_pixels']}")
        if role_change_pixels < MIN_ROLE_CHANGE_PIXELS:
            local_errors.append(f"missing-role-module={role_change_pixels}")
        if ImageChops.difference(export, compact_export(master)).getbbox() is not None:
            local_errors.append("static-export-master-drift")

        entry = {
            "asset_id": asset_id,
            "label": LABELS[asset_id],
            "master": source_path.relative_to(ROOT).as_posix(),
            "export": export_path.relative_to(ROOT).as_posix(),
            "master_bbox": list(master_bbox) if master_bbox else None,
            "export_bbox": list(export_bbox) if export_bbox else None,
            "cab_metrics": metrics,
            "role_change_pixels": role_change_pixels,
            "passed": not local_errors,
            "errors": local_errors,
        }
        entries.append(entry)
        errors.extend(f"{asset_id}/{error}" for error in local_errors)

    render_before_after()
    render_live_scale()
    result = {
        "release": RELEASE_CANDIDATE,
        "scope": list(MOUNTED_CARRIER_IDS),
        "front_preservation_region": list(FRONT_REGION),
        "minimum_master_width": MIN_MASTER_WIDTH,
        "minimum_export_width": MIN_EXPORT_WIDTH,
        "minimum_dark_cab_pixels": MIN_DARK_CAB_PIXELS,
        "minimum_glazing_pixels": MIN_GLAZING_PIXELS,
        "minimum_role_change_pixels": MIN_ROLE_CHANGE_PIXELS,
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
