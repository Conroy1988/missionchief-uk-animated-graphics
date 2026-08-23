#!/usr/bin/env python3
"""Validate and render the retained v2.1.1 unified mounted-carrier correction."""

from __future__ import annotations

import json

from PIL import Image, ImageChops, ImageDraw, ImageFont

from build_v2_mounted_pod_carriers import (
    CAB_REGION,
    CHASSIS_REGION,
    COUPLING_REGION,
    MIN_COMPONENT_COVERAGE,
    MIN_DARK_WHEEL_PIXELS,
    MIN_OPAQUE_PIXELS,
    MIN_REGION_OPAQUE,
    ROLE_BODY_REGION,
    WHEEL_REGIONS,
    integration_metrics,
    source_path,
    validation_errors,
)
from v2_profile import (
    MOUNTED_CARRIER_IDS,
    PREVIOUS_OVERRIDE_DIR,
    PREVIOUS_OVERRIDE_RELEASE,
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
REPORT = ROOT / f"data/{RELEASE}-mounted-carrier-report.json"
BEFORE_AFTER = PREVIEW_DIR / "mounted-carrier-before-after.png"
LIVE_SCALE = PREVIEW_DIR / "mounted-carrier-live-map.png"
MIN_CHANGED_PIXELS = 4_000
MIN_EXPORT_WIDTH = 100


def changed_pixels(left: Image.Image, right: Image.Image) -> int:
    difference = ImageChops.difference(left.convert("RGBA"), right.convert("RGBA"))
    return sum(max(pixel) >= 12 for pixel in difference.get_flattened_data())


def render_before_after() -> None:
    columns = 5
    tile_width, tile_height = 420, 250
    rows = (len(MOUNTED_CARRIER_IDS) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * tile_width, rows * tile_height + 52), (13, 20, 28))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text((14, 10), f"{RELEASE} unified mounted-carrier correction", fill="white", font=font)
    draw.text(
        (14, 29),
        "Each role body is seated on one continuous rigid three-axle chassis; no legacy trailer underframe remains.",
        fill=(172, 184, 194),
        font=font,
    )

    for index, asset_id in enumerate(MOUNTED_CARRIER_IDS):
        column, row = index % columns, index // columns
        x, y = column * tile_width, 52 + row * tile_height
        tile = Image.new("RGB", (tile_width, tile_height), (31, 43, 53))
        tile_draw = ImageDraw.Draw(tile)
        before = Image.open(PREVIOUS_OVERRIDE_DIR / f"{asset_id}.png").convert("RGBA")
        after = Image.open(master_path(asset_id)).convert("RGBA")
        before = before.resize((190, 190), Image.Resampling.LANCZOS)
        after = after.resize((190, 190), Image.Resampling.LANCZOS)
        tile.paste(before, (8, 34), before)
        tile.paste(after, (220, 34), after)
        tile_draw.text((10, 8), LABELS[asset_id], fill="white", font=font)
        tile_draw.text(
            (10, 228),
            f"{PREVIOUS_OVERRIDE_RELEASE} · composited module",
            fill=(255, 174, 154),
            font=font,
        )
        tile_draw.text(
            (220, 228),
            f"{RELEASE} · unified carrier",
            fill=(113, 223, 176),
            font=font,
        )
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
    tile_width, tile_height = 390, 174
    rows = (len(MOUNTED_CARRIER_IDS) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * tile_width, rows * tile_height + 48), (13, 20, 28))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text((14, 10), f"{RELEASE} actual 110×110 unified-carrier audit", fill="white", font=font)
    draw.text((14, 28), "Sprites are pasted at native pixels with no enlargement.", fill=(172, 184, 194), font=font)

    for index, asset_id in enumerate(MOUNTED_CARRIER_IDS):
        column, row = index % columns, index // columns
        x, y = column * tile_width, 48 + row * tile_height
        sprite = Image.open(STATIC_DIR / f"{asset_id}.png").convert("RGBA")
        for theme_index, (name, background, road, route, foreground) in enumerate(themes):
            sub_x = x + theme_index * 130
            tile = Image.new("RGB", (130, tile_height), background)
            tile_draw = ImageDraw.Draw(tile)
            tile_draw.line((0, 126, 130, 90), fill=road, width=9)
            tile_draw.line((0, 134, 130, 98), fill=route, width=3)
            tile.paste(sprite, (10, 34), sprite)
            tile_draw.text((5, 5), name, fill=foreground, font=font)
            tile_draw.text((5, 159), LABELS[asset_id], fill=foreground, font=font)
            sheet.paste(tile, (sub_x, y))
            draw.rectangle((sub_x, y, sub_x + 129, y + tile_height - 1), outline=(67, 86, 100))

    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    sheet.save(LIVE_SCALE, compress_level=6)


def main() -> None:
    entries: list[dict] = []
    errors: list[str] = []

    for asset_id in MOUNTED_CARRIER_IDS:
        source = source_path(asset_id)
        master_file = master_path(asset_id)
        export_file = STATIC_DIR / f"{asset_id}.png"
        previous_file = PREVIOUS_OVERRIDE_DIR / f"{asset_id}.png"
        local_errors: list[str] = []
        for label, path in (
            ("source", source),
            ("master", master_file),
            ("export", export_file),
            ("previous", previous_file),
        ):
            if not path.exists():
                local_errors.append(f"missing-{label}")
        if local_errors:
            entries.append({"asset_id": asset_id, "passed": False, "errors": local_errors})
            errors.extend(f"{asset_id}/{error}" for error in local_errors)
            continue

        master = Image.open(master_file).convert("RGBA")
        export = Image.open(export_file).convert("RGBA")
        previous = Image.open(previous_file).convert("RGBA")
        metrics = integration_metrics(master)
        local_errors.extend(
            item.split("/", 1)[1]
            for item in validation_errors(asset_id, master)
        )
        export_bbox = export.getchannel("A").getbbox()
        if export_bbox is None or export_bbox[2] - export_bbox[0] < MIN_EXPORT_WIDTH:
            local_errors.append(f"short-export={export_bbox}")
        if ImageChops.difference(export, compact_export(master)).getbbox() is not None:
            local_errors.append("static-export-master-drift")
        changed = changed_pixels(previous, master)
        if changed < MIN_CHANGED_PIXELS:
            local_errors.append(f"insufficient-correction={changed}")

        entry = {
            "asset_id": asset_id,
            "label": LABELS[asset_id],
            "source": source.relative_to(ROOT).as_posix(),
            "master": master_file.relative_to(ROOT).as_posix(),
            "export": export_file.relative_to(ROOT).as_posix(),
            "previous_master": previous_file.relative_to(ROOT).as_posix(),
            "export_bbox": list(export_bbox) if export_bbox else None,
            "changed_pixels": changed,
            "integration_metrics": metrics,
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
        "integration_contract": {
            "minimum_opaque_pixels": MIN_OPAQUE_PIXELS,
            "minimum_largest_component_coverage": MIN_COMPONENT_COVERAGE,
            "regions": {
                "coupling": list(COUPLING_REGION),
                "chassis": list(CHASSIS_REGION),
                "cab": list(CAB_REGION),
                "role_body": list(ROLE_BODY_REGION),
            },
            "minimum_region_opaque_pixels": MIN_REGION_OPAQUE,
            "wheel_regions": {name: list(region) for name, region in WHEEL_REGIONS.items()},
            "minimum_dark_wheel_pixels": MIN_DARK_WHEEL_PIXELS,
        },
        "minimum_changed_pixels": MIN_CHANGED_PIXELS,
        "minimum_export_width": MIN_EXPORT_WIDTH,
        "previews": [
            BEFORE_AFTER.relative_to(ROOT).as_posix(),
            LIVE_SCALE.relative_to(ROOT).as_posix(),
        ],
        "all_passed": not errors,
        "errors": errors,
        "entries": entries,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("release", "scope", "all_passed", "errors")}, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
