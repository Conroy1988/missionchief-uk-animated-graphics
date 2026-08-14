#!/usr/bin/env python3
"""Reject any return of the Armed Traffic Car's raised roof pods and mast."""

from __future__ import annotations

import io
import json
import subprocess
from collections import deque
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSET_ID = "armed-traffic-car"
MASTER_PATH = ROOT / "assets" / "masters" / "v1.3.0" / f"{ASSET_ID}.png"
STATIC_PATH = ROOT / "assets" / "exports" / "command" / "static" / f"{ASSET_ID}.png"
ANIMATED_PATH = ROOT / "assets" / "exports" / "command" / "animated" / f"{ASSET_ID}.png"
PROFILE_PATH = ROOT / "data" / "v1.4-overhaul-profile.json"
BASELINE = "v1.4.10"
MASTER_LENSES = {(26, 1), (32, 1)}
COMMAND_LENSES = {(30, 5), (36, 5)}


def strong_blue(pixel: tuple[int, int, int, int]) -> bool:
    red, green, blue, alpha = pixel
    return alpha >= 128 and blue >= 220 and blue - red >= 70 and blue - green >= 40


def blue_points(image: Image.Image, box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    rgba = image.convert("RGBA")
    left, top, right, bottom = box
    return {
        (x, y)
        for y in range(top, bottom)
        for x in range(left, right)
        if strong_blue(rgba.getpixel((x, y)))
    }


def components(points: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(points)
    found: list[set[tuple[int, int]]] = []
    while remaining:
        start = remaining.pop()
        component = {start}
        queue = deque([start])
        while queue:
            x, y = queue.popleft()
            for candidate in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if candidate in remaining:
                    remaining.remove(candidate)
                    component.add(candidate)
                    queue.append(candidate)
        found.append(component)
    return found


def require_isolated_pair(
    image: Image.Image,
    box: tuple[int, int, int, int],
    expected: set[tuple[int, int]],
    label: str,
) -> None:
    actual = blue_points(image, box)
    if actual != expected:
        raise SystemExit(f"{label} roof lenses changed: expected {sorted(expected)}, found {sorted(actual)}")
    if any(len(component) != 1 for component in components(actual)):
        raise SystemExit(f"{label} contains a joined blue roof-light component")


def require_no_unexpected_roof_blue(
    image: Image.Image,
    box: tuple[int, int, int, int],
    expected: set[tuple[int, int]],
    label: str,
) -> None:
    actual = blue_points(image, box)
    if not actual.issubset(expected):
        raise SystemExit(f"{label} contains unexpected roof blue: {sorted(actual - expected)}")
    if any(len(component) != 1 for component in components(actual)):
        raise SystemExit(f"{label} contains a joined blue roof-light component")


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
    draw.text((24, 18), "Armed Traffic Car roof-pod repair — MissionChief slot 26", font=font(28), fill="white")
    draw.text((340, 64), f"{BASELINE} · raised twin pods and mast", font=font(17), fill=(255, 166, 166))
    draw.text((840, 64), f"{release} · shallow integrated lightbar", font=font(17), fill=(148, 235, 190))

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

    target = ROOT / "assets" / "previews" / release / "armed-traffic-car-roof-pods-before-after.png"
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
    old_static = tagged_image(STATIC_PATH.relative_to(ROOT))

    if master.size != (66, 26):
        raise SystemExit(f"Armed Traffic Car master dimensions changed: {master.size}")
    if static.size != (74, 34):
        raise SystemExit(f"Armed Traffic Car command dimensions changed: {static.size}")
    if old_static.size != (74, 36):
        raise SystemExit(f"Armed Traffic Car baseline dimensions changed: {old_static.size}")
    if master.getchannel("A").getbbox() != (0, 1, 66, 26):
        raise SystemExit("Armed Traffic Car master no longer has the approved low roofline and bottom anchor")
    if static.getchannel("A").getbbox() != (3, 4, 71, 34):
        raise SystemExit("Armed Traffic Car command graphic moved or regained raised roof-pod geometry")

    require_isolated_pair(master, (20, 0, 60, 9), MASTER_LENSES, "master")
    require_isolated_pair(static, (23, 0, 64, 11), COMMAND_LENSES, "command static")

    expected_pixels = [(30, 5), (36, 5), (67, 17), (7, 17)]
    actual_pixels = [(int(item["x"]), int(item["y"])) for item in detail["response_light_pixels"]]
    if actual_pixels != expected_pixels:
        raise SystemExit(f"Armed Traffic Car animation fixtures changed: expected {expected_pixels}, found {actual_pixels}")
    vehicle_fixtures = fixtures["vehicles"].get(ASSET_ID, [])
    if len(vehicle_fixtures) != 4:
        raise SystemExit("Armed Traffic Car must retain two roof emitters plus front and rear emitters")
    if [item["kind"] for item in vehicle_fixtures] != ["roof_a", "roof_b", "front", "rear"]:
        raise SystemExit("Armed Traffic Car fixture roles changed")
    compression = detail["apng_compression"]
    if compression["full_canvas_frames"] != 12 or compression["partial_update_frames"] != 0:
        raise SystemExit("Armed Traffic Car APNG must retain twelve full-canvas frames")

    roof_activity: list[tuple[bool, bool]] = []
    with Image.open(ANIMATED_PATH) as animation:
        if int(getattr(animation, "n_frames", 1)) != 12:
            raise SystemExit("Armed Traffic Car APNG must contain 12 full frames")
        for index in range(animation.n_frames):
            animation.seek(index)
            frame = animation.convert("RGBA")
            if index == 0 and ImageChops.difference(frame, static).getbbox() is not None:
                raise SystemExit("Armed Traffic Car APNG frame zero no longer matches the static PNG")
            require_no_unexpected_roof_blue(frame, (23, 0, 64, 11), COMMAND_LENSES, f"frame {index}")
            roof_activity.append(tuple(frame.getpixel(point) != static.getpixel(point) for point in sorted(COMMAND_LENSES)))

    if not any(first and not second for first, second in roof_activity):
        raise SystemExit("Armed Traffic Car first roof emitter never flashes independently")
    if not any(second and not first for first, second in roof_activity):
        raise SystemExit("Armed Traffic Car second roof emitter never flashes independently")

    preview = render_before_after(static, release)
    print(json.dumps({
        "status": "PASS",
        "release": release,
        "asset": ASSET_ID,
        "master_dimensions": list(master.size),
        "command_dimensions": list(static.size),
        "baseline_command_dimensions": list(old_static.size),
        "master_roof_lenses": 2,
        "command_roof_lenses": 2,
        "maximum_roof_blue_component_pixels": 1,
        "raised_roof_pods": 0,
        "beacon_masts": 0,
        "animated_roof_emitters": 2,
        "frames": 12,
        "preview": str(preview.relative_to(ROOT)),
    }, indent=2))


if __name__ == "__main__":
    main()
