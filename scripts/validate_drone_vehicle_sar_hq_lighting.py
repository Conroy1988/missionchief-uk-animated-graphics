#!/usr/bin/env python3
"""Reject any return of the SAR drone vehicle's detached launch assembly."""

from __future__ import annotations

import io
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

from build_v1_1_enhanced import crop_to_alpha
from build_v1_3_masters import master_tone


ROOT = Path(__file__).resolve().parents[1]
ASSET_ID = "drone-vehicle-sar-hq"
MASTER_PATH = ROOT / "assets" / "masters" / "v1.3.0" / f"{ASSET_ID}.png"
STANDARD_PATH = ROOT / "assets" / "exports" / "standard" / "static" / f"{ASSET_ID}.png"
STATIC_PATH = ROOT / "assets" / "exports" / "command" / "static" / f"{ASSET_ID}.png"
ANIMATED_PATH = ROOT / "assets" / "exports" / "command" / "animated" / f"{ASSET_ID}.png"
PROFILE_PATH = ROOT / "data" / "v1.4-overhaul-profile.json"
BASELINE = "v1.4.12"
MASTER_MARKERS = {(35, 14), (45, 14)}
COMMAND_MARKERS = {(39, 18), (49, 18)}
EXPECTED_MASTER_CHANGED = (
    {(40, 13)}
    | {(x, 14) for x in range(35, 46)}
    | {(x, 15) for x in range(30, 52)}
)
EXPECTED_ADDED_ALPHA = (
    {(40, 13)}
    | {(x, 14) for x in range(35, 46)}
    | {(x, 15) for x in range(30, 49)}
)
EXPECTED_FOLDED_AIRFRAME = {(40, 13)} | {(x, 14) for x in range(38, 43)}
EXPECTED_RESPONSE_PIXELS = [(38, 20), (6, 34), (80, 34)]
FIXED_COMMAND_HARDWARE_BOX = (33, 17, 56, 20)


def warm_marker(pixel: tuple[int, int, int, int]) -> bool:
    red, green, blue, alpha = pixel
    return (
        alpha >= 180
        and red >= 240
        and 100 <= green <= 240
        and blue <= 70
        and red - green >= 10
    )


def marker_points(
    image: Image.Image,
    box: tuple[int, int, int, int],
) -> set[tuple[int, int]]:
    rgba = image.convert("RGBA")
    left, top, right, bottom = box
    return {
        (x, y)
        for y in range(top, bottom)
        for x in range(left, right)
        if warm_marker(rgba.getpixel((x, y)))
    }


def tagged_image(relative: Path) -> Image.Image:
    data = subprocess.check_output(["git", "show", f"{BASELINE}:{relative.as_posix()}"], cwd=ROOT)
    return Image.open(io.BytesIO(data)).convert("RGBA")


def approved_source_canvas(master_size: tuple[int, int]) -> Image.Image:
    with Image.open(STANDARD_PATH) as source:
        original = master_tone(crop_to_alpha(source, padding=1))
    if original.size != (81, 44):
        raise SystemExit(f"SAR Drone Vehicle standard source dimensions changed: {original.size}")
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
    draw.text((24, 18), "SAR Drone Vehicle roof-equipment repair — MissionChief slot 90", font=font(28), fill="white")
    draw.text((340, 64), f"{BASELINE} · deep launch box and spread drone", font=font(17), fill=(255, 166, 166))
    draw.text((840, 64), f"{release} · attached folded-drone rail", font=font(17), fill=(148, 235, 190))

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

    target = ROOT / "assets" / "previews" / release / "drone-vehicle-sar-hq-roof-equipment-before-after.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target, format="PNG", optimize=True)
    return target


def main() -> None:
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    release = str(profile["release"])
    fixtures = json.loads((ROOT / profile["current_light_fixtures_path"]).read_text(encoding="utf-8"))
    build = json.loads((ROOT / "data" / f"{release}-build-report.json").read_text(encoding="utf-8"))
    detail = next(item for item in build["vehicles_detail"] if item["id"] == ASSET_ID)
    manifest = json.loads((ROOT / "data" / "prototypes.json").read_text(encoding="utf-8"))
    manifest_item = next(item for item in manifest["vehicles"] if item["id"] == ASSET_ID)

    with Image.open(MASTER_PATH) as image:
        master = image.convert("RGBA")
    with Image.open(STATIC_PATH) as image:
        static = image.convert("RGBA")
    old_master = tagged_image(MASTER_PATH.relative_to(ROOT))
    old_static = tagged_image(STATIC_PATH.relative_to(ROOT))

    if int(manifest_item["missionchief_slot"]) != 90:
        raise SystemExit("SAR Drone Vehicle must remain mapped to MissionChief slot 90 / edit index 89")
    if master.size != (81, 45):
        raise SystemExit(f"SAR Drone Vehicle master dimensions changed: {master.size}")
    if static.size != (89, 53) or old_static.size != (89, 53):
        raise SystemExit(f"SAR Drone Vehicle command dimensions changed: {old_static.size} -> {static.size}")
    if master.getchannel("A").getbbox() != (0, 1, 81, 45):
        raise SystemExit("SAR Drone Vehicle master moved away from its approved source anchor")
    if static.getchannel("A").getbbox() != (3, 4, 86, 53):
        raise SystemExit("SAR Drone Vehicle command graphic moved away from its bottom-centre map anchor")
    if old_master.size != master.size or old_master.getchannel("A").getbbox() != master.getchannel("A").getbbox():
        raise SystemExit("SAR Drone Vehicle repair changed the established canvas or map anchor")

    source = approved_source_canvas(master.size)
    changed = pixel_changes(master, source)
    if changed != EXPECTED_MASTER_CHANGED:
        raise SystemExit(
            "SAR Drone Vehicle may only differ from its approved source on the compact stowage rail: "
            f"expected {sorted(EXPECTED_MASTER_CHANGED)}, found {sorted(changed)}"
        )
    added = added_alpha(master, source)
    if added != EXPECTED_ADDED_ALPHA:
        raise SystemExit(
            f"SAR folded-drone alpha geometry changed: expected {sorted(EXPECTED_ADDED_ALPHA)}, found {sorted(added)}"
        )
    if marker_points(master, (25, 5, 60, 20)) != MASTER_MARKERS:
        raise SystemExit("SAR master must retain exactly two isolated folded-drone stowage markers")
    if marker_points(static, (28, 8, 62, 20)) != COMMAND_MARKERS:
        raise SystemExit("SAR command static must retain exactly two isolated folded-drone stowage markers")
    steel = (185, 200, 208, 248)
    actual_airframe = {point for point in EXPECTED_MASTER_CHANGED if master.getpixel(point) == steel}
    if actual_airframe != EXPECTED_FOLDED_AIRFRAME:
        raise SystemExit("SAR master must retain one compact longitudinally folded airframe")
    if any(y < 13 for x, y in changed) or max(y for x, y in added) - min(y for x, y in added) + 1 != 3:
        raise SystemExit("SAR repair reintroduced a raised launch box or spread rotor silhouette")
    if ImageChops.difference(master.crop((42, 9, 46, 14)), source.crop((42, 9, 46, 14))).getbbox() is not None:
        raise SystemExit("SAR repair changed the genuine source emergency lightbar")
    if ImageChops.difference(master.crop((26, 16, 44, 18)), source.crop((26, 16, 44, 18))).getbbox() is not None:
        raise SystemExit("SAR repair changed the genuine source emergency lightbar base")
    if ImageChops.difference(master.crop((65, 1, 73, 16)), source.crop((65, 1, 73, 16))).getbbox() is not None:
        raise SystemExit("SAR repair changed the genuine source rear communications mast")
    if ImageChops.difference(old_master, master).getbbox() != (30, 8, 54, 19):
        raise SystemExit("SAR repair no longer removes exactly the defective detached launch-assembly region")

    actual_pixels = [(int(item["x"]), int(item["y"])) for item in detail["response_light_pixels"]]
    if actual_pixels != EXPECTED_RESPONSE_PIXELS:
        raise SystemExit(f"SAR Drone Vehicle animation fixtures changed: expected {EXPECTED_RESPONSE_PIXELS}, found {actual_pixels}")
    if int(detail["response_light_count"]) != 3:
        raise SystemExit("SAR Drone Vehicle must retain exactly three response emitters")
    if any(item["fixture"] != "point-emitter" for item in detail["response_light_pixels"]):
        raise SystemExit("SAR Drone Vehicle response lights must remain isolated point emitters")
    if fixtures["vehicles"].get(ASSET_ID):
        raise SystemExit("SAR Drone Vehicle must continue using its audited three-emitter default geometry")
    compression = detail["apng_compression"]
    if compression["full_canvas_frames"] != 12 or compression["partial_update_frames"] != 0:
        raise SystemExit("SAR Drone Vehicle APNG must retain twelve full-canvas frames")

    emitter_activity = {point: [] for point in EXPECTED_RESPONSE_PIXELS}
    fixed_hardware = static.crop(FIXED_COMMAND_HARDWARE_BOX)
    with Image.open(ANIMATED_PATH) as animation:
        if int(getattr(animation, "n_frames", 1)) != 12:
            raise SystemExit("SAR Drone Vehicle APNG must contain 12 full frames")
        for index in range(animation.n_frames):
            animation.seek(index)
            frame = animation.convert("RGBA")
            if frame.size != static.size:
                raise SystemExit(f"SAR Drone Vehicle APNG frame {index} is not full canvas")
            if index == 0 and ImageChops.difference(frame, static).getbbox() is not None:
                raise SystemExit("SAR Drone Vehicle APNG frame zero no longer matches the static PNG")
            if marker_points(frame, (28, 8, 62, 20)) != COMMAND_MARKERS:
                raise SystemExit(f"SAR folded-drone stowage markers animate or drift in frame {index}")
            if ImageChops.difference(frame.crop(FIXED_COMMAND_HARDWARE_BOX), fixed_hardware).getbbox() is not None:
                raise SystemExit(f"SAR folded-drone rail animates or drifts in frame {index}")
            for point in EXPECTED_RESPONSE_PIXELS:
                emitter_activity[point].append(frame.getpixel(point) != static.getpixel(point))

    for point, activity in emitter_activity.items():
        if not any(activity):
            raise SystemExit(f"SAR Drone Vehicle response emitter {point} never flashes")

    preview = render_before_after(static, release)
    print(json.dumps({
        "status": "PASS",
        "release": release,
        "asset": ASSET_ID,
        "slot": 90,
        "edit_index": 89,
        "master_dimensions": list(master.size),
        "command_dimensions": list(static.size),
        "stowage_profile_height_pixels": 3,
        "stowage_markers": 2,
        "deep_launch_boxes": 0,
        "spread_drone_silhouettes": 0,
        "preserved_source_emergency_lightbars": 1,
        "preserved_source_communications_masts": 1,
        "animated_response_emitters": 3,
        "frames": 12,
        "preview": str(preview.relative_to(ROOT)),
    }, indent=2))


if __name__ == "__main__":
    main()
