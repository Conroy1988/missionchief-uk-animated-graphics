#!/usr/bin/env python3
"""Render a fleet-wide emergency-light placement contact sheet."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageSequence


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "prototypes.json"
PROFILE_PATH = ROOT / "data" / "v1.4-overhaul-profile.json"
STATIC_DIR = ROOT / "assets" / "exports" / "command" / "static"
ANIMATED_DIR = ROOT / "assets" / "exports" / "command" / "animated"


def font(size: int) -> ImageFont.ImageFont:
    for candidate in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ):
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def peak_frame(path: Path, static: Image.Image) -> Image.Image:
    with Image.open(path) as image:
        frames = [frame.convert("RGBA") for frame in ImageSequence.Iterator(image)]
    return max(
        frames,
        key=lambda frame: sum(
            sum(pixel[:3])
            for pixel in ImageChops.difference(frame, static).get_flattened_data()
        ),
    )


def nearest_alpha_distance(image: Image.Image, x: int, y: int) -> float:
    alpha = image.getchannel("A")
    visible = []
    for py in range(alpha.height):
        for px in range(alpha.width):
            if alpha.getpixel((px, py)) >= 80:
                visible.append((px, py))
    return min((math.hypot(x - px, y - py) for px, py in visible), default=999.0)


def render_page(
    vehicles: list[dict],
    profile: dict,
    details: dict[str, dict],
    page_index: int,
    output_dir: Path,
) -> Path:
    width = 1800
    header_height = 78
    row_height = 210
    canvas = Image.new("RGBA", (width, header_height + row_height * len(vehicles)), (15, 23, 31, 255))
    draw = ImageDraw.Draw(canvas)
    title_font = font(28)
    label_font = font(18)
    small_font = font(13)
    draw.text((22, 18), f"Emergency-light placement audit — page {page_index}", fill=(242, 247, 250, 255), font=title_font)
    headings = ((390, "STATIC"), (850, "TARGETS"), (1310, "BRIGHTEST FRAME"))
    for x, text in headings:
        draw.text((x, 48), text, fill=(145, 169, 187, 255), font=small_font)

    for row, vehicle in enumerate(vehicles):
        asset_id = vehicle["id"]
        detail = details[asset_id]
        lights = profile.get("light_overrides", {}).get(asset_id, vehicle.get("lights", []))
        y0 = header_height + row * row_height
        draw.rounded_rectangle((12, y0 + 8, width - 12, y0 + row_height - 8), radius=9, fill=(32, 45, 57, 255))
        draw.text((28, y0 + 24), f"{int(vehicle['missionchief_slot']):03}  {vehicle['display_name']}", fill="white", font=label_font)
        draw.text((28, y0 + 53), asset_id, fill=(159, 181, 197, 255), font=small_font)

        static = Image.open(STATIC_DIR / f"{asset_id}.png").convert("RGBA")
        active = peak_frame(ANIMATED_DIR / f"{asset_id}.png", static)
        annotated = static.copy()
        target_draw = ImageDraw.Draw(annotated)
        body_width = int(detail["motion_reference_dimensions"]["width"])
        body_height = int(detail["motion_reference_dimensions"]["height"])
        edge_padding = int(detail["edge_padding"])
        placement_notes = []
        palette = ((255, 58, 72, 255), (255, 196, 42, 255), (48, 225, 145, 255), (184, 105, 255, 255))
        for index, light in enumerate(lights, start=1):
            px = edge_padding + round(float(light["x"]) * (body_width - 1))
            py = edge_padding + round(float(light["y"]) * (body_height - 1))
            color = palette[(index - 1) % len(palette)]
            target_draw.ellipse((px - 4, py - 4, px + 4, py + 4), outline=color, width=2)
            target_draw.line((px - 6, py, px + 6, py), fill=color, width=1)
            target_draw.line((px, py - 6, px, py + 6), fill=color, width=1)
            target_draw.text((px + 5, py - 9), str(index), fill=color, font=small_font)
            distance = nearest_alpha_distance(static, px, py)
            placement_notes.append(f"L{index} ({px},{py}) alpha distance {distance:.1f}px")

        max_width = 410
        max_height = 145
        scale = min(max_width / static.width, max_height / static.height)
        target_size = (max(1, round(static.width * scale)), max(1, round(static.height * scale)))
        for column, image in enumerate((static, annotated, active)):
            resized = image.resize(target_size, Image.Resampling.NEAREST)
            x0 = 340 + column * 460 + (max_width - resized.width) // 2
            yy = y0 + 28 + (max_height - resized.height) // 2
            canvas.alpha_composite(resized, (x0, yy))

        draw.text((340, y0 + 178), "   |   ".join(placement_notes), fill=(177, 198, 212, 255), font=small_font)

    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / f"emergency-light-placement-{page_index:02}.png"
    canvas.convert("RGB").save(target, quality=94)
    return target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT / "assets" / "previews" / "light-placement-audit")
    parser.add_argument("--page-size", type=int, default=10)
    args = parser.parse_args()

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    light_overrides = dict(profile.get("light_overrides", {}))
    light_overrides_path = profile.get("light_overrides_path")
    if light_overrides_path:
        placement_data = json.loads((ROOT / light_overrides_path).read_text(encoding="utf-8"))
        light_overrides.update(placement_data["vehicles"])
    profile["light_overrides"] = light_overrides
    report = json.loads((ROOT / "data" / f"{profile['release']}-build-report.json").read_text(encoding="utf-8"))
    details = {item["id"]: item for item in report["vehicles_detail"]}
    lit = [
        vehicle
        for vehicle in manifest["vehicles"]
        if profile.get("light_overrides", {}).get(vehicle["id"], vehicle.get("lights", []))
    ]
    paths = []
    for start in range(0, len(lit), args.page_size):
        page = lit[start : start + args.page_size]
        paths.append(render_page(page, profile, details, len(paths) + 1, args.output_dir))
    print(json.dumps({"vehicles": len(lit), "pages": [str(path) for path in paths]}, indent=2))


if __name__ == "__main__":
    main()
