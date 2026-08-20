#!/usr/bin/env python3
"""Build all v2 MissionChief-native response APNGs and lighting metadata."""

from __future__ import annotations

import json
import math

from PIL import Image, ImageDraw, ImageFilter

from v2_emergency_light import Fixture, FlashFrame, ROAD_DOUBLE_FLASH, render_lit_frame, save_apng
from v2_helicopter_rotors import (
    geometry_manifest,
    prepare_helicopter_base,
    render_helicopter_motion,
)
from v2_profile import (
    ANIMATED_DIR,
    EXPORT_CANVAS,
    EXPORT_SCALE,
    MASTER_CANVAS,
    MASTER_DIR,
    RELEASE,
    RELEASE_CANDIDATE,
    ROOT,
    compact_export,
)


SLOTS = json.loads((ROOT / "data/vehicle-slots.json").read_text())["slots"]
PROTOTYPES = {
    item["id"]: item
    for item in json.loads((ROOT / "data/prototypes.json").read_text())["vehicles"]
}
FIXTURE_REPORT = ROOT / f"data/{RELEASE}-light-fixtures.json"
BUILD_REPORT = ROOT / f"data/{RELEASE}-animation-build-report.json"


AIRCRAFT_IDS = {
    "hems",
    "police-helicopter",
    "coastguard-rescue-helicopter",
    "coastguard-rescue-helicopter-large",
}
MARINE_IDS = {"ilb", "alb"}
AMBER_IDS = {
    "airfield-operations-vehicle",
    "airfield-operations-supervisor",
    "recovery-vehicle",
    "flatbed-recovery-vehicle",
    "hgv-recovery-vehicle",
    "rescue-stairs",
    "medical-equipment-trailer",
}
GREEN_IDS = {"general-practitioner"}
CYCLE_IDS = {"medical-cycle-responder"}
TOWED_IDS = {
    "flood-rescue-unit-trailer",
    "inland-rescue-boat-trailer",
    "rescue-watercraft-trailer",
    "hovercraft-trailer",
    "hovercraft-transporter",
    "boat-trailer",
    "medical-equipment-trailer",
    "pump-trailer",
    "operational-support-trailer",
    "sar-flood-rescue-trailer",
}
POD_IDS = {
    "water-pod",
    "bulk-foam-pod",
    "rescue-pod",
    "command-pod",
    "welfare-pod",
    "basu-pod",
    "misting-pod",
    "hazardous-materials-pod",
    "osu-pod",
    "hvp",
}


AIRCRAFT_PATTERN = tuple(
    FlashFrame(groups, duration)
    for groups, duration in (
        ({"a": 1.00, "nav": 0.45}, 70),
        ({"nav": 0.28}, 55),
        ({"a": 0.82, "nav": 0.45}, 70),
        ({"nav": 0.28}, 75),
        ({"b": 1.00, "nav": 0.45}, 70),
        ({"nav": 0.28}, 55),
        ({"b": 0.82, "nav": 0.45}, 70),
        ({"nav": 0.28}, 75),
        ({"a": 0.95, "b": 0.18, "nav": 0.45}, 70),
        ({"nav": 0.28}, 55),
        ({"a": 0.18, "b": 0.95, "nav": 0.45}, 70),
        ({"nav": 0.28}, 75),
        ({"strobe": 1.00, "nav": 0.55}, 65),
        ({"nav": 0.25}, 70),
        ({"strobe": 0.88, "nav": 0.55}, 65),
        ({"nav": 0.25}, 90),
        ({"a": 0.75, "b": 0.75, "nav": 0.45}, 80),
        ({"nav": 0.25}, 145),
    )
)


MARINE_PATTERN = tuple(
    FlashFrame(groups, duration)
    for groups, duration in (
        ({"a": 1.00, "nav": 0.55}, 85),
        ({"nav": 0.35}, 60),
        ({"a": 0.82, "nav": 0.55}, 85),
        ({"nav": 0.35}, 70),
        ({"b": 1.00, "nav": 0.55}, 85),
        ({"nav": 0.35}, 60),
        ({"b": 0.82, "nav": 0.55}, 85),
        ({"nav": 0.35}, 70),
        ({"a": 0.92, "b": 0.20, "nav": 0.60}, 85),
        ({"nav": 0.35}, 60),
        ({"a": 0.20, "b": 0.92, "nav": 0.60}, 85),
        ({"nav": 0.35}, 70),
        ({"a": 0.78, "nav": 0.55}, 80),
        ({"nav": 0.35}, 60),
        ({"b": 0.78, "nav": 0.55}, 80),
        ({"nav": 0.35}, 70),
        ({"a": 0.72, "b": 0.72, "nav": 0.65}, 90),
        ({"nav": 0.35}, 145),
    )
)


def point_at(bbox: tuple[int, int, int, int], fx: float, fy: float) -> tuple[int, int]:
    x1, y1, x2, y2 = bbox
    return round(x1 + (x2 - x1) * fx), round(y1 + (y2 - y1) * fy)


def snap_to_vehicle(alpha: Image.Image, point: tuple[int, int], radius: int = 12) -> tuple[int, int]:
    px, py = point
    pixels = alpha.load()
    best: tuple[float, int, int] | None = None
    for y in range(max(0, py - radius), min(alpha.height, py + radius + 1)):
        for x in range(max(0, px - radius), min(alpha.width, px + radius + 1)):
            if pixels[x, y] < 96:
                continue
            distance = (x - px) ** 2 + (y - py) ** 2
            candidate = (distance, y, x)
            if best is None or candidate < best:
                best = candidate
    return (best[2], best[1]) if best else point


def module(group: str, centre: tuple[int, int], colour: str, radius: float = 2.1) -> Fixture:
    cx, cy = centre
    return Fixture(
        group,
        "polygon",
        ((cx - 2, cy - 1), (cx + 2, cy - 2), (cx + 3, cy), (cx - 2, cy + 2)),
        colour=colour,
        bloom_radius=radius,
    )


def repeater(group: str, centre: tuple[int, int], colour: str) -> Fixture:
    cx, cy = centre
    return Fixture(group, "ellipse", ((cx - 2, cy - 2), (cx + 2, cy + 2)), colour=colour, bloom_radius=2.0)


def bar_fixtures(
    alpha: Image.Image,
    centre: tuple[int, int],
    colour: str,
    module_count: int = 4,
) -> list[Fixture]:
    centre = snap_to_vehicle(alpha, centre, radius=13)
    offsets = (-9, -3, 3, 9) if module_count == 4 else (-6, 0, 6)
    fixtures: list[Fixture] = []
    for index, dx in enumerate(offsets):
        desired = (centre[0] + dx, centre[1] - round(dx * 0.28))
        snapped = snap_to_vehicle(alpha, desired, radius=12)
        fixtures.append(module("a" if index < len(offsets) / 2 else "b", snapped, colour))
    return fixtures


def road_kind(asset_id: str, bbox: tuple[int, int, int, int], length: float) -> str:
    width, height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    if asset_id in CYCLE_IDS:
        return "cycle"
    if asset_id in POD_IDS:
        return "pod"
    if asset_id in TOWED_IDS:
        return "towed"
    if length >= 7.4 or width >= 158:
        return "heavy"
    if length >= 5.8 or height >= 82:
        return "van"
    return "car"


def road_fixtures(
    asset_id: str,
    base: Image.Image,
    bbox: tuple[int, int, int, int],
    length: float,
    colour: str,
) -> tuple[str, list[Fixture]]:
    if asset_id == "fire-rescue-pump":
        alpha = base.getchannel("A")
        return "heavy-calibrated", [
            module("a", snap_to_vehicle(alpha, (131, 106), 8), colour, 2.2),
            module("a", snap_to_vehicle(alpha, (142, 103), 8), colour, 2.2),
            module("b", snap_to_vehicle(alpha, (155, 100), 8), colour, 2.2),
            module("b", snap_to_vehicle(alpha, (167, 97), 10), colour, 2.2),
            repeater("a", snap_to_vehicle(alpha, (176, 143), 8), colour),
            repeater("b", snap_to_vehicle(alpha, (158, 159), 8), colour),
            repeater("a", snap_to_vehicle(alpha, (33, 93), 8), colour),
            repeater("b", snap_to_vehicle(alpha, (45, 114), 8), colour),
        ]

    alpha = base.getchannel("A")
    kind = road_kind(asset_id, bbox, length)
    if kind == "heavy":
        bar_at, front_a, front_b, rear_a, rear_b = (
            (0.79, 0.39), (0.91, 0.69), (0.82, 0.82), (0.10, 0.40), (0.17, 0.53)
        )
    elif kind == "van":
        bar_at, front_a, front_b, rear_a, rear_b = (
            (0.66, 0.34), (0.91, 0.70), (0.80, 0.84), (0.11, 0.40), (0.18, 0.54)
        )
    elif kind == "car":
        bar_at, front_a, front_b, rear_a, rear_b = (
            (0.58, 0.32), (0.91, 0.69), (0.78, 0.83), (0.12, 0.43), (0.20, 0.56)
        )
    elif kind == "towed":
        bar_at, front_a, front_b, rear_a, rear_b = (
            (0.79, 0.48), (0.92, 0.73), (0.83, 0.85), (0.09, 0.38), (0.17, 0.53)
        )
    elif kind == "cycle":
        bar_at, front_a, front_b, rear_a, rear_b = (
            (0.58, 0.41), (0.90, 0.62), (0.80, 0.77), (0.14, 0.42), (0.22, 0.57)
        )
    else:  # pod
        bar_at, front_a, front_b, rear_a, rear_b = (
            (0.58, 0.27), (0.90, 0.54), (0.82, 0.72), (0.10, 0.40), (0.18, 0.62)
        )

    fixtures = bar_fixtures(alpha, point_at(bbox, *bar_at), colour, 3 if kind == "cycle" else 4)
    for group, location in (("a", front_a), ("b", front_b), ("a", rear_a), ("b", rear_b)):
        fixtures.append(repeater(group, snap_to_vehicle(alpha, point_at(bbox, *location), 20), colour))
    return kind, fixtures


def aircraft_fixtures(base: Image.Image, bbox: tuple[int, int, int, int]) -> list[Fixture]:
    alpha = base.getchannel("A")
    specs = (
        ("a", 0.70, 0.43, "blue"),
        ("b", 0.83, 0.62, "blue"),
        ("a", 0.14, 0.36, "red"),
        ("nav", 0.58, 0.78, "green"),
        ("nav", 0.34, 0.22, "red"),
        ("strobe", 0.53, 0.42, "white"),
    )
    return [
        repeater(group, snap_to_vehicle(alpha, point_at(bbox, fx, fy), 20), colour)
        for group, fx, fy, colour in specs
    ]


def marine_fixtures(base: Image.Image, bbox: tuple[int, int, int, int]) -> list[Fixture]:
    alpha = base.getchannel("A")
    specs = (
        ("a", 0.63, 0.35, "blue"),
        ("b", 0.74, 0.48, "blue"),
        ("nav", 0.35, 0.34, "red"),
        ("nav", 0.55, 0.36, "green"),
        ("nav", 0.44, 0.18, "white"),
    )
    return [
        repeater(group, snap_to_vehicle(alpha, point_at(bbox, fx, fy), 20), colour)
        for group, fx, fy, colour in specs
    ]


def marine_motion(base: Image.Image, bbox: tuple[int, int, int, int], frame_index: int) -> Image.Image:
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    stern = point_at(bbox, 0.10, 0.67)
    pulse = 0.55 + 0.35 * math.sin(frame_index * math.tau / 6.0)
    for index in range(3):
        start = (stern[0] - 3 - index * 3, stern[1] + index * 2)
        end = (stern[0] - 13 - index * 5, stern[1] + 4 + index * 3)
        draw.line((start, end), fill=(203, 241, 255, round((95 - index * 18) * pulse)), width=1)
    layer = layer.filter(ImageFilter.GaussianBlur(0.45))
    result = base.copy()
    result.alpha_composite(layer)
    return result


def fixture_dict(fixture: Fixture) -> dict:
    return {
        "group": fixture.group,
        "shape": fixture.shape,
        "points": [list(point) for point in fixture.points],
        "colour": fixture.colour,
        "bloom_radius": fixture.bloom_radius,
    }


def main() -> None:
    ANIMATED_DIR.mkdir(parents=True, exist_ok=True)
    fixture_manifest: dict[str, dict] = {}
    build_entries: list[dict] = []

    for slot in SLOTS:
        asset_id = slot["asset_id"]
        base = Image.open(MASTER_DIR / f"{asset_id}.png").convert("RGBA")
        bbox = base.getchannel("A").getbbox()
        if bbox is None:
            raise RuntimeError(f"Empty v2 master: {asset_id}")
        length = float(PROTOTYPES[asset_id]["real_length_metres"])

        if asset_id in AIRCRAFT_IDS:
            profile = "aircraft-response"
            kind = "aircraft"
            fixtures = aircraft_fixtures(base, bbox)
            pattern = AIRCRAFT_PATTERN
        elif asset_id in MARINE_IDS:
            profile = "marine-response"
            kind = "marine"
            fixtures = marine_fixtures(base, bbox)
            pattern = MARINE_PATTERN
        else:
            colour = "amber" if asset_id in AMBER_IDS else "green" if asset_id in GREEN_IDS else "blue"
            profile = f"road-{colour}"
            kind, fixtures = road_fixtures(asset_id, base, bbox, length, colour)
            pattern = ROAD_DOUBLE_FLASH

        helicopter_base = prepare_helicopter_base(asset_id, base) if kind == "aircraft" else None
        master_frames: list[Image.Image] = []
        for index, state in enumerate(pattern):
            motion_base = (
                render_helicopter_motion(asset_id, helicopter_base, base, index, len(pattern))
                if kind == "aircraft"
                else marine_motion(base, bbox, index)
                if kind == "marine"
                else base
            )
            master_frames.append(
                render_lit_frame(motion_base, fixtures, state.groups, base.getchannel("A"))
            )
        frames = [compact_export(frame) for frame in master_frames]
        durations = [state.duration_ms for state in pattern]
        target = ANIMATED_DIR / f"{asset_id}.png"
        save_apng(str(target), frames, durations)

        fixture_manifest[asset_id] = {
            "slot": slot["slot"],
            "profile": profile,
            "kind": kind,
            "master_bbox": list(bbox),
            "export_bbox": list(compact_export(base).getchannel("A").getbbox()),
            "fixtures": [fixture_dict(fixture) for fixture in fixtures],
        }
        if kind == "aircraft":
            fixture_manifest[asset_id]["rotor_geometry"] = geometry_manifest(asset_id)
        build_entries.append(
            {
                "slot": slot["slot"],
                "asset_id": asset_id,
                "profile": profile,
                "kind": kind,
                "frames": len(frames),
                "duration_ms": sum(durations),
                "fixture_count": len(fixtures),
                "master_canvas": list(MASTER_CANVAS),
                "export_canvas": list(EXPORT_CANVAS),
                "target": str(target.relative_to(ROOT)),
            }
        )

    FIXTURE_REPORT.write_text(
        json.dumps(
            {
                "release": RELEASE_CANDIDATE,
                "master_coordinate_space": "absolute 200x200 master-canvas pixels",
                "export_canvas": list(EXPORT_CANVAS),
                "export_scale": EXPORT_SCALE,
                "fixture_standard": "physical lens + compact inner flare + faint outer bloom",
                "vehicles": fixture_manifest,
            },
            indent=2,
        )
        + "\n"
    )
    BUILD_REPORT.write_text(
        json.dumps(
            {
                "release": RELEASE_CANDIDATE,
                "master_canvas": list(MASTER_CANVAS),
                "export_canvas": list(EXPORT_CANVAS),
                "export_scale": EXPORT_SCALE,
                "assets": len(build_entries),
                "road_12_frame": sum(entry["frames"] == 12 for entry in build_entries),
                "aircraft_or_marine_18_frame": sum(entry["frames"] == 18 for entry in build_entries),
                "entries": build_entries,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"animated={len(build_entries)}")
    print(f"fixtures={FIXTURE_REPORT.relative_to(ROOT)}")
    print(f"report={BUILD_REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
