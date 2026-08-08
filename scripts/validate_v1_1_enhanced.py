#!/usr/bin/env python3
"""Validate Modern Command Clarity exports and render busy-map QA evidence."""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "prototypes.json"
PROFILE_PATH = ROOT / "data" / "v1.2-enhancement-profile.json"
PROFILE = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
RELEASE = str(PROFILE["release"])
BUILD_REPORT_PATH = ROOT / "data" / f"{RELEASE}-build-report.json"
REPORT_PATH = ROOT / "data" / f"{RELEASE}-qa-report.json"
STANDARD_DIR = ROOT / "assets" / "exports" / "standard" / "static"
STATIC_DIR = ROOT / "assets" / "exports" / "command" / "static"
ANIMATED_DIR = ROOT / "assets" / "exports" / "command" / "animated"
PREVIEW_DIR = ROOT / "assets" / "previews" / RELEASE


THEMES = {
    "light": {"base": (226, 229, 220), "road": (250, 248, 241), "edge": (188, 196, 190), "detail": (211, 188, 102)},
    "dark": {"base": (25, 34, 44), "road": (48, 57, 66), "edge": (10, 16, 22), "detail": (104, 117, 130)},
    "satellite": {"base": (66, 83, 58), "road": (116, 111, 95), "edge": (47, 57, 45), "detail": (154, 142, 112)},
    "grayscale": {"base": (157, 160, 160), "road": (205, 205, 201), "edge": (112, 114, 115), "detail": (176, 176, 172)},
}


SHOWCASE_IDS = [
    "fire-rescue-pump",
    "frontline-ambulance",
    "police-incident-response-vehicle",
    "hems",
    "airfield-operations-vehicle",
    "ilb",
    "flood-rescue-unit-trailer",
    "medical-cycle-responder",
    "eod-heavy-equipment-vehicle",
]

ROTOR_SHOWCASE_IDS = [
    "hems",
    "police-helicopter",
    "coastguard-rescue-helicopter",
    "coastguard-rescue-helicopter-large",
]

EXPECTED_MOUNTED_CARRIERS = {
    "water-pod",
    "bulk-foam-pod",
    "rescue-pod",
    "command-pod",
    "welfare-pod",
    "basu-pod",
    "misting-pod",
    "hazardous-materials-pod",
    "osu-pod",
    "hvp",
}

EXPECTED_FULL_TAIL_SOURCES = {
    "hems": "hems-full-tail.png",
    "police-helicopter": "police-helicopter-full-tail.png",
}

EXPECTED_PRESERVED_TAIL_ROTORS = {
    "coastguard-rescue-helicopter",
    "coastguard-rescue-helicopter-large",
}


def rgba(path: Path) -> Image.Image:
    with Image.open(path) as image:
        image.load()
        return image.convert("RGBA")


def frames_and_durations(path: Path) -> tuple[list[Image.Image], list[int]]:
    frames: list[Image.Image] = []
    durations: list[int] = []
    with Image.open(path) as image:
        for index in range(int(getattr(image, "n_frames", 1))):
            image.seek(index)
            durations.append(int(image.info.get("duration", 0)))
            frames.append(image.convert("RGBA").copy())
    return frames, durations


def changed(left: Image.Image, right: Image.Image) -> bool:
    return ImageChops.difference(left, right).getbbox() is not None


def alpha_centroid(image: Image.Image) -> tuple[float, float]:
    alpha = image.getchannel("A")
    width, height = image.size
    total = sx = sy = 0.0
    for y in range(height):
        for x in range(width):
            value = alpha.getpixel((x, y))
            if value < 96:
                continue
            total += value
            sx += x * value
            sy += y * value
    if total == 0:
        return 0.0, 0.0
    return sx / total, sy / total


def complete_tail_upper_pixels(
    image: Image.Image,
    width_fraction: float,
    height_fraction: float,
) -> int:
    """Count structural tail pixels in the upper-left tail-integrity zone."""
    alpha = image.getchannel("A")
    right = max(1, round(image.width * width_fraction))
    bottom = max(1, round(image.height * height_fraction))
    return sum(
        value >= 96
        for value in alpha.crop((0, 0, right, bottom)).get_flattened_data()
    )


def half_zoom_visible_pixels(image: Image.Image) -> int:
    width = max(1, round(image.width * 0.5))
    height = max(1, round(image.height * 0.5))
    reduced = image.resize((width, height), Image.Resampling.LANCZOS)
    return sum(1 for value in reduced.getchannel("A").get_flattened_data() if value >= 64)


def luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def edge_contrast(image: Image.Image, background: tuple[int, int, int]) -> float:
    alpha = image.getchannel("A")
    eroded = alpha.filter(ImageFilter.MinFilter(3))
    edge = ImageChops.subtract(alpha, eroded)
    background_image = Image.new("RGBA", image.size, (*background, 255))
    composed = Image.alpha_composite(background_image, image).convert("RGB")
    bg_luminance = luminance(background)
    samples = []
    for pixel, mask in zip(composed.get_flattened_data(), edge.get_flattened_data()):
        if mask >= 24:
            samples.append(abs(luminance(pixel) - bg_luminance))
    return round(sum(samples) / len(samples), 2) if samples else 0.0


def silhouette_hash(image: Image.Image) -> str:
    alpha = image.getchannel("A")
    alpha = ImageOps.fit(alpha, (32, 16), method=Image.Resampling.LANCZOS)
    pixels = list(alpha.get_flattened_data())
    average = sum(pixels) / (32 * 16)
    return "".join("1" if value >= average else "0" for value in pixels)


def rotor_clear_region(size: tuple[int, int], geometry: dict, padding: int = 5) -> Image.Image:
    """Return the source-blade region that must remain free of a strong static underlay."""
    width, height = size
    body_width = width - padding * 2
    body_height = height - padding * 2
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    clear_y = padding + round(body_height * float(geometry["clear_below"]))
    hub_x = padding + round(float(geometry["hub"][0]) * (body_width - 1))
    rotor_radius = max(12, round(body_width * float(geometry["disc_width"]) / 2))
    clear_left = max(padding, hub_x - rotor_radius)
    clear_right = min(padding + body_width - 1, hub_x + rotor_radius)
    draw.rectangle((clear_left, padding, clear_right, clear_y), fill=255)

    keep_points = [
        (
            padding + round(float(x) * (body_width - 1)),
            padding + round(float(y) * (body_height - 1)),
        )
        for x, y in geometry["body_keep_polygon"]
    ]
    draw.polygon(keep_points, fill=0)

    hub_y = padding + round(float(geometry["hub"][1]) * (body_height - 1))
    hub_rx = max(5, round(body_width * 0.032))
    hub_ry = max(3, round(body_height * 0.09))
    draw.ellipse((hub_x - hub_rx, hub_y - hub_ry, hub_x + hub_rx, hub_y + hub_ry), fill=0)
    return mask


def strong_rotor_underlay_pixels(image: Image.Image, geometry: dict) -> int:
    mask = rotor_clear_region(image.size, geometry)
    return sum(
        1
        for alpha, selected in zip(
            image.getchannel("A").get_flattened_data(),
            mask.get_flattened_data(),
        )
        if selected and alpha >= 96
    )


def hamming(left: str, right: str) -> int:
    return sum(a != b for a, b in zip(left, right))


def background(theme_name: str, size: tuple[int, int]) -> Image.Image:
    theme = THEMES[theme_name]
    canvas = Image.new("RGBA", size, (*theme["base"], 255))
    draw = ImageDraw.Draw(canvas)
    width, height = size
    for x in range(-240, width + 240, 215):
        draw.line((x, 0, x + 420, height), fill=(*theme["edge"], 255), width=24)
        draw.line((x, 0, x + 420, height), fill=(*theme["road"], 255), width=17)
    for y in range(118, height, 175):
        draw.line((0, y, width, y), fill=(*theme["edge"], 255), width=32)
        draw.line((0, y, width, y), fill=(*theme["road"], 255), width=23)
        draw.line((0, y, width, y), fill=(*theme["detail"], 255), width=2)
    if theme_name == "satellite":
        for x in range(50, width, 170):
            for y in range(35, height, 145):
                shade = 12 if (x + y) % 3 else -8
                color = tuple(max(0, min(255, value + shade)) for value in theme["base"])
                draw.ellipse((x, y, x + 78, y + 56), fill=(*color, 210))
    return canvas


def render_busy_map(theme_name: str, vehicles: list[dict]) -> Path:
    width, height = 1800, 1080
    canvas = background(theme_name, (width, height))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=18)
    title_font = ImageFont.load_default(size=26)
    zooms = [1.0, 0.75, 0.5]
    band_height = height // 3
    for band, zoom in enumerate(zooms):
        top = band * band_height
        draw.rounded_rectangle((18, top + 14, 280, top + 50), 8, fill=(10, 16, 22, 220))
        draw.text((31, top + 23), f"{theme_name.title()} theme - {round(zoom * 100)}% icon scale", font=font, fill="white")
        subset = vehicles[band::3]
        for index, vehicle in enumerate(subset):
            icon = rgba(STATIC_DIR / f"{vehicle['id']}.png")
            scaled = icon.resize(
                (max(1, round(icon.width * zoom)), max(1, round(icon.height * zoom))),
                Image.Resampling.LANCZOS,
            )
            column = index % 13
            row = index // 13
            x = 35 + column * 134 + ((row * 41 + column * 17) % 34)
            y = top + 83 + row * 79 + ((column * 13) % 19)
            canvas.alpha_composite(scaled, (x, y))
    draw.rounded_rectangle((width - 540, 18, width - 20, 62), 10, fill=(10, 16, 22, 225))
    draw.text((width - 520, 29), "117-vehicle automated dense-map QA", font=title_font, fill="white")
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    target = PREVIEW_DIR / f"busy-map-{theme_name}.png"
    canvas.convert("RGB").quantize(
        colors=256,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.NONE,
    ).save(target, format="PNG", optimize=True)
    return target


def render_animation_sheet(vehicle_map: dict[str, dict]) -> Path:
    columns = 12
    cell_width, cell_height = 212, 118
    label_width = 240
    width = label_width + columns * cell_width
    height = 58 + len(SHOWCASE_IDS) * cell_height
    canvas = Image.new("RGBA", (width, height), (15, 21, 28, 255))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=17)
    title_font = ImageFont.load_default(size=24)
    draw.text((20, 17), f"{RELEASE} independent-light and motion frame audit", font=title_font, fill="white")
    for row, asset_id in enumerate(SHOWCASE_IDS):
        vehicle = vehicle_map[asset_id]
        frames, _durations = frames_and_durations(ANIMATED_DIR / f"{asset_id}.png")
        top = 58 + row * cell_height
        draw.text((18, top + 45), vehicle["display_name"], font=font, fill=(225, 232, 238, 255))
        for column, frame in enumerate(frames):
            left = label_width + column * cell_width
            draw.rounded_rectangle((left + 5, top + 5, left + cell_width - 5, top + cell_height - 5), 8, fill=(38, 48, 59, 255))
            scale = min((cell_width - 20) / frame.width, (cell_height - 32) / frame.height)
            size = (max(1, round(frame.width * scale)), max(1, round(frame.height * scale)))
            thumb = frame.resize(size, Image.Resampling.NEAREST)
            canvas.alpha_composite(thumb, (left + (cell_width - thumb.width) // 2, top + (cell_height - thumb.height) // 2 + 8))
            draw.text((left + 10, top + 9), f"F{column + 1}", font=font, fill=(155, 174, 190, 255))
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    target = PREVIEW_DIR / "animation-frames.png"
    canvas.convert("RGB").save(target, format="PNG", optimize=True)
    return target


def render_desynchronised_lights_sheet(vehicle_map: dict[str, dict], asset_ids: list[str]) -> Path:
    """Render the same crowded response across all frames to expose fleet synchronisation."""
    columns = 3
    rows = 4
    card_width, card_height = 600, 252
    width, height = columns * card_width + 40, rows * card_height + 92
    canvas = background("dark", (width, height))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=16)
    title_font = ImageFont.load_default(size=26)
    draw.rounded_rectangle((18, 14, width - 18, 68), 12, fill=(10, 16, 22, 235))
    draw.text((34, 28), f"{RELEASE} desynchronised crowded-response frame audit", font=title_font, fill="white")
    frame_map = {
        asset_id: frames_and_durations(ANIMATED_DIR / f"{asset_id}.png")[0]
        for asset_id in asset_ids
    }
    placements = [
        (88, 65),
        (245, 48),
        (420, 72),
        (138, 125),
        (300, 117),
        (466, 133),
        (70, 176),
        (250, 177),
        (425, 184),
    ]
    for frame_index in range(12):
        row, column = divmod(frame_index, columns)
        left = 20 + column * card_width
        top = 82 + row * card_height
        draw.rounded_rectangle(
            (left, top, left + card_width - 14, top + card_height - 12),
            10,
            fill=(10, 16, 22, 220),
            outline=(180, 197, 210, 165),
            width=1,
        )
        draw.text((left + 14, top + 12), f"Frame {frame_index + 1}", font=font, fill="white")
        draw.ellipse((left + 270, top + 86, left + 332, top + 148), fill=(150, 37, 37, 120), outline=(255, 183, 40, 210), width=2)
        for index, asset_id in enumerate(asset_ids):
            frame = frame_map[asset_id][frame_index]
            scale = min(0.58, 116 / frame.width, 65 / frame.height)
            thumb = frame.resize(
                (max(1, round(frame.width * scale)), max(1, round(frame.height * scale))),
                Image.Resampling.LANCZOS,
            )
            px, py = placements[index % len(placements)]
            canvas.alpha_composite(
                thumb,
                (left + px - thumb.width // 2, top + py - thumb.height // 2),
            )
            if frame_index == 0:
                draw.text(
                    (left + px - 32, top + min(card_height - 30, py + 36)),
                    vehicle_map[asset_id]["display_name"][:18],
                    font=ImageFont.load_default(size=11),
                    fill=(173, 188, 200, 255),
                )
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    target = PREVIEW_DIR / "desynchronised-lights-crowd.png"
    canvas.convert("RGB").save(target, format="PNG", optimize=True)
    return target


def render_rotor_sheet(vehicle_map: dict[str, dict]) -> Path:
    columns = 12
    cell_width, cell_height = 212, 128
    label_width = 270
    width = label_width + columns * cell_width
    height = 64 + len(ROTOR_SHOWCASE_IDS) * cell_height
    canvas = Image.new("RGBA", (width, height), (15, 21, 28, 255))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=17)
    title_font = ImageFont.load_default(size=24)
    draw.text((20, 18), f"{RELEASE} helicopter rotor regression audit", font=title_font, fill="white")
    for row, asset_id in enumerate(ROTOR_SHOWCASE_IDS):
        vehicle = vehicle_map[asset_id]
        frames, _durations = frames_and_durations(ANIMATED_DIR / f"{asset_id}.png")
        top = 64 + row * cell_height
        draw.text((18, top + 50), vehicle["display_name"], font=font, fill=(225, 232, 238, 255))
        for column, frame in enumerate(frames):
            left = label_width + column * cell_width
            draw.rounded_rectangle(
                (left + 5, top + 5, left + cell_width - 5, top + cell_height - 5),
                8,
                fill=(38, 48, 59, 255),
            )
            scale = min((cell_width - 18) / frame.width, (cell_height - 32) / frame.height)
            size = (max(1, round(frame.width * scale)), max(1, round(frame.height * scale)))
            thumb = frame.resize(size, Image.Resampling.NEAREST)
            canvas.alpha_composite(
                thumb,
                (left + (cell_width - thumb.width) // 2, top + (cell_height - thumb.height) // 2 + 8),
            )
            draw.text((left + 10, top + 9), f"F{column + 1}", font=font, fill=(155, 174, 190, 255))
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    target = PREVIEW_DIR / "helicopter-rotor-frames.png"
    canvas.convert("RGB").save(target, format="PNG", optimize=True)
    return target


def render_targeted_sheet(
    title: str,
    asset_ids: list[str],
    theme_name: str,
    filename: str,
    vehicle_map: dict[str, dict],
) -> Path:
    """Render role/contrast targets at the three supported MissionChief scales."""
    columns = 3
    rows = math.ceil(len(asset_ids) / columns)
    card_width, card_height = 590, 178
    width, height = columns * card_width + 40, rows * card_height + 92
    canvas = background(theme_name, (width, height))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=16)
    title_font = ImageFont.load_default(size=26)
    draw.rounded_rectangle((18, 14, width - 18, 68), 12, fill=(10, 16, 22, 232))
    draw.text((34, 28), title, font=title_font, fill="white")
    zooms = [1.0, 0.75, 0.5]
    for index, asset_id in enumerate(asset_ids):
        row, column = divmod(index, columns)
        left = 20 + column * card_width
        top = 82 + row * card_height
        draw.rounded_rectangle(
            (left, top, left + card_width - 14, top + card_height - 12),
            10,
            fill=(10, 16, 22, 218),
            outline=(222, 232, 238, 155),
            width=1,
        )
        vehicle = vehicle_map[asset_id]
        draw.text((left + 14, top + 12), vehicle["display_name"], font=font, fill="white")
        icon = rgba(STATIC_DIR / f"{asset_id}.png")
        for zoom_index, zoom in enumerate(zooms):
            scaled = icon.resize(
                (max(1, round(icon.width * zoom)), max(1, round(icon.height * zoom))),
                Image.Resampling.LANCZOS,
            )
            # Leave enough room for the 316px large Coastguard helicopter at
            # 100% scale; the former 115px first centre clipped the evidence
            # sheet even though the exported asset itself was complete.
            centre_x = left + (170, 350, 490)[zoom_index]
            icon_y = top + 45 + max(0, (88 - scaled.height) // 2)
            canvas.alpha_composite(scaled, (centre_x - scaled.width // 2, icon_y))
            draw.text(
                (centre_x - 19, top + card_height - 35),
                f"{round(zoom * 100)}%",
                font=font,
                fill=(205, 218, 228, 255),
            )
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    target = PREVIEW_DIR / filename
    canvas.convert("RGB").save(target, format="PNG", optimize=True)
    return target


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    profile = PROFILE
    build_report = json.loads(BUILD_REPORT_PATH.read_text(encoding="utf-8"))
    vehicles = sorted(manifest["vehicles"], key=lambda item: int(item["missionchief_slot"]))
    vehicle_map = {item["id"]: item for item in vehicles}
    detail_map = {item["id"]: item for item in build_report["vehicles_detail"]}
    expected = {item["id"] for item in vehicles}
    pack_errors: list[str] = []
    role_cues = profile.get("role_differentiation", {})
    equipment_cues = profile.get("specialist_equipment", {})
    retired_overlay_groups = profile.get("retired_generated_overlays", {})
    retired_role_assets = set(retired_overlay_groups.get("role_differentiation", []))
    retired_equipment_assets = set(retired_overlay_groups.get("specialist_equipment", []))
    retired_overlay_assets = retired_role_assets | retired_equipment_assets
    satellite_boost = set(profile.get("satellite_contrast_boost", []))
    grounding = profile.get("grounding_shadows", {})
    aerial_shadow_assets = set(grounding.get("aerial", []))
    marine_shadow_assets = set(grounding.get("marine", []))
    mounted_carriers = profile.get("mounted_carriers", {})
    map_scale_reductions = profile.get("map_scale_reductions", {})
    helicopter_edge_padding = profile.get("helicopter_edge_padding", {})
    tail_integrity = profile.get("helicopter_tail_integrity", {})
    master_source_release = str(profile.get("master_source_release", ""))

    if role_cues or equipment_cues:
        pack_errors.append("generated role and specialist roof overlays must remain retired")
    if set(retired_overlay_groups) != {"role_differentiation", "specialist_equipment"}:
        pack_errors.append("retired generated-overlay groups are incomplete")
    if len(retired_role_assets) != 15 or len(retired_equipment_assets) != 25:
        pack_errors.append("retired generated-overlay inventory must remain 15 role + 25 specialist assets")
    if retired_role_assets & retired_equipment_assets:
        pack_errors.append("retired role and specialist overlay inventories overlap")
    if len(retired_overlay_assets) != 40:
        pack_errors.append("retired generated-overlay inventory must contain exactly 40 assets")
    unknown_retired_ids = sorted(retired_overlay_assets - expected)
    if unknown_retired_ids:
        pack_errors.append(f"retired generated overlays reference unknown assets: {unknown_retired_ids}")
    unknown_satellite_ids = sorted(satellite_boost - expected)
    if unknown_satellite_ids:
        pack_errors.append(f"satellite contrast boost references unknown assets: {unknown_satellite_ids}")
    unknown_shadow_ids = sorted((aerial_shadow_assets | marine_shadow_assets) - expected)
    if unknown_shadow_ids:
        pack_errors.append(f"grounding shadow profile references unknown assets: {unknown_shadow_ids}")
    if aerial_shadow_assets & marine_shadow_assets:
        pack_errors.append("grounding shadow aerial and marine sets overlap")
    unknown_mounted_carriers = sorted(set(mounted_carriers) - expected)
    if unknown_mounted_carriers:
        pack_errors.append(f"mounted-carrier profile references unknown assets: {unknown_mounted_carriers}")
    if set(mounted_carriers) != EXPECTED_MOUNTED_CARRIERS:
        pack_errors.append(
            "mounted-carrier profile must exactly cover all ten fire-service specialist modules"
        )
    unknown_reduced_assets = sorted(set(map_scale_reductions) - expected)
    if unknown_reduced_assets:
        pack_errors.append(
            f"map-scale reductions reference unknown assets: {unknown_reduced_assets}"
        )
    for asset_id, reduction in map_scale_reductions.items():
        expected_body_width = int(reduction["target_body_width"])
        if int(profile.get("source_override_widths", {}).get(asset_id, -1)) != expected_body_width:
            pack_errors.append(
                f"{asset_id} map-scale target does not match its deterministic body-width override"
            )
    for carrier_id, carrier in mounted_carriers.items():
        expected_source = profile.get("new_source_overrides", {}).get(carrier_id)
        if carrier.get("base_vehicle") != "pm":
            pack_errors.append(f"{carrier_id} is not mounted on the PM chassis")
        if carrier.get("module") != carrier_id:
            pack_errors.append(f"{carrier_id} mounted-carrier module identity is incorrect")
        if expected_source != f"assets/masters/{master_source_release}/{carrier_id}-carrier.png":
            pack_errors.append(f"{carrier_id} does not use its release-specific carrier master")

    if {path.stem for path in STATIC_DIR.glob("*.png")} != expected:
        pack_errors.append("command static directory does not exactly match the 117-slot manifest")
    if {path.stem for path in ANIMATED_DIR.glob("*.png")} != expected:
        pack_errors.append("command animated directory does not exactly match the 117-slot manifest")
    if build_report["timing_signature_count"] < profile["qa"]["minimum_animation_signature_count"]:
        pack_errors.append("too few distinct animation timing signatures")
    if build_report["maximum_shared_timing_signature"] > profile["qa"]["maximum_shared_timing_signature"]:
        pack_errors.append("too many assets share one animation timing signature")
    if build_report["flash_phase_bucket_count"] < profile["qa"]["minimum_flash_phase_buckets"]:
        pack_errors.append("fleet does not use enough independent emergency-light phase buckets")
    if build_report["maximum_shared_flash_phase"] > profile["qa"]["maximum_shared_flash_phase"]:
        pack_errors.append("too many emergency vehicles share one flash phase")
    if build_report["flash_activity_signature_count"] < profile["qa"]["minimum_flash_activity_signatures"]:
        pack_errors.append("fleet does not have enough independent emergency-light activity signatures")
    if build_report["maximum_shared_flash_activity_signature"] > profile["qa"]["maximum_shared_flash_activity_signature"]:
        pack_errors.append("too many emergency vehicles share one light-activity signature")
    if build_report.get("retired_generated_overlay_assets") != 40:
        pack_errors.append("build report does not cover all 40 retired generated overlays")
    if build_report.get("maximum_retired_overlay_top_padding_pixels") != 0:
        pack_errors.append("build report detected artificial roof-overlay padding")
    if build_report["minimum_grounding_shadow_half_zoom_pixels"] < profile["qa"]["minimum_grounding_shadow_half_zoom_pixels"]:
        pack_errors.append("grounding shadow does not remain visible at half zoom")
    if set(profile.get("rotor_geometry", {})) != set(profile["helicopters"]):
        pack_errors.append("rotor geometry does not exactly cover the helicopter set")
    if set(helicopter_edge_padding) != set(profile["helicopters"]):
        pack_errors.append("helicopter edge-padding profile does not exactly cover the helicopter set")
    tail_thresholds = tail_integrity.get("minimum_strong_alpha_pixels", {})
    if set(tail_thresholds) != set(profile["helicopters"]):
        pack_errors.append("helicopter tail-integrity thresholds do not exactly cover the helicopter set")
    preserved_tail_rotors = {
        asset_id
        for asset_id, geometry in profile.get("rotor_geometry", {}).items()
        if geometry.get("preserve_baked_tail_rotor", False)
    }
    if preserved_tail_rotors != EXPECTED_PRESERVED_TAIL_ROTORS:
        pack_errors.append("preserved tail-rotor geometry does not exactly cover both Coastguard helicopters")
    for asset_id, filename in EXPECTED_FULL_TAIL_SOURCES.items():
        expected_source = f"assets/masters/{master_source_release}/{filename}"
        if profile.get("new_source_overrides", {}).get(asset_id) != expected_source:
            pack_errors.append(f"{asset_id} does not use its deterministic full-tail master")

    results = []
    timing_signatures: Counter[str] = Counter()
    silhouette_hashes: dict[str, str] = {}
    for vehicle in vehicles:
        asset_id = vehicle["id"]
        errors: list[str] = []
        standard = rgba(STANDARD_DIR / f"{asset_id}.png")
        static = rgba(STATIC_DIR / f"{asset_id}.png")
        frames, durations = frames_and_durations(ANIMATED_DIR / f"{asset_id}.png")
        detail = detail_map[asset_id]

        if static.mode != "RGBA":
            errors.append("static export is not RGBA")
        corners = [static.getpixel((0, 0))[3], static.getpixel((static.width - 1, 0))[3], static.getpixel((0, static.height - 1))[3], static.getpixel((static.width - 1, static.height - 1))[3]]
        if any(corners):
            errors.append("static export has a non-transparent corner")
        reduction = map_scale_reductions.get(asset_id)
        if static.width <= standard.width and reduction is None:
            errors.append("command export did not gain visible width")
        if reduction is not None:
            target_dimensions = (
                int(reduction["target_command_width"]),
                int(reduction["target_command_height"]),
            )
            if static.size != target_dimensions:
                errors.append(
                    f"intentional map-scale reduction is {static.size}, expected {target_dimensions}"
                )
        if detail["body_dimensions"]["width"] < int(profile["minimum_icon_width"]):
            errors.append("body width is below the command-visibility minimum")
        edge_padding = int(detail.get("edge_padding", 5))
        if static.width != detail["body_dimensions"]["width"] + edge_padding * 2:
            errors.append("visibility outline padding is inconsistent")
        if static.height != detail["body_dimensions"]["height"] + edge_padding * 2:
            errors.append("visibility outline vertical padding is inconsistent")
        if detail.get("role_cue") != role_cues.get(asset_id):
            errors.append("role differentiation cue does not match the profile")
        if detail.get("specialist_equipment_cue") != equipment_cues.get(asset_id):
            errors.append("specialist equipment cue does not match the profile")
        is_retired_overlay_asset = asset_id in retired_overlay_assets
        if bool(detail.get("retired_generated_overlay")) != is_retired_overlay_asset:
            errors.append("retired generated-overlay inventory does not match the build report")
        retired_top_padding = int(detail.get("retired_overlay_top_padding_pixels", 0))
        if is_retired_overlay_asset and retired_top_padding > int(
            profile["qa"]["maximum_retired_overlay_top_padding_pixels"]
        ):
            errors.append("artificial roof-overlay padding is present")
        if is_retired_overlay_asset and detail["body_dimensions"] != detail["motion_reference_dimensions"]:
            errors.append("retired overlay changed the corrected vehicle body dimensions")
        if bool(detail.get("satellite_contrast_boost")) != (asset_id in satellite_boost):
            errors.append("satellite contrast treatment does not match the profile")
        if asset_id in mounted_carriers:
            carrier = mounted_carriers[asset_id]
            expected_source = profile.get("new_source_overrides", {}).get(asset_id)
            if detail.get("source_override") != expected_source:
                errors.append("mounted carrier does not use its deterministic source override")
            if detail["body_dimensions"]["width"] < int(carrier["minimum_body_width"]):
                errors.append("mounted carrier body is too short to include its cab and chassis")
            if static.width < int(carrier["minimum_command_width"]):
                errors.append("mounted carrier command export is too short")
            if detail["motion"] != carrier["expected_motion"]:
                errors.append("mounted carrier response animation does not match policy")
            if int(detail.get("response_light_count", 0)) != int(carrier["expected_lights"]):
                errors.append("mounted carrier emergency-light inventory is incomplete")
        expected_shadow_mode = (
            "aerial"
            if asset_id in aerial_shadow_assets
            else "marine"
            if asset_id in marine_shadow_assets
            else "ground"
        )
        if detail.get("grounding_shadow", {}).get("mode") != expected_shadow_mode:
            errors.append("grounding shadow mode does not match the profile")
        if detail.get("grounding_shadow", {}).get("half_zoom_visible_pixels", 0) < int(
            profile["qa"]["minimum_grounding_shadow_half_zoom_pixels"]
        ):
            errors.append("grounding shadow disappears at half zoom")
        if len(frames) != int(profile["frames"]):
            errors.append(f"APNG has {len(frames)} frames instead of {profile['frames']}")
        elif frames:
            if changed(frames[0], static):
                errors.append("APNG frame 1 is not identical to the static export")
            changed_frames = sum(changed(frames[0], frame) for frame in frames[1:])
            should_move = detail["motion"] != "static"
            if should_move and changed_frames < 3:
                errors.append("animated asset has fewer than three visibly changed frames")
            if not should_move and changed_frames:
                errors.append("static-policy asset changes across frames")
            base_centroid = alpha_centroid(frames[0])
            maximum_shift = 0.0
            for frame in frames[1:]:
                cx, cy = alpha_centroid(frame)
                maximum_shift = max(maximum_shift, math.dist(base_centroid, (cx, cy)))
            if maximum_shift > 2.5:
                errors.append(f"animation alpha centroid shifts {maximum_shift:.2f}px")
        if durations != detail["durations_ms"]:
            errors.append("APNG timing does not match the deterministic build report")
        timing_signatures[",".join(str(value) for value in durations)] += 1

        rotor_underlay_pixels = None
        rotor_underlay_limit = None
        tail_upper_pixels = None
        if asset_id in profile["helicopters"]:
            geometry = profile["rotor_geometry"][asset_id]
            rotor_underlay_pixels = strong_rotor_underlay_pixels(static, geometry)
            rotor_underlay_limit = max(120, round(static.width * static.height * 0.015))
            if rotor_underlay_pixels > rotor_underlay_limit:
                errors.append(
                    f"strong static rotor underlay remains ({rotor_underlay_pixels} > {rotor_underlay_limit})"
                )
            tail_margin = min(
                image.getchannel("A").getbbox()[0]
                for image in [static, *frames]
                if image.getchannel("A").getbbox() is not None
            )
            if tail_margin < int(profile["qa"]["minimum_helicopter_tail_margin_pixels"]):
                errors.append(
                    f"helicopter tail margin is clipped ({tail_margin} < "
                    f"{profile['qa']['minimum_helicopter_tail_margin_pixels']})"
                )
            tail_upper_pixels = min(
                complete_tail_upper_pixels(
                    image,
                    float(tail_integrity["zone_width_fraction"]),
                    float(tail_integrity["zone_height_fraction"]),
                )
                for image in [static, *frames]
            )
            tail_threshold = int(tail_thresholds[asset_id])
            if tail_upper_pixels < tail_threshold:
                errors.append(
                    f"helicopter upper tail is structurally incomplete "
                    f"({tail_upper_pixels} < {tail_threshold})"
                )
        else:
            tail_margin = None

        visible_pixels = half_zoom_visible_pixels(static)
        if visible_pixels < int(profile["qa"]["minimum_visible_pixels_at_half_zoom"]):
            errors.append("too few visible pixels remain at half zoom")
        contrasts = {
            theme: edge_contrast(static, values["base"])
            for theme, values in THEMES.items()
        }
        if min(contrasts.values()) < 9.0:
            errors.append("outline contrast is too weak on at least one map theme")
        if asset_id in satellite_boost and contrasts["satellite"] < float(
            profile["qa"]["minimum_boosted_satellite_edge_contrast"]
        ):
            errors.append(
                "boosted satellite edge contrast is below the v1.2 target "
                f"({contrasts['satellite']} < {profile['qa']['minimum_boosted_satellite_edge_contrast']})"
            )
        if not changed(standard, static.resize(standard.size, Image.Resampling.LANCZOS)):
            errors.append("modern command treatment is pixel-identical to v1.0")

        silhouette_hashes[asset_id] = silhouette_hash(static)
        results.append(
            {
                "slot": vehicle["missionchief_slot"],
                "id": asset_id,
                "motion": detail["motion"],
                "dimensions": {"width": static.width, "height": static.height},
                "frames": len(frames),
                "changed_frames": sum(changed(frames[0], frame) for frame in frames[1:]) if frames else 0,
                "cycle_ms": sum(durations),
                "flash_phase": detail.get("flash_phase"),
                "flash_activity_signature": detail.get("flash_activity_signature"),
                "specialist_equipment_cue": detail.get("specialist_equipment_cue"),
                "specialist_equipment_half_zoom_added_alpha_pixels": detail.get(
                    "specialist_equipment_half_zoom_added_alpha_pixels"
                ),
                "retired_generated_overlay": detail.get("retired_generated_overlay"),
                "retired_overlay_top_padding_pixels": detail.get(
                    "retired_overlay_top_padding_pixels"
                ),
                "grounding_shadow": detail.get("grounding_shadow"),
                "strong_rotor_underlay_pixels": rotor_underlay_pixels,
                "strong_rotor_underlay_limit": rotor_underlay_limit,
                "helicopter_tail_margin_pixels": tail_margin,
                "helicopter_complete_tail_upper_pixels": tail_upper_pixels,
                "half_zoom_visible_pixels": visible_pixels,
                "edge_contrast": contrasts,
                "passed": not errors,
                "errors": errors,
            }
        )

    rare_ids = profile["rare_showcase"]
    closest_pair = None
    closest_distance = 10_000
    for index, left in enumerate(rare_ids):
        for right in rare_ids[index + 1 :]:
            distance = hamming(silhouette_hashes[left], silhouette_hashes[right])
            if distance < closest_distance:
                closest_distance = distance
                closest_pair = [left, right]
    if closest_distance == 0:
        pack_errors.append(f"rare showcase silhouettes collide: {closest_pair}")

    previews = [str(render_busy_map(theme, vehicles).relative_to(ROOT)) for theme in profile["qa"]["themes"]]
    previews.append(str(render_animation_sheet(vehicle_map).relative_to(ROOT)))
    previews.append(
        str(
            render_desynchronised_lights_sheet(
                vehicle_map,
                list(profile["animation_desynchronisation"]["showcase"]),
            ).relative_to(ROOT)
        )
    )
    previews.append(str(render_rotor_sheet(vehicle_map).relative_to(ROOT)))
    previews.append(
        str(
            render_targeted_sheet(
                f"{RELEASE} complete helicopter tails - 100% / 75% / 50%",
                ROTOR_SHOWCASE_IDS,
                "dark",
                "complete-helicopter-tails-map-scale.png",
                vehicle_map,
            ).relative_to(ROOT)
        )
    )
    previews.append(
        str(
            render_targeted_sheet(
                f"{RELEASE} corrected role rooflines - 100% / 75% / 50%",
                sorted(retired_role_assets),
                "dark",
                "corrected-role-rooflines-map-scale.png",
                vehicle_map,
            ).relative_to(ROOT)
        )
    )
    previews.append(
        str(
            render_targeted_sheet(
                f"{RELEASE} corrected specialist rooflines - 100% / 75% / 50%",
                sorted(retired_equipment_assets),
                "dark",
                "corrected-specialist-rooflines-map-scale.png",
                vehicle_map,
            ).relative_to(ROOT)
        )
    )
    previews.append(
        str(
            render_targeted_sheet(
                f"{RELEASE} grounding-shadow audit - 100% / 75% / 50%",
                list(grounding.get("showcase", [])),
                "satellite",
                "grounding-shadows-map-scale.png",
                vehicle_map,
            ).relative_to(ROOT)
        )
    )
    previews.append(
        str(
            render_targeted_sheet(
                f"{RELEASE} satellite-contrast audit - 100% / 75% / 50%",
                list(profile.get("satellite_contrast_boost", [])),
                "satellite",
                "satellite-contrast-map-scale.png",
                vehicle_map,
            ).relative_to(ROOT)
        )
    )
    previews.append(
        str(
            render_targeted_sheet(
                f"{RELEASE} mounted specialist-carrier audit - 100% / 75% / 50%",
                sorted(mounted_carriers),
                "light",
                "mounted-specialist-carrier-map-scale.png",
                vehicle_map,
            ).relative_to(ROOT)
        )
    )

    report = {
        "release": profile["release"],
        "profile": profile["profile"],
        "vehicles": len(results),
        "static_pngs": len(list(STATIC_DIR.glob("*.png"))),
        "animated_apngs": len(list(ANIMATED_DIR.glob("*.png"))),
        "frames_per_asset": profile["frames"],
        "themes_tested": profile["qa"]["themes"],
        "zoom_factors_tested": profile["qa"]["zoom_factors"],
        "timing_signature_count": len(timing_signatures),
        "maximum_shared_timing_signature": max(timing_signatures.values()),
        "flash_phase_bucket_count": build_report["flash_phase_bucket_count"],
        "maximum_shared_flash_phase": build_report["maximum_shared_flash_phase"],
        "flash_activity_signature_count": build_report["flash_activity_signature_count"],
        "maximum_shared_flash_activity_signature": build_report[
            "maximum_shared_flash_activity_signature"
        ],
        "minimum_half_zoom_visible_pixels": min(item["half_zoom_visible_pixels"] for item in results),
        "minimum_edge_contrast": min(min(item["edge_contrast"].values()) for item in results),
        "closest_rare_silhouette_pair": closest_pair,
        "closest_rare_silhouette_distance": closest_distance,
        "role_differentiated_assets": len(role_cues),
        "specialist_equipment_assets": len(equipment_cues),
        "retired_generated_overlay_assets": len(retired_overlay_assets),
        "maximum_retired_overlay_top_padding_pixels": max(
            item["retired_overlay_top_padding_pixels"]
            for item in results
            if item["retired_generated_overlay"]
        ),
        "grounding_shadow_assets": len(results),
        "minimum_grounding_shadow_half_zoom_pixels": min(
            item["grounding_shadow"]["half_zoom_visible_pixels"] for item in results
        ),
        "satellite_contrast_boosted_assets": len(satellite_boost),
        "mounted_carrier_assets": len(mounted_carriers),
        "mounted_carrier_ids": sorted(mounted_carriers),
        "minimum_helicopter_tail_margin_pixels": min(
            item["helicopter_tail_margin_pixels"]
            for item in results
            if item["helicopter_tail_margin_pixels"] is not None
        ),
        "minimum_helicopter_complete_tail_upper_pixels": min(
            item["helicopter_complete_tail_upper_pixels"]
            for item in results
            if item["helicopter_complete_tail_upper_pixels"] is not None
        ),
        "minimum_boosted_satellite_edge_contrast": min(
            item["edge_contrast"]["satellite"]
            for item in results
            if item["id"] in satellite_boost
        ),
        "role_group_results": [],
        "preview_files": previews,
        "pack_errors": pack_errors,
        "vehicles_detail": results,
        "all_passed": not pack_errors and all(item["passed"] for item in results),
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "vehicles_detail"}, indent=2))
    if not report["all_passed"]:
        failed = [item for item in results if not item["passed"]]
        print(json.dumps({"failed": failed}, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
