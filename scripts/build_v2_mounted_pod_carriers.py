#!/usr/bin/env python3
"""Build the ten v2.1.1 unified mounted specialist-carrier masters.

The previous correction composited a complete legacy module behind a Prime
Mover cab. Several of those sources retained their own underframe and wheels,
so the result read as an articulated trailer at live map scale. v2.1.1 uses
purpose-built full-vehicle chroma sources: one continuous rigid chassis,
exactly three road axles and a role body seated directly behind the cab.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops

from process_v2_generated import (
    extract_chroma,
    fit_to_canvas,
    validate_chroma_screen,
    vehicle_record,
)
from v2_profile import (
    ARTWORK_RELEASE,
    EXPECTED_OVERRIDE_IDS,
    MASTER_CANVAS,
    MASTER_OVERRIDE_DIR,
    MOUNTED_CARRIER_IDS,
    RELEASE,
    ROOT,
)


SOURCE_DIR = ROOT / "assets" / "sources" / ARTWORK_RELEASE
OUTPUT_DIR = MASTER_OVERRIDE_DIR

EXPECTED_LEFT = 8
EXPECTED_RIGHT = 192
EXPECTED_BASELINE = 186
MIN_MASTER_HEIGHT = 105
MAX_MASTER_HEIGHT = 120
MIN_OPAQUE_PIXELS = 12_000
MIN_COMPONENT_COVERAGE = 0.998

COUPLING_REGION = (96, 115, 132, 176)
CHASSIS_REGION = (20, 145, 145, 186)
CAB_REGION = (118, 90, 192, 186)
ROLE_BODY_REGION = (8, 68, 118, 160)
MIN_REGION_OPAQUE = {
    "coupling": 1_850,
    "chassis": 2_000,
    "cab": 5_500,
    "role_body": 6_200,
}
WHEEL_REGIONS = {
    "rear_axle_1": (16, 142, 45, 184),
    "rear_axle_2": (43, 149, 74, 188),
    "front_axle": (138, 150, 173, 192),
}
MIN_DARK_WHEEL_PIXELS = {
    "rear_axle_1": 100,
    "rear_axle_2": 100,
    "front_axle": 580,
}


def source_path(asset_id: str) -> Path:
    return SOURCE_DIR / f"{asset_id}-chroma.png"


def expected_master(asset_id: str) -> Image.Image:
    source = source_path(asset_id)
    if not source.exists():
        raise FileNotFoundError(f"Missing unified carrier source: {source.relative_to(ROOT)}")
    extracted = extract_chroma(Image.open(source))
    validate_chroma_screen(extracted)
    record = vehicle_record(asset_id)
    canvas, _ = fit_to_canvas(extracted, asset_id, float(record["real_length_metres"]))
    return canvas


def images_equal(left: Image.Image, right: Image.Image) -> bool:
    return (
        left.mode == right.mode
        and left.size == right.size
        and ImageChops.difference(left, right).getbbox() is None
    )


def opaque_in_region(alpha: Image.Image, region: tuple[int, int, int, int]) -> int:
    return sum(value >= 96 for value in alpha.crop(region).get_flattened_data())


def dark_in_region(image: Image.Image, region: tuple[int, int, int, int]) -> int:
    return sum(
        alpha >= 96 and max(red, green, blue) < 95
        for red, green, blue, alpha in image.crop(region).get_flattened_data()
    )


def largest_component_coverage(alpha: Image.Image) -> float:
    opaque = np.asarray(alpha) >= 96
    total = int(np.count_nonzero(opaque))
    if not total:
        return 0.0

    visited = np.zeros_like(opaque, dtype=bool)
    largest = 0
    height, width = opaque.shape
    for start_y, start_x in zip(*np.where(opaque & ~visited)):
        if visited[start_y, start_x]:
            continue
        stack = [(int(start_y), int(start_x))]
        visited[start_y, start_x] = True
        size = 0
        while stack:
            y, x = stack.pop()
            size += 1
            for dy, dx in (
                (-1, -1), (-1, 0), (-1, 1),
                (0, -1),             (0, 1),
                (1, -1),  (1, 0),  (1, 1),
            ):
                next_y, next_x = y + dy, x + dx
                if (
                    0 <= next_y < height
                    and 0 <= next_x < width
                    and opaque[next_y, next_x]
                    and not visited[next_y, next_x]
                ):
                    visited[next_y, next_x] = True
                    stack.append((next_y, next_x))
        largest = max(largest, size)
    return largest / total


def integration_metrics(image: Image.Image) -> dict:
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    return {
        "bbox": list(bbox) if bbox else None,
        "opaque_pixels": sum(value >= 96 for value in alpha.get_flattened_data()),
        "largest_component_coverage": largest_component_coverage(alpha),
        "region_opaque_pixels": {
            "coupling": opaque_in_region(alpha, COUPLING_REGION),
            "chassis": opaque_in_region(alpha, CHASSIS_REGION),
            "cab": opaque_in_region(alpha, CAB_REGION),
            "role_body": opaque_in_region(alpha, ROLE_BODY_REGION),
        },
        "wheel_dark_pixels": {
            name: dark_in_region(image, region)
            for name, region in WHEEL_REGIONS.items()
        },
    }


def validation_errors(asset_id: str, image: Image.Image) -> list[str]:
    metrics = integration_metrics(image)
    errors: list[str] = []
    bbox = metrics["bbox"]
    if image.size != MASTER_CANVAS:
        errors.append(f"canvas={image.size}")
    if bbox is None:
        return [*errors, "empty-subject"]
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    if (bbox[0], bbox[2], bbox[3]) != (EXPECTED_LEFT, EXPECTED_RIGHT, EXPECTED_BASELINE):
        errors.append(f"geometry={bbox}")
    if not MIN_MASTER_HEIGHT <= height <= MAX_MASTER_HEIGHT:
        errors.append(f"height={height}")
    if width != EXPECTED_RIGHT - EXPECTED_LEFT:
        errors.append(f"width={width}")
    if metrics["opaque_pixels"] < MIN_OPAQUE_PIXELS:
        errors.append(f"opaque={metrics['opaque_pixels']}")
    if metrics["largest_component_coverage"] < MIN_COMPONENT_COVERAGE:
        errors.append(
            "disconnected-subject="
            f"{metrics['largest_component_coverage']:.4f}"
        )
    for name, minimum in MIN_REGION_OPAQUE.items():
        actual = metrics["region_opaque_pixels"][name]
        if actual < minimum:
            errors.append(f"{name}-integration={actual}")
    for name, minimum in MIN_DARK_WHEEL_PIXELS.items():
        actual = metrics["wheel_dark_pixels"][name]
        if actual < minimum:
            errors.append(f"{name}-missing={actual}")
    return [f"{asset_id}/{error}" for error in errors]


def validate_override_scope(*, require_complete: bool) -> list[str]:
    if not OUTPUT_DIR.exists():
        return ["missing-override-directory"]
    actual = {path.stem for path in OUTPUT_DIR.glob("*.png")}
    required = EXPECTED_OVERRIDE_IDS if require_complete else frozenset(MOUNTED_CARRIER_IDS)
    return [
        *(f"missing/{asset_id}" for asset_id in sorted(required - actual)),
        *(f"unexpected/{asset_id}" for asset_id in sorted(actual - EXPECTED_OVERRIDE_IDS)),
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if committed unified-carrier masters are missing or stale",
    )
    args = parser.parse_args()

    errors: list[str] = []
    if not args.check:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for asset_id in MOUNTED_CARRIER_IDS:
        try:
            expected = expected_master(asset_id)
            errors.extend(validation_errors(asset_id, expected))
            output = OUTPUT_DIR / f"{asset_id}.png"
            if args.check:
                if not output.exists():
                    errors.append(f"missing/{asset_id}")
                    continue
                actual = Image.open(output).convert("RGBA")
                if not images_equal(actual, expected):
                    errors.append(f"stale/{asset_id}")
                errors.extend(validation_errors(asset_id, actual))
            else:
                expected.save(output, optimize=True)
        except Exception as exc:
            errors.append(f"{asset_id}/{exc}")

    errors.extend(validate_override_scope(require_complete=args.check))
    result = {
        "release": RELEASE,
        "sources": SOURCE_DIR.relative_to(ROOT).as_posix(),
        "output": OUTPUT_DIR.relative_to(ROOT).as_posix(),
        "mounted_carriers": list(MOUNTED_CARRIER_IDS),
        "all_passed": not errors,
        "errors": sorted(set(errors)),
    }
    print(result)
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
