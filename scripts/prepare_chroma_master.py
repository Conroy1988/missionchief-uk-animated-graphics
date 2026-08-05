#!/usr/bin/env python3
"""Convert a generated magenta-key source into a transparent RGBA master."""

from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path

from PIL import Image


def is_background(r: int, g: int, b: int) -> bool:
    """Identify the deliberately saturated magenta key without touching red livery."""
    return r >= 145 and b >= 145 and g <= 135 and min(r, b) - g >= 55 and abs(r - b) <= 105


def is_strong_key(r: int, g: int, b: int) -> bool:
    """Remove enclosed holes that cannot be reached by the border flood fill."""
    return r >= 170 and b >= 170 and g <= 110 and min(r, b) - g >= 80 and abs(r - b) <= 80


def key_to_alpha(source: Image.Image) -> Image.Image:
    rgb = source.convert("RGB")
    width, height = rgb.size
    pixels = rgb.load()
    transparent = bytearray(width * height)
    queue: deque[tuple[int, int]] = deque()

    def enqueue(x: int, y: int) -> None:
        index = y * width + x
        if transparent[index] or not is_background(*pixels[x, y]):
            return
        transparent[index] = 1
        queue.append((x, y))

    for x in range(width):
        enqueue(x, 0)
        enqueue(x, height - 1)
    for y in range(height):
        enqueue(0, y)
        enqueue(width - 1, y)

    while queue:
        x, y = queue.popleft()
        if x:
            enqueue(x - 1, y)
        if x + 1 < width:
            enqueue(x + 1, y)
        if y:
            enqueue(x, y - 1)
        if y + 1 < height:
            enqueue(x, y + 1)

    output = rgb.convert("RGBA")
    out = output.load()
    for y in range(height):
        for x in range(width):
            if transparent[y * width + x] or is_strong_key(*pixels[x, y]):
                out[x, y] = (0, 0, 0, 0)

    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    args = parser.parse_args()

    result = key_to_alpha(Image.open(args.source))
    args.target.parent.mkdir(parents=True, exist_ok=True)
    # Pillow's aggressive PNG optimiser can truncate very large RGBA outputs on
    # some builds. A normal compressed save is deterministic and lossless.
    result.save(args.target, format="PNG", compress_level=6)
    # A small number of large RGBA images can be cut short by the bundled zlib
    # writer despite save() returning successfully. Verify the complete stream
    # and fall back to an uncompressed, still-lossless PNG when that occurs.
    try:
        with Image.open(args.target) as check:
            check.verify()
        with Image.open(args.target) as check:
            check.load()
    except Exception:
        result.save(args.target, format="PNG", compress_level=0)
        with Image.open(args.target) as check:
            check.verify()
        with Image.open(args.target) as check:
            check.load()

    corners = [
        result.getpixel((0, 0))[3],
        result.getpixel((result.width - 1, 0))[3],
        result.getpixel((0, result.height - 1))[3],
        result.getpixel((result.width - 1, result.height - 1))[3],
    ]
    if not all(alpha == 0 for alpha in corners):
        raise SystemExit("chroma extraction failed: one or more corners remain opaque")
    print(f"prepared {args.target} ({result.width}x{result.height})")


if __name__ == "__main__":
    main()
