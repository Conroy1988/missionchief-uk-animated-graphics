#!/usr/bin/env python3
"""Build the complete mounted fire-service pod-carrier family deterministically."""

from __future__ import annotations

import argparse
import hashlib
import json
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
STANDARD_DIR = ROOT / "assets" / "exports" / "standard" / "static"
PRIME_MOVER_PATH = STANDARD_DIR / "pm.png"
TARGET_DIR = ROOT / "assets" / "masters" / "v1.2.3"

POD_CONFIG = {
    "water-pod": (83, 30),
    "bulk-foam-pod": (83, 29),
    "rescue-pod": (83, 33),
    "command-pod": (83, 49),
    "welfare-pod": (83, 33),
    "basu-pod": (83, 26),
    "misting-pod": (75, 35),
    "hazardous-materials-pod": (83, 28),
    "osu-pod": (86, 29),
}

MODULE_WIDTH = 79
MODULE_X = 1
MODULE_Y = 2
STANDARD_CHASSIS_TOP = 29


def rgba(path: Path) -> Image.Image:
    with Image.open(path) as image:
        image.load()
        return image.convert("RGBA")


def png_bytes(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def target_path(asset_id: str) -> Path:
    return TARGET_DIR / f"{asset_id}-carrier.png"


def build_one(asset_id: str, prime_mover: Image.Image) -> tuple[Image.Image, Image.Image, int]:
    """Mount one existing pod body on the established three-axle PM chassis."""
    source_path = STANDARD_DIR / f"{asset_id}.png"
    pod = rgba(source_path)
    expected_size = POD_CONFIG[asset_id]
    if pod.size != expected_size:
        raise ValueError(f"unexpected {asset_id} source dimensions: {pod.size}")

    module_height = max(1, round(pod.height * MODULE_WIDTH / pod.width))
    mounted_pod = pod.resize((MODULE_WIDTH, module_height), Image.Resampling.LANCZOS)

    # Tall specialist modules gain real canvas height instead of being squashed.
    # The PM moves down just enough to keep the module above the road chassis.
    chassis_shift = max(0, mounted_pod.height - (STANDARD_CHASSIS_TOP - MODULE_Y))
    carrier = Image.new(
        "RGBA",
        (prime_mover.width, prime_mover.height + chassis_shift),
        (0, 0, 0, 0),
    )
    carrier.alpha_composite(prime_mover, (0, chassis_shift))

    alpha = carrier.getchannel("A")
    alpha_draw = ImageDraw.Draw(alpha)
    # Remove the empty hook-lift boom while retaining the cab and road chassis.
    alpha_draw.rectangle((0, chassis_shift, 77, chassis_shift + 28), fill=0)
    carrier.putalpha(alpha)
    carrier.alpha_composite(mounted_pod, (MODULE_X, MODULE_Y))
    return carrier, mounted_pod, chassis_shift


def validate_one(
    asset_id: str,
    carrier: Image.Image,
    mounted_pod: Image.Image,
    prime_mover: Image.Image,
    chassis_shift: int,
) -> None:
    if carrier.width != prime_mover.width:
        raise ValueError(f"{asset_id}: carrier must retain the PM chassis width")
    if carrier.height != prime_mover.height + chassis_shift:
        raise ValueError(f"{asset_id}: carrier canvas height is inconsistent")
    if carrier.getchannel("A").getbbox() is None:
        raise ValueError(f"{asset_id}: carrier contains no visible pixels")

    cab_box = (80, chassis_shift, carrier.width, chassis_shift + prime_mover.height)
    if ImageChops.difference(
        carrier.crop(cab_box),
        prime_mover.crop((80, 0, prime_mover.width, prime_mover.height)),
    ).getbbox():
        raise ValueError(f"{asset_id}: prime-mover cab changed while mounting the pod")

    chassis_box = (
        0,
        chassis_shift + STANDARD_CHASSIS_TOP,
        carrier.width,
        chassis_shift + prime_mover.height,
    )
    if ImageChops.difference(
        carrier.crop(chassis_box),
        prime_mover.crop((0, STANDARD_CHASSIS_TOP, prime_mover.width, prime_mover.height)),
    ).getbbox():
        raise ValueError(f"{asset_id}: three-axle road chassis changed")

    module_box = (
        MODULE_X,
        MODULE_Y,
        MODULE_X + mounted_pod.width,
        MODULE_Y + mounted_pod.height,
    )
    module_alpha = carrier.getchannel("A").crop(module_box)
    source_alpha = mounted_pod.getchannel("A")
    visible = sum(value >= 96 for value in module_alpha.get_flattened_data())
    required = sum(value >= 96 for value in source_alpha.get_flattened_data())
    if visible < required:
        raise ValueError(f"{asset_id}: mounted pod body is incomplete")

    wheel_alpha = carrier.getchannel("A").crop(chassis_box)
    if sum(value >= 96 for value in wheel_alpha.get_flattened_data()) < 500:
        raise ValueError(f"{asset_id}: carrier chassis or wheels are incomplete")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify every committed master is the exact deterministic output",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    prime_mover = rgba(PRIME_MOVER_PATH)
    if prime_mover.size != (110, 43):
        raise ValueError(f"unexpected PM source dimensions: {prime_mover.size}")

    results = []
    for asset_id in POD_CONFIG:
        carrier, mounted_pod, chassis_shift = build_one(asset_id, prime_mover)
        validate_one(asset_id, carrier, mounted_pod, prime_mover, chassis_shift)
        rendered = png_bytes(carrier)
        digest = hashlib.sha256(rendered).hexdigest()
        target = target_path(asset_id)

        if args.check:
            if not target.is_file():
                raise FileNotFoundError(target)
            if target.read_bytes() != rendered:
                raise ValueError(f"committed {asset_id} carrier master is stale")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(rendered)

        results.append(
            {
                "id": asset_id,
                "target": str(target.relative_to(ROOT)),
                "dimensions": list(carrier.size),
                "chassis_shift": chassis_shift,
                "sha256": digest,
            }
        )

    mode = "Verified" if args.check else "Built"
    print(json.dumps({"status": mode, "mounted_carriers": results}, indent=2))


if __name__ == "__main__":
    main()
