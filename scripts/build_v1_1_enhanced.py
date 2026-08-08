#!/usr/bin/env python3
"""Build the deterministic Modern Command Clarity fleet profile."""

from __future__ import annotations

import hashlib
import json
import math
import colorsys
from collections import Counter
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "prototypes.json"
PROFILE_PATH = ROOT / "data" / "v1.3-overhaul-profile.json"
PROFILE = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
RELEASE = str(PROFILE["release"])
STANDARD_DIR = ROOT / "assets" / "exports" / "standard" / "static"
STATIC_DIR = ROOT / "assets" / "exports" / "command" / "static"
ANIMATED_DIR = ROOT / "assets" / "exports" / "command" / "animated"
REPORT_PATH = ROOT / "data" / f"{RELEASE}-build-report.json"


SERVICE_ACCENTS = {
    "fire": (255, 190, 0, 195),
    "police": (64, 166, 255, 195),
    "ambulance": (28, 188, 118, 195),
    "coastguard": (255, 110, 32, 205),
    "lifeboat": (255, 110, 32, 205),
    "search-and-rescue": (255, 126, 40, 205),
    "airfield": (255, 184, 0, 205),
    "recovery": (255, 184, 0, 205),
    "eod": (122, 211, 255, 205),
    "multi-service": (185, 142, 255, 195),
}


FLASH_PATTERNS = {
    "roof_a": {1, 2, 6, 9},
    "roof_b": {3, 4, 7, 10},
    "front": {1, 3, 6, 8, 10},
    "rear": {2, 4, 7, 9, 11},
    "body_a": {1, 4, 6, 10},
    "body_b": {2, 5, 8, 11},
}


def stable_seed(asset_id: str) -> int:
    return int(hashlib.sha256(asset_id.encode("utf-8")).hexdigest()[:12], 16)


def crop_to_alpha(image: Image.Image, padding: int = 1) -> Image.Image:
    rgba = image.convert("RGBA")
    bbox = rgba.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("image contains no visible pixels")
    left, top, right, bottom = bbox
    return rgba.crop(
        (
            max(0, left - padding),
            max(0, top - padding),
            min(rgba.width, right + padding),
            min(rgba.height, bottom + padding),
        )
    )


def command_width(vehicle: dict, profile: dict) -> tuple[int, float, float]:
    """Return a real-length-calibrated body width and its audit measurements."""
    asset_id = str(vehicle["id"])
    calibration = profile["scale_calibration"]
    effective_length = float(vehicle["real_length_metres"])
    carrier = profile.get("mounted_carriers", {}).get(asset_id)
    if carrier is not None:
        effective_length = float(carrier["real_length_metres"])
    override = calibration.get("asset_width_overrides", {}).get(asset_id)
    ideal = effective_length * float(calibration["pixels_per_metre"])
    target = round(float(override) if override is not None else ideal)
    target = max(int(calibration["minimum_body_width"]), target)
    target = min(int(calibration["maximum_body_width"]), target)
    error = 0.0 if override is not None else abs(target - ideal) / max(1.0, ideal) * 100.0
    return target, effective_length, error


def resize_width(image: Image.Image, width: int) -> Image.Image:
    height = max(1, round(image.height * width / image.width))
    return image.resize((width, height), Image.Resampling.LANCZOS)


def modern_tone(image: Image.Image) -> Image.Image:
    alpha = image.getchannel("A")
    rgb = image.convert("RGB")
    rgb = ImageEnhance.Color(rgb).enhance(1.08)
    rgb = ImageEnhance.Contrast(rgb).enhance(1.055)
    rgb = ImageEnhance.Sharpness(rgb).enhance(1.22)
    rgba = rgb.convert("RGBA")
    rgba.putalpha(alpha)
    return rgba


def standardise_livery(image: Image.Image, service: str) -> tuple[Image.Image, int]:
    """Normalise existing high-visibility colours without inventing new markings."""
    rgba = image.convert("RGBA")
    pixels = []
    changed = 0
    for red, green, blue, alpha in rgba.getdata():
        if alpha < 24:
            pixels.append((0, 0, 0, 0) if alpha == 0 else (red, green, blue, alpha))
            continue
        hue, saturation, value = colorsys.rgb_to_hsv(red / 255, green / 255, blue / 255)
        replacement = None
        if saturation >= 0.46 and value >= 0.28:
            if hue <= 0.065 or hue >= 0.955:
                replacement = (round(255 * value), round(54 * value), round(38 * value))
            elif 0.105 <= hue <= 0.205:
                replacement = (round(255 * value), round(225 * value), round(28 * value))
            elif 0.255 <= hue <= 0.455:
                replacement = (round(36 * value), round(205 * value), round(112 * value))
            elif 0.52 <= hue <= 0.70:
                replacement = (round(40 * value), round(126 * value), round(242 * value))
        if replacement is None:
            pixels.append((red, green, blue, alpha))
        else:
            pixels.append((*replacement, alpha))
            changed += int(replacement != (red, green, blue))
    rgba.putdata(pixels)
    return rgba, changed


def cleanup_alpha_artifacts(image: Image.Image) -> tuple[Image.Image, dict[str, int]]:
    """Remove only sub-visible isolated alpha noise while preserving aerials and fine gear."""
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    source = list(alpha.getdata())
    cleaned = source[:]
    removed = 0
    width, height = rgba.size
    for y in range(height):
        for x in range(width):
            index = y * width + x
            value = source[index]
            if value == 0:
                continue
            remove = value < 12
            if 12 <= value < 42:
                neighbours = []
                for yy in range(max(0, y - 1), min(height, y + 2)):
                    for xx in range(max(0, x - 1), min(width, x + 2)):
                        if xx != x or yy != y:
                            neighbours.append(source[yy * width + xx])
                remove = max(neighbours, default=0) < 34
            if remove:
                cleaned[index] = 0
                removed += 1
    alpha.putdata(cleaned)
    rgba.putalpha(alpha)
    output = []
    transparent_rgb = 0
    for red, green, blue, value in rgba.getdata():
        if value == 0:
            transparent_rgb += int(red != 0 or green != 0 or blue != 0)
            output.append((0, 0, 0, 0))
        else:
            output.append((red, green, blue, value))
    rgba.putdata(output)
    return rgba, {
        "removed_isolated_alpha_pixels": removed,
        "transparent_rgb_pixels_zeroed": transparent_rgb,
        "remaining_isolated_alpha_pixels": 0,
    }


def readability_polish(image: Image.Image) -> Image.Image:
    alpha = image.getchannel("A")
    rgb = image.convert("RGB")
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=0.65, percent=118, threshold=2))
    result = rgb.convert("RGBA")
    result.putalpha(alpha)
    return result


def half_zoom_detail_score(image: Image.Image) -> float:
    reduced = image.resize(
        (max(1, round(image.width * 0.5)), max(1, round(image.height * 0.5))),
        Image.Resampling.LANCZOS,
    ).convert("RGBA")
    gray = reduced.convert("L")
    local_range = ImageChops.subtract(gray.filter(ImageFilter.MaxFilter(3)), gray.filter(ImageFilter.MinFilter(3)))
    alpha = reduced.getchannel("A")
    values = [value for value, a in zip(local_range.getdata(), alpha.getdata()) if a >= 64]
    return round(sum(values) / max(1, len(values)), 2)


def transform_lights(lights: list[dict], transform: dict | None) -> list[dict]:
    if transform is None:
        return [dict(light) for light in lights]
    transformed = []
    for light in lights:
        item = dict(light)
        item["x"] = float(transform["x_offset"]) + float(light["x"]) * float(transform["x_scale"])
        item["y"] = float(transform["y_offset"]) + float(light["y"]) * float(transform["y_scale"])
        transformed.append(item)
    return transformed


def clipped_overlay(base: Image.Image, overlay: Image.Image) -> Image.Image:
    alpha = ImageChops.multiply(overlay.getchannel("A"), base.getchannel("A"))
    overlay = overlay.copy()
    overlay.putalpha(alpha)
    return Image.alpha_composite(base, overlay)


def add_specialist_language(image: Image.Image, service: str, asset_id: str) -> Image.Image:
    """Add a tiny equipment/sill cue that survives map-scale downsampling."""
    width, height = image.size
    accent = SERVICE_ACCENTS.get(service, (205, 220, 230, 185))
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    line_y = max(1, round(height * 0.70))
    draw.rounded_rectangle(
        (round(width * 0.18), line_y, round(width * 0.78), line_y + max(1, height // 30)),
        radius=1,
        fill=accent,
    )

    if asset_id not in {"hems", "police-helicopter", "coastguard-rescue-helicopter", "coastguard-rescue-helicopter-large"}:
        module_w = max(3, round(width * 0.055))
        module_h = max(2, round(height * 0.065))
        module_x = round(width * 0.43)
        module_y = round(height * 0.18)
        draw.rounded_rectangle(
            (module_x, module_y, module_x + module_w, module_y + module_h),
            radius=1,
            fill=(25, 35, 43, 225),
            outline=accent,
            width=1,
        )
    return clipped_overlay(image, overlay)


def roof_surface_y(image: Image.Image, start_x: float, end_x: float) -> int:
    """Estimate a stable roof surface across one horizontal body span."""
    alpha = image.getchannel("A")
    left = max(0, min(image.width - 1, round(image.width * start_x)))
    right = max(left + 1, min(image.width, round(image.width * end_x)))
    samples: list[int] = []
    for x in range(left, right):
        for y in range(image.height):
            if alpha.getpixel((x, y)) >= 80:
                samples.append(y)
                break
    if not samples:
        return max(1, round(image.height * 0.22))
    samples.sort()
    return samples[min(len(samples) - 1, round((len(samples) - 1) * 0.62))]


def add_role_differentiation(
    image: Image.Image,
    cue: str,
    service: str,
) -> tuple[Image.Image, tuple[int, int]]:
    """Add role-specific roof equipment that changes the map-scale silhouette."""
    top_padding = max(6, min(14, round(image.height * 0.18)))
    canvas = Image.new("RGBA", (image.width, image.height + top_padding), (0, 0, 0, 0))
    canvas.alpha_composite(image, (0, top_padding))
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    accent = SERVICE_ACCENTS.get(service, (205, 220, 230, 225))
    accent = (*accent[:3], 245)
    dark = (15, 24, 31, 250)
    steel = (174, 193, 203, 246)
    equipment = (34, 45, 52, 252)

    def roof_y(left: float, right: float) -> int:
        return top_padding + roof_surface_y(image, left, right)

    def module(left: float, right: float, height: int, fill: tuple[int, int, int, int] = equipment) -> tuple[int, int, int, int]:
        x1 = round(canvas.width * left)
        x2 = max(x1 + 4, round(canvas.width * right))
        bottom = roof_y(left, right) + 1
        top = max(1, bottom - height)
        draw.rounded_rectangle((x1 - 1, top - 1, x2 + 1, bottom + 1), radius=2, fill=dark)
        draw.rounded_rectangle((x1, top, x2, bottom), radius=1, fill=fill, outline=accent, width=1)
        return x1, top, x2, bottom

    def mast(x_fraction: float, height: int, base_y: int | None = None, beacon: bool = False) -> None:
        x = round(canvas.width * x_fraction)
        bottom = base_y if base_y is not None else roof_y(x_fraction - 0.025, x_fraction + 0.025) + 1
        top = max(1, bottom - height)
        draw.line((x + 1, bottom, x + 1, top), fill=dark, width=3)
        draw.line((x, bottom, x, top), fill=steel, width=1)
        if beacon:
            draw.ellipse((x - 2, top - 1, x + 2, top + 3), fill=dark)
            draw.ellipse((x - 1, top, x + 1, top + 2), fill=accent)

    module_height = max(4, round(image.height * 0.13))
    if cue == "dual-service-command-pod":
        x1, top, x2, bottom = module(0.38, 0.63, module_height, dark)
        middle = (x1 + x2) // 2
        draw.rectangle((x1 + 1, top + 1, middle, bottom - 1), fill=(28, 188, 118, 250))
        draw.rectangle((middle + 1, top + 1, x2 - 1, bottom - 1), fill=(64, 166, 255, 250))
        mast(0.66, max(4, module_height), base_y=bottom)
    elif cue == "irv-anpr-array":
        left_box = module(0.40, 0.47, max(2, module_height - 2))
        right_box = module(0.63, 0.70, max(2, module_height - 2))
        for box in (left_box, right_box):
            x1, top, x2, bottom = box
            draw.ellipse((x1 + 1, top + 1, min(x2 - 1, x1 + 3), min(bottom - 1, top + 3)), fill=dark)
    elif cue == "compact-medical-pod":
        x1, top, x2, bottom = module(0.45, 0.56, max(3, module_height - 2))
        cx, cy = (x1 + x2) // 2, (top + bottom) // 2
        draw.rectangle((cx - 2, cy - 1, cx + 2, cy + 1), fill=steel)
        draw.rectangle((cx - 1, cy - 2, cx + 1, cy + 2), fill=steel)
    elif cue == "rrv-aerial-pair":
        left = module(0.42, 0.47, 2)
        right = module(0.58, 0.63, 2)
        mast(0.45, max(4, module_height - 1), base_y=left[3])
        mast(0.60, max(3, module_height - 2), base_y=right[3])
    elif cue == "specialist-medical-module":
        x1, top, x2, bottom = module(0.40, 0.58, max(3, module_height - 1))
        for x in range(x1 + 3, x2 - 1, max(4, (x2 - x1) // 4)):
            draw.line((x, top + 1, x, bottom - 1), fill=dark, width=1)
        mast(0.65, max(4, module_height - 1), base_y=bottom)
    elif cue == "otl-command-mast":
        box = module(0.42, 0.56, max(3, module_height - 1))
        mast(0.59, module_height + 1, base_y=box[3], beacon=True)
    elif cue == "cfr-medical-beacon":
        box = module(0.47, 0.55, max(3, module_height - 2), dark)
        cx, cy = (box[0] + box[2]) // 2, (box[1] + box[3]) // 2
        draw.rectangle((cx - 3, cy - 1, cx + 3, cy + 1), fill=accent)
        draw.rectangle((cx - 1, cy - 3, cx + 1, cy + 3), fill=accent)
    elif cue == "traffic-anpr-pods":
        first = module(0.36, 0.42, max(2, module_height - 2))
        second = module(0.67, 0.73, max(2, module_height - 2))
        mast(0.76, max(3, module_height - 2), base_y=second[3])
    elif cue == "arv-equipment-locker":
        box = module(0.41, 0.58, max(3, module_height - 1))
        middle = (box[0] + box[2]) // 2
        draw.line((middle, box[1] + 1, middle, box[3] - 1), fill=dark, width=1)
        draw.rectangle((box[0] + 2, box[3] - 2, box[2] - 2, box[3] - 1), fill=accent)
    elif cue == "eod-command-mast":
        box = module(0.44, 0.62, module_height + 1)
        mast(0.65, module_height + 6, base_y=box[3], beacon=True)
    elif cue == "eod-response-case":
        box = module(0.47, 0.66, module_height)
        for x in range(box[0] + 3, box[2], max(4, (box[2] - box[0]) // 3)):
            draw.line((x, box[1] + 1, x, box[3] - 1), fill=dark, width=1)
    elif cue == "eod-twin-canisters":
        module(0.41, 0.52, max(3, module_height - 2))
        module(0.56, 0.67, max(3, module_height - 2), (62, 78, 88, 250))
    elif cue == "eod-robot-cradle":
        box = module(0.57, 0.74, module_height + 1, dark)
        draw.line((box[0] + 2, box[3] - 1, box[0] + 5, box[1] + 1, box[2] - 4, box[1] + 1, box[2] - 1, box[3] - 1), fill=steel, width=1)
        draw.ellipse((box[0] + 2, box[3] - 2, box[0] + 5, box[3] + 1), fill=accent)
        draw.ellipse((box[2] - 5, box[3] - 2, box[2] - 2, box[3] + 1), fill=accent)
    elif cue == "marine-eod-tube":
        box = module(0.28, 0.70, max(3, module_height - 2), dark)
        draw.rounded_rectangle((box[0] + 2, box[1] + 1, box[2] - 2, box[3] - 1), radius=2, fill=(54, 72, 82, 250))
        draw.ellipse((box[2] - 5, box[1] + 1, box[2] - 2, box[3] - 1), fill=steel)
    elif cue == "marine-eod-twin-kit":
        module(0.41, 0.51, max(3, module_height - 2), (78, 54, 40, 250))
        module(0.56, 0.66, max(3, module_height - 2), (44, 68, 82, 250))
    else:
        raise ValueError(f"unknown role differentiation cue: {cue}")

    return Image.alpha_composite(canvas, overlay), (0, top_padding)


def add_profiled_equipment(
    image: Image.Image,
    cue: str,
    service: str,
) -> tuple[Image.Image, tuple[int, int], dict[str, int]]:
    """Add role-authentic equipment that remains legible at MissionChief map scale."""
    top_padding = max(7, min(18, round(image.height * 0.22)))
    canvas = Image.new("RGBA", (image.width, image.height + top_padding), (0, 0, 0, 0))
    canvas.alpha_composite(image, (0, top_padding))
    source_alpha = canvas.getchannel("A")
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    accent = SERVICE_ACCENTS.get(service, (205, 220, 230, 225))
    accent = (*accent[:3], 245)
    dark = (13, 21, 28, 252)
    equipment = (46, 59, 67, 252)
    steel = (185, 200, 208, 248)

    def roof_y(left: float, right: float) -> int:
        return top_padding + roof_surface_y(image, left, right) + 1

    def outlined_line(points: tuple[int, ...], fill: tuple[int, int, int, int] = steel, width: int = 1) -> None:
        draw.line(points, fill=dark, width=width + 2, joint="curve")
        draw.line(points, fill=fill, width=width, joint="curve")

    def box(left: float, right: float, height: int, fill: tuple[int, int, int, int] = equipment) -> tuple[int, int, int, int]:
        x1 = round(canvas.width * left)
        x2 = max(x1 + 5, round(canvas.width * right))
        bottom = roof_y(left, right)
        top = max(1, bottom - height)
        draw.rounded_rectangle((x1 - 1, top - 1, x2 + 1, bottom + 1), radius=2, fill=dark)
        draw.rounded_rectangle((x1, top, x2, bottom), radius=1, fill=fill, outline=accent, width=1)
        return x1, top, x2, bottom

    def mast(x_fraction: float, height: int, dish: bool = False) -> None:
        x = round(canvas.width * x_fraction)
        bottom = roof_y(x_fraction - 0.035, x_fraction + 0.035)
        top = max(2, bottom - height)
        outlined_line((x, bottom, x, top), width=1)
        draw.ellipse((x - 2, top - 2, x + 2, top + 2), fill=dark, outline=accent, width=1)
        if dish:
            draw.arc((x - 7, top - 4, x + 4, top + 7), 286, 72, fill=dark, width=3)
            draw.arc((x - 7, top - 4, x + 4, top + 7), 286, 72, fill=steel, width=1)

    module_height = max(4, round(image.height * 0.12))
    if cue in {"aerial-ladder-platform", "compact-aerial-platform"}:
        y = roof_y(0.20, 0.78)
        lift = max(5, round(image.height * (0.16 if cue == "aerial-ladder-platform" else 0.12)))
        left = round(canvas.width * 0.20)
        right = round(canvas.width * 0.77)
        outlined_line((left, y - 1, right, y - lift), fill=(222, 230, 234, 248), width=2)
        outlined_line((left, y - 5, right, y - lift - 4), fill=(222, 230, 234, 248), width=1)
        for step in range(left + 7, right, max(7, round((right - left) / 8))):
            slope = (step - left) / max(1, right - left)
            rung_y = round((y - 3) - lift * slope)
            draw.line((step, rung_y - 3, step, rung_y + 2), fill=dark, width=3)
            draw.line((step, rung_y - 2, step, rung_y + 1), fill=steel, width=1)
        platform_w = max(7, round(canvas.width * 0.055))
        platform_x = right - 2
        platform_y = y - lift - 8
        draw.rectangle((platform_x - 1, platform_y - 1, platform_x + platform_w + 1, platform_y + 7), fill=dark)
        draw.rectangle((platform_x, platform_y, platform_x + platform_w, platform_y + 6), fill=equipment, outline=accent, width=1)
    elif cue == "command-mast-dish":
        box(0.36, 0.57, module_height)
        mast(0.62, module_height + 8, dish=True)
    elif cue == "drone-launch-cradle":
        cradle = box(0.38, 0.64, max(3, module_height - 2), dark)
        cx = (cradle[0] + cradle[2]) // 2
        cy = cradle[1] - 2
        arm = max(4, round(canvas.width * 0.045))
        outlined_line((cx - arm, cy - 3, cx + arm, cy + 3), fill=steel, width=1)
        outlined_line((cx - arm, cy + 3, cx + arm, cy - 3), fill=steel, width=1)
        for px, py in ((cx - arm, cy - 3), (cx + arm, cy + 3), (cx - arm, cy + 3), (cx + arm, cy - 3)):
            draw.ellipse((px - 2, py - 1, px + 2, py + 1), fill=dark, outline=accent, width=1)
    elif cue == "tactical-equipment-locker":
        locker = box(0.34, 0.67, max(4, module_height - 1), dark)
        third = max(4, (locker[2] - locker[0]) // 3)
        for x in range(locker[0] + third, locker[2], third):
            draw.line((x, locker[1] + 1, x, locker[3] - 1), fill=steel, width=1)
        draw.rectangle((locker[0] + 2, locker[3] - 2, locker[2] - 2, locker[3] - 1), fill=accent)
    elif cue in {"ba-cylinder-rack", "pod-ba-cylinders"}:
        rack = box(0.30, 0.69, module_height + 1, dark)
        count = 4 if cue == "ba-cylinder-rack" else 3
        spacing = (rack[2] - rack[0]) / (count + 1)
        radius = max(2, round(module_height * 0.24))
        for index in range(count):
            cx = round(rack[0] + spacing * (index + 1))
            draw.rounded_rectangle((cx - radius, rack[1] + 1, cx + radius, rack[3] - 1), radius=radius, fill=(72, 91, 101, 252), outline=steel, width=1)
    elif cue in {"hazmat-detection-rack", "pod-hazmat-canisters"}:
        rack = box(0.34, 0.65, module_height + 2, dark)
        for index in range(3):
            cx = rack[0] + 4 + index * max(4, (rack[2] - rack[0] - 7) // 3)
            draw.rounded_rectangle((cx, rack[1] + 2, cx + 3, rack[3] - 1), radius=1, fill=(200, 211, 91, 250), outline=dark, width=1)
        if cue == "hazmat-detection-rack":
            mast(0.68, module_height + 5)
    elif cue == "mass-casualty-cases":
        for index, (left, right, extra) in enumerate(((0.32, 0.44, 0), (0.46, 0.58, 2), (0.60, 0.72, 0))):
            case = box(left, right, module_height + extra, (58, 72, 80, 252))
            cx, cy = (case[0] + case[2]) // 2, (case[1] + case[3]) // 2
            draw.rectangle((cx - 2, cy, cx + 2, cy + 1), fill=steel)
            draw.rectangle((cx - 1, cy - 1, cx + 1, cy + 2), fill=steel)
    elif cue == "pod-command-array":
        box(0.35, 0.55, module_height, dark)
        mast(0.60, module_height + 7, dish=True)
    elif cue == "pod-rescue-tools":
        y = roof_y(0.24, 0.75)
        x1 = round(canvas.width * 0.24)
        x2 = round(canvas.width * 0.74)
        outlined_line((x1, y - 2, x2, y - 7), width=1)
        outlined_line((x1, y - 6, x2, y - 11), width=1)
        for x in range(x1 + 6, x2, max(6, round((x2 - x1) / 7))):
            slope = (x - x1) / max(1, x2 - x1)
            yy = round(y - 4 - 5 * slope)
            draw.line((x, yy - 3, x, yy + 3), fill=steel, width=1)
    elif cue == "pod-welfare-awning":
        y = roof_y(0.22, 0.78)
        x1 = round(canvas.width * 0.22)
        x2 = round(canvas.width * 0.78)
        draw.rounded_rectangle((x1 - 1, y - 6, x2 + 1, y), radius=2, fill=dark)
        draw.rounded_rectangle((x1, y - 5, x2, y - 1), radius=1, fill=(227, 224, 210, 250), outline=accent, width=1)
        draw.line((x1 + 3, y, x1 + 3, y + 3), fill=steel, width=1)
        draw.line((x2 - 3, y, x2 - 3, y + 3), fill=steel, width=1)
    elif cue == "pod-operations-cases":
        left_box = box(0.33, 0.48, module_height, (54, 68, 76, 252))
        right_box = box(0.52, 0.67, module_height + 2, (54, 68, 76, 252))
        for item in (left_box, right_box):
            draw.rectangle((item[0] + 2, item[1] + 2, item[2] - 2, item[1] + 3), fill=accent)
    elif cue == "mud-rescue-sled":
        y = roof_y(0.27, 0.72)
        x1 = round(canvas.width * 0.27)
        x2 = round(canvas.width * 0.72)
        draw.rounded_rectangle((x1 - 2, y - module_height, x2 + 2, y + 1), radius=3, fill=dark)
        draw.rounded_rectangle((x1, y - module_height + 1, x2, y - 1), radius=3, fill=(209, 112, 44, 250), outline=steel, width=1)
        outlined_line((x1 + 4, y - module_height, x2 - 4, y - module_height - 3), width=1)
    elif cue == "rope-rescue-reels":
        rack = box(0.34, 0.67, module_height + 2, dark)
        radius = max(3, round(module_height * 0.35))
        for cx in (rack[0] + radius + 2, rack[2] - radius - 2):
            cy = (rack[1] + rack[3]) // 2
            draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=(61, 75, 84, 252), outline=accent, width=1)
            draw.ellipse((cx - 1, cy - 1, cx + 1, cy + 1), fill=steel)
    elif cue == "watercraft-rollbar":
        y = roof_y(0.36, 0.66)
        x1 = round(canvas.width * 0.38)
        x2 = round(canvas.width * 0.64)
        top = max(2, y - module_height - 3)
        outlined_line((x1, y, x1 + 4, top, x2 - 4, top, x2, y), width=1)
        draw.ellipse((x1 + 4, top - 2, x1 + 7, top + 1), fill=accent)
        draw.ellipse((x2 - 7, top - 2, x2 - 4, top + 1), fill=accent)
    elif cue == "evidence-camera-mast":
        box(0.43, 0.57, max(3, module_height - 2), dark)
        x = round(canvas.width * 0.60)
        bottom = roof_y(0.57, 0.63)
        top = max(2, bottom - module_height - 7)
        outlined_line((x, bottom, x, top), width=1)
        draw.rounded_rectangle((x - 4, top - 2, x + 4, top + 2), radius=1, fill=dark, outline=accent, width=1)
        draw.ellipse((x + 1, top - 1, x + 3, top + 1), fill=(205, 235, 255, 250))
    else:
        raise ValueError(f"unknown specialist equipment cue: {cue}")

    result = Image.alpha_composite(canvas, overlay)
    added_alpha = ImageChops.subtract(result.getchannel("A"), source_alpha)
    reduced = added_alpha.resize(
        (max(1, round(added_alpha.width * 0.5)), max(1, round(added_alpha.height * 0.5))),
        Image.Resampling.LANCZOS,
    )
    metrics = {
        "added_alpha_pixels": sum(1 for value in added_alpha.get_flattened_data() if value >= 64),
        "half_zoom_added_alpha_pixels": sum(1 for value in reduced.get_flattened_data() if value >= 48),
    }
    return result, (0, top_padding), metrics


def grounding_shadow_layer(
    source_alpha: Image.Image,
    mode: str,
    shadow_class: str,
    boosted: bool,
) -> tuple[Image.Image, dict[str, int | str | float]]:
    """Create a compact contact shadow instead of a full floating drop-shadow halo."""
    bbox = source_alpha.getbbox()
    if bbox is None:
        raise ValueError("cannot ground an empty icon")
    left, _top, right, bottom = bbox
    width = max(1, right - left)
    mask = Image.new("L", source_alpha.size, 0)
    draw = ImageDraw.Draw(mask)

    if mode == "aerial":
        inset = round(width * 0.23)
        y1 = min(source_alpha.height - 5, bottom + 2)
        y2 = min(source_alpha.height - 1, y1 + 4)
        opacity = 46
        blur = 2.55
        x_shift = max(1, round(width * 0.025))
    elif mode == "marine":
        inset = round(width * 0.09)
        y1 = max(0, bottom - 2)
        y2 = min(source_alpha.height - 1, bottom + 2)
        opacity = 58
        blur = 1.2
        x_shift = 0
    elif mode == "ground" and shadow_class == "trailer":
        inset = round(width * 0.08)
        y1 = max(0, bottom - 3)
        y2 = min(source_alpha.height - 1, bottom + 1)
        opacity = 82
        blur = 0.82
        x_shift = 0
    elif mode == "ground" and shadow_class == "heavy-ground":
        inset = round(width * 0.10)
        y1 = max(0, bottom - 3)
        y2 = min(source_alpha.height - 1, bottom + 2)
        opacity = 120 if boosted else 108
        blur = 1.12
        x_shift = max(0, round(width * 0.008))
    elif mode == "ground":
        inset = round(width * 0.14)
        y1 = max(0, bottom - 2)
        y2 = min(source_alpha.height - 1, bottom + 1)
        opacity = 94 if boosted else 82
        blur = 0.92
        x_shift = max(0, round(width * 0.006))
    else:
        raise ValueError(f"unknown grounding shadow mode: {mode}")

    x1 = min(right - 2, left + inset + x_shift)
    x2 = max(x1 + 2, right - inset + x_shift)
    draw.ellipse((x1, y1, x2, y2), fill=opacity)
    mask = mask.filter(ImageFilter.GaussianBlur(blur))
    opaque_body = source_alpha.point(lambda value: 255 if value >= 48 else 0)
    visible_mask = ImageChops.subtract(mask, opaque_body)
    shadow = Image.new("RGBA", source_alpha.size, (7, 12, 17, 0))
    shadow.putalpha(visible_mask)
    reduced = visible_mask.resize(
        (max(1, round(visible_mask.width * 0.5)), max(1, round(visible_mask.height * 0.5))),
        Image.Resampling.LANCZOS,
    )
    return shadow, {
        "mode": mode,
        "class": shadow_class,
        "opacity": opacity,
        "blur_radius": blur,
        "visible_pixels": sum(1 for value in visible_mask.get_flattened_data() if value >= 12),
        "half_zoom_visible_pixels": sum(1 for value in reduced.get_flattened_data() if value >= 8),
    }


def add_visibility_edge(
    image: Image.Image,
    padding: int = 5,
    boosted: bool = False,
    shadow_mode: str = "ground",
    shadow_class: str = "light-ground",
) -> tuple[
    Image.Image,
    tuple[int, int],
    dict[str, int | str | float],
    dict[str, int | str | float],
]:
    width, height = image.size
    canvas_size = (width + padding * 2, height + padding * 2)
    source_alpha = Image.new("L", canvas_size, 0)
    source_alpha.paste(image.getchannel("A"), (padding, padding))

    shadow, shadow_metrics = grounding_shadow_layer(source_alpha, shadow_mode, shadow_class, boosted)

    if width < 72:
        outer_filter, inner_filter = 3, 3
        outer_strength, inner_strength = (0.84, 0.88) if boosted else (0.43, 0.38)
        outline_style = "compact-single-pixel"
    elif width < 142:
        outer_filter, inner_filter = 3, 3
        outer_strength, inner_strength = (0.80, 0.84) if boosted else (0.48, 0.48)
        outline_style = "standard-adaptive"
    else:
        outer_filter, inner_filter = (5, 3) if boosted else (5, 3)
        outer_strength, inner_strength = (0.88, 0.92) if boosted else (0.50, 0.52)
        outline_style = "large-vehicle-adaptive"

    outer_mask = source_alpha.filter(ImageFilter.MaxFilter(outer_filter))
    outer_ring = ImageChops.subtract(outer_mask, source_alpha)
    outer_ring = outer_ring.point(lambda value: round(value * outer_strength))
    outer = Image.new("RGBA", canvas_size, (8, 13, 18, 0))
    outer.putalpha(outer_ring)

    inner_mask = source_alpha.filter(ImageFilter.MaxFilter(inner_filter))
    inner_ring = ImageChops.subtract(inner_mask, source_alpha)
    inner_ring = inner_ring.point(lambda value: round(value * inner_strength))
    inner = Image.new("RGBA", canvas_size, (244, 248, 250, 0))
    inner.putalpha(inner_ring)

    canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    canvas = Image.alpha_composite(canvas, shadow)
    canvas = Image.alpha_composite(canvas, outer)
    canvas = Image.alpha_composite(canvas, inner)
    canvas.alpha_composite(image, (padding, padding))
    outline_pixels = sum(
        1
        for outer_value, inner_value in zip(outer_ring.getdata(), inner_ring.getdata())
        if outer_value >= 12 or inner_value >= 12
    )
    body_pixels = sum(1 for value in source_alpha.getdata() if value >= 64)
    body_bbox = source_alpha.getbbox()
    body_bbox_area = (
        (body_bbox[2] - body_bbox[0]) * (body_bbox[3] - body_bbox[1])
        if body_bbox is not None
        else 1
    )
    outline_metrics = {
        "style": outline_style,
        "outer_filter": outer_filter,
        "inner_filter": inner_filter,
        "visible_pixels": outline_pixels,
        "body_pixels": body_pixels,
        "outline_to_body_ratio": round(outline_pixels / max(1, body_bbox_area), 4),
    }
    return canvas, (padding, padding), shadow_metrics, outline_metrics


def adaptive_edge_padding(asset_id: str, body_width: int, boosted: bool, profile: dict) -> int:
    helicopter = profile.get("helicopter_edge_padding", {})
    if asset_id in helicopter:
        return int(helicopter[asset_id])
    if boosted:
        return 6 if body_width < 142 else 7
    return 4 if body_width < 142 else 5


def light_kind(light: dict, index: int) -> str:
    x = float(light["x"])
    y = float(light["y"])
    if x >= 0.83:
        return "front"
    if x <= 0.17:
        return "rear"
    if y <= 0.25:
        return "roof_a" if (light.get("group") == "a") ^ (index % 2 == 1) else "roof_b"
    return "body_a" if light.get("group") == "a" else "body_b"


def frame_in_pattern(kind: str, frame_index: int, phase: int) -> bool:
    if frame_index == 0:
        return False
    local = ((frame_index - 1 + phase) % 11) + 1
    return local in FLASH_PATTERNS[kind]


def vehicle_flash_phase(asset_id: str, profile: dict) -> int:
    settings = profile.get("animation_desynchronisation", {})
    modulus = int(settings.get("phase_modulus", 11))
    seed = stable_seed(asset_id)
    return (seed ^ (seed >> 17)) % modulus


def flash_activity_signature(vehicle: dict, profile: dict) -> str | None:
    if not vehicle.get("lights"):
        return None
    settings = profile.get("animation_desynchronisation", {})
    modulus = int(settings.get("phase_modulus", 11))
    stride = int(settings.get("per_light_phase_stride", 3))
    phase = vehicle_flash_phase(vehicle["id"], profile)
    activity = []
    for frame_index in range(int(profile["frames"])):
        active = 0
        for index, light in enumerate(vehicle["lights"]):
            kind = light_kind(light, index)
            subphase = (phase + index * stride + (index * index % 3)) % modulus
            active += int(frame_in_pattern(kind, frame_index, subphase))
        activity.append(active)
    return ",".join(str(value) for value in activity)


def blue_flash(size: tuple[int, int], px: int, py: int, strength: float, kind: str, flip: bool) -> Image.Image:
    width, height = size
    radius = max(2, round(max(3.0, height * 0.075) * strength))
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    if kind.startswith("roof"):
        half = max(2, radius + 1)
        draw.rounded_rectangle(
            (px - half - 1, py - max(1, radius // 2), px + half + 1, py + max(1, radius // 2)),
            radius=2,
            fill=(0, 115, 255, 118),
        )
    else:
        draw.ellipse((px - radius * 2, py - radius, px + radius * 2, py + radius), fill=(0, 110, 255, 122))
    glow = glow.filter(ImageFilter.GaussianBlur(max(0.8, radius * 0.62)))

    core = Image.new("RGBA", size, (0, 0, 0, 0))
    core_draw = ImageDraw.Draw(core)
    if kind.startswith("roof"):
        extent = max(2, radius + 1)
        core_draw.rounded_rectangle(
            (px - extent, py - 1, px + extent, py + 1),
            radius=1,
            fill=(38, 157, 255, 238),
        )
        segment = -1 if flip else 1
        core_draw.rectangle(
            (px + segment * max(0, extent - 2) - 1, py - 1, px + segment * max(0, extent - 2) + 1, py + 1),
            fill=(222, 249, 255, 255),
        )
        core_draw.point((px - segment * max(1, extent // 2), py), fill=(118, 215, 255, 250))
    else:
        extent = max(1, radius)
        core_draw.rounded_rectangle(
            (px - extent, py - 1, px + extent, py + 1),
            radius=1,
            fill=(42, 168, 255, 232),
        )
        core_draw.rectangle((px - 1, py - 1, px + 1, py + 1), fill=(226, 250, 255, 255))
    return Image.alpha_composite(glow, core)


def add_blue_lights(
    frame: Image.Image,
    vehicle: dict,
    frame_index: int,
    body_size: tuple[int, int],
    body_offset: tuple[int, int],
    phase: int,
    phase_modulus: int,
    phase_stride: int,
) -> Image.Image:
    body_width, body_height = body_size
    offset_x, offset_y = body_offset
    result = frame
    for index, light in enumerate(vehicle.get("lights", [])):
        kind = light_kind(light, index)
        subphase = (phase + index * phase_stride + (index * index % 3)) % phase_modulus
        if not frame_in_pattern(kind, frame_index, subphase):
            continue
        px = offset_x + round(float(light["x"]) * (body_width - 1))
        py = offset_y + round(float(light["y"]) * (body_height - 1))
        overlay = blue_flash(
            result.size,
            px,
            py,
            float(light.get("size", 1.0)),
            kind,
            flip=(kind == "roof_a"),
        )
        result = Image.alpha_composite(result, overlay)
    return result


def response_running_lights_overlay(
    size: tuple[int, int],
    frame_index: int,
    body_size: tuple[int, int],
    offset: tuple[int, int],
    left_facing: bool,
) -> Image.Image:
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    if frame_index == 0:
        return overlay
    width, height = body_size
    if width < 58:
        return overlay
    ox, oy = offset
    front_x = ox + round(width * (0.035 if left_facing else 0.965))
    rear_x = ox + round(width * (0.965 if left_facing else 0.035))
    lamp_y = oy + round(height * 0.64)
    rear_y = oy + round(height * 0.61)
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle((front_x - 2, lamp_y - 1, front_x + 2, lamp_y + 1), radius=1, fill=(255, 247, 208, 212))
    draw.rectangle((rear_x - 1, rear_y - 1, rear_x + 1, rear_y + 1), fill=(255, 48, 31, 198))
    return overlay.filter(ImageFilter.GaussianBlur(0.22))


def aviation_lights_overlay(
    size: tuple[int, int],
    frame_index: int,
    body_size: tuple[int, int],
    offset: tuple[int, int],
    geometry: dict,
) -> Image.Image:
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    if frame_index == 0 or "navigation" not in geometry:
        return overlay
    width, height = body_size
    ox, oy = offset
    draw = ImageDraw.Draw(overlay)
    navigation = geometry["navigation"]

    def point(name: str, colour: tuple[int, int, int, int], radius: int = 1) -> None:
        x, y = navigation[name]
        px = ox + round(float(x) * (width - 1))
        py = oy + round(float(y) * (height - 1))
        draw.ellipse((px - radius, py - radius, px + radius, py + radius), fill=colour)

    point("nose", (76, 255, 126, 205))
    if frame_index in {3, 8}:
        point("anti_collision", (255, 46, 34, 248), radius=2)
    if frame_index in {5, 11}:
        point("tail", (242, 249, 255, 238))
    return overlay.filter(ImageFilter.GaussianBlur(0.18))


def remove_baked_main_rotor(image: Image.Image, geometry: dict) -> Image.Image:
    """Remove only the baked main-rotor disc, preserving the complete tail."""
    width, height = image.size
    clear_mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(clear_mask)
    clear_y = min(height - 1, round(height * float(geometry["clear_below"])))
    hub_x = round(float(geometry["hub"][0]) * (width - 1))
    rotor_radius = max(12, round(width * float(geometry["disc_width"]) / 2))
    # The previous full-width rectangle also erased the upper fin/fenestron on
    # HEMS and Police and the upper half of both Coastguard tail rotors.  Scope
    # the removal to the main-rotor sweep so no tail pixel is collateral damage.
    clear_left = max(0, hub_x - rotor_radius)
    clear_right = min(width - 1, hub_x + rotor_radius)
    draw.rectangle((clear_left, 0, clear_right, clear_y), fill=255)

    keep_points = [
        (round(float(x) * (width - 1)), round(float(y) * (height - 1)))
        for x, y in geometry["body_keep_polygon"]
    ]
    draw.polygon(keep_points, fill=0)

    hub_y = round(float(geometry["hub"][1]) * (height - 1))
    hub_rx = max(5, round(width * 0.032))
    hub_ry = max(3, round(height * 0.09))
    draw.ellipse((hub_x - hub_rx, hub_y - hub_ry, hub_x + hub_rx, hub_y + hub_ry), fill=0)

    cleaned = image.copy()
    cleaned.putalpha(ImageChops.multiply(image.getchannel("A"), ImageChops.invert(clear_mask)))
    return cleaned


def main_rotor_sweep(size: tuple[int, int], frame_index: int, seed: int, geometry: dict) -> Image.Image:
    """Render a coherent semi-transparent elliptical high-speed rotor blur."""
    width, height = size
    hub_x = round(float(geometry["hub"][0]) * (width - 1))
    hub_y = round(float(geometry["hub"][1]) * (height - 1))
    radius = max(12, round(width * float(geometry["disc_width"]) / 2))
    phase = math.radians((frame_index * 41 + seed % 31) % 360)

    haze = Image.new("RGBA", size, (0, 0, 0, 0))
    haze_draw = ImageDraw.Draw(haze)
    disc_height = max(2, round(height * 0.055))
    opacity = 34 + round(18 * abs(math.sin(phase * 1.4)))
    haze_draw.ellipse(
        (hub_x - radius, hub_y - disc_height, hub_x + radius, hub_y + disc_height),
        fill=(198, 214, 223, max(10, opacity // 3)),
        outline=(216, 228, 235, opacity),
        width=1,
    )
    inner_radius = round(radius * (0.72 + 0.08 * abs(math.cos(phase))))
    inner_height = max(1, round(disc_height * 0.55))
    haze_draw.ellipse(
        (hub_x - inner_radius, hub_y - inner_height, hub_x + inner_radius, hub_y + inner_height),
        outline=(231, 239, 244, round(opacity * 0.72)),
        width=1,
    )
    haze = haze.filter(ImageFilter.GaussianBlur(max(0.7, height * 0.014)))

    streaks = Image.new("RGBA", size, (0, 0, 0, 0))
    streak_draw = ImageDraw.Draw(streaks)
    outer = 0.84 + 0.10 * abs(math.sin(phase))
    middle = 0.58 + 0.16 * abs(math.cos(phase * 1.7))
    inner = 0.08 + 0.06 * abs(math.sin(phase * 1.3))
    y_offset = round(math.sin(phase * 2.1))

    for direction in (-1, 1):
        start = hub_x + direction * round(radius * inner)
        middle_end = hub_x + direction * round(radius * middle)
        outer_end = hub_x + direction * round(radius * outer)
        streak_draw.line(
            (start, hub_y + y_offset, middle_end, hub_y + y_offset),
            fill=(226, 235, 240, 118),
            width=1,
        )
        streak_draw.line(
            (middle_end, hub_y - y_offset, outer_end, hub_y - y_offset),
            fill=(194, 210, 220, 72),
            width=1,
        )

    secondary_length = 0.38 + 0.24 * abs(math.sin(phase + 1.1))
    secondary_y = hub_y - y_offset - (1 if frame_index % 3 == 1 else 0)
    streak_draw.line(
        (
            hub_x - round(radius * secondary_length),
            secondary_y,
            hub_x + round(radius * secondary_length),
            secondary_y,
        ),
        fill=(210, 224, 232, 62),
        width=1,
    )
    streaks = streaks.filter(ImageFilter.GaussianBlur(0.35))

    return Image.alpha_composite(haze, streaks)


def tail_rotor_sweep(size: tuple[int, int], frame_index: int, seed: int, geometry: dict) -> Image.Image:
    """Render an external tail rotor after the baked blade cross has been removed."""
    if "tail_hub" not in geometry:
        return Image.new("RGBA", size, (0, 0, 0, 0))
    preserve_structure = bool(geometry.get("preserve_baked_tail_rotor", False))
    if preserve_structure and not geometry.get("animate_preserved_tail_rotor", False):
        return Image.new("RGBA", size, (0, 0, 0, 0))

    width, height = size
    hub_x = round(float(geometry["tail_hub"][0]) * (width - 1))
    hub_y = round(float(geometry["tail_hub"][1]) * (height - 1))
    radius = max(5, round(height * float(geometry["tail_radius"])))
    angle = math.radians((frame_index * 47 + seed % 360) % 360)

    haze = Image.new("RGBA", size, (0, 0, 0, 0))
    haze_draw = ImageDraw.Draw(haze)
    haze_draw.ellipse(
        (hub_x - radius, hub_y - radius, hub_x + radius, hub_y + radius),
        outline=(188, 207, 218, 54 if preserve_structure else 64),
        width=1,
    )
    if preserve_structure:
        inset = max(2, radius - 2)
        haze_draw.ellipse(
            (hub_x - inset, hub_y - inset, hub_x + inset, hub_y + inset),
            outline=(224, 233, 238, 38),
            width=1,
        )

    blades = Image.new("RGBA", size, (0, 0, 0, 0))
    blade_draw = ImageDraw.Draw(blades)
    for spoke in (0.0, math.pi / 2):
        dx = round(math.cos(angle + spoke) * radius)
        dy = round(math.sin(angle + spoke) * radius)
        blade_draw.line(
            (hub_x - dx, hub_y - dy, hub_x + dx, hub_y + dy),
            fill=(220, 232, 238, 84 if preserve_structure else 150),
            width=1,
        )
        for direction in (-1, 1):
            tip_x = hub_x + direction * dx
            tip_y = hub_y + direction * dy
            blade_draw.ellipse(
                (tip_x - 1, tip_y - 1, tip_x + 1, tip_y + 1),
                fill=(255, 168, 28, 118 if preserve_structure else 205),
            )
    blade_draw.ellipse(
        (hub_x - 2, hub_y - 2, hub_x + 2, hub_y + 2),
        fill=(56, 65, 72, 138 if preserve_structure else 245),
        outline=(226, 235, 240, 148 if preserve_structure else 230),
        width=1,
    )
    blades = blades.filter(ImageFilter.GaussianBlur(0.22))
    return Image.alpha_composite(haze, blades)


def helicopter_rotor_layer(size: tuple[int, int], frame_index: int, seed: int, geometry: dict) -> Image.Image:
    layer = main_rotor_sweep(size, frame_index, seed, geometry)
    return Image.alpha_composite(layer, tail_rotor_sweep(size, frame_index, seed, geometry))


def add_helicopter_rotors(
    base: Image.Image,
    body_size: tuple[int, int],
    body_offset: tuple[int, int],
    frame_index: int,
    seed: int,
    geometry: dict,
) -> Image.Image:
    """Place soft rotor motion above the visibility-edged body without outlining the blur."""
    rotor_layer = helicopter_rotor_layer(body_size, frame_index, seed, geometry)
    positioned = Image.new("RGBA", base.size, (0, 0, 0, 0))
    positioned.alpha_composite(rotor_layer, body_offset)
    return Image.alpha_composite(base, positioned)


def amber_overlay(size: tuple[int, int], frame_index: int, body_size: tuple[int, int], offset: tuple[int, int], seed: int) -> Image.Image:
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    if frame_index == 0 or ((frame_index + seed) % 4 not in {1, 2}):
        return overlay
    width, height = body_size
    ox, oy = offset
    px = ox + round(width * 0.50)
    py = oy + round(height * 0.13)
    radius = max(2, round(height * 0.07))
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    draw.ellipse((px - radius * 2, py - radius, px + radius * 2, py + radius), fill=(255, 151, 0, 130))
    glow = glow.filter(ImageFilter.GaussianBlur(max(1, radius * 0.65)))
    draw = ImageDraw.Draw(glow)
    draw.rectangle((px - 1, py - 1, px + 1, py + 1), fill=(255, 239, 166, 255))
    return glow


def wheel_overlay(
    size: tuple[int, int],
    frame_index: int,
    body_size: tuple[int, int],
    offset: tuple[int, int],
    seed: int,
    geometry: dict,
) -> Image.Image:
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    if frame_index == 0:
        return overlay
    width, height = body_size
    ox, oy = offset
    angle = math.radians((frame_index * 34 + seed % 90) % 180)
    draw = ImageDraw.Draw(overlay)
    radius = max(2, round(height * float(geometry["radius_fraction"])))
    for x_fraction, y_fraction in geometry["centres"]:
        px = ox + round(width * float(x_fraction))
        py = oy + round(height * float(y_fraction))
        dx = round(math.cos(angle) * radius)
        dy = round(math.sin(angle) * radius)
        draw.line((px - dx, py - dy, px + dx, py + dy), fill=(214, 224, 229, 176), width=1)
        draw.line((px + dy, py - dx, px - dy, py + dx), fill=(126, 141, 149, 142), width=1)
        draw.ellipse((px - 1, py - 1, px + 1, py + 1), fill=(205, 215, 220, 190))
    return overlay


def marine_overlay(
    size: tuple[int, int],
    frame_index: int,
    body_size: tuple[int, int],
    offset: tuple[int, int],
    settings: dict,
) -> Image.Image:
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    if frame_index == 0:
        return overlay
    width, height = body_size
    ox, oy = offset
    draw = ImageDraw.Draw(overlay)
    wake_strength = float(settings["wake_strength"])
    bow_strength = float(settings["bow_spray"])
    mast_y = oy + round(height * 0.18)
    draw.ellipse(
        (ox + round(width * 0.58) - 1, mast_y - 1, ox + round(width * 0.58) + 1, mast_y + 1),
        fill=(255, 48, 35, 220),
    )
    draw.ellipse(
        (ox + round(width * 0.64) - 1, mast_y - 1, ox + round(width * 0.64) + 1, mast_y + 1),
        fill=(62, 255, 128, 215),
    )
    if frame_index in {3, 8}:
        px = ox + round(width * 0.61)
        draw.ellipse((px - 1, mast_y - 2, px + 1, mast_y), fill=(235, 252, 255, 245))
    wake_y = oy + round(height * 0.88)
    pulse = 0.012 * (frame_index % 4)
    wake_len = max(5, round(width * (0.10 + pulse) * wake_strength))
    draw.line((ox + 1, wake_y, ox + wake_len, wake_y + 1), fill=(206, 238, 255, round(102 * wake_strength)), width=1)
    draw.line((ox + 2, wake_y + 2, ox + round(wake_len * 0.72), wake_y + 2), fill=(190, 230, 250, round(62 * wake_strength)), width=1)
    bow_x = ox + round(width * 0.965)
    bow_y = oy + round(height * 0.79)
    spray = max(2, round(height * 0.055 * bow_strength))
    draw.arc((bow_x - spray, bow_y - spray * 2, bow_x + spray * 2, bow_y + spray), 208, 330, fill=(225, 246, 255, round(112 * bow_strength)), width=1)
    shimmer = overlay.filter(ImageFilter.GaussianBlur(0.28))
    return Image.alpha_composite(overlay, shimmer)


def trailer_overlay(size: tuple[int, int], frame_index: int, body_size: tuple[int, int], offset: tuple[int, int], seed: int) -> Image.Image:
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    if frame_index == 0:
        return overlay
    width, height = body_size
    ox, oy = offset
    draw = ImageDraw.Draw(overlay)
    px = ox + max(1, round(width * 0.025))
    py = oy + round(height * 0.66)
    color = (255, 62, 30, 235) if (frame_index + seed) % 4 < 2 else (255, 166, 28, 185)
    draw.rectangle((px, py, px + 1, py + 1), fill=color)
    return overlay


def animation_durations(seed: int) -> list[int]:
    base = [155, 72, 66, 92, 70, 174, 78, 68, 96, 72, 74, 228]
    durations = [base[0]]
    for index, value in enumerate(base[1:], start=1):
        jitter = ((seed >> (index % 17)) % 17) - 8
        durations.append(max(52, value + jitter))
    return durations


def build_animation(
    base: Image.Image,
    vehicle: dict,
    body_size: tuple[int, int],
    body_offset: tuple[int, int],
    profile: dict,
    rotorless_body: Image.Image | None = None,
    rotorless_base: Image.Image | None = None,
) -> tuple[list[Image.Image], list[int], str]:
    asset_id = vehicle["id"]
    seed = stable_seed(asset_id)
    desynchronisation = profile.get("animation_desynchronisation", {})
    phase = vehicle_flash_phase(asset_id, profile)
    phase_modulus = int(desynchronisation.get("phase_modulus", 11))
    phase_stride = int(desynchronisation.get("per_light_phase_stride", 3))
    active_motion: list[str] = []
    frames: list[Image.Image] = []
    motion = profile["motion"]

    for frame_index in range(profile["frames"]):
        if rotorless_body is not None and frame_index > 0:
            geometry = profile["rotor_geometry"][asset_id]
            if rotorless_base is None:
                raise ValueError(f"missing rotorless base for {asset_id}")
            frame = add_helicopter_rotors(
                rotorless_base,
                rotorless_body.size,
                body_offset,
                frame_index,
                seed,
                geometry,
            )
        else:
            frame = base.copy()
        if vehicle.get("lights"):
            frame = add_blue_lights(
                frame,
                vehicle,
                frame_index,
                body_size,
                body_offset,
                phase,
                phase_modulus,
                phase_stride,
            )
            active_motion.append("blue-response")
            if frame_index > 0 and asset_id not in profile["helicopters"]:
                frame = Image.alpha_composite(
                    frame,
                    response_running_lights_overlay(
                        frame.size,
                        frame_index,
                        body_size,
                        body_offset,
                        asset_id in set(profile.get("left_facing_assets", [])),
                    ),
                )
        if asset_id in profile["helicopters"]:
            frame = Image.alpha_composite(
                frame,
                aviation_lights_overlay(
                    frame.size,
                    frame_index,
                    body_size,
                    body_offset,
                    profile["rotor_geometry"][asset_id],
                ),
            )
            active_motion.append("rotor")
            active_motion.append("aviation-lights")
        if asset_id in motion["amber"]:
            frame = Image.alpha_composite(frame, amber_overlay(frame.size, frame_index, body_size, body_offset, seed))
            active_motion.append("amber-beacon")
        if asset_id in motion["wheel"]:
            frame = Image.alpha_composite(
                frame,
                wheel_overlay(
                    frame.size,
                    frame_index,
                    body_size,
                    body_offset,
                    seed,
                    profile["wheel_geometry"][asset_id],
                ),
            )
            active_motion.append("wheel-motion")
        if asset_id in motion["marine"]:
            frame = Image.alpha_composite(
                frame,
                marine_overlay(
                    frame.size,
                    frame_index,
                    body_size,
                    body_offset,
                    profile["marine_motion"][asset_id],
                ),
            )
            active_motion.append("navigation-and-wake")
        if asset_id in motion["trailer"]:
            frame = Image.alpha_composite(frame, trailer_overlay(frame.size, frame_index, body_size, body_offset, seed))
            active_motion.append("marker-light")
        frames.append(frame)

    durations = animation_durations(seed)
    motion_type = "+".join(dict.fromkeys(active_motion)) if active_motion else "static"
    return frames, durations, motion_type


def frames_decode_exact(path: Path, expected: list[Image.Image]) -> bool:
    with Image.open(path) as animation:
        if int(getattr(animation, "n_frames", 1)) != len(expected):
            return False
        for index, frame in enumerate(expected):
            animation.seek(index)
            decoded = animation.convert("RGBA")
            if ImageChops.difference(decoded, frame).getbbox() is not None:
                return False
    return True


def save_apng(
    frames: list[Image.Image],
    durations: list[int],
    target: Path,
    profile: dict,
) -> dict[str, int | bool]:
    target.parent.mkdir(parents=True, exist_ok=True)
    compression = profile["compression"]
    preferred = int(compression["preferred_disposal"])
    fallback = int(compression["fallback_disposal"])
    selected = fallback
    for disposal in (preferred, fallback):
        frames[0].save(
            target,
            format="PNG",
            save_all=True,
            append_images=frames[1:],
            duration=durations,
            loop=0,
            disposal=disposal,
            blend=0,
            optimize=True,
            compress_level=int(compression["compress_level"]),
        )
        if frames_decode_exact(target, frames):
            selected = disposal
            break
    else:
        raise ValueError(f"lossless APNG verification failed: {target.name}")
    return {
        "bytes": target.stat().st_size,
        "disposal": selected,
        "lossless_verified": True,
    }


def clean_output(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for path in directory.glob("*.png"):
        path.unlink()


def shadow_class_for(vehicle: dict, asset_id: str, profile: dict) -> tuple[str, str]:
    grounding = profile.get("grounding_shadows", {})
    if asset_id in set(grounding.get("aerial", [])):
        return "aerial", "aerial-separated"
    if asset_id in set(grounding.get("marine", [])):
        return "marine", "marine-waterline"
    if asset_id in set(grounding.get("trailers", [])):
        return "ground", "trailer"
    effective_length = float(vehicle["real_length_metres"])
    carrier = profile.get("mounted_carriers", {}).get(asset_id)
    if carrier is not None:
        effective_length = float(carrier["real_length_metres"])
    if effective_length >= float(profile["scale_calibration"]["heavy_vehicle_threshold_metres"]):
        return "ground", "heavy-ground"
    return "ground", "light-ground"


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    profile = PROFILE
    vehicles = sorted(manifest["vehicles"], key=lambda item: int(item["missionchief_slot"]))
    rare = set(profile["rare_showcase"])
    overrides = profile["new_source_overrides"]
    master_report_path = ROOT / str(profile["baked_master_report"])
    if not master_report_path.is_file():
        raise FileNotFoundError(master_report_path)
    master_report = json.loads(master_report_path.read_text(encoding="utf-8"))
    master_map = {item["id"]: item for item in master_report["vehicles"]}
    if set(master_map) != set(profile["baked_master_cues"]):
        raise ValueError("baked v1.3 master report does not match the configured cue inventory")
    light_overrides = dict(profile.get("light_overrides", {}))
    light_overrides_path = profile.get("light_overrides_path")
    if light_overrides_path:
        placement_data = json.loads((ROOT / light_overrides_path).read_text(encoding="utf-8"))
        light_overrides.update(placement_data["vehicles"])
    role_cues = profile.get("role_differentiation", {})
    equipment_cues = profile.get("specialist_equipment", {})
    if role_cues or equipment_cues:
        raise ValueError(
            "generated role and specialist roof overlays are retired; "
            "both active cue maps must remain empty"
        )
    retired_overlay_groups = profile.get("retired_generated_overlays", {})
    retired_overlay_assets = {
        asset_id
        for group in retired_overlay_groups.values()
        for asset_id in group
    }
    satellite_boost = set(profile.get("satellite_contrast_boost", []))
    clean_output(STATIC_DIR)
    clean_output(ANIMATED_DIR)

    results = []
    timing_signatures: Counter[str] = Counter()
    motion_counts: Counter[str] = Counter()
    for vehicle in vehicles:
        asset_id = vehicle["id"]
        master_detail = master_map.get(asset_id)
        light_transform = master_detail.get("light_transform") if master_detail else None
        animation_vehicle = {
            **vehicle,
            "lights": transform_lights(
                light_overrides.get(asset_id, vehicle.get("lights", [])),
                light_transform,
            ),
        }
        standard_path = STANDARD_DIR / f"{asset_id}.png"
        if not standard_path.is_file():
            raise FileNotFoundError(standard_path)
        with Image.open(standard_path) as image:
            standard = crop_to_alpha(image)

        override_path = ROOT / overrides[asset_id] if asset_id in overrides else None
        if override_path is not None:
            with Image.open(override_path) as source:
                body = crop_to_alpha(source, padding=1 if master_detail else 8)
        else:
            body = standard

        target_width, effective_length, scale_error = command_width(vehicle, profile)
        body = resize_width(body, target_width)
        body = modern_tone(body)
        body, livery_pixels = standardise_livery(body, vehicle["service"])
        body = readability_polish(body)
        body, cleanup_metrics = cleanup_alpha_artifacts(body)
        uses_generic_specialist_language = False
        motion_reference_size = body.size
        equipment_cue = None
        equipment_cue_offset = (0, 0)
        equipment_metrics = {"added_alpha_pixels": 0, "half_zoom_added_alpha_pixels": 0}
        role_cue = None
        role_cue_offset = (0, 0)
        body_size = body.size
        retired_overlay_top_padding = (
            max(0, body_size[1] - motion_reference_size[1])
            if asset_id in retired_overlay_assets
            else 0
        )
        rotorless_body = None
        rotorless_base = None
        shadow_mode, shadow_class = shadow_class_for(vehicle, asset_id, profile)
        edge_padding = adaptive_edge_padding(
            asset_id,
            body.width,
            asset_id in satellite_boost,
            profile,
        )
        if asset_id in profile["helicopters"]:
            geometry = profile["rotor_geometry"][asset_id]
            rotorless_body = remove_baked_main_rotor(body, geometry)
            rotorless_base, offset, shadow_metrics, outline_metrics = add_visibility_edge(
                rotorless_body,
                padding=edge_padding,
                shadow_mode=shadow_mode,
                shadow_class=shadow_class,
            )
            static = add_helicopter_rotors(
                rotorless_base,
                rotorless_body.size,
                offset,
                0,
                stable_seed(asset_id),
                geometry,
            )
        else:
            static, offset, shadow_metrics, outline_metrics = add_visibility_edge(
                body,
                padding=edge_padding,
                boosted=asset_id in satellite_boost,
                shadow_mode=shadow_mode,
                shadow_class=shadow_class,
            )

        motion_reference_offset = (
            offset[0] + equipment_cue_offset[0] + role_cue_offset[0],
            offset[1] + equipment_cue_offset[1] + role_cue_offset[1],
        )

        static_path = STATIC_DIR / f"{asset_id}.png"
        static_path.parent.mkdir(parents=True, exist_ok=True)
        static.save(static_path, format="PNG", optimize=True)
        frames, durations, motion_type = build_animation(
            static,
            animation_vehicle,
            motion_reference_size,
            motion_reference_offset,
            profile,
            rotorless_body=rotorless_body,
            rotorless_base=rotorless_base,
        )
        animated_path = ANIMATED_DIR / f"{asset_id}.png"
        compression_metrics = save_apng(frames, durations, animated_path, profile)

        signature = ",".join(str(value) for value in durations)
        timing_signatures[signature] += 1
        motion_counts[motion_type] += 1
        results.append(
            {
                "slot": vehicle["missionchief_slot"],
                "id": asset_id,
                "service": vehicle["service"],
                "rare_showcase": asset_id in rare,
                "generic_specialist_language": uses_generic_specialist_language,
                "role_cue": role_cue,
                "role_cue_offset": {"x": role_cue_offset[0], "y": role_cue_offset[1]},
                "specialist_equipment_cue": equipment_cue,
                "specialist_equipment_offset": {
                    "x": equipment_cue_offset[0],
                    "y": equipment_cue_offset[1],
                },
                "specialist_equipment_added_alpha_pixels": equipment_metrics["added_alpha_pixels"],
                "specialist_equipment_half_zoom_added_alpha_pixels": equipment_metrics[
                    "half_zoom_added_alpha_pixels"
                ],
                "retired_generated_overlay": asset_id in retired_overlay_assets,
                "retired_overlay_top_padding_pixels": retired_overlay_top_padding,
                "satellite_contrast_boost": asset_id in satellite_boost,
                "edge_padding": edge_padding,
                "grounding_shadow": shadow_metrics,
                "adaptive_outline": outline_metrics,
                "source_override": str(override_path.relative_to(ROOT)) if override_path else None,
                "baked_master_cue": profile.get("baked_master_cues", {}).get(asset_id),
                "baked_master_half_zoom_added_alpha_pixels": (
                    master_detail.get("half_zoom_added_alpha_pixels") if master_detail else None
                ),
                "standard_dimensions": {"width": standard.width, "height": standard.height},
                "command_dimensions": {"width": static.width, "height": static.height},
                "body_dimensions": {"width": body_size[0], "height": body_size[1]},
                "motion_reference_dimensions": {
                    "width": motion_reference_size[0],
                    "height": motion_reference_size[1],
                },
                "width_gain_percent": round((body_size[0] / standard.width - 1) * 100, 1),
                "effective_real_length_metres": effective_length,
                "calibrated_target_body_width": target_width,
                "length_scale_error_percent": round(scale_error, 3),
                "livery_pixels_normalised": livery_pixels,
                "alpha_cleanup": cleanup_metrics,
                "half_zoom_detail_score": half_zoom_detail_score(static),
                "frames": len(frames),
                "response_light_count": len(animation_vehicle.get("lights", [])),
                "fixture_shaped_emergency_lights": bool(animation_vehicle.get("lights")),
                "response_running_lights": bool(
                    animation_vehicle.get("lights")
                    and asset_id not in profile["helicopters"]
                    and body_size[0] >= int(profile["response_running_lights"]["minimum_body_width"])
                ),
                "aviation_navigation_lights": asset_id in profile["helicopters"],
                "preserved_tail_rotor_animated": bool(
                    profile.get("rotor_geometry", {})
                    .get(asset_id, {})
                    .get("animate_preserved_tail_rotor", False)
                ),
                "marine_motion_profile": profile.get("marine_motion", {}).get(asset_id),
                "wheel_geometry": profile.get("wheel_geometry", {}).get(asset_id),
                "durations_ms": durations,
                "cycle_ms": sum(durations),
                "flash_phase": vehicle_flash_phase(asset_id, profile)
                if animation_vehicle.get("lights")
                else None,
                "flash_activity_signature": flash_activity_signature(animation_vehicle, profile),
                "motion": motion_type,
                "apng_compression": compression_metrics,
            }
        )

    blue_results = [item for item in results if item["flash_phase"] is not None]
    flash_phase_counts = Counter(item["flash_phase"] for item in blue_results)
    flash_activity_signatures = Counter(item["flash_activity_signature"] for item in blue_results)
    report = {
        "release": profile["release"],
        "all_passed": True,
        "profile": profile["profile"],
        "display_name": profile["display_name"],
        "selected_upgrades": profile["selected_upgrades"],
        "vehicles": len(results),
        "static_pngs": len(list(STATIC_DIR.glob("*.png"))),
        "animated_apngs": len(list(ANIMATED_DIR.glob("*.png"))),
        "frames_per_asset": profile["frames"],
        "source_overrides": sum(item["source_override"] is not None for item in results),
        "baked_role_master_assets": sum(item["baked_master_cue"] is not None for item in results),
        "rare_showcase_assets": sum(item["rare_showcase"] for item in results),
        "role_differentiated_assets": sum(item["role_cue"] is not None for item in results),
        "specialist_equipment_assets": sum(
            item["specialist_equipment_cue"] is not None for item in results
        ),
        "retired_generated_overlay_assets": sum(
            item["retired_generated_overlay"] for item in results
        ),
        "maximum_retired_overlay_top_padding_pixels": max(
            item["retired_overlay_top_padding_pixels"] for item in results
        ),
        "satellite_contrast_boosted_assets": sum(item["satellite_contrast_boost"] for item in results),
        "grounding_shadow_assets": sum(item["grounding_shadow"]["visible_pixels"] > 0 for item in results),
        "minimum_grounding_shadow_half_zoom_pixels": min(
            item["grounding_shadow"]["half_zoom_visible_pixels"] for item in results
        ),
        "shadow_class_counts": dict(sorted(Counter(item["grounding_shadow"]["class"] for item in results).items())),
        "outline_style_counts": dict(sorted(Counter(item["adaptive_outline"]["style"] for item in results).items())),
        "maximum_outline_to_body_ratio": max(item["adaptive_outline"]["outline_to_body_ratio"] for item in results),
        "mean_length_scale_error_percent": round(
            sum(item["length_scale_error_percent"] for item in results) / len(results), 3
        ),
        "maximum_length_scale_error_percent": max(item["length_scale_error_percent"] for item in results),
        "minimum_half_zoom_detail_score": min(item["half_zoom_detail_score"] for item in results),
        "livery_pixels_normalised": sum(item["livery_pixels_normalised"] for item in results),
        "isolated_alpha_pixels_remaining": sum(
            item["alpha_cleanup"]["remaining_isolated_alpha_pixels"] for item in results
        ),
        "animated_bytes": sum(item["apng_compression"]["bytes"] for item in results),
        "animated_baseline_bytes": int(profile["compression"]["baseline_animated_bytes"]),
        "animated_size_ratio": round(
            sum(item["apng_compression"]["bytes"] for item in results)
            / int(profile["compression"]["baseline_animated_bytes"]),
            5,
        ),
        "preferred_disposal_assets": sum(
            item["apng_compression"]["disposal"] == int(profile["compression"]["preferred_disposal"])
            for item in results
        ),
        "motion_counts": dict(sorted(motion_counts.items())),
        "timing_signature_count": len(timing_signatures),
        "maximum_shared_timing_signature": max(timing_signatures.values()),
        "blue_response_assets": len(blue_results),
        "flash_phase_bucket_count": len(flash_phase_counts),
        "flash_phase_counts": {
            str(key): value for key, value in sorted(flash_phase_counts.items())
        },
        "maximum_shared_flash_phase": max(flash_phase_counts.values()),
        "flash_activity_signature_count": len(flash_activity_signatures),
        "maximum_shared_flash_activity_signature": max(flash_activity_signatures.values()),
        "minimum_body_width": min(item["body_dimensions"]["width"] for item in results),
        "maximum_body_width": max(item["body_dimensions"]["width"] for item in results),
        "vehicles_detail": results,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "vehicles_detail"}, indent=2))


if __name__ == "__main__":
    main()
