#!/usr/bin/env python3
"""Validate the v1.4.1 fixture-accurate emergency-light correction batch."""

from __future__ import annotations

import argparse
import io
import json
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageSequence

from build_v1_1_enhanced import FLASH_PATTERNS, blue_flash


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "data" / "v1.4-overhaul-profile.json"
STATIC_DIR = ROOT / "assets" / "exports" / "command" / "static"
ANIMATED_DIR = ROOT / "assets" / "exports" / "command" / "animated"
BASELINE = "v1.4.0"
EXPECTED_ASSETS = {
    "armed-response-vehicle",
    "joint-response-unit",
    "otl",
    "community-first-responder",
    "armed-traffic-car",
    "cbrn-vehicle",
    "control-van-sar",
    "drone-vehicle-police-station",
    "specialist-paramedic-rrv",
    "eod-commander",
    "eod-response-vehicle",
    "eod-medium-equipment-van",
    "eod-heavy-equipment-vehicle",
    "marine-eod-response-vehicle",
    "marine-eod-equipment-van",
}
ALLOWED_FIXTURES = {"compact-bar", "compact-point"}


def git_bytes(revision: str, path: Path) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{revision}:{path.as_posix()}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return result.stdout


def nearest_alpha_distance(alpha: Image.Image, x: int, y: int) -> float:
    nearest = math.inf
    for py in range(alpha.height):
        for px in range(alpha.width):
            if alpha.getpixel((px, py)) >= 80:
                nearest = min(nearest, math.hypot(x - px, y - py))
    return nearest


def maximum_local_difference(frames: list[Image.Image], static: Image.Image, x: int, y: int) -> int:
    maximum = 0
    for frame in frames:
        difference = ImageChops.difference(frame, static)
        crop = difference.crop((max(0, x - 2), max(0, y - 2), min(difference.width, x + 3), min(difference.height, y + 3)))
        maximum = max(maximum, *(sum(pixel[:3]) for pixel in crop.get_flattened_data()))
    return maximum


def significant_difference(frame: Image.Image, static: Image.Image) -> Image.Image:
    difference = ImageChops.difference(frame, static)
    red, green, blue = difference.convert("RGB").split()
    strongest = ImageChops.lighter(red, ImageChops.lighter(green, blue))
    return strongest.point(lambda value: 255 if value >= 12 else 0)


def peak_frame(frames: list[Image.Image], static: Image.Image) -> Image.Image:
    return max(
        frames,
        key=lambda frame: sum(significant_difference(frame, static).get_flattened_data()),
    )


def font(size: int) -> ImageFont.ImageFont:
    for candidate in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ):
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def render_preview(
    target: Path,
    ordered_assets: list[str],
    labels: dict[str, str],
    current_frames: dict[str, list[Image.Image]],
) -> None:
    width = 1700
    header = 76
    row_height = 138
    canvas = Image.new("RGB", (width, header + row_height * len(ordered_assets)), (14, 22, 30))
    draw = ImageDraw.Draw(canvas)
    draw.text((20, 16), "v1.4.1 fixture-accurate emergency lighting", fill="white", font=font(27))
    for x, heading in ((330, "STATIC"), (770, "v1.4.0 PEAK"), (1210, "v1.4.1 CORRECTED PEAK")):
        draw.text((x, 50), heading, fill=(149, 175, 194), font=font(13))

    for row, asset_id in enumerate(ordered_assets):
        y0 = header + row * row_height
        draw.rounded_rectangle((10, y0 + 6, width - 10, y0 + row_height - 6), radius=8, fill=(31, 44, 56))
        draw.text((24, y0 + 25), labels[asset_id], fill="white", font=font(17))
        draw.text((24, y0 + 52), asset_id, fill=(158, 182, 199), font=font(12))
        static = Image.open(STATIC_DIR / f"{asset_id}.png").convert("RGBA")
        baseline_bytes = git_bytes(BASELINE, Path("assets/exports/command/animated") / f"{asset_id}.png")
        with Image.open(io.BytesIO(baseline_bytes)) as baseline:
            baseline_frames = [frame.convert("RGBA") for frame in ImageSequence.Iterator(baseline)]
        examples = (static, peak_frame(baseline_frames, static), peak_frame(current_frames[asset_id], static))
        for column, image in enumerate(examples):
            scale = min(380 / image.width, 100 / image.height)
            resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.NEAREST)
            x0 = 300 + column * 440 + (400 - resized.width) // 2
            yy = y0 + 18 + (100 - resized.height) // 2
            canvas.paste(resized.convert("RGB"), (x0, yy))

    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target, format="PNG", optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=ROOT / "data" / "v1.4.1-fixture-accuracy-report.json")
    parser.add_argument("--preview", type=Path, default=ROOT / "assets" / "previews" / "v1.4.1" / "corrected-light-fixtures.png")
    args = parser.parse_args()

    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    release = str(profile["release"])
    fixture_path = ROOT / str(profile["current_light_fixtures_path"])
    fixtures = json.loads(fixture_path.read_text(encoding="utf-8"))
    if release != "v1.4.1" or str(fixtures.get("release")) != release:
        raise SystemExit("fixture-accuracy validator is not bound to v1.4.1")
    if set(fixtures["vehicles"]) != EXPECTED_ASSETS:
        raise SystemExit("fixture-correction asset inventory does not match the approved 15 vehicles")
    if set(fixtures["running_lights"]) != EXPECTED_ASSETS:
        raise SystemExit("vehicle-specific running-light inventory is incomplete")

    build = json.loads((ROOT / f"data/{release}-build-report.json").read_text(encoding="utf-8"))
    details = {item["id"]: item for item in build["vehicles_detail"]}
    manifest = json.loads((ROOT / "data/prototypes.json").read_text(encoding="utf-8"))
    vehicle_map = {item["id"]: item for item in manifest["vehicles"]}
    ordered_assets = sorted(EXPECTED_ASSETS, key=lambda asset_id: int(vehicle_map[asset_id]["missionchief_slot"]))

    errors: list[str] = []
    results = []
    current_frames: dict[str, list[Image.Image]] = {}
    for asset_id in ordered_assets:
        detail = details[asset_id]
        body_width = int(detail["motion_reference_dimensions"]["width"])
        body_height = int(detail["motion_reference_dimensions"]["height"])
        offset = int(detail["edge_padding"])
        static_path = STATIC_DIR / f"{asset_id}.png"
        animated_path = ANIMATED_DIR / f"{asset_id}.png"
        static = Image.open(static_path).convert("RGBA")
        with Image.open(animated_path) as animation:
            frames = [frame.convert("RGBA") for frame in ImageSequence.Iterator(animation)]
        current_frames[asset_id] = frames
        vehicle_errors: list[str] = []

        if static_path.read_bytes() != git_bytes(BASELINE, Path("assets/exports/command/static") / static_path.name):
            vehicle_errors.append("static artwork changed from v1.4.0")
        if ImageChops.difference(frames[0], static).getbbox() is not None:
            vehicle_errors.append("APNG frame 0 does not exactly match the static asset")
        if animated_path.read_bytes() == git_bytes(BASELINE, Path("assets/exports/command/animated") / animated_path.name):
            vehicle_errors.append("animated asset did not change from the defective v1.4.0 baseline")

        alpha = static.getchannel("A")
        allowed = Image.new("L", static.size, 0)
        allowed_draw = ImageDraw.Draw(allowed)
        anchor_details = []
        for index, light in enumerate(fixtures["vehicles"][asset_id], start=1):
            if light.get("fixture") not in ALLOWED_FIXTURES:
                vehicle_errors.append(f"light {index} is not a compact fixture")
            if light.get("kind") not in FLASH_PATTERNS:
                vehicle_errors.append(f"light {index} has no explicit valid kind")
            x_fraction, y_fraction = float(light["x"]), float(light["y"])
            if not 0.0 <= x_fraction <= 1.0 or not 0.0 <= y_fraction <= 1.0:
                vehicle_errors.append(f"light {index} is outside body coordinates")
            px = offset + round(x_fraction * (body_width - 1))
            py = offset + round(y_fraction * (body_height - 1))
            distance = nearest_alpha_distance(alpha, px, py)
            visible = maximum_local_difference(frames, static, px, py)
            if distance > 1.5:
                vehicle_errors.append(f"light {index} misses its physical fixture by {distance:.2f}px")
            if visible < 48:
                vehicle_errors.append(f"light {index} never flashes visibly")
            sample = blue_flash(static.size, px, py, float(light["size"]), str(light["kind"]), light["kind"] == "roof_a", str(light["fixture"]))
            bbox = sample.getchannel("A").point(lambda value: 255 if value >= 12 else 0).getbbox()
            if bbox is None or bbox[2] - bbox[0] > 7 or bbox[3] - bbox[1] > 5:
                vehicle_errors.append(f"light {index} exceeds the compact LED envelope")
            allowed_draw.rectangle((px - 4, py - 3, px + 4, py + 3), fill=255)
            anchor_details.append({"index": index, "pixel": {"x": px, "y": py}, "distance": round(distance, 2), "maximum_difference": visible})

        running_details = {}
        for name in ("front", "rear"):
            x_fraction, y_fraction = fixtures["running_lights"][asset_id][name]
            px = offset + round(float(x_fraction) * (body_width - 1))
            py = offset + round(float(y_fraction) * (body_height - 1))
            distance = nearest_alpha_distance(alpha, px, py)
            if distance > 1.5:
                vehicle_errors.append(f"{name} running lamp misses the vehicle by {distance:.2f}px")
            allowed_draw.rectangle((px - 2, py - 2, px + 2, py + 2), fill=255)
            running_details[name] = {"pixel": {"x": px, "y": py}, "distance": round(distance, 2)}

        outside_pixels = 0
        maximum_changed_pixels = 0
        changed_frames = 0
        for frame in frames:
            changed = significant_difference(frame, static)
            changed_count = sum(value == 255 for value in changed.get_flattened_data())
            changed_frames += int(changed_count > 0)
            maximum_changed_pixels = max(maximum_changed_pixels, changed_count)
            outside = ImageChops.multiply(changed, ImageChops.invert(allowed))
            outside_pixels += sum(value == 255 for value in outside.get_flattened_data())
        if outside_pixels:
            vehicle_errors.append(f"{outside_pixels} changed pixels fall outside declared lamp fixtures")
        if maximum_changed_pixels > 90:
            vehicle_errors.append(f"flash footprint is too large: {maximum_changed_pixels}px")
        if changed_frames < 3:
            vehicle_errors.append("fewer than three frames contain visible lamp activity")

        errors.extend(f"{asset_id}: {error}" for error in vehicle_errors)
        results.append({
            "slot": int(vehicle_map[asset_id]["missionchief_slot"]),
            "id": asset_id,
            "lights": anchor_details,
            "running_lights": running_details,
            "changed_frames": changed_frames,
            "maximum_changed_pixels": maximum_changed_pixels,
            "outside_fixture_pixels": outside_pixels,
            "passed": not vehicle_errors,
            "errors": vehicle_errors,
        })

    report = {
        "release": release,
        "baseline": BASELINE,
        "corrected_assets": len(results),
        "static_assets_unchanged": all(not any("static artwork changed" in error for error in item["errors"]) for item in results),
        "equipment_modules_preserved": all(item["outside_fixture_pixels"] == 0 for item in results),
        "floating_lamp_pixels": sum(item["outside_fixture_pixels"] for item in results),
        "all_passed": not errors,
        "errors": errors,
        "vehicles": results,
    }
    report_target = args.report if args.report.is_absolute() else ROOT / args.report
    preview_target = args.preview if args.preview.is_absolute() else ROOT / args.preview
    report_target.parent.mkdir(parents=True, exist_ok=True)
    report_target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    render_preview(
        preview_target,
        ordered_assets,
        {asset_id: vehicle_map[asset_id]["display_name"] for asset_id in ordered_assets},
        current_frames,
    )
    print(json.dumps({key: value for key, value in report.items() if key != "vehicles"}, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
