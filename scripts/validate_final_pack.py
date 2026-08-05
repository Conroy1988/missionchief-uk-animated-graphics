#!/usr/bin/env python3
"""Run release-level validation across the complete 117-slot pack."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageChops


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "prototypes.json"
SLOTS_PATH = ROOT / "data" / "vehicle-slots.json"
BUILD_REPORT_PATH = ROOT / "data" / "prototype-validation.json"
REPORT_PATH = ROOT / "data" / "final-pack-validation.json"
STATIC_DIR = ROOT / "assets" / "exports" / "standard" / "static"
ANIMATED_DIR = ROOT / "assets" / "exports" / "standard" / "animated"


def decoded_rgba(path: Path) -> Image.Image:
    with Image.open(path) as image:
        image.load()
        return image.convert("RGBA")


def different(left: Image.Image, right: Image.Image) -> bool:
    return ImageChops.difference(left, right).getbbox() is not None


def validate_vehicle(vehicle: dict) -> dict:
    asset_id = vehicle["id"]
    source_path = ROOT / vehicle["source"]
    static_path = STATIC_DIR / f"{asset_id}.png"
    animated_path = ANIMATED_DIR / f"{asset_id}.png"
    errors: list[str] = []

    for label, path in (("master", source_path), ("static", static_path), ("animated", animated_path)):
        if not path.is_file():
            errors.append(f"missing {label}: {path.relative_to(ROOT)}")

    if errors:
        return {"id": asset_id, "slot": vehicle["missionchief_slot"], "passed": False, "errors": errors}

    master = decoded_rgba(source_path)
    static = decoded_rgba(static_path)
    if master.getchannel("A").getbbox() is None:
        errors.append("master contains no visible pixels")
    corners = [
        static.getpixel((0, 0))[3],
        static.getpixel((static.width - 1, 0))[3],
        static.getpixel((0, static.height - 1))[3],
        static.getpixel((static.width - 1, static.height - 1))[3],
    ]
    if any(corners):
        errors.append("static export has a non-transparent canvas corner")

    with Image.open(animated_path) as animated:
        frame_count = int(getattr(animated, "n_frames", 1))
        durations: list[int] = []
        frames: list[Image.Image] = []
        for index in range(frame_count):
            animated.seek(index)
            durations.append(int(animated.info.get("duration", 0)))
            frames.append(animated.convert("RGBA").copy())

    if frame_count != 6:
        errors.append(f"APNG has {frame_count} frames instead of 6")
    elif frames:
        if different(frames[0], static):
            errors.append("APNG frame 1 is not pixel-aligned with the static PNG")
        changed = any(different(frames[0], frame) for frame in frames[1:])
        expects_flash = bool(vehicle.get("lights"))
        if expects_flash and not changed:
            errors.append("lit asset has no visible APNG frame changes")
        if not expects_flash and changed:
            errors.append("non-lit asset changes across APNG frames")

    return {
        "id": asset_id,
        "slot": vehicle["missionchief_slot"],
        "dimensions": {"width": static.width, "height": static.height},
        "apng_frames": frame_count,
        "durations_ms": durations,
        "flashing": bool(vehicle.get("lights")),
        "passed": not errors,
        "errors": errors,
    }


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    slot_data = json.loads(SLOTS_PATH.read_text(encoding="utf-8"))
    build_report = json.loads(BUILD_REPORT_PATH.read_text(encoding="utf-8"))
    vehicles = sorted(manifest["vehicles"], key=lambda item: int(item["missionchief_slot"]))
    slots = sorted(slot_data["slots"], key=lambda item: int(item["slot"]))

    pack_errors: list[str] = []
    vehicle_slots = [int(item["missionchief_slot"]) for item in vehicles]
    vehicle_ids = [item["id"] for item in vehicles]
    slot_numbers = [int(item["slot"]) for item in slots]
    if vehicle_slots != list(range(1, 118)):
        pack_errors.append("production manifest is not a complete ordered 1-117 sequence")
    if slot_numbers != list(range(1, 118)):
        pack_errors.append("slot manifest is not a complete ordered 1-117 sequence")
    if len(set(vehicle_ids)) != 117:
        pack_errors.append("production manifest contains duplicate asset IDs")
    if any(item.get("asset_status") != "approved-golden" for item in slots):
        pack_errors.append("one or more slot records are not approved-golden")
    if any(not item.get("asset_id") for item in slots):
        pack_errors.append("one or more slot records lack an asset ID")
    if slot_data.get("totals") != {"slots": 117, "approved_golden": 117, "planned": 0}:
        pack_errors.append("slot totals are not final")
    if not build_report.get("all_passed"):
        pack_errors.append("standard build report is not green")

    static_names = {path.stem for path in STATIC_DIR.glob("*.png")}
    animated_names = {path.stem for path in ANIMATED_DIR.glob("*.png")}
    expected_names = set(vehicle_ids)
    if static_names != expected_names:
        pack_errors.append("static export directory does not exactly match the manifest")
    if animated_names != expected_names:
        pack_errors.append("animated export directory does not exactly match the manifest")

    results = [validate_vehicle(vehicle) for vehicle in vehicles]
    report = {
        "release": "v1.0.0",
        "pack": manifest["pack"]["name"],
        "slots": len(slots),
        "static_pngs": len(static_names),
        "animated_apngs": len(animated_names),
        "flashing_assets": sum(bool(item.get("lights")) for item in vehicles),
        "non_flashing_assets": sum(not item.get("lights") for item in vehicles),
        "pack_errors": pack_errors,
        "vehicles": results,
        "all_passed": not pack_errors and all(item["passed"] for item in results),
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in report if key != "vehicles"}, indent=2))
    if not report["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
