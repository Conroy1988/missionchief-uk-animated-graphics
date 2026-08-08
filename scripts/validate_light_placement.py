#!/usr/bin/env python3
"""Validate audited emergency-light anchors against the rendered fleet body."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageSequence


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "data" / "v1.4-overhaul-profile.json"
MANIFEST_PATH = ROOT / "data" / "prototypes.json"
STATIC_DIR = ROOT / "assets" / "exports" / "command" / "static"
ANIMATED_DIR = ROOT / "assets" / "exports" / "command" / "animated"
MAXIMUM_ANCHOR_DISTANCE = 1.5


def nearest_alpha_distance(alpha: Image.Image, x: int, y: int) -> float:
    nearest = math.inf
    for py in range(alpha.height):
        for px in range(alpha.width):
            if alpha.getpixel((px, py)) >= 80:
                nearest = min(nearest, math.hypot(x - px, y - py))
    return nearest


def maximum_frame_difference(path: Path, static: Image.Image, x: int, y: int) -> int:
    maximum = 0
    with Image.open(path) as image:
        for frame in ImageSequence.Iterator(image):
            difference = ImageChops.difference(frame.convert("RGBA"), static)
            left = max(0, x - 2)
            top = max(0, y - 2)
            right = min(difference.width, x + 3)
            bottom = min(difference.height, y + 3)
            for pixel in difference.crop((left, top, right, bottom)).get_flattened_data():
                maximum = max(maximum, sum(pixel[:3]))
    return maximum


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    release = str(profile["release"])
    overrides_path = profile.get("light_overrides_path")
    if not overrides_path:
        raise SystemExit("profile does not declare light_overrides_path")
    placement_data = json.loads((ROOT / overrides_path).read_text(encoding="utf-8"))
    placement_release = str(profile.get("light_overrides_release", release))
    if placement_data.get("release") != placement_release:
        raise SystemExit("light-placement data does not match the declared source release")

    build_report = json.loads((ROOT / "data" / f"{release}-build-report.json").read_text(encoding="utf-8"))
    details = {item["id"]: item for item in build_report["vehicles_detail"]}
    master_report = json.loads((ROOT / profile["baked_master_report"]).read_text(encoding="utf-8"))
    master_transforms = {
        item["id"]: item["light_transform"] for item in master_report["vehicles"]
    }
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    current_fixture_data = {"vehicles": {}}
    current_fixtures_path = profile.get("current_light_fixtures_path")
    if current_fixtures_path:
        current_fixture_data = json.loads(
            (ROOT / str(current_fixtures_path)).read_text(encoding="utf-8")
        )
        if str(current_fixture_data.get("release")) != release:
            raise SystemExit("current light-fixture data does not match the active release")
    current_lights = current_fixture_data.get("vehicles", {})
    base_overrides = placement_data["vehicles"]
    audited_ids = set(base_overrides) | set(current_lights)
    effective_lights = {}
    for vehicle in manifest["vehicles"]:
        asset_id = str(vehicle["id"])
        if asset_id not in audited_ids:
            continue
        lights = base_overrides.get(asset_id, vehicle.get("lights", []))
        transform = master_transforms.get(asset_id)
        transformed = []
        for light in lights:
            item = dict(light)
            if transform is not None:
                item["x"] = float(transform["x_offset"]) + float(item["x"]) * float(transform["x_scale"])
                item["y"] = float(transform["y_offset"]) + float(item["y"]) * float(transform["y_scale"])
            transformed.append(item)
        effective_lights[asset_id] = current_lights.get(asset_id, transformed)
    errors: list[str] = []
    vehicles_detail = []
    maximum_distance = 0.0
    minimum_flash_difference = math.inf

    for asset_id, lights in effective_lights.items():
        if not lights:
            continue
        detail = details.get(asset_id)
        if detail is None:
            errors.append(f"unknown audited asset: {asset_id}")
            continue
        static_path = STATIC_DIR / f"{asset_id}.png"
        animated_path = ANIMATED_DIR / f"{asset_id}.png"
        static = Image.open(static_path).convert("RGBA")
        alpha = static.getchannel("A")
        body_width = int(detail["motion_reference_dimensions"]["width"])
        body_height = int(detail["motion_reference_dimensions"]["height"])
        edge_padding = int(detail["edge_padding"])
        light_detail = []
        vehicle_errors = []

        for index, light in enumerate(lights, start=1):
            x_fraction = float(light["x"])
            y_fraction = float(light["y"])
            if not 0.0 <= x_fraction <= 1.0 or not 0.0 <= y_fraction <= 1.0:
                vehicle_errors.append(f"light {index} is outside normalised body coordinates")
            px = edge_padding + round(x_fraction * (body_width - 1))
            py = edge_padding + round(y_fraction * (body_height - 1))
            distance = nearest_alpha_distance(alpha, px, py)
            difference = maximum_frame_difference(animated_path, static, px, py)
            maximum_distance = max(maximum_distance, distance)
            minimum_flash_difference = min(minimum_flash_difference, difference)
            if distance > MAXIMUM_ANCHOR_DISTANCE:
                vehicle_errors.append(
                    f"light {index} is {distance:.2f}px from the rendered vehicle"
                )
            if difference < 80:
                vehicle_errors.append(f"light {index} never produces a visible flash at its anchor")
            light_detail.append(
                {
                    "index": index,
                    "pixel": {"x": px, "y": py},
                    "anchor_distance_pixels": round(distance, 2),
                    "maximum_flash_difference": difference,
                }
            )

        errors.extend(f"{asset_id}: {error}" for error in vehicle_errors)
        vehicles_detail.append(
            {
                "id": asset_id,
                "lights": light_detail,
                "passed": not vehicle_errors,
                "errors": vehicle_errors,
            }
        )

    report = {
        "release": release,
        "audited_assets": sum(bool(lights) for lights in effective_lights.values()),
        "audited_lights": sum(len(lights) for lights in effective_lights.values()),
        "maximum_anchor_distance_pixels": round(maximum_distance, 2),
        "maximum_allowed_anchor_distance_pixels": MAXIMUM_ANCHOR_DISTANCE,
        "minimum_flash_difference": int(minimum_flash_difference),
        "all_passed": not errors,
        "errors": errors,
        "vehicles_detail": vehicles_detail,
    }
    if args.report:
        target = args.report if args.report.is_absolute() else ROOT / args.report
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "vehicles_detail"}, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
