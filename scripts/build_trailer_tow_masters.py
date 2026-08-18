#!/usr/bin/env python3
"""Build deterministic complete towing units for standalone trailer slots.

MissionChief moves each vehicle-graphics slot as one map object.  A bare trailer
therefore appears to propel itself.  These masters retain the existing trailer
artwork but connect it to a service-appropriate tow vehicle so the complete
road-going unit is represented by the one graphic the game animates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import tempfile
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "data" / "v1.4-overhaul-profile.json"
PROFILE = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
RELEASE = str(PROFILE["release"])
OUTPUT_DIR = ROOT / "assets" / "masters" / RELEASE
REPORT_PATH = ROOT / "data" / f"{RELEASE}-trailer-tow-master-report.json"
FIXTURE_PATH = ROOT / str(PROFILE["current_light_fixtures_path"])


def rgba(path: Path) -> Image.Image:
    with Image.open(path) as image:
        image.load()
        return image.convert("RGBA")


def png_bytes(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True, compress_level=9)
    return buffer.getvalue()


def alpha_pixels(image: Image.Image, threshold: int = 96) -> int:
    return sum(value >= threshold for value in image.getchannel("A").get_flattened_data())


def edge_hitch_y(image: Image.Image, side: str) -> int:
    """Locate the road-height hitch/bumper pixels at one outside edge."""
    width, height = image.size
    band = range(min(5, width)) if side == "left" else range(max(0, width - 5), width)
    lower_limit = round(height * 0.52)
    candidates = [
        y
        for x in band
        for y in range(lower_limit, height)
        if image.getpixel((x, y))[3] >= 96
    ]
    if not candidates:
        raise ValueError(f"no strong lower-edge hitch pixels on {side} side of {image.size}")
    return round(statistics.median(candidates))


def component_geometry(
    tow: Image.Image,
    trailer: Image.Image,
    hitch_side: str,
    gap: int,
) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]]:
    """Return canvas size plus bottom-aligned tow and trailer offsets."""
    height = max(tow.height, trailer.height)
    tow_y = height - tow.height
    trailer_y = height - trailer.height
    if hitch_side == "right":
        trailer_offset = (0, trailer_y)
        tow_offset = (trailer.width + gap, tow_y)
    elif hitch_side == "left":
        tow_offset = (0, tow_y)
        trailer_offset = (tow.width + gap, trailer_y)
    else:
        raise ValueError(f"unsupported hitch side: {hitch_side}")
    return (tow.width + gap + trailer.width, height), tow_offset, trailer_offset, (gap, height)


def build_one(asset_id: str, config: dict) -> tuple[Image.Image, dict]:
    tow_path = ROOT / str(config["tow_source"])
    trailer_path = ROOT / str(config["trailer_source"])
    tow = rgba(tow_path)
    trailer = rgba(trailer_path)
    gap = int(config.get("hitch_gap_pixels", 2))
    hitch_side = str(config["hitch_side"])
    canvas_size, tow_offset, trailer_offset, _ = component_geometry(tow, trailer, hitch_side, gap)
    output = Image.new("RGBA", canvas_size, (0, 0, 0, 0))

    if hitch_side == "right":
        trailer_anchor = (
            trailer_offset[0] + trailer.width - 1,
            trailer_offset[1] + edge_hitch_y(trailer, "right"),
        )
        tow_anchor = (
            tow_offset[0],
            tow_offset[1] + edge_hitch_y(tow, "left"),
        )
    else:
        tow_anchor = (
            tow_offset[0] + tow.width - 1,
            tow_offset[1] + edge_hitch_y(tow, "right"),
        )
        trailer_anchor = (
            trailer_offset[0],
            trailer_offset[1] + edge_hitch_y(trailer, "left"),
        )

    # A dark steel drawbar joins two already-authored hitch/bumper pixels.  It
    # is painted first so the original vehicle and trailer artwork remains on
    # top and unchanged at the attachment points.
    draw = ImageDraw.Draw(output)
    draw.line([trailer_anchor, tow_anchor], fill=(24, 31, 35, 255), width=2)
    draw.point([trailer_anchor, tow_anchor], fill=(24, 31, 35, 255))
    output.alpha_composite(trailer, trailer_offset)
    output.alpha_composite(tow, tow_offset)

    master_pixels = alpha_pixels(output)
    tow_pixels = alpha_pixels(tow)
    trailer_pixels = alpha_pixels(trailer)
    if output.width <= max(tow.width, trailer.width) + round(min(tow.width, trailer.width) * 0.72):
        raise ValueError(f"{asset_id}: composite is too short to contain both road units")
    if master_pixels < round((tow_pixels + trailer_pixels) * 0.94):
        raise ValueError(f"{asset_id}: tow vehicle or trailer lost visible structure")
    if not all(output.getpixel(point)[3] for point in (tow_anchor, trailer_anchor)):
        raise ValueError(f"{asset_id}: hitch does not connect both components")

    metadata = {
        "id": asset_id,
        "tow_vehicle": str(config["tow_vehicle"]),
        "hitch_side": hitch_side,
        "hitch_gap_pixels": gap,
        "tow_source": str(tow_path.relative_to(ROOT)),
        "trailer_source": str(trailer_path.relative_to(ROOT)),
        "target": str((OUTPUT_DIR / f"{asset_id}.png").relative_to(ROOT)),
        "tow_dimensions": {"width": tow.width, "height": tow.height},
        "trailer_dimensions": {"width": trailer.width, "height": trailer.height},
        "master_dimensions": {"width": output.width, "height": output.height},
        "tow_offset": {"x": tow_offset[0], "y": tow_offset[1]},
        "trailer_offset": {"x": trailer_offset[0], "y": trailer_offset[1]},
        "tow_anchor": {"x": tow_anchor[0], "y": tow_anchor[1]},
        "trailer_anchor": {"x": trailer_anchor[0], "y": trailer_anchor[1]},
        "tow_visible_pixels": tow_pixels,
        "trailer_visible_pixels": trailer_pixels,
        "master_visible_pixels": master_pixels,
        "hitch_connected": True,
        "complete_towing_unit": True,
        "effective_real_length_metres": float(config["real_length_metres"]),
    }
    return output, metadata


def response_geometry(config: dict, metadata: dict, vehicles: dict[str, dict]) -> tuple[list[dict], dict | None]:
    """Map the tow vehicle's authored lamps into the composite coordinate space."""
    if str(config.get("response_lighting", "blue")) != "blue":
        return [], None
    tow_id = str(config["tow_vehicle"])
    source_lights = vehicles[tow_id].get("lights", [])
    if len(source_lights) != 3:
        raise ValueError(f"{tow_id}: trailer tow source must expose exactly three response fixtures")
    width = int(metadata["master_dimensions"]["width"])
    height = int(metadata["master_dimensions"]["height"])
    tow_width = int(metadata["tow_dimensions"]["width"])
    tow_height = int(metadata["tow_dimensions"]["height"])
    ox = int(metadata["tow_offset"]["x"])
    oy = int(metadata["tow_offset"]["y"])
    right_facing = str(config["hitch_side"]) == "right"
    kinds = ("roof_a", "rear", "front") if right_facing else ("roof_a", "front", "rear")
    lights = []
    for index, light in enumerate(source_lights):
        x = (ox + float(light["x"]) * (tow_width - 1)) / max(1, width - 1)
        y = (oy + float(light["y"]) * (tow_height - 1)) / max(1, height - 1)
        if kinds[index] == "front" and not right_facing:
            # Keep the left-facing grille emitter one pixel inside the drawn
            # bumper after the complete unit is resized at map scale.
            x = max(x, 0.025)
        if kinds[index].startswith("roof") and config.get("roof_light_x_override") is not None:
            x = float(config["roof_light_x_override"])
        lights.append(
            {
                "x": round(x, 4),
                "y": round(y, 4),
                "group": str(light.get("group", "a")),
                "kind": kinds[index],
                "fixture": "point-emitter",
                "size": float(light.get("size", 0.58)),
            }
        )
    running = {
        "front": [0.985 if right_facing else 0.015, 0.64],
        "rear": [0.012 if right_facing else 0.988, 0.68],
    }
    return lights, running


def fixture_data(report: dict) -> dict:
    baseline_path = ROOT / str(PROFILE["towed_unit_fixture_baseline"])
    data = json.loads(baseline_path.read_text(encoding="utf-8"))
    data["release"] = RELEASE
    data["coordinate_space"] = "normalised current baked-master motion-reference body coordinates"
    for item in report["vehicles"]:
        asset_id = str(item["id"])
        if item["response_lights"]:
            data["vehicles"][asset_id] = item["response_lights"]
            data["running_lights"][asset_id] = item["running_lights"]
        else:
            data["vehicles"].pop(asset_id, None)
            data["running_lights"].pop(asset_id, None)
    return data


def build(destination: Path) -> dict:
    configurations = PROFILE.get("towed_units", {})
    expected_ids = set(PROFILE.get("motion", {}).get("trailer", []))
    if set(configurations) != expected_ids or len(configurations) != 9:
        raise ValueError("towed-unit profile must exactly cover all nine standalone trailer slots")

    vehicles = {
        item["id"]: item
        for item in json.loads((ROOT / "data" / "prototypes.json").read_text(encoding="utf-8"))["vehicles"]
    }
    destination.mkdir(parents=True, exist_ok=True)
    results = []
    for asset_id in sorted(configurations, key=lambda item: int(vehicles[item]["missionchief_slot"])):
        config = configurations[asset_id]
        output, metadata = build_one(asset_id, config)
        response_lights, running_lights = response_geometry(config, metadata, vehicles)
        metadata["response_lights"] = response_lights
        metadata["running_lights"] = running_lights
        metadata["response_lighting"] = str(config.get("response_lighting", "blue"))
        target = destination / f"{asset_id}.png"
        rendered = png_bytes(output)
        target.write_bytes(rendered)
        metadata.update(
            {
                "slot": int(vehicles[asset_id]["missionchief_slot"]),
                "service": str(vehicles[asset_id]["service"]),
                "sha256": hashlib.sha256(rendered).hexdigest(),
            }
        )
        results.append(metadata)

    return {
        "release": RELEASE,
        "purpose": "complete road-going tow vehicle and trailer composites for standalone MissionChief slots",
        "trailer_composites": len(results),
        "bare_trailers_remaining": 0,
        "vehicles": results,
        "all_passed": len(results) == 9 and all(item["hitch_connected"] for item in results),
    }


def check() -> None:
    if not REPORT_PATH.is_file():
        raise SystemExit(f"missing committed trailer-tow report: {REPORT_PATH.relative_to(ROOT)}")
    committed = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="trailer-tow-masters-") as temp:
        generated = build(Path(temp))
        expected_ids = set(PROFILE["towed_units"])
        actual_ids = {path.stem for path in OUTPUT_DIR.glob("*.png") if path.stem in expected_ids}
        if actual_ids != expected_ids:
            raise SystemExit(f"committed trailer-tow inventory mismatch: {sorted(actual_ids ^ expected_ids)}")
        for asset_id in sorted(expected_ids):
            if (Path(temp) / f"{asset_id}.png").read_bytes() != (OUTPUT_DIR / f"{asset_id}.png").read_bytes():
                raise SystemExit(f"deterministic trailer-tow master mismatch: {asset_id}")
        if generated != committed:
            raise SystemExit("deterministic trailer-tow report mismatch")
        expected_fixtures = fixture_data(generated)
        if not FIXTURE_PATH.is_file():
            raise SystemExit(f"missing committed light fixtures: {FIXTURE_PATH.relative_to(ROOT)}")
        if json.loads(FIXTURE_PATH.read_text(encoding="utf-8")) != expected_fixtures:
            raise SystemExit("deterministic trailer-tow light fixtures mismatch")
    print(json.dumps({"status": "PASS", "trailer_composites": 9}, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> None:
    if parse_args().check:
        check()
        return
    report = build(OUTPUT_DIR)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    FIXTURE_PATH.write_text(json.dumps(fixture_data(report), indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
