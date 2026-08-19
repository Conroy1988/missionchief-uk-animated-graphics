#!/usr/bin/env python3
"""Validate and render the complete v2 direction-neutral static fleet."""

from __future__ import annotations

import json

from PIL import Image, ImageChops, ImageDraw, ImageFont

from v2_profile import (
    EXPORT_CANVAS,
    EXPORT_SCALE,
    MASTER_CANVAS,
    MASTER_DIR,
    PREVIEW_DIR,
    RELEASE_CANDIDATE,
    ROOT,
    STATIC_DIR,
    compact_export,
)


SLOTS = json.loads((ROOT / "data/vehicle-slots.json").read_text())["slots"]
REPORT = ROOT / "data/v2.0.1-static-qa-report.json"


THEMES = {
    "light": ((235, 238, 233), (22, 27, 32), (120, 128, 134)),
    "dark": ((37, 43, 49), (245, 247, 249), (154, 166, 177)),
    "satellite": ((83, 103, 72), (250, 252, 247), (185, 200, 176)),
    "grayscale": ((116, 120, 123), (255, 255, 255), (210, 213, 216)),
}


def render_sheet(theme: str) -> Path:
    background, foreground, secondary = THEMES[theme]
    columns = 8
    tile_width, tile_height = 156, 168
    rows = (len(SLOTS) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * tile_width, rows * tile_height), background)
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for index, slot in enumerate(SLOTS):
        x = (index % columns) * tile_width
        y = (index // columns) * tile_height
        asset_id = slot["asset_id"]
        sprite = Image.open(STATIC_DIR / f"{asset_id}.png").convert("RGBA")
        sprite_x = x + (tile_width - sprite.width) // 2
        sprite_y = y + 24
        sheet.paste(sprite, (sprite_x, sprite_y), sprite)
        draw.rectangle((x, y, x + tile_width - 1, y + tile_height - 1), outline=secondary)
        draw.text((x + 5, y + 4), f"{slot['slot']:03d}  {slot['label']}", fill=foreground, font=font)
        draw.text((x + 5, y + 154), asset_id, fill=secondary, font=font)

    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    target = PREVIEW_DIR / f"full-fleet-static-{theme}.png"
    # Pillow's exhaustive PNG optimiser can truncate very tall contact sheets
    # under constrained runners.  Normal DEFLATE is deterministic and is
    # verified immediately before the path is admitted to the QA report.
    temporary = target.with_suffix(".tmp.png")
    sheet.save(temporary, compress_level=6)
    with Image.open(temporary) as verification:
        verification.load()
    temporary.replace(target)
    return target


def main() -> None:
    expected = {slot["asset_id"] for slot in SLOTS}
    actual = {path.stem for path in STATIC_DIR.glob("*.png")}
    checks: list[dict] = []

    for slot in SLOTS:
        asset_id = slot["asset_id"]
        path = STATIC_DIR / f"{asset_id}.png"
        entry = {"slot": slot["slot"], "asset_id": asset_id, "passed": False}
        if not path.exists():
            entry["error"] = "missing"
            checks.append(entry)
            continue
        image = Image.open(path).convert("RGBA")
        alpha = image.getchannel("A")
        bbox = alpha.getbbox()
        errors: list[str] = []
        master_path = MASTER_DIR / f"{asset_id}.png"
        matches_master = False
        if not master_path.exists():
            errors.append("missing-master")
        else:
            master = Image.open(master_path).convert("RGBA")
            if master.size != MASTER_CANVAS:
                errors.append(f"master-canvas={master.size}")
            else:
                expected_export = compact_export(master)
                matches_master = ImageChops.difference(image, expected_export).getbbox() is None
                if not matches_master:
                    errors.append("compact-export-master-drift")
        if image.size != EXPORT_CANVAS:
            errors.append(f"canvas={image.size}")
        if bbox is None:
            errors.append("empty-alpha")
        else:
            if bbox[0] < 1 or bbox[1] < 1 or bbox[2] > EXPORT_CANVAS[0] - 1 or bbox[3] > EXPORT_CANVAS[1] - 1:
                errors.append(f"clipping-risk={bbox}")
            if bbox[3] > 105:
                errors.append(f"baseline={bbox[3]}")
        if alpha.getextrema() != (0, 255):
            errors.append(f"alpha-extrema={alpha.getextrema()}")
        entry.update(
            {
                "bbox": list(bbox) if bbox else None,
                "matches_200px_master": matches_master,
                "alpha_extrema": list(alpha.getextrema()),
                "errors": errors,
                "passed": not errors,
            }
        )
        checks.append(entry)

    previews = [render_sheet(theme) for theme in THEMES]
    report = {
        "release": RELEASE_CANDIDATE,
        "master_canvas": list(MASTER_CANVAS),
        "export_canvas": list(EXPORT_CANVAS),
        "export_scale": EXPORT_SCALE,
        "expected_assets": len(expected),
        "actual_assets": len(actual),
        "missing": sorted(expected - actual),
        "extra": sorted(actual - expected),
        "passed_assets": sum(check["passed"] for check in checks),
        "failed_assets": sum(not check["passed"] for check in checks),
        "all_passed": expected == actual and all(check["passed"] for check in checks),
        "previews": [str(path.relative_to(ROOT)) for path in previews],
        "checks": checks,
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("expected_assets", "actual_assets", "passed_assets", "failed_assets", "all_passed")}, indent=2))
    print(f"report={REPORT.relative_to(ROOT)}")
    for preview in previews:
        print(f"preview={preview.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
