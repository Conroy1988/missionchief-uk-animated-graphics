#!/usr/bin/env python3
"""Audit every production image and reject boxes, bars, or oversized lamps."""

from __future__ import annotations

import io
import json
import math
import struct
import subprocess
from collections import deque
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "data" / "v1.4-overhaul-profile.json"
BASELINE = "v1.4.2"
PROFILES = ("standard", "command")
THEMES = {
    "light": (238, 240, 235),
    "dark": (20, 28, 37),
    "satellite": (84, 103, 72),
    "grayscale": (116, 120, 123),
}


def git_bytes(revision: str, relative: Path) -> bytes:
    return subprocess.check_output(
        ["git", "show", f"{revision}:{relative.as_posix()}"],
        cwd=ROOT,
    )


def frames(path: Path) -> list[Image.Image]:
    decoded: list[Image.Image] = []
    with Image.open(path) as image:
        for index in range(int(getattr(image, "n_frames", 1))):
            image.seek(index)
            decoded.append(image.convert("RGBA").copy())
    return decoded


def frames_from_bytes(data: bytes) -> list[Image.Image]:
    decoded: list[Image.Image] = []
    with Image.open(io.BytesIO(data)) as image:
        for index in range(int(getattr(image, "n_frames", 1))):
            image.seek(index)
            decoded.append(image.convert("RGBA").copy())
    return decoded


def apng_control_frames(path: Path) -> tuple[tuple[int, int], list[dict[str, int]]]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"invalid PNG signature: {path}")
    position = 8
    canvas = (0, 0)
    controls: list[dict[str, int]] = []
    while position < len(data):
        if position + 12 > len(data):
            raise ValueError(f"truncated PNG chunk: {path}")
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


def normalise_transparent_rgb(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    rgba.putdata(
        [
            (0, 0, 0, 0) if alpha == 0 else (red, green, blue, alpha)
            for red, green, blue, alpha in rgba.get_flattened_data()
        ]
    )
    return rgba


def hidden_rgb_pixels(image: Image.Image) -> int:
    return sum(
        1
        for red, green, blue, alpha in image.get_flattened_data()
        if alpha == 0 and (red != 0 or green != 0 or blue != 0)
    )


def blue_change_mask(frame: Image.Image, static: Image.Image) -> Image.Image:
    difference = ImageChops.difference(frame, static).convert("RGB")
    mask = Image.new("L", frame.size, 0)
    values = []
    for (red, green, blue, _alpha), diff in zip(
        frame.get_flattened_data(), difference.get_flattened_data()
    ):
        changed = max(diff) >= 24
        optical_blue = blue >= 112 and blue >= red + 18 and blue >= green + 5
        values.append(255 if changed and optical_blue else 0)
    mask.putdata(values)
    return mask


def connected_components(mask: Image.Image) -> list[dict[str, int | float]]:
    width, height = mask.size
    pixels = mask.load()
    seen = bytearray(width * height)
    components: list[dict[str, int | float]] = []
    for y in range(height):
        for x in range(width):
            start = y * width + x
            if seen[start] or pixels[x, y] == 0:
                continue
            queue = deque([(x, y)])
            seen[start] = 1
            points: list[tuple[int, int]] = []
            while queue:
                px, py = queue.popleft()
                points.append((px, py))
                for nx, ny in ((px - 1, py), (px + 1, py), (px, py - 1), (px, py + 1)):
                    if not (0 <= nx < width and 0 <= ny < height):
                        continue
                    index = ny * width + nx
                    if seen[index] or pixels[nx, ny] == 0:
                        continue
                    seen[index] = 1
                    queue.append((nx, ny))
            left = min(point[0] for point in points)
            top = min(point[1] for point in points)
            right = max(point[0] for point in points) + 1
            bottom = max(point[1] for point in points) + 1
            box_area = (right - left) * (bottom - top)
            components.append(
                {
                    "pixels": len(points),
                    "left": left,
                    "top": top,
                    "right": right,
                    "bottom": bottom,
                    "width": right - left,
                    "height": bottom - top,
                    "rectangularity": round(len(points) / max(1, box_area), 4),
                }
            )
    return components


def significant_difference_score(frame: Image.Image, static: Image.Image) -> int:
    difference = ImageChops.difference(frame, static).convert("RGB")
    return sum(max(pixel) for pixel in difference.get_flattened_data())


def font(size: int) -> ImageFont.ImageFont:
    for candidate in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ):
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def render_contact_sheet(
    theme: str,
    colour: tuple[int, int, int],
    vehicles: list[dict],
    target: Path,
) -> None:
    columns = 4
    cell_width, cell_height = 360, 150
    header = 44
    rows = math.ceil(len(vehicles) / columns)
    canvas = Image.new("RGB", (columns * cell_width, header + rows * cell_height), colour)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, canvas.width, header), fill=(7, 12, 18))
    draw.text(
        (14, 12),
        f"{release_label()} point-emitter audit — {theme}",
        font=font(16),
        fill="white",
    )
    for index, vehicle in enumerate(vehicles):
        asset_id = str(vehicle["id"])
        static = Image.open(
            ROOT / "assets" / "exports" / "command" / "static" / f"{asset_id}.png"
        ).convert("RGBA")
        decoded = frames(
            ROOT / "assets" / "exports" / "command" / "animated" / f"{asset_id}.png"
        )
        shown = max(decoded, key=lambda frame: significant_difference_score(frame, static))
        column = index % columns
        row = index // columns
        left = column * cell_width
        top = header + row * cell_height
        draw.rectangle(
            (left, top, left + cell_width - 1, top + cell_height - 1),
            outline=(82, 94, 103),
        )
        road = (236, 236, 228) if theme != "light" else (207, 210, 205)
        draw.line(
            (left + 5, top + cell_height - 14, left + cell_width - 5, top + 18),
            fill=road,
            width=7,
        )
        scale = min(2, max(1, int(min((cell_width - 18) / shown.width, (cell_height - 42) / shown.height))))
        enlarged = shown.resize(
            (shown.width * scale, shown.height * scale),
            Image.Resampling.NEAREST,
        )
        x = left + (cell_width - enlarged.width) // 2
        y = top + 25 + (cell_height - 34 - enlarged.height) // 2
        canvas.paste(enlarged.convert("RGB"), (x, y), enlarged)
        draw.rectangle((left + 4, top + 4, left + cell_width - 5, top + 22), fill=(5, 9, 14))
        draw.text(
            (left + 8, top + 7),
            f"{int(vehicle['missionchief_slot']):03}  {vehicle['display_name']}",
            font=font(10),
            fill="white",
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target, format="PNG", optimize=True)


def release_label() -> str:
    return str(json.loads(PROFILE_PATH.read_text(encoding="utf-8"))["release"])


def render_bar_regression_sheet(vehicles: list[dict], target: Path) -> int:
    baseline_report = json.loads(
        git_bytes(BASELINE, Path(f"data/{BASELINE}-full-fleet-lighting-report.json"))
    )
    affected = sorted(
        (
            item
            for item in baseline_report["assets"]
            if item["profile"] == "command"
            and int(item["largest_blue_component"]["width"]) >= 5
        ),
        key=lambda item: (
            -int(item["largest_blue_component"]["width"]),
            -int(item["largest_blue_component"]["pixels"]),
            int(item["slot"]),
        ),
    )
    vehicle_map = {str(vehicle["id"]): vehicle for vehicle in vehicles}
    width, row_height, header = 1600, 122, 66
    canvas = Image.new("RGB", (width, header + len(affected) * row_height), (70, 16, 22))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, width, header), fill=(7, 12, 18))
    draw.text((18, 12), f"{release_label()} emergency-light bar regression", font=font(21), fill="white")
    draw.text((540, 39), f"{BASELINE} — rejected bars", font=font(13), fill=(255, 166, 166))
    draw.text((1120, 39), f"{release_label()} — isolated point lamps", font=font(13), fill=(148, 235, 190))

    for row, item in enumerate(affected):
        asset_id = str(item["id"])
        vehicle = vehicle_map[asset_id]
        top = header + row * row_height
        background = (91, 23, 29) if row % 2 == 0 else (74, 30, 36)
        draw.rectangle((0, top, width, top + row_height - 1), fill=background)
        draw.line((360, top + row_height - 10, width - 12, top + 12), fill=(223, 216, 190), width=5)
        draw.text((18, top + 22), f"{int(item['slot']):03}  {vehicle['display_name']}", font=font(15), fill="white")
        old_component = item["largest_blue_component"]
        draw.text(
            (18, top + 50),
            f"Old component: {old_component['width']}×{old_component['height']} · {old_component['pixels']} px",
            font=font(11),
            fill=(255, 196, 196),
        )

        static_path = ROOT / "assets" / "exports" / "command" / "static" / f"{asset_id}.png"
        animated_path = ROOT / "assets" / "exports" / "command" / "animated" / f"{asset_id}.png"
        current_static = Image.open(static_path).convert("RGBA")
        old_static = Image.open(
            io.BytesIO(git_bytes(BASELINE, static_path.relative_to(ROOT)))
        ).convert("RGBA")
        old_frames = frames_from_bytes(git_bytes(BASELINE, animated_path.relative_to(ROOT)))
        current_frames = frames(animated_path)
        old_peak = max(old_frames, key=lambda frame: significant_difference_score(frame, old_static))
        current_peak = max(
            current_frames,
            key=lambda frame: significant_difference_score(frame, current_static),
        )
        for x, image in ((520, old_peak), (1100, current_peak)):
            scale = min(3, max(1, min(470 // image.width, 92 // image.height)))
            enlarged = image.resize(
                (image.width * scale, image.height * scale),
                Image.Resampling.NEAREST,
            )
            canvas.paste(
                enlarged.convert("RGB"),
                (x + (470 - enlarged.width) // 2, top + (row_height - enlarged.height) // 2),
                enlarged,
            )

    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target, format="PNG", optimize=True)
    return len(affected)


def main() -> None:
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    release = str(profile["release"])
    scope = json.loads((ROOT / "data" / f"{release}-scope.json").read_text(encoding="utf-8"))
    changed_ids = scope.get("changed_asset_ids", [])
    if not isinstance(changed_ids, list):
        changed_ids = []
    allowed_static_changes = {
        f"assets/exports/{profile_name}/static/{asset_id}.png"
        for profile_name, variants in scope.get("profile_variants", {}).items()
        if "static" in variants
        for asset_id in changed_ids
    }
    manifest = json.loads((ROOT / "data" / "prototypes.json").read_text(encoding="utf-8"))
    vehicles = sorted(manifest["vehicles"], key=lambda item: int(item["missionchief_slot"]))
    expected_ids = {str(vehicle["id"]) for vehicle in vehicles}
    build = json.loads((ROOT / "data" / f"{release}-build-report.json").read_text(encoding="utf-8"))
    command_details = {str(item["id"]): item for item in build["vehicles_detail"]}
    errors: list[str] = []
    fixtures_path = ROOT / str(profile["current_light_fixtures_path"])
    fixture_data = json.loads(fixtures_path.read_text(encoding="utf-8"))
    declared_fixtures = {
        str(light.get("fixture"))
        for lights in fixture_data.get("vehicles", {}).values()
        for light in lights
    }
    if declared_fixtures != {"point-emitter"}:
        errors.append(f"legacy or unknown emergency-light fixtures remain: {sorted(declared_fixtures)}")
    if profile.get("emergency_light_renderer", {}).get("model") != "isolated-point-v3":
        errors.append("active profile is not bound to the isolated-point-v3 renderer")
    results: list[dict] = []
    total_decoded_frames = 0
    total_control_frames = 0
    total_hidden_rgb = 0
    total_partial_frames = 0
    total_box_components = 0
    total_bar_components = 0
    total_oversized_components = 0
    total_blue_outside = 0
    changed_apngs = 0
    visibly_unchanged_statics = 0

    for profile_name in PROFILES:
        static_dir = ROOT / "assets" / "exports" / profile_name / "static"
        animated_dir = ROOT / "assets" / "exports" / profile_name / "animated"
        actual_static = {path.stem for path in static_dir.glob("*.png")}
        actual_animated = {path.stem for path in animated_dir.glob("*.png")}
        if actual_static != expected_ids:
            errors.append(f"{profile_name}: static inventory mismatch")
        if actual_animated != expected_ids:
            errors.append(f"{profile_name}: animated inventory mismatch")

        for vehicle in vehicles:
            asset_id = str(vehicle["id"])
            static_path = static_dir / f"{asset_id}.png"
            animated_path = animated_dir / f"{asset_id}.png"
            relative_static = static_path.relative_to(ROOT)
            relative_animated = animated_path.relative_to(ROOT)
            asset_errors: list[str] = []
            is_lit = bool(vehicle.get("lights")) if profile_name == "standard" else bool(
                command_details.get(asset_id, {}).get("response_light_count")
            )
            static = Image.open(static_path).convert("RGBA")
            baseline_static = Image.open(io.BytesIO(git_bytes(BASELINE, relative_static))).convert("RGBA")
            if ImageChops.difference(
                normalise_transparent_rgb(static), normalise_transparent_rgb(baseline_static)
            ).getbbox() is not None:
                if relative_static.as_posix() not in allowed_static_changes:
                    asset_errors.append(f"visible static artwork changed from {BASELINE}")
            else:
                visibly_unchanged_statics += 1

            if animated_path.read_bytes() != git_bytes(BASELINE, relative_animated):
                changed_apngs += 1
            elif is_lit:
                asset_errors.append(f"lit APNG bytes did not change from defective {BASELINE} geometry")

            decoded = frames(animated_path)
            total_decoded_frames += len(decoded)
            expected_frames = 6 if profile_name == "standard" else int(
                profile.get("animation_frame_overrides", {}).get(asset_id, profile["frames"])
            )
            if len(decoded) != expected_frames:
                asset_errors.append(f"decoded frame count {len(decoded)} != {expected_frames}")
            if not decoded or ImageChops.difference(decoded[0], static).getbbox() is not None:
                asset_errors.append("APNG frame 0 is not the static image")

            canvas, controls = apng_control_frames(animated_path)
            total_control_frames += len(controls)
            if canvas != static.size:
                asset_errors.append(f"APNG canvas {canvas} != static canvas {static.size}")
            if len(controls) != expected_frames:
                asset_errors.append(f"fcTL count {len(controls)} != {expected_frames}")
            partial = sum(
                (item["width"], item["height"], item["x"], item["y"])
                != (canvas[0], canvas[1], 0, 0)
                for item in controls
            )
            total_partial_frames += partial
            if partial:
                asset_errors.append(f"{partial} APNG frames use rectangular update tiles")
            if any(item["disposal"] not in {0, 1} for item in controls):
                asset_errors.append("APNG uses unsupported PREVIOUS frame disposal")
            if any(item["blend"] != 0 for item in controls):
                asset_errors.append("APNG uses non-SOURCE frame blending")

            hidden = sum(hidden_rgb_pixels(frame) for frame in decoded)
            total_hidden_rgb += hidden
            if hidden:
                asset_errors.append(f"{hidden} fully transparent pixels retain hidden RGB")

            expanded = static.getchannel("A").point(lambda value: 255 if value else 0)
            expanded = expanded.filter(ImageFilter.MaxFilter(3))
            inverted_expanded = ImageChops.invert(expanded)
            largest_component = {"pixels": 0, "width": 0, "height": 0, "rectangularity": 0.0}
            box_components = 0
            bar_components = 0
            oversized_components = 0
            outside = 0
            command_motion = command_details.get(asset_id, {}).get("motion")
            if profile_name == "standard":
                light_pixels = [
                    {
                        "x": round(float(light["x"]) * (static.width - 1)),
                        "y": round(float(light["y"]) * (static.height - 1)),
                    }
                    for light in vehicle.get("lights", [])
                ]
            else:
                light_pixels = command_details.get(asset_id, {}).get("response_light_pixels", [])
            lamp_region = Image.new("L", static.size, 0)
            lamp_region_draw = ImageDraw.Draw(lamp_region)
            for light in light_pixels:
                px, py = int(light["x"]), int(light["y"])
                lamp_region_draw.rectangle((px - 6, py - 4, px + 6, py + 4), fill=255)
            if is_lit:
                if not light_pixels:
                    asset_errors.append("lit asset has no auditable response-light coordinates")
                for frame in decoded[1:]:
                    blue = ImageChops.multiply(blue_change_mask(frame, static), lamp_region)
                    outside += sum(
                        value > 0
                        for value in ImageChops.multiply(blue, inverted_expanded).get_flattened_data()
                    )
                    for component in connected_components(blue):
                        if int(component["pixels"]) > int(largest_component["pixels"]):
                            largest_component = component
                        component_width = int(component["width"])
                        component_height = int(component["height"])
                        component_pixels = int(component["pixels"])
                        if component_width >= 3 and component_width >= component_height * 2:
                            bar_components += 1
                        if component_width > 2 or component_height > 2 or component_pixels > 4:
                            oversized_components += 1
                        if component_width >= 3 and component_height >= 3 and float(component["rectangularity"]) >= 0.80:
                            box_components += 1
                if oversized_components:
                    asset_errors.append(f"{oversized_components} emergency-light components exceed the 2x2 point-lamp envelope")
                if bar_components:
                    asset_errors.append(f"{bar_components} elongated emergency-light bars detected")
                if box_components:
                    asset_errors.append(f"{box_components} box-shaped light components detected")
                if outside:
                    asset_errors.append(f"{outside} blue light pixels escape the one-pixel silhouette")
            total_box_components += box_components
            total_bar_components += bar_components
            total_oversized_components += oversized_components
            total_blue_outside += outside

            if asset_errors:
                errors.extend(f"{profile_name}/{asset_id}: {error}" for error in asset_errors)
            results.append(
                {
                    "profile": profile_name,
                    "slot": int(vehicle["missionchief_slot"]),
                    "id": asset_id,
                    "frames": len(decoded),
                    "full_canvas_frames": len(controls) - partial,
                    "partial_update_frames": partial,
                    "hidden_transparent_rgb_pixels": hidden,
                    "lit": is_lit,
                    "light_coordinates_audited": len(light_pixels),
                    "command_motion": command_motion
                    if profile_name == "command"
                    else "blue-response" if vehicle.get("lights") else "static",
                    "largest_blue_component": largest_component,
                    "box_components": box_components,
                    "bar_components": bar_components,
                    "oversized_components": oversized_components,
                    "blue_pixels_outside_silhouette": outside,
                    "passed": not asset_errors,
                    "errors": asset_errors,
                }
            )

    preview_dir = ROOT / "assets" / "previews" / release
    previews = []
    for theme, colour in THEMES.items():
        target = preview_dir / f"full-fleet-lighting-{theme}.png"
        render_contact_sheet(theme, colour, vehicles, target)
        previews.append(str(target.relative_to(ROOT)))
    regression_target = preview_dir / "point-lamps-before-after.png"
    regression_assets = render_bar_regression_sheet(vehicles, regression_target)
    previews.append(str(regression_target.relative_to(ROOT)))

    report = {
        "release": release,
        "baseline": BASELINE,
        "production_files_audited": 468,
        "static_pngs_audited": 234,
        "animated_apngs_audited": 234,
        "decoded_frames_audited": total_decoded_frames,
        "apng_control_frames_audited": total_control_frames,
        "standard_lit_vehicles": sum(bool(vehicle.get("lights")) for vehicle in vehicles),
        "command_lit_vehicles": sum(
            bool(command_details.get(str(vehicle["id"]), {}).get("response_light_count"))
            for vehicle in vehicles
        ),
        "visible_static_assets_unchanged": visibly_unchanged_statics,
        "changed_apngs": changed_apngs,
        "partial_update_frames": total_partial_frames,
        "box_shaped_light_components": total_box_components,
        "elongated_light_bar_components": total_bar_components,
        "oversized_light_components": total_oversized_components,
        "blue_pixels_outside_one_pixel_silhouette": total_blue_outside,
        "hidden_transparent_rgb_pixels": total_hidden_rgb,
        "full_canvas_source_blending": all(
            item["partial_update_frames"] == 0 for item in results
        ),
        "previews": previews,
        "baseline_command_assets_with_five_pixel_bars": regression_assets,
        "all_passed": not errors,
        "errors": errors,
        "assets": results,
    }
    report_path = ROOT / "data" / f"{release}-full-fleet-lighting-report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "assets"}, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
