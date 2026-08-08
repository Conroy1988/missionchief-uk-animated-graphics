#!/usr/bin/env python3
"""Validate every approved v1.3 fleet-overhaul objective and render evidence sheets."""

from __future__ import annotations

import io
import json
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "data" / "v1.3-overhaul-profile.json"
BUILD_REPORT_PATH = ROOT / "data" / "v1.3.0-build-report.json"
CORE_QA_PATH = ROOT / "data" / "v1.3.0-qa-report.json"
MASTER_REPORT_PATH = ROOT / "data" / "v1.3.0-master-report.json"
REPORT_PATH = ROOT / "data" / "v1.3.0-overhaul-report.json"
STATIC_DIR = ROOT / "assets" / "exports" / "command" / "static"
ANIMATED_DIR = ROOT / "assets" / "exports" / "command" / "animated"
PREVIEW_DIR = ROOT / "assets" / "previews" / "v1.3.0"


UPGRADE_NAMES = {
    1: "fleet-wide real-length scale calibration",
    2: "twenty rebuilt weak vehicle masters",
    3: "adaptive low-sticker visibility outlines",
    4: "fixture-shaped emergency lighting",
    5: "steady response headlights and rear lamps",
    6: "elliptical helicopter rotor and aviation-light motion",
    7: "class-weighted marine navigation and wake motion",
    8: "selective fixture-aligned wheel animation",
    9: "baked role differentiation",
    10: "standardised UK high-visibility livery palette",
    11: "fleet-wide alpha artefact cleanup",
    12: "native half-scale readability polish",
    13: "vehicle-class grounding shadows",
    14: "baked specialist equipment",
    16: "lossless APNG optimisation",
}


def font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default(size=size)


def alpha_paste(canvas: Image.Image, image: Image.Image, position: tuple[int, int]) -> None:
    canvas.paste(image, position, image)


def fitted(image: Image.Image, maximum: tuple[int, int]) -> Image.Image:
    scale = min(1.0, maximum[0] / image.width, maximum[1] / image.height)
    return image.resize(
        (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
        Image.Resampling.LANCZOS,
    )


def tagged_static(asset_id: str, tag: str = "v1.2.7") -> Image.Image:
    path = f"assets/exports/command/static/{asset_id}.png"
    data = subprocess.check_output(["git", "show", f"{tag}:{path}"], cwd=ROOT)
    return Image.open(io.BytesIO(data)).convert("RGBA")


def animation_frames(asset_id: str) -> list[Image.Image]:
    frames = []
    with Image.open(ANIMATED_DIR / f"{asset_id}.png") as animation:
        for index in range(animation.n_frames):
            animation.seek(index)
            frames.append(animation.convert("RGBA").copy())
    return frames


def render_before_after(ids: list[str], vehicle_map: dict[str, dict]) -> Path:
    cols = 4
    cell_w, cell_h = 440, 176
    rows = math.ceil(len(ids) / cols)
    canvas = Image.new("RGB", (cols * cell_w, 66 + rows * cell_h), (13, 19, 26))
    draw = ImageDraw.Draw(canvas)
    draw.text((18, 16), "v1.3.0 calibrated fleet — v1.2.7 / v1.3.0 at identical display scale", font=font(24), fill="white")
    for index, asset_id in enumerate(ids):
        x = (index % cols) * cell_w
        y = 66 + (index // cols) * cell_h
        old_source = tagged_static(asset_id)
        new_source = Image.open(STATIC_DIR / f"{asset_id}.png").convert("RGBA")
        shared_scale = min(
            1.0,
            180 / max(old_source.width, new_source.width),
            94 / max(old_source.height, new_source.height),
        )
        old = old_source.resize(
            (max(1, round(old_source.width * shared_scale)), max(1, round(old_source.height * shared_scale))),
            Image.Resampling.LANCZOS,
        )
        new = new_source.resize(
            (max(1, round(new_source.width * shared_scale)), max(1, round(new_source.height * shared_scale))),
            Image.Resampling.LANCZOS,
        )
        alpha_paste(canvas, old, (x + 12, y + 42 + (94 - old.height) // 2))
        alpha_paste(canvas, new, (x + 230, y + 42 + (94 - new.height) // 2))
        item = vehicle_map[asset_id]
        draw.text((x + 10, y + 8), f"{item['missionchief_slot']:03} · {item['display_name']}", font=font(15), fill="white")
        draw.text((x + 14, y + 142), "v1.2.7", font=font(13), fill=(160, 177, 190))
        draw.text((x + 232, y + 142), f"v1.3 · {item['real_length_metres']} m", font=font(13), fill=(94, 230, 172))
    target = PREVIEW_DIR / "fleet-scale-before-after.png"
    canvas.save(target, format="PNG", optimize=True)
    return target


def render_master_audit(master_report: dict, vehicle_map: dict[str, dict]) -> Path:
    ids = [item["id"] for item in master_report["vehicles"]]
    cols = 4
    cell_w, cell_h = 440, 158
    rows = math.ceil(len(ids) / cols)
    canvas = Image.new("RGB", (cols * cell_w, 64 + rows * cell_h), (13, 19, 26))
    draw = ImageDraw.Draw(canvas)
    draw.text((18, 15), "Twenty baked role and specialist masters — 100% / 50%", font=font(24), fill="white")
    details = {item["id"]: item for item in master_report["vehicles"]}
    for index, asset_id in enumerate(ids):
        x = (index % cols) * cell_w
        y = 64 + (index // cols) * cell_h
        image = Image.open(STATIC_DIR / f"{asset_id}.png").convert("RGBA")
        full = fitted(image, (238, 92))
        half = image.resize((max(1, round(image.width * 0.5)), max(1, round(image.height * 0.5))), Image.Resampling.LANCZOS)
        alpha_paste(canvas, full, (x + 12, y + 42 + (92 - full.height) // 2))
        alpha_paste(canvas, half, (x + 292, y + 64 - half.height // 2))
        draw.text((x + 10, y + 7), f"{vehicle_map[asset_id]['missionchief_slot']:03} · {asset_id}", font=font(14), fill="white")
        draw.text((x + 12, y + 134), details[asset_id]["cue"], font=font(12), fill=(96, 223, 172))
    target = PREVIEW_DIR / "baked-role-master-audit.png"
    canvas.save(target, format="PNG", optimize=True)
    return target


def render_motion_audit(ids: list[str], vehicle_map: dict[str, dict]) -> Path:
    frame_indexes = [0, 1, 3, 5, 7, 9, 11]
    cell_w, cell_h = 260, 112
    canvas = Image.new("RGB", (310 + len(frame_indexes) * cell_w, 60 + len(ids) * cell_h), (12, 18, 25))
    draw = ImageDraw.Draw(canvas)
    draw.text((18, 14), "v1.3.0 lighting and motion — selected lossless APNG frames", font=font(23), fill="white")
    for row, asset_id in enumerate(ids):
        y = 60 + row * cell_h
        frames = animation_frames(asset_id)
        draw.text((12, y + 42), vehicle_map[asset_id]["display_name"], font=font(14), fill=(220, 230, 238))
        for column, frame_index in enumerate(frame_indexes):
            x = 310 + column * cell_w
            draw.rounded_rectangle((x + 4, y + 5, x + cell_w - 6, y + cell_h - 7), radius=7, fill=(34, 45, 56))
            image = fitted(frames[frame_index], (220, 78))
            alpha_paste(canvas, image, (x + 20, y + 26 + (70 - image.height) // 2))
            draw.text((x + 10, y + 9), f"F{frame_index + 1}", font=font(12), fill=(151, 174, 190))
    target = PREVIEW_DIR / "lighting-motion-audit.png"
    canvas.save(target, format="PNG", optimize=True)
    return target


def render_outline_audit(ids: list[str], vehicle_map: dict[str, dict]) -> Path:
    backgrounds = [(235, 238, 231), (14, 21, 28), (57, 76, 54)]
    cols = 3
    cell_w, cell_h = 560, 156
    canvas = Image.new("RGB", (cols * cell_w, 62 + len(ids) * cell_h), (10, 16, 22))
    draw = ImageDraw.Draw(canvas)
    draw.text((18, 14), "Adaptive outline, livery and shadow audit — light / dark / satellite", font=font(23), fill="white")
    for row, asset_id in enumerate(ids):
        image = Image.open(STATIC_DIR / f"{asset_id}.png").convert("RGBA")
        for column, colour in enumerate(backgrounds):
            x = column * cell_w
            y = 62 + row * cell_h
            draw.rectangle((x, y, x + cell_w, y + cell_h), fill=colour)
            shown = fitted(image, (330, 104))
            alpha_paste(canvas, shown, (x + 208, y + 26 + (104 - shown.height) // 2))
            if column == 0:
                draw.text((x + 12, y + 18), f"{vehicle_map[asset_id]['missionchief_slot']:03} · {vehicle_map[asset_id]['display_name']}", font=font(14), fill=(20, 29, 36))
    target = PREVIEW_DIR / "adaptive-outline-livery-shadow-audit.png"
    canvas.save(target, format="PNG", optimize=True)
    return target


def main() -> None:
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    build = json.loads(BUILD_REPORT_PATH.read_text(encoding="utf-8"))
    core = json.loads(CORE_QA_PATH.read_text(encoding="utf-8"))
    masters = json.loads(MASTER_REPORT_PATH.read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "data" / "prototypes.json").read_text(encoding="utf-8"))
    vehicle_map = {item["id"]: item for item in manifest["vehicles"]}
    details = {item["id"]: item for item in build["vehicles_detail"]}
    errors: list[str] = []

    selected = list(profile["selected_upgrades"])
    if selected != [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16]:
        errors.append("approved v1.3 upgrade inventory changed")
    if not core.get("all_passed"):
        errors.append("core 117-vehicle QA did not pass")
    if int(masters.get("masters", 0)) != 20 or not masters.get("all_passed"):
        errors.append("twenty baked v1.3 source masters were not validated")
    if build["baked_role_master_assets"] != 20:
        errors.append("build did not consume all twenty baked source masters")
    if build["mean_length_scale_error_percent"] > float(profile["scale_calibration"]["maximum_mean_length_error_percent"]):
        errors.append("fleet mean real-length scale error is too high")
    if build["maximum_length_scale_error_percent"] > float(profile["scale_calibration"]["maximum_asset_length_error_percent"]):
        errors.append("an asset exceeds the real-length scale tolerance")
    if Image.open(STATIC_DIR / "alb.png").size != (169, 84):
        errors.append("approved 169x84 ALB exception was not preserved")
    if build["maximum_outline_to_body_ratio"] > float(profile["qa"]["maximum_outline_to_body_ratio"]):
        errors.append("adaptive outline coverage exceeds the anti-sticker limit")
    if set(build["outline_style_counts"]) != {"compact-single-pixel", "standard-adaptive", "large-vehicle-adaptive"}:
        errors.append("adaptive outline system did not exercise all three size classes")
    if not all(item["fixture_shaped_emergency_lights"] for item in details.values() if item["response_light_count"]):
        errors.append("an emergency vehicle lacks fixture-shaped lighting")
    if sum(item["response_running_lights"] for item in details.values()) < 85:
        errors.append("response running lights do not cover the expected road fleet")
    if not all(details[asset_id]["aviation_navigation_lights"] for asset_id in profile["helicopters"]):
        errors.append("helicopter aviation-light motion is incomplete")
    coastguard = {"coastguard-rescue-helicopter", "coastguard-rescue-helicopter-large"}
    if not all(details[asset_id]["preserved_tail_rotor_animated"] for asset_id in coastguard):
        errors.append("Coastguard preserved tail rotors are not animated")
    if set(profile["marine_motion"]) != {"ilb", "alb"}:
        errors.append("marine motion inventory changed")
    if not all(details[asset_id]["marine_motion_profile"] for asset_id in profile["marine_motion"]):
        errors.append("marine wake profiles are missing")
    if set(profile["wheel_geometry"]) != set(profile["motion"]["wheel"]):
        errors.append("wheel-animation inventory does not match its geometry")
    if not all(details[asset_id]["wheel_geometry"] for asset_id in profile["motion"]["wheel"]):
        errors.append("a selective wheel animation lacks fixture geometry")
    if len(build["shadow_class_counts"]) != 5:
        errors.append("vehicle-class grounding shadows are incomplete")
    if build["livery_pixels_normalised"] < 10000:
        errors.append("fleet-wide livery normalisation did not materially run")
    if build["isolated_alpha_pixels_remaining"] > int(profile["qa"]["maximum_isolated_alpha_pixels"]):
        errors.append("isolated alpha artefacts remain")
    if build["minimum_half_zoom_detail_score"] < float(profile["qa"]["minimum_half_zoom_detail_score"]):
        errors.append("a vehicle fails the native half-scale detail gate")
    if build["animated_size_ratio"] > float(profile["compression"]["maximum_total_ratio"]):
        errors.append("lossless APNG size target was not met")
    if not all(item["apng_compression"]["lossless_verified"] for item in details.values()):
        errors.append("an APNG did not pass pixel-exact compression verification")
    if build["preferred_disposal_assets"] < 90:
        errors.append("too few APNGs accepted the smaller lossless delta-frame encoding")

    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    scale_ids = [
        "police-incident-response-vehicle", "rapid-response-vehicle", "fire-rescue-pump",
        "frontline-ambulance", "aerial-appliance", "incident-command-control-unit",
        "hems", "police-helicopter", "coastguard-rescue-helicopter-large", "ilb", "alb",
        "medical-cycle-responder", "recovery-vehicle", "hgv-recovery-vehicle",
        "eod-heavy-equipment-vehicle", "major-foam-tender",
    ]
    previews = [
        render_before_after(scale_ids, vehicle_map),
        render_master_audit(masters, vehicle_map),
        render_motion_audit(
            [
                "fire-rescue-pump", "frontline-ambulance", "police-incident-response-vehicle",
                "hems", "coastguard-rescue-helicopter", "ilb",
                "medical-cycle-responder", "hgv-recovery-vehicle",
            ],
            vehicle_map,
        ),
        render_outline_audit(
            [
                "police-incident-response-vehicle", "frontline-ambulance", "fire-rescue-pump",
                "rescue-pod", "medical-cycle-responder", "hems", "ilb",
                "eod-heavy-equipment-vehicle",
            ],
            vehicle_map,
        ),
    ]

    report = {
        "release": profile["release"],
        "approved_upgrades": {str(key): UPGRADE_NAMES[key] for key in selected},
        "vehicles": build["vehicles"],
        "baked_source_masters": masters["masters"],
        "mean_length_scale_error_percent": build["mean_length_scale_error_percent"],
        "maximum_length_scale_error_percent": build["maximum_length_scale_error_percent"],
        "maximum_outline_to_body_ratio": build["maximum_outline_to_body_ratio"],
        "response_running_light_assets": sum(item["response_running_lights"] for item in details.values()),
        "animated_coastguard_tail_rotors": 2,
        "marine_motion_assets": len(profile["marine_motion"]),
        "selective_wheel_motion_assets": len(profile["wheel_geometry"]),
        "shadow_classes": build["shadow_class_counts"],
        "livery_pixels_normalised": build["livery_pixels_normalised"],
        "isolated_alpha_pixels_remaining": build["isolated_alpha_pixels_remaining"],
        "minimum_half_zoom_detail_score": build["minimum_half_zoom_detail_score"],
        "baseline_animated_bytes": build["animated_baseline_bytes"],
        "v1_3_animated_bytes": build["animated_bytes"],
        "animated_size_reduction_percent": round((1.0 - build["animated_size_ratio"]) * 100.0, 2),
        "lossless_verified_apngs": sum(item["apng_compression"]["lossless_verified"] for item in details.values()),
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
