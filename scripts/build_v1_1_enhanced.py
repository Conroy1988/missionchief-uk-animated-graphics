#!/usr/bin/env python3
"""Build the deterministic v1.1 Modern Command Visibility fleet profile."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "prototypes.json"
PROFILE_PATH = ROOT / "data" / "v1.1-enhancement-profile.json"
STANDARD_DIR = ROOT / "assets" / "exports" / "standard" / "static"
STATIC_DIR = ROOT / "assets" / "exports" / "command" / "static"
ANIMATED_DIR = ROOT / "assets" / "exports" / "command" / "animated"
REPORT_PATH = ROOT / "data" / "v1.1-build-report.json"


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


def command_width(width: int, asset_id: str, rare: bool, override: bool, maximum: int) -> int:
    if override:
        target = 60
    elif width < 42:
        target = max(54, round(width * 1.75))
    elif width < 60:
        target = round(width * 1.38)
    elif width < 90:
        target = round(width * 1.20)
    else:
        target = round(width * 1.08)
    if rare:
        target = max(target, round(width * 1.14), 72)
    if "helicopter" in asset_id or asset_id == "hems":
        target = max(target, round(width * 1.10))
    return min(maximum, target)


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


def add_visibility_edge(image: Image.Image, padding: int = 5) -> tuple[Image.Image, tuple[int, int]]:
    width, height = image.size
    canvas_size = (width + padding * 2, height + padding * 2)
    source_alpha = Image.new("L", canvas_size, 0)
    source_alpha.paste(image.getchannel("A"), (padding, padding))

    shadow_alpha = source_alpha.filter(ImageFilter.GaussianBlur(1.5)).point(lambda value: round(value * 0.34))
    shadow = Image.new("RGBA", canvas_size, (10, 15, 20, 0))
    shifted_shadow = Image.new("L", canvas_size, 0)
    shifted_shadow.paste(shadow_alpha, (1, 2))
    shadow.putalpha(shifted_shadow)

    outer_mask = source_alpha.filter(ImageFilter.MaxFilter(5))
    outer_ring = ImageChops.subtract(outer_mask, source_alpha)
    outer_ring = outer_ring.point(lambda value: round(value * 0.54))
    outer = Image.new("RGBA", canvas_size, (8, 13, 18, 0))
    outer.putalpha(outer_ring)

    inner_mask = source_alpha.filter(ImageFilter.MaxFilter(3))
    inner_ring = ImageChops.subtract(inner_mask, source_alpha)
    inner_ring = inner_ring.point(lambda value: round(value * 0.62))
    inner = Image.new("RGBA", canvas_size, (244, 248, 250, 0))
    inner.putalpha(inner_ring)

    canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    canvas = Image.alpha_composite(canvas, shadow)
    canvas = Image.alpha_composite(canvas, outer)
    canvas = Image.alpha_composite(canvas, inner)
    canvas.alpha_composite(image, (padding, padding))
    return canvas, (padding, padding)


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


def blue_flash(size: tuple[int, int], px: int, py: int, strength: float, kind: str, flip: bool) -> Image.Image:
    width, height = size
    radius = max(2, round(max(3.0, height * 0.075) * strength))
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    if kind.startswith("roof"):
        half = max(2, radius * 2)
        direction = -1 if flip else 1
        x1 = px - half if direction < 0 else px
        x2 = px if direction < 0 else px + half
        draw.rounded_rectangle((x1, py - max(1, radius // 2), x2, py + max(1, radius // 2)), radius=2, fill=(0, 115, 255, 145))
    else:
        draw.ellipse((px - radius * 2, py - radius, px + radius * 2, py + radius), fill=(0, 110, 255, 122))
    glow = glow.filter(ImageFilter.GaussianBlur(max(0.8, radius * 0.62)))

    core = Image.new("RGBA", size, (0, 0, 0, 0))
    core_draw = ImageDraw.Draw(core)
    if kind.startswith("roof"):
        core_draw.rounded_rectangle((px - radius, py - 1, px + radius, py + 1), radius=1, fill=(65, 183, 255, 242))
        core_draw.point((px, py), fill=(225, 250, 255, 255))
    else:
        core_draw.ellipse((px - 1, py - 1, px + 1, py + 1), fill=(226, 250, 255, 255))
        core_draw.line((px - radius, py, px + radius, py), fill=(48, 169, 255, 230), width=1)
    return Image.alpha_composite(glow, core)


def add_blue_lights(
    frame: Image.Image,
    vehicle: dict,
    frame_index: int,
    body_size: tuple[int, int],
    body_offset: tuple[int, int],
    phase: int,
) -> Image.Image:
    body_width, body_height = body_size
    offset_x, offset_y = body_offset
    result = frame
    for index, light in enumerate(vehicle.get("lights", [])):
        kind = light_kind(light, index)
        subphase = (phase + index * 2) % 5
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


def rotor_overlay(size: tuple[int, int], frame_index: int, seed: int, body_size: tuple[int, int], offset: tuple[int, int]) -> Image.Image:
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    if frame_index == 0:
        return overlay
    draw = ImageDraw.Draw(overlay)
    width, height = body_size
    ox, oy = offset
    main_x = ox + round(width * 0.53)
    main_y = oy + round(height * 0.12)
    rotor_width = round(width * (0.58 + 0.10 * math.sin((frame_index + seed % 5) * 1.6)))
    draw.ellipse(
        (main_x - rotor_width // 2, main_y - 2, main_x + rotor_width // 2, main_y + 2),
        outline=(205, 220, 228, 86),
        width=1,
    )
    draw.line((main_x - rotor_width // 2, main_y, main_x + rotor_width // 2, main_y), fill=(232, 240, 244, 170), width=1)

    tail_x = ox + round(width * 0.105)
    tail_y = oy + round(height * 0.47)
    radius = max(3, round(height * 0.105))
    angle = math.radians((frame_index * 47 + seed % 360) % 360)
    for spoke in (0, math.pi / 2):
        dx = round(math.cos(angle + spoke) * radius)
        dy = round(math.sin(angle + spoke) * radius)
        draw.line((tail_x - dx, tail_y - dy, tail_x + dx, tail_y + dy), fill=(225, 237, 243, 188), width=1)
    draw.ellipse((tail_x - radius, tail_y - radius, tail_x + radius, tail_y + radius), outline=(180, 203, 216, 105), width=1)
    return overlay.filter(ImageFilter.GaussianBlur(0.25))


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


def wheel_overlay(size: tuple[int, int], frame_index: int, body_size: tuple[int, int], offset: tuple[int, int], seed: int) -> Image.Image:
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    if frame_index == 0:
        return overlay
    width, height = body_size
    ox, oy = offset
    radius = max(2, round(height * 0.085))
    angle = math.radians((frame_index * 34 + seed % 90) % 180)
    draw = ImageDraw.Draw(overlay)
    for fraction in (0.24, 0.78):
        px = ox + round(width * fraction)
        py = oy + round(height * 0.80)
        dx = round(math.cos(angle) * radius)
        dy = round(math.sin(angle) * radius)
        draw.line((px - dx, py - dy, px + dx, py + dy), fill=(204, 215, 220, 185), width=1)
        draw.line((px + dy, py - dx, px - dy, py + dx), fill=(130, 145, 152, 150), width=1)
    return overlay


def marine_overlay(size: tuple[int, int], frame_index: int, body_size: tuple[int, int], offset: tuple[int, int]) -> Image.Image:
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    if frame_index == 0:
        return overlay
    width, height = body_size
    ox, oy = offset
    draw = ImageDraw.Draw(overlay)
    if frame_index % 3 == 1:
        px = ox + round(width * 0.61)
        py = oy + round(height * 0.18)
        draw.ellipse((px - 1, py - 1, px + 1, py + 1), fill=(232, 252, 255, 245))
    wake_y = oy + round(height * 0.88)
    wake_len = max(4, round(width * (0.09 + (frame_index % 4) * 0.012)))
    draw.line((ox + 1, wake_y, ox + wake_len, wake_y + 1), fill=(206, 238, 255, 95), width=1)
    return overlay


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
) -> tuple[list[Image.Image], list[int], str]:
    asset_id = vehicle["id"]
    seed = stable_seed(asset_id)
    phase = seed % 5
    motion_type = "static"
    frames: list[Image.Image] = []
    motion = profile["motion"]

    for frame_index in range(profile["frames"]):
        frame = base.copy()
        if vehicle.get("lights"):
            frame = add_blue_lights(frame, vehicle, frame_index, body_size, body_offset, phase)
            motion_type = "blue-response"
        if asset_id in profile["helicopters"]:
            frame = Image.alpha_composite(frame, rotor_overlay(frame.size, frame_index, seed, body_size, body_offset))
            motion_type = "rotor-and-blue-response"
        elif asset_id in motion["amber"]:
            frame = Image.alpha_composite(frame, amber_overlay(frame.size, frame_index, body_size, body_offset, seed))
            motion_type = "amber-beacon"
        elif asset_id in motion["road"]:
            frame = Image.alpha_composite(frame, wheel_overlay(frame.size, frame_index, body_size, body_offset, seed))
            motion_type = "wheel-motion"
        elif asset_id in motion["marine"]:
            frame = Image.alpha_composite(frame, marine_overlay(frame.size, frame_index, body_size, body_offset))
            motion_type = "navigation-and-wake"
        elif asset_id in motion["trailer"]:
            frame = Image.alpha_composite(frame, trailer_overlay(frame.size, frame_index, body_size, body_offset, seed))
            motion_type = "marker-light"
        frames.append(frame)

    durations = animation_durations(seed)
    return frames, durations, motion_type


def save_apng(frames: list[Image.Image], durations: list[int], target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        target,
        format="PNG",
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        disposal=1,
        blend=0,
        optimize=False,
    )


def clean_output(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for path in directory.glob("*.png"):
        path.unlink()


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    vehicles = sorted(manifest["vehicles"], key=lambda item: int(item["missionchief_slot"]))
    rare = set(profile["rare_showcase"])
    overrides = profile["new_source_overrides"]
    clean_output(STATIC_DIR)
    clean_output(ANIMATED_DIR)

    results = []
    timing_signatures: Counter[str] = Counter()
    motion_counts: Counter[str] = Counter()
    for vehicle in vehicles:
        asset_id = vehicle["id"]
        standard_path = STANDARD_DIR / f"{asset_id}.png"
        if not standard_path.is_file():
            raise FileNotFoundError(standard_path)
        with Image.open(standard_path) as image:
            standard = crop_to_alpha(image)

        override_path = ROOT / overrides[asset_id] if asset_id in overrides else None
        if override_path is not None:
            with Image.open(override_path) as source:
                body = crop_to_alpha(source, padding=8)
        else:
            body = standard

        target_width = command_width(
            standard.width,
            asset_id,
            asset_id in rare,
            override_path is not None,
            int(profile["maximum_icon_width"]),
        )
        body = resize_width(body, target_width)
        body = modern_tone(body)
        if asset_id in rare:
            body = add_specialist_language(body, vehicle["service"], asset_id)
        body_size = body.size
        static, offset = add_visibility_edge(body)

        static_path = STATIC_DIR / f"{asset_id}.png"
        static_path.parent.mkdir(parents=True, exist_ok=True)
        static.save(static_path, format="PNG", optimize=True)
        frames, durations, motion_type = build_animation(static, vehicle, body_size, offset, profile)
        animated_path = ANIMATED_DIR / f"{asset_id}.png"
        save_apng(frames, durations, animated_path)

        signature = ",".join(str(value) for value in durations)
        timing_signatures[signature] += 1
        motion_counts[motion_type] += 1
        results.append(
            {
                "slot": vehicle["missionchief_slot"],
                "id": asset_id,
                "service": vehicle["service"],
                "rare_showcase": asset_id in rare,
                "source_override": str(override_path.relative_to(ROOT)) if override_path else None,
                "standard_dimensions": {"width": standard.width, "height": standard.height},
                "command_dimensions": {"width": static.width, "height": static.height},
                "body_dimensions": {"width": body_size[0], "height": body_size[1]},
                "width_gain_percent": round((body_size[0] / standard.width - 1) * 100, 1),
                "frames": len(frames),
                "durations_ms": durations,
                "cycle_ms": sum(durations),
                "motion": motion_type,
            }
        )

    report = {
        "release": profile["release"],
        "profile": profile["profile"],
        "display_name": profile["display_name"],
        "selected_upgrades": profile["selected_upgrades"],
        "vehicles": len(results),
        "static_pngs": len(list(STATIC_DIR.glob("*.png"))),
        "animated_apngs": len(list(ANIMATED_DIR.glob("*.png"))),
        "frames_per_asset": profile["frames"],
        "source_overrides": sum(item["source_override"] is not None for item in results),
        "rare_showcase_assets": sum(item["rare_showcase"] for item in results),
        "motion_counts": dict(sorted(motion_counts.items())),
        "timing_signature_count": len(timing_signatures),
        "maximum_shared_timing_signature": max(timing_signatures.values()),
        "minimum_body_width": min(item["body_dimensions"]["width"] for item in results),
        "maximum_body_width": max(item["body_dimensions"]["width"] for item in results),
        "vehicles_detail": results,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "vehicles_detail"}, indent=2))


if __name__ == "__main__":
    main()
