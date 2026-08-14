#!/usr/bin/env python3
"""Reject any return of the SAR Control Van cabinet or duplicate dish mast."""

from __future__ import annotations

import io
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

from build_v1_1_enhanced import crop_to_alpha
from build_v1_3_masters import master_tone


ROOT = Path(__file__).resolve().parents[1]
ASSET_ID = "control-van-sar"
MASTER_PATH = ROOT / "assets" / "masters" / "v1.3.0" / f"{ASSET_ID}.png"
STANDARD_PATH = ROOT / "assets" / "exports" / "standard" / "static" / f"{ASSET_ID}.png"
STATIC_PATH = ROOT / "assets" / "exports" / "command" / "static" / f"{ASSET_ID}.png"
ANIMATED_PATH = ROOT / "assets" / "exports" / "command" / "animated" / f"{ASSET_ID}.png"
PROFILE_PATH = ROOT / "data" / "v1.4-overhaul-profile.json"
BASELINE = "v1.4.11"
MASTER_INDICATORS = {(38, 18), (44, 18), (50, 18)}
COMMAND_INDICATORS = {(42, 22), (48, 22), (54, 22)}
EXPECTED_MASTER_CHANGED = {(x, 18) for x in range(34, 55)}
EXPECTED_ADDED_ALPHA = {(x, 18) for x in range(36, 55)}
COMMAND_ROOF_EMITTERS = ((33, 23), (36, 23))


def amber_status(pixel: tuple[int, int, int, int]) -> bool:
    red, green, blue, alpha = pixel
    return (
        alpha >= 180
        and red >= 180
        and 90 <= green <= 190
        and blue <= 110
        and red - green >= 40
    )


def status_points(
    image: Image.Image,
    box: tuple[int, int, int, int],
) -> set[tuple[int, int]]:
    rgba = image.convert("RGBA")
    left, top, right, bottom = box
    return {
        (x, y)
        for y in range(top, bottom)
        for x in range(left, right)
        if amber_status(rgba.getpixel((x, y)))
    }


def tagged_image(relative: Path) -> Image.Image:
    data = subprocess.check_output(["git", "show", f"{BASELINE}:{relative.as_posix()}"], cwd=ROOT)
    return Image.open(io.BytesIO(data)).convert("RGBA")


def approved_source_canvas(master_size: tuple[int, int]) -> Image.Image:
    with Image.open(STANDARD_PATH) as source:
        original = master_tone(crop_to_alpha(source, padding=1))
    if original.size != (94, 56):
        raise SystemExit(f"SAR Control Van standard source dimensions changed: {original.size}")
    canvas = Image.new("RGBA", master_size, (0, 0, 0, 0))
    canvas.alpha_composite(original, (0, 1))
    return canvas


def pixel_changes(first: Image.Image, second: Image.Image) -> set[tuple[int, int]]:
    if first.size != second.size:
        raise SystemExit(f"cannot compare differently sized images: {first.size} and {second.size}")
    return {
        (x, y)
        for y in range(first.height)
        for x in range(first.width)
        if first.getpixel((x, y)) != second.getpixel((x, y))
    }


def added_alpha(first: Image.Image, second: Image.Image) -> set[tuple[int, int]]:
    return {
        (x, y)
        for y in range(first.height)
        for x in range(first.width)
        if first.getpixel((x, y))[3] > second.getpixel((x, y))[3]
    }


def peak_frame(path: Path, static: Image.Image, tagged: bool = False) -> Image.Image:
    data = (
        subprocess.check_output(["git", "show", f"{BASELINE}:{path.relative_to(ROOT).as_posix()}"], cwd=ROOT)
        if tagged
        else path.read_bytes()
    )
    frames: list[Image.Image] = []
    with Image.open(io.BytesIO(data)) as animation:
        for index in range(int(getattr(animation, "n_frames", 1))):
            animation.seek(index)
            frames.append(animation.convert("RGBA").copy())
    return max(
        frames,
        key=lambda frame: sum(ImageChops.difference(frame, static).convert("L").get_flattened_data()),
    )


def font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default(size=size)


def render_before_after(static: Image.Image, release: str) -> Path:
    old_static = tagged_image(STATIC_PATH.relative_to(ROOT))
    old_peak = peak_frame(ANIMATED_PATH, old_static, tagged=True)
    new_peak = peak_frame(ANIMATED_PATH, static)
    canvas = Image.new("RGB", (1240, 520), (13, 20, 28))
    draw = ImageDraw.Draw(canvas)
    draw.text((24, 18), "SAR Control Van roof-equipment repair — MissionChief slot 86", font=font(28), fill="white")
    draw.text((340, 64), f"{BASELINE} · raised cabinet and duplicate dish mast", font=font(17), fill=(255, 166, 166))
    draw.text((840, 64), f"{release} · low-profile command rail", font=font(17), fill=(148, 235, 190))

    rows = [
        ("Native static", old_static, static, 1),
        ("Static ×4", old_static, static, 4),
        ("Peak flash ×4", old_peak, new_peak, 4),
    ]
    backgrounds = [(235, 238, 231), (84, 103, 72), (20, 28, 37)]
    for row, ((label, old, new, scale), background) in enumerate(zip(rows, backgrounds)):
        top = 102 + row * 132
        draw.text((24, top + 49), label, font=font(16), fill=(218, 228, 236))
        for left, image in ((250, old), (750, new)):
            draw.rounded_rectangle((left, top, left + 450, top + 112), radius=8, fill=background)
            enlarged = image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)
            x = left + (450 - enlarged.width) // 2
            y = top + (112 - enlarged.height) // 2
            canvas.paste(enlarged.convert("RGB"), (x, y), enlarged)

    target = ROOT / "assets" / "previews" / release / "control-van-sar-roof-equipment-before-after.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target, format="PNG", optimize=True)
    return target


def main() -> None:
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    release = str(profile["release"])
    fixtures = json.loads((ROOT / profile["current_light_fixtures_path"]).read_text(encoding="utf-8"))
    build = json.loads((ROOT / "data" / f"{release}-build-report.json").read_text(encoding="utf-8"))
    detail = next(item for item in build["vehicles_detail"] if item["id"] == ASSET_ID)

    with Image.open(MASTER_PATH) as image:
        master = image.convert("RGBA")
    with Image.open(STATIC_PATH) as image:
        static = image.convert("RGBA")
    old_master = tagged_image(MASTER_PATH.relative_to(ROOT))
    old_static = tagged_image(STATIC_PATH.relative_to(ROOT))

    if master.size != (94, 57):
        raise SystemExit(f"SAR Control Van master dimensions changed: {master.size}")
    if static.size != (102, 65) or old_static.size != (102, 65):
        raise SystemExit(f"SAR Control Van command dimensions changed: {old_static.size} -> {static.size}")
    if master.getchannel("A").getbbox() != (0, 1, 94, 57):
        raise SystemExit("SAR Control Van master moved away from its approved source anchor")
    if static.getchannel("A").getbbox() != (3, 4, 99, 65):
        raise SystemExit("SAR Control Van command graphic moved away from its bottom-centre map anchor")
    if old_master.size != master.size or old_master.getchannel("A").getbbox() != master.getchannel("A").getbbox():
        raise SystemExit("SAR Control Van repair changed the established canvas or map anchor")

    source = approved_source_canvas(master.size)
    changed = pixel_changes(master, source)
    if changed != EXPECTED_MASTER_CHANGED:
        raise SystemExit(
            f"SAR Control Van may only differ from its approved source on the command rail: "
            f"expected {sorted(EXPECTED_MASTER_CHANGED)}, found {sorted(changed)}"
        )
    added = added_alpha(master, source)
    if added != EXPECTED_ADDED_ALPHA:
        raise SystemExit(f"SAR command-rail alpha geometry changed: expected {sorted(EXPECTED_ADDED_ALPHA)}, found {sorted(added)}")
    if status_points(master, (20, 0, 70, 23)) != MASTER_INDICATORS:
        raise SystemExit("SAR master must retain exactly three isolated amber command-rail indicators")
    if status_points(static, (20, 0, 75, 27)) != COMMAND_INDICATORS:
        raise SystemExit("SAR command static must retain exactly three isolated amber command-rail indicators")
    if ImageChops.difference(old_master, master).getbbox() != (33, 1, 63, 22):
        raise SystemExit("SAR Control Van repair no longer removes exactly the defective cabinet and duplicate mast region")

    expected_pixels = [(33, 23), (36, 23), (8, 46), (92, 40)]
    actual_pixels = [(int(item["x"]), int(item["y"])) for item in detail["response_light_pixels"]]
    if actual_pixels != expected_pixels:
        raise SystemExit(f"SAR Control Van animation fixtures changed: expected {expected_pixels}, found {actual_pixels}")
    vehicle_fixtures = fixtures["vehicles"].get(ASSET_ID, [])
    if [item["kind"] for item in vehicle_fixtures] != ["roof_a", "roof_b", "front", "rear"]:
        raise SystemExit("SAR Control Van must retain two roof emitters plus front and rear emitters")
    compression = detail["apng_compression"]
    if compression["full_canvas_frames"] != 12 or compression["partial_update_frames"] != 0:
        raise SystemExit("SAR Control Van APNG must retain twelve full-canvas frames")

    roof_activity: list[tuple[bool, bool]] = []
    with Image.open(ANIMATED_PATH) as animation:
        if int(getattr(animation, "n_frames", 1)) != 12:
            raise SystemExit("SAR Control Van APNG must contain 12 full frames")
        for index in range(animation.n_frames):
            animation.seek(index)
            frame = animation.convert("RGBA")
            if frame.size != static.size:
                raise SystemExit(f"SAR Control Van APNG frame {index} is not full canvas")
            if index == 0 and ImageChops.difference(frame, static).getbbox() is not None:
                raise SystemExit("SAR Control Van APNG frame zero no longer matches the static PNG")
            if status_points(frame, (20, 0, 75, 27)) != COMMAND_INDICATORS:
                raise SystemExit(f"SAR command-rail indicators animate or drift in frame {index}")
            roof_activity.append(tuple(frame.getpixel(point) != static.getpixel(point) for point in COMMAND_ROOF_EMITTERS))

    if not any(first and not second for first, second in roof_activity):
        raise SystemExit("SAR Control Van first roof emitter never flashes independently")
    if not any(second and not first for first, second in roof_activity):
        raise SystemExit("SAR Control Van second roof emitter never flashes independently")

    preview = render_before_after(static, release)
    print(json.dumps({
        "status": "PASS",
        "release": release,
        "asset": ASSET_ID,
        "slot": 86,
        "edit_index": 85,
        "master_dimensions": list(master.size),
        "command_dimensions": list(static.size),
        "command_rail_pixels": 21,
        "command_rail_indicators": 3,
        "raised_command_cabinets": 0,
        "duplicate_dish_masts": 0,
        "preserved_source_communications_masts": 1,
        "animated_response_emitters": 4,
        "frames": 12,
        "preview": str(preview.relative_to(ROOT)),
    }, indent=2))


if __name__ == "__main__":
    main()
