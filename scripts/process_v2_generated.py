#!/usr/bin/env python3
"""Convert a generated chroma-screen v2 master into a MissionChief sprite."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image

from v2_profile import MASTER_CANVAS, MASTER_OVERRIDE_DIR, STATIC_DIR, compact_export


ROOT = Path(__file__).resolve().parents[1]
PROTOTYPES = ROOT / "data/prototypes.json"


CYCLE_IDS = {"medical-cycle-responder"}
AIRCRAFT_IDS = {
    "hems",
    "police-helicopter",
    "coastguard-rescue-helicopter",
    "coastguard-rescue-helicopter-large",
}
MARINE_IDS = {"ilb", "alb"}
TRAILER_IDS = {
    "flood-rescue-unit-trailer",
    "inland-rescue-boat-trailer",
    "rescue-watercraft-trailer",
    "hovercraft-trailer",
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


def extract_chroma(image: Image.Image) -> Image.Image:
    """Remove a saturated magenta screen with a narrow antialias transition."""

    rgb = np.asarray(image.convert("RGB"), dtype=np.int16)
    red = rgb[:, :, 0]
    green = rgb[:, :, 1]
    blue = rgb[:, :, 2]
    magenta_excess = np.minimum(red - green, blue - green)
    alpha = np.clip((72 - magenta_excess) * (255.0 / 58.0), 0, 255).astype(np.uint8)
    alpha[(red > 118) & (blue > 108) & (magenta_excess >= 72)] = 0

    rgba = np.dstack((rgb.astype(np.uint8), alpha))
    rgba[alpha == 0, :3] = 0
    return Image.fromarray(rgba, "RGBA")


def validate_chroma_screen(image: Image.Image) -> None:
    """Reject generations that substituted a scene or gradient background."""

    alpha = np.asarray(image.getchannel("A"))
    edge = max(8, min(image.size) // 32)
    border = np.concatenate(
        (
            alpha[:edge, :].ravel(),
            alpha[-edge:, :].ravel(),
            alpha[:, :edge].ravel(),
            alpha[:, -edge:].ravel(),
        )
    )
    transparent_fraction = float(np.count_nonzero(border <= 5)) / float(border.size)
    if transparent_fraction < 0.92:
        raise ValueError(
            "Generated source failed chroma-screen QA: "
            f"only {transparent_fraction:.1%} of the outer border extracted cleanly"
        )


def vehicle_record(asset_id: str) -> dict:
    data = json.loads(PROTOTYPES.read_text())
    for vehicle in data["vehicles"]:
        if vehicle["id"] == asset_id:
            return vehicle
    raise KeyError(f"Unknown vehicle id: {asset_id}")


def target_geometry(asset_id: str, length_metres: float) -> tuple[int, int, int]:
    """Return maximum subject width, height and ground baseline."""

    if asset_id in CYCLE_IDS:
        return 76, 100, 181
    if asset_id in AIRCRAFT_IDS:
        return 188, 176, 184
    if asset_id in MARINE_IDS:
        return min(188, round(length_metres * 15.0)), 142, 181
    if asset_id in TRAILER_IDS:
        return min(184, max(104, round(length_metres * 18.0))), 134, 184
    if asset_id in POD_IDS:
        return min(158, max(110, round(length_metres * 18.0))), 126, 181
    return min(188, max(104, round(length_metres * 20.0))), 150, 187


def fit_to_canvas(image: Image.Image, asset_id: str, length_metres: float) -> tuple[Image.Image, tuple[int, int, int, int]]:
    bbox = image.getchannel("A").getbbox()
    if bbox is None:
        raise RuntimeError("Chroma extraction produced an empty image")
    subject = image.crop(bbox)
    max_width, max_height, baseline = target_geometry(asset_id, length_metres)
    scale = min(max_width / subject.width, max_height / subject.height)
    size = (max(1, round(subject.width * scale)), max(1, round(subject.height * scale)))
    subject = subject.resize(size, Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", MASTER_CANVAS, (0, 0, 0, 0))
    left = (MASTER_CANVAS[0] - subject.width) // 2
    top = baseline - subject.height
    canvas.alpha_composite(subject, (left, top))

    pixels = np.asarray(canvas).copy()
    pixels[pixels[:, :, 3] <= 5] = 0
    canvas = Image.fromarray(pixels, "RGBA")
    return canvas, (left, top, left + subject.width, top + subject.height)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("asset_id")
    parser.add_argument("source", type=Path)
    parser.add_argument(
        "--master-dir",
        type=Path,
        default=MASTER_OVERRIDE_DIR,
        help="destination directory for the 200 px master override",
    )
    parser.add_argument(
        "--static-dir",
        type=Path,
        default=STATIC_DIR,
        help="destination directory for the derived 110 px static export",
    )
    args = parser.parse_args()

    record = vehicle_record(args.asset_id)
    extracted = extract_chroma(Image.open(args.source))
    validate_chroma_screen(extracted)
    canvas, bbox = fit_to_canvas(extracted, args.asset_id, float(record["real_length_metres"]))

    master = args.master_dir / f"{args.asset_id}.png"
    static = args.static_dir / f"{args.asset_id}.png"
    master.parent.mkdir(parents=True, exist_ok=True)
    static.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(master, optimize=True)
    compact = compact_export(canvas)
    compact.save(static, optimize=True)
    print(
        f"asset_id={args.asset_id} master_bbox={bbox} "
        f"export_bbox={compact.getchannel('A').getbbox()} "
        f"master={master.relative_to(ROOT) if master.is_relative_to(ROOT) else master}"
    )


if __name__ == "__main__":
    main()
