#!/usr/bin/env python3
"""Build and validate the MissionChief UK golden-set prototype exports."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from apng_full_frame import save_full_frame_apng


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "prototypes.json"
STATIC_DIR = ROOT / "assets" / "exports" / "standard" / "static"
ANIMATED_DIR = ROOT / "assets" / "exports" / "standard" / "animated"
PREVIEW_DIR = ROOT / "assets" / "previews"
REPORT_PATH = ROOT / "data" / "prototype-validation.json"


def crop_to_alpha(image: Image.Image, padding: int = 6) -> Image.Image:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        raise ValueError("image contains no visible pixels")
    left, top, right, bottom = bbox
    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(rgba.width, right + padding)
    bottom = min(rgba.height, bottom + padding)
    return rgba.crop((left, top, right, bottom))


def normalise_transparent_rgb(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    rgba.putdata(
        [
            (0, 0, 0, 0) if alpha == 0 else (red, green, blue, alpha)
            for red, green, blue, alpha in rgba.get_flattened_data()
        ]
    )
    return rgba


def resize_to_real_scale(image: Image.Image, metres: float, ppm: float) -> Image.Image:
    target_width = max(1, round(metres * ppm))
    target_height = max(1, round(image.height * target_width / image.width))
    resized = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
    # Lanczos can introduce alpha values of 1-3 in otherwise empty edge pixels.
    # Removing that invisible ringing keeps MissionChief exports truly clean at
    # the canvas corners without changing any visible vehicle detail.
    alpha = resized.getchannel("A").point(lambda value: 0 if value <= 3 else value)
    # Very long, shallow pod masters can compress the source padding below one
    # output pixel. Keep the four canvas corners unambiguously transparent while
    # preserving side-mounted feet and hook gear elsewhere on the border.
    alpha_pixels = alpha.load()
    alpha_pixels[0, 0] = 0
    alpha_pixels[target_width - 1, 0] = 0
    alpha_pixels[0, target_height - 1] = 0
    alpha_pixels[target_width - 1, target_height - 1] = 0
    resized.putalpha(alpha)
    # Normalise fully transparent pixels as transparent black. Hidden source
    # colours can bleed at APNG update-tile boundaries in some map renderers.
    return normalise_transparent_rgb(resized)


def blue_flash(
    size: tuple[int, int],
    x: float,
    y: float,
    strength: float,
    clip_mask: Image.Image,
) -> Image.Image:
    """Render a compact optical emitter without a rectangular APNG light tile.

    The original standard renderer painted a broad, filled ellipse around every
    coordinate. At MissionChief map scale that falloff quantised into a visible
    block. Keep the flare to a tiny antialiased lens and clip it to the vehicle
    silhouette plus one pixel, so a lamp can shine without producing a floating
    patch on the map.
    """
    width, height = size
    px = round(x * (width - 1))
    py = round(y * (height - 1))

    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    draw.ellipse(
        (px - 2, py - 1, px + 2, py + 1),
        fill=(0, 118, 255, round(72 + 18 * min(1.0, strength))),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(0.52))
    glow.putalpha(ImageChops.multiply(glow.getchannel("A"), clip_mask))

    core = Image.new("RGBA", size, (0, 0, 0, 0))
    core_draw = ImageDraw.Draw(core)
    core_draw.line((px - 1, py, px + 1, py), fill=(52, 176, 255, 248), width=1)
    core_draw.point((px, py), fill=(228, 251, 255, 255))
    core.putalpha(ImageChops.multiply(core.getchannel("A"), clip_mask))
    return Image.alpha_composite(glow, core)


def light_frame(base: Image.Image, lights: list[dict], active: set[str]) -> Image.Image:
    frame = base.copy()
    clip_mask = base.getchannel("A").point(lambda value: 255 if value else 0)
    clip_mask = clip_mask.filter(ImageFilter.MaxFilter(3))
    for light in lights:
        if light["group"] not in active:
            continue
        overlay = blue_flash(
            frame.size,
            float(light["x"]),
            float(light["y"]),
            float(light.get("size", 1.0)),
            clip_mask,
        )
        frame = Image.alpha_composite(frame, overlay)
    return frame


def save_apng(base: Image.Image, lights: list[dict], target: Path) -> tuple[list[Image.Image], list[int]]:
    sequence = [set(), {"a"}, set(), {"b"}, {"a", "b"}, set()]
    durations = [120, 105, 85, 105, 90, 275]
    frames = [light_frame(base, lights, state) for state in sequence]
    target.parent.mkdir(parents=True, exist_ok=True)
    save_full_frame_apng(
        frames,
        durations,
        target,
        compress_level=9,
        disposal=0,
        blend=0,
    )
    return frames, durations


def build_animation_preview(rows: list[tuple[dict, list[Image.Image]]]) -> None:
    cell_width, cell_height = 360, 170
    left_gutter = 245
    canvas = Image.new(
        "RGBA",
        (left_gutter + cell_width * 6, cell_height * len(rows) + 55),
        (15, 21, 28, 255),
    )
    draw = ImageDraw.Draw(canvas)
    draw.text((24, 20), "Production-set APNG frame QA", fill=(255, 255, 255, 255))

    for row_index, (vehicle, frames) in enumerate(rows):
        top = 55 + row_index * cell_height
        draw.text((24, top + 64), vehicle["display_name"], fill=(224, 232, 240, 255))
        for frame_index, frame in enumerate(frames):
            left = left_gutter + frame_index * cell_width
            draw.rounded_rectangle(
                (left + 8, top + 8, left + cell_width - 8, top + cell_height - 8),
                10,
                fill=(34, 44, 55, 255),
            )
            scale = max(1, min(3, (cell_width - 32) // frame.width, (cell_height - 42) // frame.height))
            enlarged = frame.resize((frame.width * scale, frame.height * scale), Image.Resampling.NEAREST)
            x = left + (cell_width - enlarged.width) // 2
            y = top + (cell_height - enlarged.height) // 2
            canvas.alpha_composite(enlarged, (x, y))
            draw.text((left + 16, top + 15), f"Frame {frame_index + 1}", fill=(151, 166, 181, 255))

    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(PREVIEW_DIR / "production-set-animation-frames.png", quality=95)


def build_map_preview(exports: list[tuple[dict, Image.Image]]) -> None:
    columns = 2
    rows = (len(exports) + columns - 1) // columns
    width, height = 1100, 105 + rows * 145
    canvas = Image.new("RGBA", (width, height), (220, 226, 218, 255))
    draw = ImageDraw.Draw(canvas)

    for offset in range(-300, width + 300, 115):
        draw.line((offset, 0, offset + 480, height), fill=(196, 204, 194, 255), width=18)
        draw.line((offset, 0, offset + 480, height), fill=(247, 247, 242, 255), width=12)
    road_levels = [105 + row * 145 for row in range(rows)]
    for y in road_levels:
        draw.line((0, y, width, y), fill=(188, 197, 189, 255), width=30)
        draw.line((0, y, width, y), fill=(250, 249, 244, 255), width=21)
        draw.line((0, y, width, y), fill=(221, 197, 102, 255), width=2)

    for index, (vehicle, image) in enumerate(exports):
        row, column = divmod(index, columns)
        x = 70 + column * 545
        y = road_levels[row]
        shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
        shadow.putalpha(image.getchannel("A").filter(ImageFilter.GaussianBlur(2)))
        black = Image.new("RGBA", image.size, (18, 25, 31, 100))
        black.putalpha(shadow.getchannel("A").point(lambda value: value // 3))
        canvas.alpha_composite(black, (x + 2, y + 3 - image.height))
        canvas.alpha_composite(image, (x, y - image.height))
        label = vehicle["display_name"]
        draw.rounded_rectangle((x - 4, y + 7, x + max(155, len(label) * 7), y + 31), 7, fill=(20, 27, 34, 220))
        draw.text((x + 5, y + 12), label, fill=(255, 255, 255, 255))

    draw.rounded_rectangle((24, 22, 370, 66), 12, fill=(20, 27, 34, 230))
    draw.text((39, 35), "MissionChief map-scale production set", fill=(255, 255, 255, 255))
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(PREVIEW_DIR / "production-set-map-scale.png", quality=94)


def frame_count(path: Path) -> int:
    image = Image.open(path)
    return int(getattr(image, "n_frames", 1))


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ppm = float(manifest["pack"]["pixels_per_metre"])
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    ANIMATED_DIR.mkdir(parents=True, exist_ok=True)

    preview_exports: list[tuple[dict, Image.Image]] = []
    animation_rows: list[tuple[dict, list[Image.Image]]] = []
    results = []

    vehicles = sorted(manifest["vehicles"], key=lambda item: int(item.get("missionchief_slot", 9999)))
    for vehicle in vehicles:
        source = ROOT / vehicle["source"]
        static_path = STATIC_DIR / f"{vehicle['id']}.png"
        animated_path = ANIMATED_DIR / f"{vehicle['id']}.png"
        source_fallback = False
        if source.is_file():
            master = Image.open(source).convert("RGBA")
            cropped = crop_to_alpha(master)
            export = resize_to_real_scale(cropped, float(vehicle["real_length_metres"]), ppm)
        elif static_path.is_file():
            # Some original true-scale source masters were never committed.
            # Their approved production PNGs are lossless and remain the only
            # authoritative source available to local and CI rebuilds.
            export = normalise_transparent_rgb(Image.open(static_path).convert("RGBA"))
            source_fallback = True
        else:
            raise FileNotFoundError(f"missing source and production fallback for {vehicle['id']}")
        if not source_fallback:
            export.save(static_path, format="PNG", optimize=True)
        frames, _durations = save_apng(export, vehicle["lights"], animated_path)

        corners = [export.getpixel((0, 0))[3], export.getpixel((export.width - 1, 0))[3], export.getpixel((0, export.height - 1))[3], export.getpixel((export.width - 1, export.height - 1))[3]]
        result = {
            "id": vehicle["id"],
            "static": str(static_path.relative_to(ROOT)),
            "animated": str(animated_path.relative_to(ROOT)),
            "source_fallback": source_fallback,
            "static_preserved_from_production_fallback": source_fallback,
            "dimensions": {"width": export.width, "height": export.height},
            "alpha_mode": export.mode,
            "transparent_corners": all(value == 0 for value in corners),
            "apng_frames": frame_count(animated_path),
            "passed": export.mode == "RGBA" and all(value == 0 for value in corners) and frame_count(animated_path) == 6,
        }
        results.append(result)
        preview_exports.append((vehicle, export))
        animation_rows.append((vehicle, frames))

    build_map_preview(preview_exports)
    build_animation_preview(animation_rows)
    report = {
        "pack": manifest["pack"]["name"],
        "profile": "standard",
        "production_static_fallbacks": sum(item["source_fallback"] for item in results),
        "all_passed": all(item["passed"] for item in results),
        "vehicles": results,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
