#!/usr/bin/env python3
"""Build and validate the MissionChief UK golden-set prototype exports."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


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
    return resized


def blue_flash(size: tuple[int, int], x: float, y: float, strength: float) -> Image.Image:
    width, height = size
    px = round(x * (width - 1))
    py = round(y * (height - 1))
    radius = max(2, round(max(3.0, height * 0.10) * strength))

    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    draw.ellipse(
        (px - radius * 2, py - radius, px + radius * 2, py + radius),
        fill=(0, 120, 255, 105),
    )
    glow = glow.filter(ImageFilter.GaussianBlur(max(1.0, radius * 0.72)))

    core = Image.new("RGBA", size, (0, 0, 0, 0))
    core_draw = ImageDraw.Draw(core)
    core_radius = max(1, radius // 3)
    core_draw.ellipse(
        (px - core_radius, py - core_radius, px + core_radius, py + core_radius),
        fill=(210, 242, 255, 255),
    )
    core_draw.ellipse(
        (px - radius, py - max(1, radius // 3), px + radius, py + max(1, radius // 3)),
        fill=(45, 165, 255, 225),
    )
    return Image.alpha_composite(glow, core)


def light_frame(base: Image.Image, lights: list[dict], active: set[str]) -> Image.Image:
    frame = base.copy()
    for light in lights:
        if light["group"] not in active:
            continue
        overlay = blue_flash(
            frame.size,
            float(light["x"]),
            float(light["y"]),
            float(light.get("size", 1.0)),
        )
        frame = Image.alpha_composite(frame, overlay)
    return frame


def save_apng(base: Image.Image, lights: list[dict], target: Path) -> tuple[list[Image.Image], list[int]]:
    sequence = [set(), {"a"}, set(), {"b"}, {"a", "b"}, set()]
    durations = [120, 105, 85, 105, 90, 275]
    frames = [light_frame(base, lights, state) for state in sequence]
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
        master = Image.open(source).convert("RGBA")
        cropped = crop_to_alpha(master)
        export = resize_to_real_scale(cropped, float(vehicle["real_length_metres"]), ppm)

        static_path = STATIC_DIR / f"{vehicle['id']}.png"
        animated_path = ANIMATED_DIR / f"{vehicle['id']}.png"
        export.save(static_path, format="PNG", optimize=True)
        frames, _durations = save_apng(export, vehicle["lights"], animated_path)

        corners = [export.getpixel((0, 0))[3], export.getpixel((export.width - 1, 0))[3], export.getpixel((0, export.height - 1))[3], export.getpixel((export.width - 1, export.height - 1))[3]]
        result = {
            "id": vehicle["id"],
            "static": str(static_path.relative_to(ROOT)),
            "animated": str(animated_path.relative_to(ROOT)),
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
        "all_passed": all(item["passed"] for item in results),
        "vehicles": results,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
