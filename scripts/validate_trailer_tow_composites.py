#!/usr/bin/env python3
"""Fail closed if any standalone trailer ships without its complete tow unit."""

from __future__ import annotations

import json
import subprocess
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
PROFILE = json.loads((ROOT / "data" / "v1.4-overhaul-profile.json").read_text(encoding="utf-8"))
RELEASE = str(PROFILE["release"])
MASTER_REPORT_PATH = ROOT / "data" / f"{RELEASE}-trailer-tow-master-report.json"
BUILD_REPORT_PATH = ROOT / "data" / f"{RELEASE}-build-report.json"
REPORT_PATH = ROOT / "data" / f"{RELEASE}-trailer-tow-validation.json"
STATIC_DIR = ROOT / "assets" / "exports" / "command" / "static"
ANIMATED_DIR = ROOT / "assets" / "exports" / "command" / "animated"
PREVIEW_DIR = ROOT / "assets" / "previews" / RELEASE

EXPECTED = {
    "flood-rescue-unit-trailer": (62, "coastguard", "4x4-vehicle", "right"),
    "inland-rescue-boat-trailer": (68, "coastguard", "4x4-vehicle", "right"),
    "rescue-watercraft-trailer": (71, "lifeboat", "hovercraft-transporter", "right"),
    "hovercraft-trailer": (72, "lifeboat", "hovercraft-transporter", "right"),
    "boat-trailer": (75, "fire", "light-4x4", "right"),
    "medical-equipment-trailer": (82, "airfield", "airfield-operations-vehicle", "left"),
    "pump-trailer": (85, "search-and-rescue", "sar-4x4", "left"),
    "operational-support-trailer": (88, "search-and-rescue", "sar-4x4", "left"),
    "sar-flood-rescue-trailer": (89, "search-and-rescue", "sar-4x4", "left"),
}


def rgba(path: Path) -> Image.Image:
    with Image.open(path) as image:
        image.load()
        return image.convert("RGBA")


def frames(path: Path) -> list[Image.Image]:
    output = []
    with Image.open(path) as image:
        for index in range(int(getattr(image, "n_frames", 1))):
            image.seek(index)
            output.append(image.convert("RGBA").copy())
    return output


def baseline_static(asset_id: str) -> Image.Image:
    path = f"assets/exports/command/static/{asset_id}.png"
    content = subprocess.run(
        ["git", "show", f"v1.4.13:{path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    with Image.open(BytesIO(content)) as image:
        image.load()
        return image.convert("RGBA")


def font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    candidates = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    )
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def checkerboard(width: int, height: int) -> Image.Image:
    image = Image.new("RGBA", (width, height), (64, 78, 58, 255))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, round(height * 0.34), width, round(height * 0.82)), fill=(116, 111, 95, 255))
    draw.line((0, round(height * 0.34), width, round(height * 0.34)), fill=(47, 57, 45, 255), width=2)
    draw.line((0, round(height * 0.82), width, round(height * 0.82)), fill=(47, 57, 45, 255), width=2)
    return image


def render_before_after(vehicle_map: dict[str, dict]) -> Path:
    width, title_height, row_height = 1180, 74, 118
    canvas = Image.new("RGBA", (width, title_height + len(EXPECTED) * row_height), (31, 39, 44, 255))
    draw = ImageDraw.Draw(canvas)
    draw.text((24, 16), f"{RELEASE} complete trailer-tow repair", font=font(25, True), fill=(245, 248, 249, 255))
    draw.text((640, 26), "v1.4.13 · bare trailer", font=font(15, True), fill=(255, 178, 100, 255))
    draw.text((890, 26), f"{RELEASE} · complete unit", font=font(15, True), fill=(105, 220, 159, 255))
    ordered = sorted(EXPECTED, key=lambda item: EXPECTED[item][0])
    for row, asset_id in enumerate(ordered):
        y = title_height + row * row_height
        road = checkerboard(width - 300, row_height - 10)
        canvas.alpha_composite(road, (290, y + 5))
        vehicle = vehicle_map[asset_id]
        draw.text((22, y + 25), f"Slot {vehicle['missionchief_slot']}", font=font(14, True), fill=(255, 218, 76, 255))
        draw.text((22, y + 48), str(vehicle["display_name"]), font=font(14), fill=(236, 241, 243, 255))
        before = baseline_static(asset_id)
        after = rgba(STATIC_DIR / f"{asset_id}.png")
        before_scaled = before.resize((before.width * 2, before.height * 2), Image.Resampling.NEAREST)
        after_scaled = after.resize((after.width * 2, after.height * 2), Image.Resampling.NEAREST)
        canvas.alpha_composite(before_scaled, (670 - before_scaled.width // 2, y + 58 - before_scaled.height // 2))
        canvas.alpha_composite(after_scaled, (930 - after_scaled.width // 2, y + 58 - after_scaled.height // 2))
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    target = PREVIEW_DIR / "trailer-tow-composites-before-after.png"
    canvas.convert("RGB").save(target, format="PNG", optimize=True)
    return target


def render_inland_focus() -> Path:
    before = baseline_static("inland-rescue-boat-trailer")
    after = rgba(STATIC_DIR / "inland-rescue-boat-trailer.png")
    width, height = 1080, 360
    canvas = Image.new("RGBA", (width, height), (31, 39, 44, 255))
    draw = ImageDraw.Draw(canvas)
    draw.text((28, 20), "Inland Rescue Boat (Trailer) · towing-unit repair", font=font(25, True), fill=(245, 248, 249, 255))
    for left, title, image, colour in (
        (24, "Before · trailer moved by itself", before, (255, 178, 100, 255)),
        (544, "After · Coastguard response 4×4 towing", after, (105, 220, 159, 255)),
    ):
        draw.text((left + 18, 74), title, font=font(16, True), fill=colour)
        road = checkerboard(488, 230)
        canvas.alpha_composite(road, (left, 108))
        scale = 4 if image.width < 130 else 3
        enlarged = image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)
        canvas.alpha_composite(enlarged, (left + 244 - enlarged.width // 2, 222 - enlarged.height // 2))
    target = PREVIEW_DIR / "inland-rescue-boat-tow-repair-before-after.png"
    canvas.convert("RGB").save(target, format="PNG", optimize=True)
    return target


def main() -> None:
    master_report = json.loads(MASTER_REPORT_PATH.read_text(encoding="utf-8"))
    build_report = json.loads(BUILD_REPORT_PATH.read_text(encoding="utf-8"))
    fixture_data = json.loads((ROOT / str(PROFILE["current_light_fixtures_path"])).read_text(encoding="utf-8"))
    prototypes = json.loads((ROOT / "data" / "prototypes.json").read_text(encoding="utf-8"))["vehicles"]
    vehicle_map = {item["id"]: item for item in prototypes}
    master_map = {item["id"]: item for item in master_report["vehicles"]}
    detail_map = {item["id"]: item for item in build_report["vehicles_detail"]}
    configured = PROFILE.get("towed_units", {})
    errors: list[str] = []
    results = []

    if set(configured) != set(EXPECTED) or set(master_map) != set(EXPECTED):
        errors.append("complete trailer-tow inventory is not exactly the nine standalone trailer slots")
    if not master_report.get("all_passed") or int(master_report.get("bare_trailers_remaining", -1)) != 0:
        errors.append("deterministic master report does not certify zero bare trailers")

    for asset_id, (slot, service, tow_vehicle, hitch_side) in EXPECTED.items():
        item_errors = []
        config = configured[asset_id]
        master = master_map[asset_id]
        detail = detail_map[asset_id]
        static = rgba(STATIC_DIR / f"{asset_id}.png")
        animation = frames(ANIMATED_DIR / f"{asset_id}.png")
        master_image = rgba(ROOT / str(master["target"]))

        if (int(master["slot"]), master["service"], master["tow_vehicle"], master["hitch_side"]) != (
            slot,
            service,
            tow_vehicle,
            hitch_side,
        ):
            item_errors.append("service, slot, tow vehicle or hitch orientation mismatch")
        if not master.get("complete_towing_unit") or not master.get("hitch_connected"):
            item_errors.append("master is not a connected complete towing unit")
        if master_image.size != (
            int(master["master_dimensions"]["width"]),
            int(master["master_dimensions"]["height"]),
        ):
            item_errors.append("committed master dimensions differ from its deterministic report")
        if master_image.width <= max(
            int(master["tow_dimensions"]["width"]),
            int(master["trailer_dimensions"]["width"]),
        ):
            item_errors.append("master width does not contain both tow vehicle and trailer")
        if min(int(master["tow_visible_pixels"]), int(master["trailer_visible_pixels"])) < 500:
            item_errors.append("tow vehicle or trailer has insufficient retained structure")
        if detail.get("source_override") != f"assets/masters/{RELEASE}/{asset_id}.png":
            item_errors.append("production export does not use the release-specific tow master")
        if detail.get("towed_unit") != config:
            item_errors.append("production build metadata does not match towing policy")
        if float(detail["effective_real_length_metres"]) != float(config["real_length_metres"]):
            item_errors.append("production scale does not use the combined road-unit length")
        if detail["motion"] != config["expected_motion"]:
            item_errors.append("production APNG motion policy is incomplete")
        if int(detail["response_light_count"]) != int(config["expected_lights"]):
            item_errors.append("tow-vehicle response-light count is incorrect")
        marker_x = float(PROFILE["trailer_marker_geometry"][asset_id][0])
        if (hitch_side == "right" and marker_x > 0.05) or (hitch_side == "left" and marker_x < 0.95):
            item_errors.append("trailer rear marker is on the towing end")
        if len(animation) != int(PROFILE["frames"]):
            item_errors.append("complete towing-unit APNG frame count is incorrect")
        elif ImageChops.difference(animation[0], static).getbbox() is not None:
            item_errors.append("APNG frame 1 is not identical to the static complete unit")
        elif sum(ImageChops.difference(animation[0], frame).getbbox() is not None for frame in animation[1:]) < 3:
            item_errors.append("complete towing-unit APNG has insufficient active frames")
        fixture_count = len(fixture_data["vehicles"].get(asset_id, []))
        if fixture_count != int(config["expected_lights"]):
            item_errors.append("current fixture file does not match the tow-vehicle lamp inventory")

        errors.extend(f"{asset_id}: {error}" for error in item_errors)
        results.append(
            {
                "slot": slot,
                "id": asset_id,
                "tow_vehicle": tow_vehicle,
                "hitch_side": hitch_side,
                "master_dimensions": list(master_image.size),
                "command_dimensions": list(static.size),
                "frames": len(animation),
                "response_lights": fixture_count,
                "motion": detail["motion"],
                "passed": not item_errors,
                "errors": item_errors,
            }
        )

    previews = [render_before_after(vehicle_map), render_inland_focus()]
    report = {
        "release": RELEASE,
        "standalone_trailer_slots": len(EXPECTED),
        "complete_towing_units": sum(item["passed"] for item in results),
        "bare_trailers_remaining": 0 if not errors else None,
        "tow_vehicle_families": sorted({value[2] for value in EXPECTED.values()}),
        "preview_files": [str(path.relative_to(ROOT)) for path in previews],
        "vehicles": results,
        "errors": errors,
        "all_passed": not errors and len(results) == 9,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if not report["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
