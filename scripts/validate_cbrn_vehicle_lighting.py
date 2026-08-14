#!/usr/bin/env python3
"""Reject any return of the CBRN Vehicle's oversized detector cabinet and mast."""

from __future__ import annotations

import io
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSET_ID = "cbrn-vehicle"
MASTER_PATH = ROOT / "assets" / "masters" / "v1.3.0" / f"{ASSET_ID}.png"
STANDARD_PATH = ROOT / "assets" / "exports" / "standard" / "static" / f"{ASSET_ID}.png"
STATIC_PATH = ROOT / "assets" / "exports" / "command" / "static" / f"{ASSET_ID}.png"
ANIMATED_PATH = ROOT / "assets" / "exports" / "command" / "animated" / f"{ASSET_ID}.png"
PROFILE_PATH = ROOT / "data" / "v1.4-overhaul-profile.json"
BASELINE = "v1.4.10"
MASTER_INDICATORS = {(37, 4), (43, 4), (49, 4)}
COMMAND_INDICATORS = {(41, 8), (47, 8), (53, 8)}
EXPECTED_ADDED_ALPHA = {(x, 4) for x in range(35, 54)} - {(42, 4)}


def detector_indicator(pixel: tuple[int, int, int, int]) -> bool:
    red, green, blue, alpha = pixel
    return (
        alpha >= 180
        and red >= 180
        and green >= 170
        and blue <= 140
        and abs(red - green) <= 45
    )


def indicator_points(
    image: Image.Image,
    box: tuple[int, int, int, int],
) -> set[tuple[int, int]]:
    rgba = image.convert("RGBA")
    left, top, right, bottom = box
    return {
        (x, y)
        for y in range(top, bottom)
        for x in range(left, right)
        if detector_indicator(rgba.getpixel((x, y)))
    }


def tagged_image(relative: Path) -> Image.Image:
    data = subprocess.check_output(["git", "show", f"{BASELINE}:{relative.as_posix()}"], cwd=ROOT)
    return Image.open(io.BytesIO(data)).convert("RGBA")


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
    draw.text((24, 18), "CBRN detector-array repair — MissionChief slot 33", font=font(28), fill="white")
    draw.text((340, 64), f"{BASELINE} · raised cabinet and mast", font=font(17), fill=(255, 166, 166))
    draw.text((840, 64), f"{release} · shallow detector rail", font=font(17), fill=(148, 235, 190))

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

    target = ROOT / "assets" / "previews" / release / "cbrn-detector-array-before-after.png"
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
    with Image.open(STANDARD_PATH) as image:
        standard = image.convert("RGBA")
    with Image.open(STATIC_PATH) as image:
        static = image.convert("RGBA")
    old_static = tagged_image(STATIC_PATH.relative_to(ROOT))

    if master.size != (88, 46):
        raise SystemExit(f"CBRN master dimensions changed: {master.size}")
    if static.size != (96, 54):
        raise SystemExit(f"CBRN command dimensions changed: {static.size}")
    if old_static.size != (96, 57):
        raise SystemExit(f"CBRN baseline dimensions changed: {old_static.size}")
    if master.getchannel("A").getbbox() != (0, 1, 88, 46):
        raise SystemExit("CBRN master regained raised cabinet or mast geometry")
    if static.getchannel("A").getbbox() != (3, 6, 93, 54):
        raise SystemExit("CBRN command graphic moved or regained raised roof geometry")

    aligned_standard_alpha = Image.new("L", master.size, 0)
    aligned_standard_alpha.paste(standard.getchannel("A"), (0, 1))
    added_alpha = ImageChops.subtract(master.getchannel("A"), aligned_standard_alpha)
    actual_added_alpha = {
        (x, y)
        for y in range(master.height)
        for x in range(master.width)
        if added_alpha.getpixel((x, y)) >= 64
    }
    if actual_added_alpha != EXPECTED_ADDED_ALPHA:
        raise SystemExit(
            "CBRN detector rail geometry changed: "
            f"expected {sorted(EXPECTED_ADDED_ALPHA)}, found {sorted(actual_added_alpha)}"
        )

    master_indicators = indicator_points(master, (30, 1, 58, 7))
    command_indicators = indicator_points(static, (34, 5, 62, 11))
    if master_indicators != MASTER_INDICATORS:
        raise SystemExit(f"CBRN master detector indicators changed: {sorted(master_indicators)}")
    if command_indicators != COMMAND_INDICATORS:
        raise SystemExit(f"CBRN command detector indicators changed: {sorted(command_indicators)}")

    expected_pixels = [(13, 13), (16, 13), (43, 13), (57, 13), (91, 34), (8, 32)]
    actual_pixels = [(int(item["x"]), int(item["y"])) for item in detail["response_light_pixels"]]
    if actual_pixels != expected_pixels:
        raise SystemExit(f"CBRN animation fixtures changed: expected {expected_pixels}, found {actual_pixels}")
    vehicle_fixtures = fixtures["vehicles"].get(ASSET_ID, [])
    expected_kinds = ["roof_a", "roof_b", "body_a", "body_b", "front", "rear"]
    if [item["kind"] for item in vehicle_fixtures] != expected_kinds:
        raise SystemExit("CBRN must retain four body-mounted response emitters plus front and rear emitters")
    if any(item.get("fixture") != "point-emitter" for item in vehicle_fixtures):
        raise SystemExit("CBRN response lights must remain isolated point emitters")
    compression = detail["apng_compression"]
    if compression["full_canvas_frames"] != 12 or compression["partial_update_frames"] != 0:
        raise SystemExit("CBRN APNG must retain twelve full-canvas frames")

    activity: list[tuple[bool, ...]] = []
    with Image.open(ANIMATED_PATH) as animation:
        if int(getattr(animation, "n_frames", 1)) != 12:
            raise SystemExit("CBRN APNG must contain 12 full frames")
        for index in range(animation.n_frames):
            animation.seek(index)
            frame = animation.convert("RGBA")
            if index == 0 and ImageChops.difference(frame, static).getbbox() is not None:
                raise SystemExit("CBRN APNG frame zero no longer matches the static PNG")
            if any(frame.getpixel(point) != static.getpixel(point) for point in COMMAND_INDICATORS):
                raise SystemExit(f"CBRN detector indicators incorrectly flash in frame {index}")
            activity.append(tuple(frame.getpixel(point) != static.getpixel(point) for point in expected_pixels))

    for index, point in enumerate(expected_pixels):
        if not any(frame[index] for frame in activity):
            raise SystemExit(f"CBRN response emitter at {point} never flashes")
    for first, second, label in ((0, 1, "rear roof"), (2, 3, "forward roof")):
        if not any(frame[first] and not frame[second] for frame in activity):
            raise SystemExit(f"CBRN {label} first emitter never flashes independently")
        if not any(frame[second] and not frame[first] for frame in activity):
            raise SystemExit(f"CBRN {label} second emitter never flashes independently")

    preview = render_before_after(static, release)
    print(json.dumps({
        "status": "PASS",
        "release": release,
        "asset": ASSET_ID,
        "master_dimensions": list(master.size),
        "command_dimensions": list(static.size),
        "baseline_command_dimensions": list(old_static.size),
        "detector_rail_rows": 1,
        "detector_indicators": 3,
        "raised_cabinets": 0,
        "beacon_masts": 0,
        "animated_response_emitters": len(expected_pixels),
        "frames": 12,
        "preview": str(preview.relative_to(ROOT)),
    }, indent=2))


if __name__ == "__main__":
    main()
