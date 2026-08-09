#!/usr/bin/env python3
"""Reject any return of the RRV roof-box and misaligned-light regression."""

from __future__ import annotations

import io
import json
import subprocess
from collections import deque
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ASSET_ID = "rapid-response-vehicle"
MASTER_PATH = ROOT / "assets" / "masters" / "v1.3.0" / f"{ASSET_ID}.png"
STATIC_PATH = ROOT / "assets" / "exports" / "command" / "static" / f"{ASSET_ID}.png"
ANIMATED_PATH = ROOT / "assets" / "exports" / "command" / "animated" / f"{ASSET_ID}.png"
PROFILE_PATH = ROOT / "data" / "v1.4-overhaul-profile.json"
BASELINE = "v1.4.4"


def strong_blue(pixel: tuple[int, int, int, int]) -> bool:
    red, green, blue, alpha = pixel
    return alpha >= 128 and blue >= 220 and blue - red >= 20 and blue - green >= 5


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


def alpha_span(image: Image.Image, y: int, minimum_x: int, maximum_x: int) -> tuple[int, int]:
    points = [
        x
        for x in range(minimum_x, maximum_x)
        if image.convert("RGBA").getpixel((x, y))[3] >= 128
    ]
    if not points:
        raise SystemExit("RRV roof housing disappeared")
    return min(points), max(points)


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
        key=lambda frame: sum(
            ImageChops.difference(frame, static).convert("L").get_flattened_data()
        ),
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
    draw.text((24, 18), "RRV roof-light repair — MissionChief slot 11", font=font(28), fill="white")
    draw.text((340, 64), f"{BASELINE} · oversized medical box", font=font(17), fill=(255, 166, 166))
    draw.text((840, 64), f"{release} · slim isolated lightbar", font=font(17), fill=(148, 235, 190))

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

    target = ROOT / "assets" / "previews" / release / "rrv-roof-light-before-after.png"
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

    if master.size != (64, 23):
        raise SystemExit(f"RRV master dimensions changed: {master.size}")
    if static.size != (72, 31):
        raise SystemExit(f"RRV command dimensions changed: {static.size}")
    if alpha_span(master, 1, 16, 40) != (22, 31):
        raise SystemExit("RRV master roof housing is no longer low profile")

    require_isolated_pair(master, (20, 1, 35, 2), {(25, 1), (28, 1)}, "master")
    require_isolated_pair(static, (24, 5, 39, 6), {(29, 5), (32, 5)}, "command static")

    expected_pixels = [(29, 5), (32, 5), (65, 18)]
    actual_pixels = [(int(item["x"]), int(item["y"])) for item in detail["response_light_pixels"]]
    if actual_pixels != expected_pixels:
        raise SystemExit(f"RRV animation fixtures changed: expected {expected_pixels}, found {actual_pixels}")
    if len(fixtures["vehicles"].get(ASSET_ID, [])) != 3:
        raise SystemExit("RRV must retain two roof emitters and one front emitter")

    changed_roof_points: set[tuple[int, int]] = set()
    with Image.open(ANIMATED_PATH) as animation:
        if int(getattr(animation, "n_frames", 1)) != 12:
            raise SystemExit("RRV APNG must contain 12 full frames")
        for index in range(animation.n_frames):
            animation.seek(index)
            frame = animation.convert("RGBA")
            if index == 0 and ImageChops.difference(frame, static).getbbox() is not None:
                raise SystemExit("RRV APNG frame zero no longer matches the static PNG")
            require_isolated_pair(frame, (24, 5, 39, 6), {(29, 5), (32, 5)}, f"frame {index}")
            difference = ImageChops.difference(frame, static)
            for point in ((29, 5), (32, 5)):
                if difference.getpixel(point) != (0, 0, 0, 0):
                    changed_roof_points.add(point)

    if changed_roof_points != {(29, 5), (32, 5)}:
        raise SystemExit(f"RRV roof emitters do not flash independently: {sorted(changed_roof_points)}")

    preview = render_before_after(static, release)
    print(json.dumps({
        "status": "PASS",
        "release": release,
        "asset": ASSET_ID,
        "master_roof_lenses": 2,
        "command_roof_lenses": 2,
        "maximum_roof_blue_component_pixels": 1,
        "animated_roof_emitters": 2,
        "frames": 12,
        "preview": str(preview.relative_to(ROOT)),
    }, indent=2))


if __name__ == "__main__":
    main()
