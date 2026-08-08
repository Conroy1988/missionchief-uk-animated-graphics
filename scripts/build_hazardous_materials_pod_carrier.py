#!/usr/bin/env python3
"""Build the mounted Hazardous Materials Pod carrier master deterministically."""

from __future__ import annotations

import argparse
import hashlib
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
PRIME_MOVER_PATH = ROOT / "assets" / "exports" / "standard" / "static" / "pm.png"
POD_PATH = (
    ROOT
    / "assets"
    / "exports"
    / "standard"
    / "static"
    / "hazardous-materials-pod.png"
)
TARGET_PATH = (
    ROOT
    / "assets"
    / "masters"
    / "v1.2.2"
    / "hazardous-materials-pod-carrier.png"
)


def rgba(path: Path) -> Image.Image:
    with Image.open(path) as image:
        image.load()
        return image.convert("RGBA")


def build() -> tuple[Image.Image, Image.Image]:
    """Mount the existing pod module on the fleet's matching prime-mover chassis."""
    prime_mover = rgba(PRIME_MOVER_PATH)
    pod = rgba(POD_PATH)
    if prime_mover.size != (110, 43):
        raise ValueError(f"unexpected PM source dimensions: {prime_mover.size}")
    if pod.size != (83, 28):
        raise ValueError(f"unexpected pod source dimensions: {pod.size}")

    carrier = prime_mover.copy()
    alpha = carrier.getchannel("A")
    alpha_draw = ImageDraw.Draw(alpha)
    # Remove the empty hook-lift boom while retaining the three-axle chassis and cab.
    alpha_draw.rectangle((0, 0, 77, 28), fill=0)
    carrier.putalpha(alpha)

    mounted_pod = pod.resize((79, 27), Image.Resampling.LANCZOS)
    carrier.alpha_composite(mounted_pod, (1, 2))
    return carrier, prime_mover


def png_bytes(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def validate(carrier: Image.Image, prime_mover: Image.Image) -> None:
    if carrier.size != prime_mover.size:
        raise ValueError("carrier must retain the PM chassis canvas")
    if carrier.getchannel("A").getbbox() is None:
        raise ValueError("carrier contains no visible pixels")

    # The complete front cab must remain byte-identical to the established PM artwork.
    cab_box = (80, 0, carrier.width, carrier.height)
    if ImageChops.difference(carrier.crop(cab_box), prime_mover.crop(cab_box)).getbbox():
        raise ValueError("prime-mover cab changed while mounting the pod")

    # Require a clearly visible mounted body and the full three-axle road chassis.
    body_alpha = carrier.getchannel("A").crop((1, 2, 80, 29))
    if sum(value >= 96 for value in body_alpha.get_flattened_data()) < 1_450:
        raise ValueError("mounted pod body is incomplete")
    wheel_alpha = carrier.getchannel("A").crop((0, 29, 110, 43))
    if sum(value >= 96 for value in wheel_alpha.get_flattened_data()) < 500:
        raise ValueError("carrier chassis or wheels are incomplete")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the committed master is the exact deterministic output",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    carrier, prime_mover = build()
    validate(carrier, prime_mover)
    rendered = png_bytes(carrier)
    digest = hashlib.sha256(rendered).hexdigest()

    if args.check:
        if not TARGET_PATH.is_file():
            raise FileNotFoundError(TARGET_PATH)
        if TARGET_PATH.read_bytes() != rendered:
            raise ValueError("committed Hazardous Materials Pod carrier master is stale")
        print(f"PASS {TARGET_PATH.relative_to(ROOT)} sha256={digest}")
        return

    TARGET_PATH.parent.mkdir(parents=True, exist_ok=True)
    TARGET_PATH.write_bytes(rendered)
    print(f"Built {TARGET_PATH.relative_to(ROOT)} sha256={digest}")


if __name__ == "__main__":
    main()
