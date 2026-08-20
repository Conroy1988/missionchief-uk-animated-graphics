#!/usr/bin/env python3
"""Validate every v2 response APNG and render fleet-wide flash phases."""

from __future__ import annotations

import json
import shutil
import struct
import tempfile
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

from v2_helicopter_rotors import HELICOPTER_GEOMETRY
from v2_profile import (
    ANIMATED_DIR,
    EXPORT_CANVAS,
    EXPORT_SCALE,
    MASTER_CANVAS,
    PREVIEW_DIR,
    RELEASE,
    RELEASE_CANDIDATE,
    ROOT,
    STATIC_DIR,
    master_path,
)


SLOTS = json.loads((ROOT / "data/vehicle-slots.json").read_text())["slots"]
FIXTURES = json.loads((ROOT / f"data/{RELEASE}-light-fixtures.json").read_text())["vehicles"]
REPORT = ROOT / f"data/{RELEASE}-animation-qa-report.json"


THEMES = {
    "light": ((235, 238, 233), (22, 27, 32), (120, 128, 134)),
    "dark": ((37, 43, 49), (245, 247, 249), (154, 166, 177)),
    "satellite": ((83, 103, 72), (250, 252, 247), (185, 200, 176)),
    "grayscale": ((116, 120, 123), (255, 255, 255), (210, 213, 216)),
}


def frames(path: Path) -> tuple[list[Image.Image], list[int], int | None]:
    decoded: list[Image.Image] = []
    durations: list[int] = []
    with Image.open(path) as image:
        loop = image.info.get("loop")
        for index in range(int(getattr(image, "n_frames", 1))):
            image.seek(index)
            decoded.append(image.convert("RGBA").copy())
            durations.append(round(float(image.info.get("duration", 0))))
    return decoded, durations, loop


def apng_controls(path: Path) -> tuple[tuple[int, int], list[dict[str, int]]]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("invalid PNG signature")
    position = 8
    canvas = (0, 0)
    controls: list[dict[str, int]] = []
    while position < len(data):
        if position + 12 > len(data):
            raise ValueError("truncated PNG chunk")
        length = struct.unpack(">I", data[position : position + 4])[0]
        chunk_type = data[position + 4 : position + 8]
        payload = data[position + 8 : position + 8 + length]
        position += length + 12
        if chunk_type == b"IHDR":
            canvas = struct.unpack(">II", payload[:8])
        elif chunk_type == b"fcTL":
            sequence, width, height, x, y, delay_num, delay_den, disposal, blend = struct.unpack(
                ">IIIIIHHBB", payload
            )
            controls.append(
                {
                    "sequence": sequence,
                    "width": width,
                    "height": height,
                    "x": x,
                    "y": y,
                    "delay_num": delay_num,
                    "delay_den": delay_den,
                    "disposal": disposal,
                    "blend": blend,
                }
            )
    return canvas, controls


def change_metrics(static: Image.Image, animation_frames: list[Image.Image]) -> dict[str, int]:
    sizes = {
        "full": EXPORT_CANVAS,
        "75pct": tuple(round(value * 0.75) for value in EXPORT_CANVAS),
        "50pct": tuple(round(value * 0.50) for value in EXPORT_CANVAS),
    }
    reduced_statics = {
        name: static if name == "full" else static.resize(size, Image.Resampling.LANCZOS)
        for name, size in sizes.items()
    }
    best_pixels = {name: 0 for name in sizes}
    best_peak = {name: 0 for name in sizes}
    for frame in animation_frames:
        for name, size in sizes.items():
            shown = frame if name == "full" else frame.resize(size, Image.Resampling.LANCZOS)
            difference = ImageChops.difference(shown, reduced_statics[name]).convert("RGB")
            values = list(difference.get_flattened_data())
            best_pixels[name] = max(
                best_pixels[name], sum(max(pixel) >= 18 for pixel in values)
            )
            best_peak[name] = max(
                best_peak[name], max((max(pixel) for pixel in values), default=0)
            )
    return {
        **{f"changed_pixels_{name}_max": best_pixels[name] for name in sizes},
        **{f"peak_change_{name}": best_peak[name] for name in sizes},
    }


def fixture_overlap(static: Image.Image, fixture: dict) -> float:
    mask = Image.new("L", static.size, 0)
    draw = ImageDraw.Draw(mask)
    points = [tuple(point) for point in fixture["points"]]
    if fixture["shape"] == "polygon":
        draw.polygon(points, fill=255)
    else:
        draw.ellipse((*points[0], *points[1]), fill=255)
    fixture_pixels = sum(value > 0 for value in mask.get_flattened_data())
    if fixture_pixels == 0:
        return 0.0
    overlap = ImageChops.multiply(mask, static.getchannel("A"))
    return sum(value > 32 for value in overlap.get_flattened_data()) / fixture_pixels


def local_motion_minimum(
    animation_frames: list[Image.Image],
    centre: tuple[int, int],
    radii: tuple[int, int],
) -> int:
    centre_x = round(centre[0] * EXPORT_SCALE)
    centre_y = round(centre[1] * EXPORT_SCALE)
    radius_x = max(2, round(radii[0] * EXPORT_SCALE) + 2)
    radius_y = max(2, round(radii[1] * EXPORT_SCALE) + 2)
    box = (
        max(0, centre_x - radius_x),
        max(0, centre_y - radius_y),
        min(EXPORT_CANVAS[0], centre_x + radius_x + 1),
        min(EXPORT_CANVAS[1], centre_y + radius_y + 1),
    )
    changes: list[int] = []
    for index, frame in enumerate(animation_frames):
        following = animation_frames[(index + 1) % len(animation_frames)]
        difference = ImageChops.difference(frame.crop(box), following.crop(box)).convert("RGB")
        changes.append(sum(max(pixel) >= 5 for pixel in difference.get_flattened_data()))
    return min(changes, default=0)


def render_sheet(theme: str, frame_index: int, phase: str) -> Path:
    background, foreground, secondary = THEMES[theme]
    columns = 8
    tile_width, tile_height = 156, 168
    rows = (len(SLOTS) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * tile_width, rows * tile_height), background)
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for index, slot in enumerate(SLOTS):
        x = (index % columns) * tile_width
        y = (index // columns) * tile_height
        asset_id = slot["asset_id"]
        animation_frames, _durations, _loop = frames(ANIMATED_DIR / f"{asset_id}.png")
        sprite = animation_frames[min(frame_index, len(animation_frames) - 1)]
        sprite_x = x + (tile_width - sprite.width) // 2
        sprite_y = y + 24
        sheet.paste(sprite, (sprite_x, sprite_y), sprite)
        draw.rectangle((x, y, x + tile_width - 1, y + tile_height - 1), outline=secondary)
        draw.text((x + 5, y + 4), f"{slot['slot']:03d}  {slot['label']}", fill=foreground, font=font)
        draw.text((x + 5, y + 154), f"{asset_id} / phase {phase}", fill=secondary, font=font)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    target = PREVIEW_DIR / f"full-fleet-response-{phase}-{theme}.png"
    with tempfile.NamedTemporaryFile(prefix=f"{target.stem}-", suffix=".png", delete=False) as handle:
        temporary = Path(handle.name)
    try:
        sheet.save(temporary, compress_level=6)
        with Image.open(temporary) as verification:
            verification.load()
        shutil.copyfile(temporary, target)
        with Image.open(target) as verification:
            verification.load()
    finally:
        temporary.unlink(missing_ok=True)
    return target


def main() -> None:
    expected = {slot["asset_id"] for slot in SLOTS}
    actual = {path.stem for path in ANIMATED_DIR.glob("*.png")}
    checks: list[dict] = []

    for slot in SLOTS:
        asset_id = slot["asset_id"]
        static = Image.open(STATIC_DIR / f"{asset_id}.png").convert("RGBA")
        master = Image.open(master_path(asset_id)).convert("RGBA")
        path = ANIMATED_DIR / f"{asset_id}.png"
        errors: list[str] = []
        if not path.exists():
            checks.append({"slot": slot["slot"], "asset_id": asset_id, "passed": False, "errors": ["missing"]})
            continue

        decoded, durations, loop = frames(path)
        expected_frames = 18 if FIXTURES[asset_id]["kind"] in {"aircraft", "marine"} else 12
        canvas, controls = apng_controls(path)
        if len(decoded) != expected_frames:
            errors.append(f"decoded-frames={len(decoded)}")
        if loop != 0:
            errors.append(f"loop={loop}")
        if canvas != EXPORT_CANVAS:
            errors.append(f"canvas={canvas}")
        if len(controls) != expected_frames:
            errors.append(f"controls={len(controls)}")
        for control in controls:
            if (control["width"], control["height"], control["x"], control["y"]) != (*EXPORT_CANVAS, 0, 0):
                errors.append("partial-frame-control")
                break
            if control["disposal"] != 0 or control["blend"] != 0:
                errors.append("unsupported-disposal-or-blend")
                break
        if any(frame.size != EXPORT_CANVAS for frame in decoded):
            errors.append("decoded-frame-size")
        if any(duration <= 0 for duration in durations):
            errors.append("non-positive-duration")

        metrics = change_metrics(static, decoded)
        if metrics["changed_pixels_full_max"] < 12:
            errors.append("flash-too-small-at-map-scale")
        if metrics["peak_change_full"] < 90:
            errors.append("flash-too-dim-at-map-scale")
        if metrics["changed_pixels_75pct_max"] < 8:
            errors.append("flash-too-small-at-75pct")
        if metrics["peak_change_75pct"] < 70:
            errors.append("flash-too-dim-at-75pct")
        if metrics["changed_pixels_50pct_max"] < 4:
            errors.append("flash-too-small-at-50pct")
        if metrics["peak_change_50pct"] < 55:
            errors.append("flash-too-dim-at-50pct")
        effect_pixel_limit = 5500 if asset_id in HELICOPTER_GEOMETRY else 2500
        if metrics["changed_pixels_full_max"] > effect_pixel_limit:
            errors.append("effect-too-large")

        tail_motion_min = None
        tail_centre_alpha = None
        if asset_id in HELICOPTER_GEOMETRY:
            rotor_geometry = HELICOPTER_GEOMETRY[asset_id]
            tail_centre_alpha = master.getpixel(rotor_geometry.tail.centre)[3]
            tail_motion_min = local_motion_minimum(
                decoded,
                rotor_geometry.tail.centre,
                rotor_geometry.tail.radii,
            )
            if tail_centre_alpha < 64:
                errors.append("tail-rotor-centre-off-airframe")
            minimum_tail_motion = 18 if rotor_geometry.tail.kind == "exposed" else 8
            if tail_motion_min < minimum_tail_motion:
                errors.append("tail-rotor-motion-too-small")

        overlaps = [fixture_overlap(master, fixture) for fixture in FIXTURES[asset_id]["fixtures"]]
        if any(overlap < 0.12 for overlap in overlaps):
            errors.append("floating-fixture-core")

        checks.append(
            {
                "slot": slot["slot"],
                "asset_id": asset_id,
                "expected_frames": expected_frames,
                "decoded_frames": len(decoded),
                "duration_ms": sum(durations),
                "fixture_overlap_min": round(min(overlaps), 3) if overlaps else None,
                "effect_pixel_limit": effect_pixel_limit,
                "tail_centre_alpha": tail_centre_alpha,
                "tail_motion_changed_pixels_min": tail_motion_min,
                **metrics,
                "errors": sorted(set(errors)),
                "passed": not errors,
            }
        )

    previews = [
        render_sheet(theme, frame_index, phase)
        for phase, frame_index in (("a", 0), ("b", 4))
        for theme in THEMES
    ]
    report = {
        "release": RELEASE_CANDIDATE,
        "master_canvas": list(MASTER_CANVAS),
        "export_canvas": list(EXPORT_CANVAS),
        "export_scale": EXPORT_SCALE,
        "expected_assets": len(expected),
        "actual_assets": len(actual),
        "missing": sorted(expected - actual),
        "extra": sorted(actual - expected),
        "passed_assets": sum(check["passed"] for check in checks),
        "failed_assets": sum(not check["passed"] for check in checks),
        "all_passed": expected == actual and all(check["passed"] for check in checks),
        "previews": [str(path.relative_to(ROOT)) for path in previews],
        "checks": checks,
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("expected_assets", "actual_assets", "passed_assets", "failed_assets", "all_passed")}, indent=2))
    print(f"report={REPORT.relative_to(ROOT)}")
    for preview in previews:
        print(f"preview={preview.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
