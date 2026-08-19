#!/usr/bin/env python3
"""Upscale legacy sprites into clear chroma boards for v2 redraw reference."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SLOTS = json.loads((ROOT / "data/vehicle-slots.json").read_text())["slots"]
SOURCE_DIR = ROOT / "assets/exports/command/static"
TARGET_DIR = Path("/tmp/missionchief-v2-generation-references")


def main() -> None:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    for slot in SLOTS:
        asset_id = slot["asset_id"]
        source = Image.open(SOURCE_DIR / f"{asset_id}.png").convert("RGBA")
        bbox = source.getchannel("A").getbbox()
        if bbox is None:
            raise RuntimeError(f"Empty source sprite: {asset_id}")
        subject = source.crop(bbox)
        scale = min(860 / subject.width, 680 / subject.height)
        size = (round(subject.width * scale), round(subject.height * scale))
        subject = subject.resize(size, Image.Resampling.NEAREST)
        board = Image.new("RGB", (1024, 1024), (255, 0, 255))
        board.paste(subject, ((1024 - size[0]) // 2, (1024 - size[1]) // 2), subject)
        board.save(TARGET_DIR / f"{asset_id}.png", optimize=True)
    print(f"references={len(SLOTS)} target={TARGET_DIR}")


if __name__ == "__main__":
    main()
