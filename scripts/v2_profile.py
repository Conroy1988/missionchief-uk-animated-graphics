#!/usr/bin/env python3
"""Shared geometry and release contract for the compact v2 fleet exports."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from PIL import Image


ROOT = Path(__file__).resolve().parents[1]

RELEASE = "v2.0.3"
RELEASE_CANDIDATE = f"{RELEASE}-candidate"
MASTER_RELEASE = "v2.0.0"
MASTER_OVERRIDE_RELEASE = RELEASE

MASTER_CANVAS = (200, 200)
EXPORT_CANVAS = (110, 110)
EXPORT_SCALE = EXPORT_CANVAS[0] / MASTER_CANVAS[0]

MASTER_DIR = ROOT / "assets" / "masters" / MASTER_RELEASE
MASTER_OVERRIDE_DIR = ROOT / "assets" / "masters" / MASTER_OVERRIDE_RELEASE
STATIC_DIR = ROOT / "assets" / "exports" / "v2" / "static"
ANIMATED_DIR = ROOT / "assets" / "exports" / "v2" / "animated"
PREVIEW_DIR = ROOT / "assets" / "previews" / RELEASE


def master_path(asset_id: str) -> Path:
    """Return a release override when present, otherwise the immutable v2 base."""

    override = MASTER_OVERRIDE_DIR / f"{asset_id}.png"
    return override if override.exists() else MASTER_DIR / f"{asset_id}.png"


def resolved_master_ids() -> set[str]:
    """Return the complete logical master set across base and release overrides."""

    return {
        *(path.stem for path in MASTER_DIR.glob("*.png")),
        *(path.stem for path in MASTER_OVERRIDE_DIR.glob("*.png")),
    }


def compact_export(image: Image.Image) -> Image.Image:
    """Downsample a full 200px master/frame to the 110px map export contract."""

    from PIL import Image

    source = image.convert("RGBA")
    if source.size != MASTER_CANVAS:
        raise ValueError(f"Expected {MASTER_CANVAS} master canvas, found {source.size}")

    resized = source.resize(EXPORT_CANVAS, Image.Resampling.LANCZOS)
    # Lanczos creates a one-pixel near-transparent ringing fringe around the
    # sprite. Normalise alpha <= 5 exactly as the approved master pipeline does;
    # this removes invisible map footprint without touching visible edge or
    # light-bloom samples.
    resized.putdata(
        [pixel if pixel[3] > 5 else (0, 0, 0, 0) for pixel in resized.get_flattened_data()]
    )
    return resized


def scale_bbox(bbox: tuple[int, int, int, int] | None) -> tuple[int, int, int, int] | None:
    """Return the expected geometric bbox approximation in export coordinates."""

    if bbox is None:
        return None
    return tuple(round(value * EXPORT_SCALE) for value in bbox)
