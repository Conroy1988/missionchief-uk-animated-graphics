#!/usr/bin/env python3
"""Shared point-emitter primitive for every MissionChief fleet profile."""

from __future__ import annotations

from PIL import Image, ImageChops, ImageDraw


POINT_EMITTER_FIXTURE = "point-emitter"
ALLOWED_EMERGENCY_FIXTURES = {POINT_EMITTER_FIXTURE}


def render_point_emitter(
    size: tuple[int, int],
    px: int,
    py: int,
    strength: float = 1.0,
    clip_mask: Image.Image | None = None,
    variant: int = 0,
) -> Image.Image:
    """Render a bright lamp lens with no line, ellipse, blur, or filled tile.

    The output is exactly one physical source pixel. MissionChief sprites are
    too small for a synthetic bloom: neighbouring glow pixels reconnect after
    browser scaling and become the bars this renderer exists to prevent.
    """
    intensity = max(0.0, min(1.0, float(strength)))
    emitter = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(emitter)
    if 0 <= px < size[0] and 0 <= py < size[1]:
        colour = (
            (0, round(82 + 24 * intensity), 255, 255)
            if variant % 2
            else (188, 246, 255, 255)
        )
        draw.point((px, py), fill=colour)

    if clip_mask is not None:
        emitter.putalpha(ImageChops.multiply(emitter.getchannel("A"), clip_mask))
    return emitter
