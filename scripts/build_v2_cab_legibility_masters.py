#!/usr/bin/env python3
"""Build the v2.0.3 cab-legibility master overrides.

The original v2.0.0 F/WrC, WrL CAFS and RP CAFS artwork showed only the
equipment body or rear of the appliance.  At MissionChief map scale those
sprites read as driverless modules.  This builder deliberately derives each
replacement from the already-approved, correctly cabbed vehicle of the same
physical class, then adds a small role cue without altering the shared fleet
perspective or canvas.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass

from PIL import Image, ImageChops, ImageDraw, ImageFont

from v2_profile import MASTER_CANVAS, MASTER_DIR, MASTER_OVERRIDE_DIR, ROOT


SOURCE_DIR = MASTER_DIR
OUTPUT_DIR = MASTER_OVERRIDE_DIR
CANVAS = MASTER_CANVAS


@dataclass(frozen=True)
class CabOverride:
    source_id: str
    badge: str
    badge_xy: tuple[int, int]
    badge_size: tuple[int, int]


OVERRIDES = {
    # A Foam/Water Carrier is a complete driven tanker, not the tank module
    # that was inherited by v2.0.0.
    "f-wrc": CabOverride("water-carrier", "F/WrC", (63, 108), (39, 12)),
    # The CAFS variants retain the approved Water Ladder and Rescue Pump cab,
    # chassis and wheel geometry.  A restrained plaque distinguishes the
    # compressed-air-foam installation at native map scale.
    "wrl-cafs": CabOverride(
        "fire-rescue-pump", "CAFS", (57, 116), (35, 12)
    ),
    "rp-cafs": CabOverride(
        "rescue-pump", "CAFS", (56, 116), (35, 12)
    ),
}


def add_role_badge(
    image: Image.Image,
    text: str,
    xy: tuple[int, int],
    size: tuple[int, int],
) -> None:
    """Add a restrained perspective-neutral identification plaque."""

    width, height = size
    badge = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(badge)
    draw.rounded_rectangle(
        (0, 0, width - 1, height - 1),
        radius=1,
        fill=(116, 24, 18, 224),
        outline=(208, 166, 33, 242),
        width=1,
    )
    font = ImageFont.load_default(size=7)
    text_box = draw.textbbox((0, 0), text, font=font, stroke_width=0)
    text_width = text_box[2] - text_box[0]
    text_height = text_box[3] - text_box[1]
    draw.text(
        ((width - text_width) // 2, (height - text_height) // 2 - text_box[1]),
        text,
        font=font,
        fill=(242, 210, 82, 246),
    )
    image.alpha_composite(badge, xy)


def render_override(spec: CabOverride) -> Image.Image:
    source_path = SOURCE_DIR / f"{spec.source_id}.png"
    with Image.open(source_path) as source_image:
        image = source_image.convert("RGBA")
    if image.size != CANVAS:
        raise ValueError(f"Expected {CANVAS} source canvas, found {image.size}: {source_path}")

    add_role_badge(image, spec.badge, spec.badge_xy, spec.badge_size)
    return image


def images_equal(left: Image.Image, right: Image.Image) -> bool:
    return (
        left.mode == right.mode
        and left.size == right.size
        and ImageChops.difference(left, right).getbbox() is None
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Fail if committed cab-legibility overrides are missing or stale",
    )
    args = parser.parse_args()

    errors: list[str] = []
    if not args.check:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for asset_id, spec in OVERRIDES.items():
        expected = render_override(spec)
        output_path = OUTPUT_DIR / f"{asset_id}.png"
        if args.check:
            if not output_path.exists():
                errors.append(f"missing/{asset_id}")
                continue
            with Image.open(output_path) as actual_image:
                actual = actual_image.convert("RGBA")
            if not images_equal(actual, expected):
                errors.append(f"stale/{asset_id}")
        else:
            expected.save(output_path, optimize=True)

    if OUTPUT_DIR.exists():
        actual_ids = {path.stem for path in OUTPUT_DIR.glob("*.png")}
        expected_ids = set(OVERRIDES)
        errors.extend(f"unexpected/{asset_id}" for asset_id in sorted(actual_ids - expected_ids))

    print(
        {
            "source": SOURCE_DIR.relative_to(ROOT).as_posix(),
            "output": OUTPUT_DIR.relative_to(ROOT).as_posix(),
            "overrides": sorted(OVERRIDES),
            "all_passed": not errors,
            "errors": errors,
        }
    )
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
