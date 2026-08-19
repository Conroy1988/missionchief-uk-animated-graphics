#!/usr/bin/env python3
"""MissionChief-native v2 emergency-light renderer.

The v2 fleet lighting is rendered on the preserved 200 x 200 master canvas
before the complete frame is downsampled once to the compact map export. At
master scale a single source pixel is too easy to lose, while an unconstrained
blur becomes a blue tile after browser resampling. This module therefore
separates each fixture into a physical lens, a compact inner flare and a faint
outer bloom.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Sequence

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from apng_full_frame import save_full_frame_apng


LightColour = Literal["blue", "amber", "red", "green", "white"]
FixtureShape = Literal["polygon", "ellipse"]


PALETTES: dict[LightColour, dict[str, tuple[int, int, int]]] = {
    "blue": {
        "outer": (0, 74, 255),
        "inner": (0, 139, 255),
        "core": (42, 172, 255),
        "hot": (220, 250, 255),
    },
    "amber": {
        "outer": (255, 108, 0),
        "inner": (255, 165, 0),
        "core": (255, 194, 30),
        "hot": (255, 249, 198),
    },
    "red": {
        "outer": (255, 25, 12),
        "inner": (255, 58, 36),
        "core": (255, 92, 64),
        "hot": (255, 225, 215),
    },
    "green": {
        "outer": (0, 185, 90),
        "inner": (0, 226, 122),
        "core": (62, 255, 154),
        "hot": (224, 255, 237),
    },
    "white": {
        "outer": (146, 209, 255),
        "inner": (197, 232, 255),
        "core": (231, 247, 255),
        "hot": (255, 255, 255),
    },
}


@dataclass(frozen=True)
class Fixture:
    """One visible lamp lens in absolute 200 x 200 canvas coordinates."""

    group: str
    shape: FixtureShape
    points: tuple[tuple[int, int], ...]
    colour: LightColour = "blue"
    bloom_radius: float = 2.2
    bloom_strength: float = 1.0


@dataclass(frozen=True)
class FlashFrame:
    """Group intensities and duration for one lossless APNG frame."""

    groups: dict[str, float]
    duration_ms: int


ROAD_DOUBLE_FLASH: tuple[FlashFrame, ...] = (
    FlashFrame({"a": 1.00, "b": 0.08}, 90),
    FlashFrame({}, 50),
    FlashFrame({"a": 0.84}, 90),
    FlashFrame({}, 70),
    FlashFrame({"a": 0.08, "b": 1.00}, 90),
    FlashFrame({}, 50),
    FlashFrame({"b": 0.84}, 90),
    FlashFrame({}, 70),
    FlashFrame({"a": 0.92, "b": 0.20}, 90),
    FlashFrame({}, 50),
    FlashFrame({"a": 0.20, "b": 0.92}, 90),
    FlashFrame({}, 140),
)


def _draw_fixture(mask: Image.Image, fixture: Fixture, fill: int) -> None:
    draw = ImageDraw.Draw(mask)
    if fixture.shape == "polygon":
        draw.polygon(fixture.points, fill=fill)
        return
    if len(fixture.points) != 2:
        raise ValueError("Ellipse fixtures require top-left and bottom-right points")
    draw.ellipse((*fixture.points[0], *fixture.points[1]), fill=fill)


def _colour_layer(
    size: tuple[int, int], colour: tuple[int, int, int], alpha: Image.Image
) -> Image.Image:
    layer = Image.new("RGBA", size, (*colour, 0))
    layer.putalpha(alpha)
    return layer


def render_fixture(
    size: tuple[int, int], fixture: Fixture, intensity: float
) -> Image.Image:
    """Render a single fixture with a crisp lens and compact optical bloom."""

    strength = max(0.0, min(1.0, float(intensity)))
    result = Image.new("RGBA", size, (0, 0, 0, 0))
    if strength <= 0:
        return result

    palette = PALETTES[fixture.colour]
    source = Image.new("L", size, 0)
    _draw_fixture(source, fixture, 255)

    outer = source.filter(ImageFilter.GaussianBlur(fixture.bloom_radius * 1.75))
    outer = outer.point(
        lambda value: round(value * 0.38 * strength * fixture.bloom_strength)
    )
    result.alpha_composite(_colour_layer(size, palette["outer"], outer))

    inner = source.filter(ImageFilter.GaussianBlur(fixture.bloom_radius * 0.72))
    inner = inner.point(
        lambda value: round(value * 0.72 * strength * fixture.bloom_strength)
    )
    result.alpha_composite(_colour_layer(size, palette["inner"], inner))

    core = source.point(lambda value: round(value * strength))
    result.alpha_composite(_colour_layer(size, palette["core"], core))

    # A one-pixel hot centre survives downsampling and makes the on-state
    # unmistakable without increasing the apparent size of the fixture.
    hot = source.filter(ImageFilter.MinFilter(3))
    if hot.getbbox() is None:
        hot = source
    hot = hot.point(lambda value: round(value * 0.92 * strength))
    result.alpha_composite(_colour_layer(size, palette["hot"], hot))
    return result


def render_lit_frame(
    base: Image.Image,
    fixtures: Sequence[Fixture],
    groups: dict[str, float],
    vehicle_clip: Image.Image | None = None,
) -> Image.Image:
    """Composite one emergency-light state over a transparent static sprite."""

    frame = base.convert("RGBA").copy()
    for fixture in fixtures:
        strength = groups.get(fixture.group, 0.0)
        if strength <= 0:
            continue
        layer = render_fixture(frame.size, fixture, strength)
        if vehicle_clip is not None:
            # Keep the solid lens on the vehicle while allowing the deliberately
            # small blurred light to spill a few pixels beyond its silhouette.
            lens = Image.new("L", frame.size, 0)
            _draw_fixture(lens, fixture, round(255 * strength))
            clipped_lens = ImageChops.multiply(lens, vehicle_clip)
            layer.alpha_composite(
                _colour_layer(frame.size, PALETTES[fixture.colour]["hot"], clipped_lens)
            )
        frame.alpha_composite(layer)
    return frame


def build_animation_frames(
    base: Image.Image,
    fixtures: Sequence[Fixture],
    pattern: Sequence[FlashFrame] = ROAD_DOUBLE_FLASH,
) -> tuple[list[Image.Image], list[int]]:
    """Return full-canvas RGBA frames and their per-frame durations."""

    clip = base.convert("RGBA").getchannel("A")
    frames = [render_lit_frame(base, fixtures, state.groups, clip) for state in pattern]
    return frames, [state.duration_ms for state in pattern]


def save_apng(
    target: str,
    frames: Sequence[Image.Image],
    durations: Sequence[int],
) -> None:
    """Write a lossless, infinitely looping, full-frame APNG."""

    if not frames:
        raise ValueError("At least one animation frame is required")
    if len(frames) != len(durations):
        raise ValueError("Frame and duration counts differ")
    save_full_frame_apng(
        list(frames),
        [int(duration) for duration in durations],
        Path(target),
        compress_level=9,
        disposal=0,
        blend=0,
    )
