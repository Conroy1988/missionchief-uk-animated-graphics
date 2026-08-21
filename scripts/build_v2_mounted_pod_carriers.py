#!/usr/bin/env python3
"""Build the ten v2.0.4 mounted specialist-carrier master overrides."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

from v2_profile import (
    EXPECTED_OVERRIDE_IDS,
    MASTER_CANVAS,
    MASTER_DIR,
    MASTER_OVERRIDE_DIR,
    MOUNTED_CARRIER_IDS,
    ROOT,
)


PRIME_MOVER_PATH = MASTER_DIR / "pm.png"
OUTPUT_DIR = MASTER_OVERRIDE_DIR
TARGET_MODULE_LEFT = 10
TARGET_MODULE_BOTTOM = 149

# The v2 PM source shows its empty hook-lift boom raised.  A loaded carrier
# keeps the approved chassis and cab but removes only that raised boom before
# the role-specific module is mounted.
HOOK_BOOM_POLYGON = (
    (58, 47),
    (73, 47),
    (96, 86),
    (96, 103),
    (85, 110),
    (75, 94),
    (57, 61),
)

# The cab is in the foreground of the fixed lower-right three-quarter view.
# Restoring it after the module composite gives the correct physical occlusion
# without redrawing a single cab, windscreen, wheel or bumper pixel.
CAB_FOREGROUND_POLYGON = (
    (98, 89),
    (151, 89),
    (199, 118),
    (199, 199),
    (88, 199),
    (88, 147),
    (97, 131),
)


@dataclass(frozen=True)
class CarrierBuild:
    image: Image.Image
    module_offset: tuple[int, int]
    module_bbox: tuple[int, int, int, int]


def rgba(path: Path) -> Image.Image:
    with Image.open(path) as image:
        image.load()
        return image.convert("RGBA")


def polygon_mask(points: tuple[tuple[int, int], ...]) -> Image.Image:
    mask = Image.new("L", MASTER_CANVAS, 0)
    ImageDraw.Draw(mask).polygon(points, fill=255)
    return mask


def masked_difference(
    left: Image.Image,
    right: Image.Image,
    mask: Image.Image,
) -> Image.Image:
    difference = ImageChops.difference(left, right)
    transparent = Image.new("RGBA", MASTER_CANVAS, (0, 0, 0, 0))
    return Image.composite(difference, transparent, mask)


def build_one(asset_id: str, prime_mover: Image.Image) -> CarrierBuild:
    module_path = MASTER_DIR / f"{asset_id}.png"
    module = rgba(module_path)
    if prime_mover.size != MASTER_CANVAS or module.size != MASTER_CANVAS:
        raise ValueError(f"{asset_id}: every source must use the {MASTER_CANVAS} master canvas")

    module_bbox = module.getchannel("A").getbbox()
    if module_bbox is None:
        raise ValueError(f"{asset_id}: source module is empty")
    offset = (
        TARGET_MODULE_LEFT - module_bbox[0],
        TARGET_MODULE_BOTTOM - module_bbox[3],
    )

    hook_mask = polygon_mask(HOOK_BOOM_POLYGON)
    carrier = prime_mover.copy()
    carrier.paste((0, 0, 0, 0), mask=hook_mask)
    carrier.alpha_composite(module, offset)

    cab_mask = polygon_mask(CAB_FOREGROUND_POLYGON)
    carrier.paste(prime_mover, (0, 0), cab_mask)

    if masked_difference(carrier, prime_mover, cab_mask).getbbox() is not None:
        raise ValueError(f"{asset_id}: approved prime-mover cab changed during mounting")
    return CarrierBuild(carrier, offset, module_bbox)


def images_equal(left: Image.Image, right: Image.Image) -> bool:
    return (
        left.mode == right.mode
        and left.size == right.size
        and ImageChops.difference(left, right).getbbox() is None
    )


def validate_build(asset_id: str, build: CarrierBuild, prime_mover: Image.Image) -> None:
    carrier = build.image
    bbox = carrier.getchannel("A").getbbox()
    if carrier.size != MASTER_CANVAS:
        raise ValueError(f"{asset_id}: carrier canvas changed")
    if bbox is None or bbox[2] - bbox[0] < 170:
        raise ValueError(f"{asset_id}: carrier is too short to contain its cab and module")
    if bbox[0] > TARGET_MODULE_LEFT or bbox[2] < 185 or bbox[3] < 187:
        raise ValueError(f"{asset_id}: complete road chassis is not retained: {bbox}")

    front_box = (135, 90, 200, 195)
    if ImageChops.difference(
        carrier.crop(front_box), prime_mover.crop(front_box)
    ).getbbox() is not None:
        raise ValueError(f"{asset_id}: windscreen, front wheel or bumper changed")

    module = rgba(MASTER_DIR / f"{asset_id}.png")
    shifted = Image.new("RGBA", MASTER_CANVAS, (0, 0, 0, 0))
    shifted.alpha_composite(module, build.module_offset)
    expected_module_alpha = shifted.getchannel("A")
    cab_mask = polygon_mask(CAB_FOREGROUND_POLYGON)
    visible_module_alpha = ImageChops.multiply(expected_module_alpha, ImageChops.invert(cab_mask))
    required = sum(value >= 96 for value in visible_module_alpha.get_flattened_data())
    retained = sum(
        value >= 96
        for value in ImageChops.multiply(carrier.getchannel("A"), visible_module_alpha).get_flattened_data()
    )
    if required < 900 or retained < round(required * 0.97):
        raise ValueError(f"{asset_id}: mounted role module is incomplete")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if committed mounted-carrier overrides are missing or stale",
    )
    args = parser.parse_args()

    prime_mover = rgba(PRIME_MOVER_PATH)
    errors: list[str] = []
    if not args.check:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for asset_id in MOUNTED_CARRIER_IDS:
        try:
            expected_build = build_one(asset_id, prime_mover)
            validate_build(asset_id, expected_build, prime_mover)
            output_path = OUTPUT_DIR / f"{asset_id}.png"
            if args.check:
                if not output_path.exists():
                    errors.append(f"missing/{asset_id}")
                    continue
                actual = rgba(output_path)
                if not images_equal(actual, expected_build.image):
                    errors.append(f"stale/{asset_id}")
            else:
                expected_build.image.save(output_path, optimize=True)
        except Exception as exc:
            errors.append(f"{asset_id}/{exc}")

    if OUTPUT_DIR.exists():
        actual_ids = {path.stem for path in OUTPUT_DIR.glob("*.png")}
        errors.extend(
            f"unexpected/{asset_id}"
            for asset_id in sorted(actual_ids - EXPECTED_OVERRIDE_IDS)
        )

    result = {
        "source_prime_mover": PRIME_MOVER_PATH.relative_to(ROOT).as_posix(),
        "source_modules": [
            (MASTER_DIR / f"{asset_id}.png").relative_to(ROOT).as_posix()
            for asset_id in MOUNTED_CARRIER_IDS
        ],
        "output": OUTPUT_DIR.relative_to(ROOT).as_posix(),
        "mounted_carriers": list(MOUNTED_CARRIER_IDS),
        "all_passed": not errors,
        "errors": errors,
    }
    print(result)
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
