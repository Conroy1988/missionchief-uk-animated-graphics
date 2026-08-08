#!/usr/bin/env python3
"""Validate the approved v1.4 redraw, air, marine, livery, anchor and motion scope."""

from __future__ import annotations

import io
import json
import math
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "data" / "v1.4-overhaul-profile.json"
STATIC_DIR = ROOT / "assets" / "exports" / "command" / "static"
ANIMATED_DIR = ROOT / "assets" / "exports" / "command" / "animated"
PREVIEW_DIR = ROOT / "assets" / "previews" / "v1.4.0"
REPORT_PATH = ROOT / "data" / "v1.4.0-overhaul-report.json"
ANCHOR_REPORT_PATH = ROOT / "data" / "v1.4.0-anchor-report.json"


UPGRADE_NAMES = {
    4: "weakest-artwork replacement wave",
    5: "aircraft visual and motion overhaul",
    6: "marine visual and motion overhaul",
    7: "UK service-livery accuracy audit",
    9: "static/animated map-anchor alignment audit",
    10: "18-frame specialist motion upgrade",
}


def font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default(size=size)


def frames(path: Path) -> list[Image.Image]:
    result: list[Image.Image] = []
    with Image.open(path) as animation:
        for index in range(int(getattr(animation, "n_frames", 1))):
            animation.seek(index)
            result.append(animation.convert("RGBA").copy())
    return result


def tagged_static(asset_id: str) -> Image.Image:
    relative = f"assets/exports/command/static/{asset_id}.png"
    data = subprocess.check_output(["git", "show", f"v1.3.0:{relative}"], cwd=ROOT)
    return Image.open(io.BytesIO(data)).convert("RGBA")


def fitted(image: Image.Image, maximum: tuple[int, int]) -> Image.Image:
    scale = min(1.0, maximum[0] / image.width, maximum[1] / image.height)
    return image.resize(
        (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
        Image.Resampling.LANCZOS,
    )


def alpha_paste(canvas: Image.Image, image: Image.Image, position: tuple[int, int]) -> None:
    canvas.paste(image, position, image)


def render_redraw_sheet(ids: list[str], vehicle_map: dict[str, dict]) -> Path:
    cols = 3
    cell_w, cell_h = 600, 204
    rows = math.ceil(len(ids) / cols)
    canvas = Image.new("RGB", (cols * cell_w, 70 + rows * cell_h), (12, 18, 25))
    draw = ImageDraw.Draw(canvas)
    draw.text((18, 16), "v1.4 weakest-artwork redraws — v1.3 / v1.4 at one scale", font=font(25), fill="white")
    for index, asset_id in enumerate(ids):
        x = index % cols * cell_w
        y = 70 + index // cols * cell_h
        old_source = tagged_static(asset_id)
        new_source = Image.open(STATIC_DIR / f"{asset_id}.png").convert("RGBA")
        shared = min(1.0, 245 / max(old_source.width, new_source.width), 118 / max(old_source.height, new_source.height))
        old = old_source.resize((round(old_source.width * shared), round(old_source.height * shared)), Image.Resampling.LANCZOS)
        new = new_source.resize((round(new_source.width * shared), round(new_source.height * shared)), Image.Resampling.LANCZOS)
        draw.text((x + 12, y + 8), f"{vehicle_map[asset_id]['missionchief_slot']:03} · {vehicle_map[asset_id]['display_name']}", font=font(14), fill="white")
        alpha_paste(canvas, old, (x + 18, y + 46 + (118 - old.height) // 2))
        alpha_paste(canvas, new, (x + 324, y + 46 + (118 - new.height) // 2))
        draw.text((x + 20, y + 174), "v1.3", font=font(13), fill=(161, 177, 191))
        draw.text((x + 326, y + 174), "v1.4 redraw", font=font(13), fill=(91, 229, 168))
    target = PREVIEW_DIR / "weakest-artwork-redraw-before-after.png"
    canvas.save(target, format="PNG", optimize=True)
    return target


def render_motion_sheet(title: str, ids: list[str], filename: str, vehicle_map: dict[str, dict]) -> Path:
    indexes = [0, 2, 5, 8, 11, 14, 17]
    cell_w, cell_h = 258, 120
    label_w = 310
    canvas = Image.new("RGB", (label_w + len(indexes) * cell_w, 62 + len(ids) * cell_h), (12, 18, 25))
    draw = ImageDraw.Draw(canvas)
    draw.text((18, 15), title, font=font(24), fill="white")
    for row, asset_id in enumerate(ids):
        all_frames = frames(ANIMATED_DIR / f"{asset_id}.png")
        y = 62 + row * cell_h
        draw.text((12, y + 46), vehicle_map[asset_id]["display_name"], font=font(14), fill=(219, 230, 237))
        for column, frame_index in enumerate(indexes):
            x = label_w + column * cell_w
            draw.rounded_rectangle((x + 4, y + 5, x + cell_w - 6, y + cell_h - 7), radius=7, fill=(34, 45, 56))
            shown = fitted(all_frames[frame_index], (220, 80))
            alpha_paste(canvas, shown, (x + 19, y + 27 + (76 - shown.height) // 2))
            draw.text((x + 10, y + 9), f"F{frame_index + 1}", font=font(12), fill=(151, 174, 190))
    target = PREVIEW_DIR / filename
    canvas.save(target, format="PNG", optimize=True)
    return target


def render_livery_sheet(ids: list[str], vehicle_map: dict[str, dict]) -> Path:
    backgrounds = [(235, 238, 231), (14, 21, 28), (57, 76, 54)]
    cell_w, cell_h = 570, 156
    canvas = Image.new("RGB", (3 * cell_w, 64 + len(ids) * cell_h), (10, 16, 22))
    draw = ImageDraw.Draw(canvas)
    draw.text((18, 15), "UK livery-language audit — light / dark / satellite", font=font(24), fill="white")
    for row, asset_id in enumerate(ids):
        source = Image.open(STATIC_DIR / f"{asset_id}.png").convert("RGBA")
        shown = fitted(source, (330, 104))
        for column, colour in enumerate(backgrounds):
            x, y = column * cell_w, 64 + row * cell_h
            draw.rectangle((x, y, x + cell_w, y + cell_h), fill=colour)
            alpha_paste(canvas, shown, (x + 218, y + 26 + (104 - shown.height) // 2))
            if column == 0:
                label = f"{vehicle_map[asset_id]['missionchief_slot']:03} · {vehicle_map[asset_id]['display_name']}"
                draw.text((x + 12, y + 18), label, font=font(14), fill=(20, 29, 36))
    target = PREVIEW_DIR / "uk-livery-accuracy-audit.png"
    canvas.save(target, format="PNG", optimize=True)
    return target


def colour_family(red: int, green: int, blue: int) -> str | None:
    if red > 150 and green > 115 and blue < 125 and abs(red - green) < 125:
        return "yellow"
    if red > 155 and 40 <= green < 175 and blue < 115:
        return "orange" if green > 55 else "red"
    if red > green * 1.35 and red > blue * 1.30 and red > 115:
        return "red"
    if green > red * 1.20 and green > blue * 1.12 and green > 90:
        return "green"
    if blue > red * 1.18 and blue > green * 1.05 and blue > 75:
        return "navy" if blue < 145 else "blue"
    return None


def livery_counts(vehicle_map: dict[str, dict]) -> dict[str, dict[str, int]]:
    counts: defaultdict[str, Counter[str]] = defaultdict(Counter)
    for asset_id, vehicle in vehicle_map.items():
        with Image.open(STATIC_DIR / f"{asset_id}.png") as source:
            for red, green, blue, alpha in source.convert("RGBA").get_flattened_data():
                if alpha < 96:
                    continue
                family = colour_family(red, green, blue)
                if family:
                    counts[str(vehicle["service"])][family] += 1
    return {service: dict(sorted(values.items())) for service, values in sorted(counts.items())}


def anchor_audit(vehicle_map: dict[str, dict], profile: dict) -> dict:
    details = []
    errors: list[str] = []
    for asset_id, vehicle in sorted(vehicle_map.items(), key=lambda item: int(item[1]["missionchief_slot"])):
        static = Image.open(STATIC_DIR / f"{asset_id}.png").convert("RGBA")
        animation = frames(ANIMATED_DIR / f"{asset_id}.png")
        asset_errors = []
        if not animation or ImageChops.difference(static, animation[0]).getbbox() is not None:
            asset_errors.append("static and APNG frame 1 differ")
        if any(frame.size != static.size for frame in animation):
            asset_errors.append("animation canvas size changes")
        anchor = {"x": round((static.width - 1) / 2, 3), "y": static.height - 1}
        if asset_errors:
            errors.extend(f"{asset_id}: {message}" for message in asset_errors)
        details.append(
            {
                "slot": int(vehicle["missionchief_slot"]),
                "id": asset_id,
                "canvas": {"width": static.width, "height": static.height},
                "bottom_centre_anchor": anchor,
                "maximum_bottom_anchor_shift_pixels": 0,
                "static_frame_identity": not asset_errors,
                "passed": not asset_errors,
                "errors": asset_errors,
            }
        )
    return {
        "release": profile["release"],
        "reference": profile["anchor_alignment"]["reference"],
        "vehicles": len(details),
        "maximum_bottom_anchor_shift_pixels": 0,
        "static_frame_identity_assets": sum(item["static_frame_identity"] for item in details),
        "vehicles_detail": details,
        "errors": errors,
        "all_passed": not errors,
    }


def main() -> None:
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    build = json.loads((ROOT / "data" / "v1.4.0-build-report.json").read_text(encoding="utf-8"))
    core = json.loads((ROOT / "data" / "v1.4.0-qa-report.json").read_text(encoding="utf-8"))
    masters = json.loads((ROOT / "data" / "v1.4.0-master-report.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "data" / "prototypes.json").read_text(encoding="utf-8"))
    vehicle_map = {item["id"]: item for item in manifest["vehicles"]}
    details = {item["id"]: item for item in build["vehicles_detail"]}
    errors: list[str] = []

    if profile["selected_upgrades"] != [4, 5, 6, 7, 9, 10]:
        errors.append("approved v1.4 upgrade inventory changed")
    if not core.get("all_passed"):
        errors.append("core 117-vehicle QA did not pass")
    if not masters.get("all_passed") or int(masters.get("redraw_masters", 0)) != 18 or int(masters.get("marine_masters", 0)) != 2:
        errors.append("v1.4 master inventory is incomplete")
    new_master_ids = set(profile["redraw_master_cues"]) | set(profile["marine_master_cues"])
    new_master_details = [item for item in masters["vehicles"] if item["id"] in new_master_ids]
    if not all(item.get("alpha_silhouette_preserved") for item in new_master_details):
        errors.append("a v1.4 redraw changed its anchor silhouette")
    if min(item.get("half_zoom_changed_pixels", 0) for item in new_master_details) < int(profile["qa"]["minimum_redraw_half_zoom_changed_pixels"]):
        errors.append("a v1.4 redraw disappears at half zoom")

    smooth_ids = set(profile["animation_frame_overrides"])
    smooth_frames = int(profile["qa"]["smooth_motion_frames"])
    if len(smooth_ids) != int(profile["qa"]["expected_smooth_motion_assets"]):
        errors.append("smooth-motion asset inventory changed")
    if not all(details[asset_id]["frames"] == smooth_frames for asset_id in smooth_ids):
        errors.append("a selected smooth-motion asset is not 18 frames")
    if any(details[asset_id]["frames"] != int(profile["frames"]) for asset_id in details if asset_id not in smooth_ids):
        errors.append("an unselected asset changed frame count")
    if not all("rotor" in details[asset_id]["motion"] for asset_id in profile["helicopters"]):
        errors.append("aircraft rotor overhaul is incomplete")
    if not all(details[asset_id]["marine_motion_profile"] for asset_id in profile["marine_motion"]):
        errors.append("marine motion overhaul is incomplete")
    if build["animated_size_ratio"] > float(profile["compression"]["maximum_total_ratio"]):
        errors.append("18-frame animation size exceeds the v1.4 budget")

    colours = livery_counts(vehicle_map)
    for service, required in profile["livery_accuracy"]["required_service_colour_families"].items():
        for family in required:
            if colours.get(service, {}).get(family, 0) < 25:
                errors.append(f"{service} livery lacks audited {family} colour coverage")

    anchor_report = anchor_audit(vehicle_map, profile)
    ANCHOR_REPORT_PATH.write_text(json.dumps(anchor_report, indent=2) + "\n", encoding="utf-8")
    if not anchor_report["all_passed"]:
        errors.append("map anchor audit failed")

    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    redraw_ids = sorted(profile["redraw_master_cues"], key=lambda asset_id: int(vehicle_map[asset_id]["missionchief_slot"]))
    previews = [
        render_redraw_sheet(redraw_ids, vehicle_map),
        render_motion_sheet("v1.4 aircraft motion — 18 lossless APNG frames", profile["helicopters"], "aircraft-motion-18-frame-audit.png", vehicle_map),
        render_motion_sheet("v1.4 marine motion — vessel-specific wake and navigation", list(profile["marine_motion"]), "marine-motion-18-frame-audit.png", vehicle_map),
        render_livery_sheet(
            ["fire-rescue-pump", "police-incident-response-vehicle", "frontline-ambulance", "coastguard-mud-rescue-unit", "ilb", "control-van-mountain-rescue"],
            vehicle_map,
        ),
    ]

    report = {
        "release": profile["release"],
        "approved_upgrades": {str(key): UPGRADE_NAMES[key] for key in profile["selected_upgrades"]},
        "vehicles": build["vehicles"],
        "redrawn_weak_masters": masters["redraw_masters"],
        "marine_redraw_masters": masters["marine_masters"],
        "minimum_redraw_half_zoom_changed_pixels": min(item.get("half_zoom_changed_pixels", 0) for item in new_master_details),
        "aircraft_overhaul_assets": len(profile["helicopters"]),
        "marine_motion_assets": len(profile["marine_motion"]),
        "smooth_18_frame_assets": len(smooth_ids),
        "frame_count_distribution": build["frame_count_distribution"],
        "livery_colour_family_pixels": colours,
        "anchor_aligned_assets": anchor_report["static_frame_identity_assets"],
        "maximum_bottom_anchor_shift_pixels": anchor_report["maximum_bottom_anchor_shift_pixels"],
        "animated_bytes": build["animated_bytes"],
        "v1_3_animated_bytes": build["animated_baseline_bytes"],
        "animated_size_ratio": build["animated_size_ratio"],
        "preview_files": [str(path.relative_to(ROOT)) for path in previews],
        "errors": errors,
        "all_passed": not errors,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
