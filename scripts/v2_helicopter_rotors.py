#!/usr/bin/env python3
"""Calibrated high-RPM rotor rendering for the compact v2 helicopter fleet.

The v2 masters contain stopped rotor blades.  Animated response graphics must
remove those baked blades before adding motion, otherwise every frame retains
a rigid cross underneath the animation.  Geometry here is deliberately tied
to each physical rotor rather than inferred from the whole vehicle bounding
box; that keeps fenestrons and exposed tail rotors correctly aligned.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

from PIL import Image, ImageChops, ImageDraw, ImageFilter


Point = tuple[int, int]
Box = tuple[int, int, int, int]
Blade = tuple[Point, Point]


@dataclass(frozen=True)
class BladeRemoval:
    hub: Point
    blades: tuple[Blade, ...]
    mask_width: int
    hub_keep_radius: int
    force_clear: frozenset[int]
    hub_ellipses: tuple[Box, ...]
    hub_rectangles: tuple[tuple[Box, int], ...] = ()
    fill_polygons: tuple[tuple[Point, ...], ...] = ()
    blade_widths: tuple[int, ...] = ()
    clone_rules: tuple[tuple[int, Point, tuple[int, int]], ...] = ()


@dataclass(frozen=True)
class MainRotor:
    removal: BladeRemoval
    disc_centre: Point
    disc_radii: Point
    tilt_degrees: float
    trace_count: int = 6


@dataclass(frozen=True)
class TailRotor:
    kind: str
    centre: Point
    radii: Point
    removal: BladeRemoval | None = None
    accent: tuple[int, int, int] | None = None
    aperture_box: Box | None = None


@dataclass(frozen=True)
class HelicopterGeometry:
    main: MainRotor
    tail: TailRotor


def _fenestron(aperture_box: Box) -> TailRotor:
    """Build tail motion directly from a measured physical duct opening."""

    left, top, right, bottom = aperture_box
    width = right - left
    height = bottom - top
    if width <= 0 or height <= 0 or width % 2 or height % 2:
        raise ValueError(f"Fenestron aperture must have a positive integer centre: {aperture_box}")
    return TailRotor(
        kind="fenestron",
        centre=(left + width // 2, top + height // 2),
        radii=(width // 2, height // 2),
        aperture_box=aperture_box,
    )


HELICOPTER_GEOMETRY: dict[str, HelicopterGeometry] = {
    "hems": HelicopterGeometry(
        main=MainRotor(
            removal=BladeRemoval(
                hub=(116, 106),
                blades=(
                    ((113, 104), (49, 73)),
                    ((119, 103), (173, 72)),
                    ((111, 109), (44, 140)),
                    ((121, 110), (192, 142)),
                ),
                mask_width=17,
                blade_widths=(17, 17, 11, 11),
                hub_keep_radius=4,
                force_clear=frozenset({0, 1}),
                hub_ellipses=((107, 99, 124, 111),),
                hub_rectangles=(((112, 105, 121, 120), 3),),
                fill_polygons=(
                    ((18, 90), (113, 99), (123, 116), (68, 127), (16, 106)),
                    ((70, 104), (118, 100), (153, 116), (181, 140), (180, 178), (92, 178), (68, 147)),
                ),
            ),
            disc_centre=(116, 106),
            disc_radii=(76, 36),
            tilt_degrees=1.0,
        ),
        tail=_fenestron((13, 84, 27, 104)),
    ),
    "police-helicopter": HelicopterGeometry(
        main=MainRotor(
            removal=BladeRemoval(
                hub=(110, 105),
                blades=(
                    ((110, 99), (49, 72)),
                    ((114, 103), (188, 82)),
                    ((103, 107), (14, 130)),
                    ((113, 108), (194, 142)),
                ),
                mask_width=17,
                blade_widths=(17, 17, 11, 11),
                hub_keep_radius=4,
                force_clear=frozenset({0, 1}),
                hub_ellipses=((101, 99, 115, 112),),
                hub_rectangles=(((104, 106, 113, 121), 3),),
                fill_polygons=(
                    ((14, 82), (109, 97), (119, 116), (68, 137), (13, 104)),
                    ((68, 99), (113, 95), (153, 107), (194, 136), (198, 184), (84, 187), (66, 144)),
                ),
            ),
            disc_centre=(110, 104),
            disc_radii=(92, 39),
            tilt_degrees=2.5,
        ),
        # Centre the motion on the measured physical duct—not the darker,
        # slightly higher stopped-blade cluster inherited from the source.
        tail=_fenestron((9, 77, 27, 97)),
    ),
    "coastguard-rescue-helicopter": HelicopterGeometry(
        main=MainRotor(
            removal=BladeRemoval(
                hub=(110, 120),
                blades=(
                    ((107, 117), (49, 97)),
                    ((113, 116), (145, 97)),
                    ((106, 121), (12, 143)),
                    ((113, 121), (194, 136)),
                    ((112, 123), (127, 182)),
                ),
                mask_width=11,
                blade_widths=(17, 17, 11, 11, 11),
                hub_keep_radius=4,
                force_clear=frozenset({0, 1}),
                hub_ellipses=((101, 112, 120, 124),),
                hub_rectangles=(((106, 116, 116, 132), 3),),
                fill_polygons=(
                    ((14, 104), (108, 112), (120, 135), (51, 148), (14, 131)),
                    ((47, 117), (113, 111), (154, 125), (181, 149), (176, 183), (65, 180), (45, 145)),
                ),
                clone_rules=(
                    (2, (0, -6), (0, 200)),
                    (4, (-8, 2), (0, 200)),
                ),
            ),
            disc_centre=(110, 120),
            disc_radii=(93, 58),
            tilt_degrees=-14.0,
            trace_count=7,
        ),
        tail=TailRotor(
            kind="exposed",
            centre=(18, 107),
            radii=(14, 14),
            removal=BladeRemoval(
                hub=(18, 107),
                blades=(
                    ((17, 105), (7, 94)),
                    ((19, 105), (26, 98)),
                    ((16, 108), (5, 114)),
                    ((20, 108), (25, 118)),
                ),
                mask_width=7,
                blade_widths=(11, 11, 11, 7),
                hub_keep_radius=2,
                force_clear=frozenset({0, 1, 2}),
                hub_ellipses=((15, 104, 21, 110),),
                fill_polygons=(((11, 101), (28, 106), (42, 124), (14, 127), (9, 112)),),
            ),
            accent=(255, 90, 58),
        ),
    ),
    "coastguard-rescue-helicopter-large": HelicopterGeometry(
        main=MainRotor(
            removal=BladeRemoval(
                hub=(118, 118),
                blades=(
                    ((116, 114), (107, 73)),
                    ((122, 116), (194, 96)),
                    ((114, 119), (25, 126)),
                    ((122, 121), (180, 161)),
                ),
                mask_width=11,
                blade_widths=(19, 19, 11, 11),
                hub_keep_radius=4,
                force_clear=frozenset({0, 1}),
                hub_ellipses=((108, 110, 127, 124),),
                hub_rectangles=(((113, 115, 123, 132), 3),),
                fill_polygons=(
                    ((13, 82), (119, 106), (129, 130), (43, 146), (12, 111)),
                    ((57, 107), (122, 106), (162, 126), (187, 158), (183, 186), (79, 184), (55, 146)),
                ),
                clone_rules=(
                    (3, (-5, 7), (0, 136)),
                    (3, (5, -7), (136, 200)),
                ),
            ),
            disc_centre=(118, 118),
            disc_radii=(98, 43),
            tilt_degrees=8.5,
        ),
        tail=TailRotor(
            kind="exposed",
            centre=(19, 84),
            radii=(15, 15),
            removal=BladeRemoval(
                hub=(19, 84),
                blades=(
                    ((18, 82), (14, 69)),
                    ((21, 83), (34, 78)),
                    ((17, 85), (6, 88)),
                    ((20, 86), (28, 100)),
                ),
                mask_width=7,
                blade_widths=(11, 11, 11, 7),
                hub_keep_radius=2,
                force_clear=frozenset({0, 1, 2}),
                hub_ellipses=((16, 81, 22, 87),),
                fill_polygons=(((11, 77), (34, 89), (44, 107), (13, 106), (8, 88)),),
            ),
            accent=(255, 90, 58),
        ),
    ),
}


def _phase_offset(asset_id: str) -> float:
    return math.radians(sum((index + 1) * ord(char) for index, char in enumerate(asset_id)) % 360)


def _blade_mask(size: tuple[int, int], removal: BladeRemoval) -> Image.Image:
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    widths = removal.blade_widths or (removal.mask_width,) * len(removal.blades)
    if len(widths) != len(removal.blades):
        raise ValueError("blade_widths must match blades")
    for (root, tip), width in zip(removal.blades, widths):
        radius = width // 2
        draw.line((root, tip), fill=255, width=width)
        draw.ellipse((tip[0] - radius, tip[1] - radius, tip[0] + radius, tip[1] + radius), fill=255)
    hub_x, hub_y = removal.hub
    keep = removal.hub_keep_radius
    draw.ellipse((hub_x - keep, hub_y - keep, hub_x + keep, hub_y + keep), fill=0)
    return mask


def _remove_baked_blades(source: Image.Image, removal: BladeRemoval) -> Image.Image:
    """Remove calibrated blade corridors using cross-blade colour sampling."""

    original = source.convert("RGBA")
    mask = _blade_mask(original.size, removal)
    source_pixels = original.load()
    mask_pixels = mask.load()
    cleared_alpha = original.getchannel("A")
    cleared_alpha.paste(0, (0, 0, *original.size), mask)
    widths = removal.blade_widths or (removal.mask_width,) * len(removal.blades)
    fill_widths = [width for index, width in enumerate(widths) if index not in removal.force_clear]
    closing_size = max(fill_widths, default=removal.mask_width) + 2
    if closing_size % 2 == 0:
        closing_size += 1
    body_support = cleared_alpha.filter(ImageFilter.MaxFilter(closing_size)).filter(
        ImageFilter.MinFilter(closing_size)
    )
    if removal.fill_polygons:
        allowed = Image.new("L", original.size, 0)
        allowed_draw = ImageDraw.Draw(allowed)
        for polygon in removal.fill_polygons:
            allowed_draw.polygon(polygon, fill=255)
        body_support = ImageChops.multiply(body_support, allowed)
    support_pixels = body_support.load()
    cleaned = original.copy()
    output_pixels = cleaned.load()
    branches: list[tuple[float, float, float, float, float, float, float, float]] = []
    for ((root_x, root_y), (tip_x, tip_y)), width in zip(removal.blades, widths):
        dx, dy = tip_x - root_x, tip_y - root_y
        length = math.hypot(dx, dy)
        branches.append(
            (
                float(root_x),
                float(root_y),
                dx / length,
                dy / length,
                -dy / length,
                dx / length,
                length,
                width / 2,
            )
        )

    hub_x, hub_y = removal.hub
    inpaint_pixels: list[Point] = []
    for y in range(original.height):
        for x in range(original.width):
            if mask_pixels[x, y] == 0:
                continue
            if math.hypot(x - hub_x, y - hub_y) <= removal.hub_keep_radius:
                continue

            best_branch_index = 0
            best_branch = branches[0]
            best_distance = float("inf")
            for branch_index, branch in enumerate(branches):
                root_x, root_y, tangent_x, tangent_y, normal_x, normal_y, length, half_width = branch
                along = (x - root_x) * tangent_x + (y - root_y) * tangent_y
                across = abs((x - root_x) * normal_x + (y - root_y) * normal_y)
                if -half_width <= along <= length + half_width and across < best_distance:
                    best_distance = across
                    best_branch_index = branch_index
                    best_branch = branch

            if best_branch_index in removal.force_clear:
                output_pixels[x, y] = (0, 0, 0, 0)
                continue

            root_x, root_y, tangent_x, tangent_y, normal_x, normal_y, _, half_width = best_branch
            samples_by_side: list[list[tuple[int, int, int, int]]] = [[], []]
            for side_index, side in enumerate((-1, 1)):
                for normal_distance in (half_width + 2, half_width + 4, half_width + 6):
                    for along_offset in (-2, 0, 2):
                        sample_x = round(
                            x + side * normal_x * normal_distance + tangent_x * along_offset
                        )
                        sample_y = round(
                            y + side * normal_y * normal_distance + tangent_y * along_offset
                        )
                        if not (0 <= sample_x < original.width and 0 <= sample_y < original.height):
                            continue
                        if mask_pixels[sample_x, sample_y] != 0:
                            continue
                        samples_by_side[side_index].append(source_pixels[sample_x, sample_y])

            if not any(samples_by_side):
                output_pixels[x, y] = (0, 0, 0, 0)
                continue
            support_alpha = support_pixels[x, y]
            if support_alpha < 16:
                output_pixels[x, y] = (0, 0, 0, 0)
                continue

            samples = [
                pixel
                for side_samples in samples_by_side
                for pixel in side_samples
                if pixel[3] >= 16
            ]
            if not samples:
                output_pixels[x, y] = (0, 0, 0, 0)
                continue
            sampled_alpha = round(sum(pixel[3] for pixel in samples) / len(samples))
            alpha = max(support_alpha, sampled_alpha)
            alpha_total = sum(pixel[3] for pixel in samples)
            if alpha_total == 0 or alpha < 3:
                output_pixels[x, y] = (0, 0, 0, 0)
                continue
            red = round(sum(pixel[0] * pixel[3] for pixel in samples) / alpha_total)
            green = round(sum(pixel[1] * pixel[3] for pixel in samples) / alpha_total)
            blue = round(sum(pixel[2] * pixel[3] for pixel in samples) / alpha_total)
            output_pixels[x, y] = (red, green, blue, alpha)

            inpaint_pixels.append((x, y))

    # Harmonic colour relaxation removes blade-colour streaks from the initial
    # cross-corridor estimate.  The alpha silhouette remains fixed to the
    # reconstructed body support, while colour diffuses only from neighbouring
    # airframe pixels—not from transparent air.
    for iteration in range(max(120, closing_size * 12)):
        max_change = 0
        for x, y in inpaint_pixels:
            neighbours: list[tuple[int, int, int, int]] = []
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < original.width and 0 <= ny < original.height:
                    pixel = output_pixels[nx, ny]
                    if pixel[3] >= 16:
                        neighbours.append(pixel)
            if not neighbours:
                continue
            current = output_pixels[x, y]
            red = round(sum(pixel[0] for pixel in neighbours) / len(neighbours))
            green = round(sum(pixel[1] for pixel in neighbours) / len(neighbours))
            blue = round(sum(pixel[2] for pixel in neighbours) / len(neighbours))
            max_change = max(
                max_change,
                abs(red - current[0]),
                abs(green - current[1]),
                abs(blue - current[2]),
            )
            output_pixels[x, y] = (red, green, blue, current[3])
        if iteration >= 40 and max_change <= 1:
            break

    if removal.clone_rules:
        snapshot = cleaned.copy()
        snapshot_pixels = snapshot.load()
        for branch_index, (offset_x, offset_y), (minimum_y, maximum_y) in removal.clone_rules:
            root, tip = removal.blades[branch_index]
            width = widths[branch_index]
            clone_mask = Image.new("L", original.size, 0)
            clone_draw = ImageDraw.Draw(clone_mask)
            clone_draw.line((root, tip), fill=255, width=width)
            clone_pixels = clone_mask.load()
            for y in range(max(0, minimum_y), min(original.height, maximum_y)):
                for x in range(original.width):
                    if clone_pixels[x, y] == 0 or support_pixels[x, y] < 16:
                        continue
                    source_x, source_y = x + offset_x, y + offset_y
                    if not (0 <= source_x < original.width and 0 <= source_y < original.height):
                        continue
                    sampled = snapshot_pixels[source_x, source_y]
                    if sampled[3] < 16:
                        continue
                    current = output_pixels[x, y]
                    output_pixels[x, y] = (sampled[0], sampled[1], sampled[2], current[3])

    return cleaned


def _ellipse_point(
    centre: tuple[float, float],
    radius_x: float,
    radius_y: float,
    tilt: float,
    angle: float,
) -> tuple[float, float]:
    x = radius_x * math.cos(angle)
    y = radius_y * math.sin(angle)
    cos_tilt, sin_tilt = math.cos(tilt), math.sin(tilt)
    return (
        centre[0] + x * cos_tilt - y * sin_tilt,
        centre[1] + x * sin_tilt + y * cos_tilt,
    )


def _draw_ellipse_arc(
    draw: ImageDraw.ImageDraw,
    centre: tuple[float, float],
    radius_x: float,
    radius_y: float,
    tilt: float,
    start: float,
    span: float,
    *,
    fill: tuple[int, int, int, int],
    width: int,
    scale: int,
) -> None:
    steps = max(12, round(abs(span) * 34 / math.pi))
    points = [
        tuple(
            round(value * scale)
            for value in _ellipse_point(
                centre,
                radius_x,
                radius_y,
                tilt,
                start + span * index / steps,
            )
        )
        for index in range(steps + 1)
    ]
    draw.line(points, fill=fill, width=max(1, width * scale), joint="curve")


def _main_rotor_layer(
    size: tuple[int, int], asset_id: str, rotor: MainRotor, frame_index: int, frame_count: int
) -> Image.Image:
    scale = 4
    layer = Image.new("RGBA", (size[0] * scale, size[1] * scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    centre = (float(rotor.disc_centre[0]), float(rotor.disc_centre[1]))
    radius_x, radius_y = rotor.disc_radii
    tilt = math.radians(rotor.tilt_degrees)
    phase = frame_index * math.tau / frame_count + _phase_offset(asset_id)

    disc_points = [
        tuple(
            round(value * scale)
            for value in _ellipse_point(centre, radius_x * 0.99, radius_y * 0.97, tilt, step * math.tau / 96)
        )
        for step in range(96)
    ]
    draw.polygon(disc_points, fill=(177, 202, 218, 10))

    for rx_scale, ry_scale, alpha in ((1.0, 1.0, 48), (0.93, 0.87, 32), (0.85, 0.74, 21)):
        _draw_ellipse_arc(
            draw,
            centre,
            radius_x * rx_scale,
            radius_y * ry_scale,
            tilt,
            0,
            math.tau,
            fill=(214, 228, 238, alpha),
            width=1,
            scale=scale,
        )

    moving_arcs = (
        (1.0, 1.0, phase + 0.05, 0.90, (244, 250, 252, 142), 2),
        (1.0, 1.0, phase + math.pi, 0.74, (225, 239, 247, 108), 2),
        (0.91, 0.86, phase + math.pi * 0.54, 0.62, (205, 222, 234, 84), 1),
        (0.83, 0.72, phase + math.pi * 1.42, 0.50, (236, 246, 250, 68), 1),
    )
    for rx_scale, ry_scale, start, span, colour, width in moving_arcs:
        _draw_ellipse_arc(
            draw,
            centre,
            radius_x * rx_scale,
            radius_y * ry_scale,
            tilt,
            start,
            span,
            fill=colour,
            width=width,
            scale=scale,
        )

    for blade in range(rotor.trace_count):
        angle = phase * 1.15 + blade * math.tau / rotor.trace_count
        startpoint = _ellipse_point(centre, radius_x * 0.14, radius_y * 0.14, tilt, angle)
        endpoint = _ellipse_point(centre, radius_x * 0.96, radius_y * 0.92, tilt, angle)
        draw.line(
            (
                (round(startpoint[0] * scale), round(startpoint[1] * scale)),
                (round(endpoint[0] * scale), round(endpoint[1] * scale)),
            ),
            fill=(220, 234, 242, 18),
            width=2 * scale,
        )

    layer = layer.filter(ImageFilter.GaussianBlur(1.30 * scale))
    crisp = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    crisp_draw = ImageDraw.Draw(crisp)
    _draw_ellipse_arc(
        crisp_draw,
        centre,
        radius_x * 0.99,
        radius_y * 0.97,
        tilt,
        phase,
        0.44,
        fill=(246, 251, 253, 128),
        width=1,
        scale=scale,
    )
    _draw_ellipse_arc(
        crisp_draw,
        centre,
        radius_x * 0.98,
        radius_y * 0.95,
        tilt,
        phase + math.pi,
        0.30,
        fill=(221, 237, 246, 94),
        width=1,
        scale=scale,
    )
    layer.alpha_composite(crisp)
    return layer.resize(size, Image.Resampling.LANCZOS)


def _soft_ellipse_mask(
    size: tuple[int, int], centre: Point, radii: Point, *, scale: int = 1, feather: float = 0.0
) -> Image.Image:
    mask = Image.new("L", (size[0] * scale, size[1] * scale), 0)
    draw = ImageDraw.Draw(mask)
    cx, cy = centre[0] * scale, centre[1] * scale
    rx, ry = radii[0] * scale, radii[1] * scale
    draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=255)
    if feather:
        mask = mask.filter(ImageFilter.GaussianBlur(feather * scale))
    return mask


def _fenestron_base(source: Image.Image, tail: TailRotor) -> Image.Image:
    result = source.copy()
    mask = _soft_ellipse_mask(source.size, tail.centre, tail.radii, feather=0.35)
    blurred = source.filter(ImageFilter.GaussianBlur(1.8))
    return Image.composite(blurred, result, mask)


def _tail_rotor_layer(
    size: tuple[int, int], asset_id: str, tail: TailRotor, frame_index: int, frame_count: int
) -> Image.Image:
    scale = 4
    layer = Image.new("RGBA", (size[0] * scale, size[1] * scale), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    cx, cy = tail.centre[0] * scale, tail.centre[1] * scale
    radius_x, radius_y = tail.radii[0] * scale, tail.radii[1] * scale
    phase = frame_index * math.tau / frame_count * 1.45 + _phase_offset(asset_id) * 1.7
    trace_count = 7 if tail.kind == "fenestron" else 6

    if tail.kind == "exposed":
        draw.ellipse(
            (cx - radius_x, cy - radius_y, cx + radius_x, cy + radius_y),
            fill=(177, 202, 218, 11),
            outline=(218, 232, 239, 55),
            width=scale,
        )

    for spoke in range(trace_count):
        angle = phase + spoke * math.tau / trace_count
        start_scale = 0.18 if tail.kind == "exposed" else 0.0
        x1 = cx + math.cos(angle) * radius_x * start_scale
        y1 = cy + math.sin(angle) * radius_y * start_scale
        x2 = cx + math.cos(angle) * radius_x
        y2 = cy + math.sin(angle) * radius_y
        draw.line(
            (round(x1), round(y1), round(x2), round(y2)),
            fill=(222, 235, 241, 54 if tail.kind == "exposed" else 62),
            width=scale,
        )

    box = (cx - radius_x, cy - radius_y, cx + radius_x, cy + radius_y)
    start = math.degrees(phase)
    draw.arc(box, start=start, end=start + 122, fill=(247, 251, 252, 132), width=2 * scale)
    draw.arc(box, start=start + 180, end=start + 258, fill=(185, 207, 221, 84), width=scale)
    if tail.accent is not None:
        draw.arc(
            box,
            start=start + 36,
            end=start + 82,
            fill=(*tail.accent, 104),
            width=scale,
        )

    blur = 0.65 if tail.kind == "fenestron" else 0.85
    layer = layer.filter(ImageFilter.GaussianBlur(blur * scale))
    if tail.kind == "fenestron":
        clip = _soft_ellipse_mask(size, tail.centre, tail.radii, scale=scale, feather=0.35)
        layer.putalpha(ImageChops.multiply(layer.getchannel("A"), clip))
    return layer.resize(size, Image.Resampling.LANCZOS)


def _reapply_hub(source: Image.Image, target: Image.Image, removal: BladeRemoval) -> None:
    mask = Image.new("L", source.size, 0)
    draw = ImageDraw.Draw(mask)
    for box in removal.hub_ellipses:
        draw.ellipse(box, fill=255)
    for box, radius in removal.hub_rectangles:
        draw.rounded_rectangle(box, radius=radius, fill=255)
    patch = Image.new("RGBA", source.size, (0, 0, 0, 0))
    patch.paste(source, (0, 0), mask)
    target.alpha_composite(patch)


def prepare_helicopter_base(asset_id: str, source: Image.Image) -> Image.Image:
    """Return the blade-free master base used by every animated frame."""

    geometry = HELICOPTER_GEOMETRY[asset_id]
    original = source.convert("RGBA")
    cleaned = _remove_baked_blades(original, geometry.main.removal)
    if geometry.tail.kind == "fenestron":
        return _fenestron_base(cleaned, geometry.tail)
    if geometry.tail.removal is None:
        raise RuntimeError(f"Missing exposed tail-rotor removal geometry for {asset_id}")
    return _remove_baked_blades(cleaned, geometry.tail.removal)


def render_helicopter_motion(
    asset_id: str,
    cleaned: Image.Image,
    source: Image.Image,
    frame_index: int,
    frame_count: int,
) -> Image.Image:
    """Render aligned main and tail rotor motion over a cleaned master."""

    geometry = HELICOPTER_GEOMETRY[asset_id]
    frame = cleaned.copy()
    frame.alpha_composite(_main_rotor_layer(frame.size, asset_id, geometry.main, frame_index, frame_count))
    frame.alpha_composite(_tail_rotor_layer(frame.size, asset_id, geometry.tail, frame_index, frame_count))
    _reapply_hub(source, frame, geometry.main.removal)
    if geometry.tail.kind == "exposed" and geometry.tail.removal is not None:
        _reapply_hub(source, frame, geometry.tail.removal)
    return frame


def geometry_manifest(asset_id: str) -> dict[str, object]:
    geometry = HELICOPTER_GEOMETRY[asset_id]
    return {
        "main_hub": list(geometry.main.removal.hub),
        "main_disc_centre": list(geometry.main.disc_centre),
        "main_disc_radii": list(geometry.main.disc_radii),
        "main_disc_tilt_degrees": geometry.main.tilt_degrees,
        "main_baked_blades_removed": len(geometry.main.removal.blades),
        "tail_kind": geometry.tail.kind,
        "tail_centre": list(geometry.tail.centre),
        "tail_radii": list(geometry.tail.radii),
        "tail_aperture_box": (
            list(geometry.tail.aperture_box) if geometry.tail.aperture_box is not None else None
        ),
        "tail_baked_blades_removed": (
            len(geometry.tail.removal.blades) if geometry.tail.removal is not None else 0
        ),
    }
