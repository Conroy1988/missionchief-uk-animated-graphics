#!/usr/bin/env python3
"""Build deterministic v1.4 redraw and marine masters without copied branding."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter

from build_v1_1_enhanced import crop_to_alpha


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "data" / "v1.4-overhaul-profile.json"
STANDARD_DIR = ROOT / "assets" / "exports" / "standard" / "static"
OUTPUT_DIR = ROOT / "assets" / "masters" / "v1.4.0"
REPORT_PATH = ROOT / "data" / "v1.4.0-master-report.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clipped_overlay(base: Image.Image, overlay: Image.Image) -> Image.Image:
    clipped = overlay.copy()
    clipped.putalpha(ImageChops.multiply(overlay.getchannel("A"), base.getchannel("A")))
    return Image.alpha_composite(base, clipped)


def crisp_tone(image: Image.Image) -> Image.Image:
    alpha = image.getchannel("A")
    rgb = image.convert("RGB")
    rgb = ImageEnhance.Contrast(rgb).enhance(1.035)
    rgb = ImageEnhance.Color(rgb).enhance(1.025)
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=0.48, percent=92, threshold=2))
    result = rgb.convert("RGBA")
    result.putalpha(alpha)
    return result


def service_colours(service: str) -> tuple[tuple[int, int, int, int], tuple[int, int, int, int]]:
    palettes = {
        "fire": ((250, 216, 34, 225), (207, 32, 29, 230)),
        "police": ((250, 221, 40, 225), (34, 105, 206, 230)),
        "ambulance": ((248, 222, 39, 225), (30, 153, 87, 230)),
        "search-and-rescue": ((247, 214, 39, 225), (232, 79, 32, 230)),
    }
    return palettes.get(service, ((237, 221, 79, 220), (52, 111, 157, 220)))


def ground_redraw(image: Image.Image, cue: str, service: str) -> Image.Image:
    """Re-ink weak masters with vehicle-specific panels, glazing and equipment detail."""
    result = crisp_tone(image.convert("RGBA"))
    width, height = result.size
    overlay = Image.new("RGBA", result.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    high_vis, service_tone = service_colours(service)
    ink = (18, 27, 34, 185)
    steel = (205, 218, 224, 185)
    glass = (126, 194, 207, 105)

    sill_y = round(height * 0.68)
    draw.line((round(width * 0.08), sill_y, round(width * 0.91), sill_y), fill=ink, width=1)
    draw.line(
        (round(width * 0.13), max(1, sill_y - 2), round(width * 0.78), max(1, sill_y - 2)),
        fill=high_vis,
        width=1,
    )

    if any(token in cue for token in ("pump", "foam", "tanker", "compartment", "locker", "support", "wildfire")):
        top = round(height * 0.29)
        bottom = round(height * 0.66)
        left = round(width * 0.10)
        right = round(width * 0.68)
        sections = 4 if width >= 120 else 3
        for index in range(1, sections):
            x = round(left + (right - left) * index / sections)
            draw.line((x, top, x, bottom), fill=ink, width=1)
            draw.rounded_rectangle((x - 1, top + 3, x + 1, top + 4), radius=1, fill=steel)
        draw.line((left, top, right, top), fill=steel, width=1)
        draw.line((left, bottom, right, bottom), fill=service_tone, width=1)

    if "command" in cue:
        window = (round(width * 0.20), round(height * 0.30), round(width * 0.47), round(height * 0.47))
        draw.rounded_rectangle(window, radius=max(1, height // 35), fill=(20, 39, 49, 185), outline=glass, width=1)
        for fraction in (0.56, 0.61, 0.66):
            x = round(width * fraction)
            draw.line((x, round(height * 0.20), x, round(height * 0.30)), fill=steel, width=1)

    if "cylinder" in cue:
        y1, y2 = round(height * 0.34), round(height * 0.61)
        for fraction in (0.28, 0.35, 0.42, 0.49):
            x = round(width * fraction)
            draw.rounded_rectangle((x - 2, y1, x + 2, y2), radius=2, fill=(68, 82, 91, 205), outline=steel, width=1)

    if "manifold" in cue:
        y = round(height * 0.57)
        for index in range(4):
            x = round(width * (0.27 + index * 0.055))
            draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(28, 38, 45, 220), outline=high_vis, width=1)

    if "tactical" in cue:
        draw.rectangle(
            (round(width * 0.25), round(height * 0.42), round(width * 0.68), round(height * 0.58)),
            fill=(18, 27, 33, 150),
            outline=service_tone,
            width=1,
        )
        for fraction in (0.36, 0.49, 0.62):
            x = round(width * fraction)
            draw.line((x, round(height * 0.43), x, round(height * 0.57)), fill=steel, width=1)

    if "critical-care" in cue:
        cross_x, cross_y = round(width * 0.54), round(height * 0.44)
        draw.rectangle((cross_x - 1, cross_y - 5, cross_x + 1, cross_y + 5), fill=service_tone)
        draw.rectangle((cross_x - 5, cross_y - 1, cross_x + 5, cross_y + 1), fill=service_tone)
        draw.line((round(width * 0.20), round(height * 0.28), round(width * 0.72), round(height * 0.28)), fill=glass, width=1)

    if "structure" in cue:
        rail_y = round(height * 0.35)
        draw.line((round(width * 0.16), rail_y, round(width * 0.78), rail_y), fill=steel, width=2)
        for fraction in (0.23, 0.42, 0.61, 0.76):
            x = round(width * fraction)
            draw.line((x, rail_y - 4, x, rail_y + 5), fill=ink, width=1)
        draw.line((round(width * 0.12), round(height * 0.73), round(width * 0.88), round(height * 0.73)), fill=service_tone, width=1)

    if "rapid-intervention" in cue:
        draw.line((round(width * 0.25), round(height * 0.24), round(width * 0.66), round(height * 0.24)), fill=steel, width=1)
        draw.rectangle((round(width * 0.42), round(height * 0.35), round(width * 0.58), round(height * 0.50)), fill=(26, 37, 44, 135), outline=high_vis, width=1)

    if "mountain" in cue:
        draw.line((round(width * 0.18), round(height * 0.25), round(width * 0.78), round(height * 0.25)), fill=steel, width=1)
        for fraction in (0.24, 0.46, 0.68):
            x = round(width * fraction)
            draw.ellipse((x - 2, round(height * 0.22), x + 2, round(height * 0.27)), fill=service_tone)

    polished = clipped_overlay(result, overlay)
    polished.putalpha(image.getchannel("A"))
    return polished


def marine_redraw(image: Image.Image, cue: str) -> Image.Image:
    """Re-ink lifeboat hull, tubes, cabin glazing and navigation fixtures."""
    result = crisp_tone(image.convert("RGBA"))
    width, height = result.size
    overlay = Image.new("RGBA", result.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    navy = (8, 42, 74, 220)
    orange = (241, 76, 29, 225)
    yellow = (249, 211, 37, 215)
    steel = (211, 224, 232, 180)
    glass = (63, 121, 150, 160)

    waterline = round(height * (0.72 if "all-weather" in cue else 0.69))
    draw.line((round(width * 0.05), waterline, round(width * 0.96), waterline), fill=navy, width=2)
    draw.line((round(width * 0.08), waterline - 2, round(width * 0.92), waterline - 2), fill=yellow, width=1)

    if "inshore" in cue:
        for fraction in (0.19, 0.34, 0.49, 0.65, 0.80):
            x = round(width * fraction)
            draw.arc((x - 6, round(height * 0.47), x + 6, round(height * 0.69)), 190, 350, fill=steel, width=1)
        draw.line((round(width * 0.20), round(height * 0.43), round(width * 0.78), round(height * 0.43)), fill=orange, width=1)
        draw.rounded_rectangle(
            (round(width * 0.42), round(height * 0.23), round(width * 0.55), round(height * 0.39)),
            radius=2,
            fill=glass,
            outline=steel,
            width=1,
        )
    else:
        cabin = (round(width * 0.37), round(height * 0.25), round(width * 0.74), round(height * 0.52))
        draw.rounded_rectangle(cabin, radius=2, fill=(21, 76, 102, 105), outline=steel, width=1)
        for fraction in (0.45, 0.53, 0.61, 0.69):
            x = round(width * fraction)
            draw.line((x, cabin[1] + 1, x, cabin[3] - 1), fill=steel, width=1)
        draw.line((round(width * 0.20), round(height * 0.57), round(width * 0.88), round(height * 0.57)), fill=orange, width=2)
        draw.line((round(width * 0.43), round(height * 0.16), round(width * 0.68), round(height * 0.16)), fill=steel, width=1)

    polished = clipped_overlay(result, overlay)
    polished.putalpha(image.getchannel("A"))
    return polished


def half_zoom_changed_pixels(before: Image.Image, after: Image.Image) -> int:
    size = (max(1, round(before.width * 0.5)), max(1, round(before.height * 0.5)))
    left = before.resize(size, Image.Resampling.LANCZOS).convert("RGBA")
    right = after.resize(size, Image.Resampling.LANCZOS).convert("RGBA")
    difference = ImageChops.difference(left, right).convert("RGB")
    return sum(1 for pixel in difference.get_flattened_data() if max(pixel) >= 8)


def build(destination: Path) -> dict:
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "data" / "prototypes.json").read_text(encoding="utf-8"))
    vehicles = {item["id"]: item for item in manifest["vehicles"]}
    legacy = json.loads((ROOT / str(profile["legacy_master_report"])).read_text(encoding="utf-8"))
    legacy_details = {item["id"]: item for item in legacy["vehicles"]}
    redraws = dict(profile["redraw_master_cues"])
    marine = dict(profile["marine_master_cues"])
    destination.mkdir(parents=True, exist_ok=True)
    for old in destination.glob("*.png"):
        old.unlink()

    generated: list[dict] = []
    for asset_id in sorted({*redraws, *marine}):
        source_path = STANDARD_DIR / f"{asset_id}.png"
        with Image.open(source_path) as source:
            original = crop_to_alpha(source, padding=1)
        if asset_id in redraws:
            family = "redraw"
            cue = redraws[asset_id]
            output = ground_redraw(original, cue, str(vehicles[asset_id]["service"]))
        else:
            family = "marine"
            cue = marine[asset_id]
            output = marine_redraw(original, cue)
        if output.size != original.size or output.getchannel("A").tobytes() != original.getchannel("A").tobytes():
            raise ValueError(f"{asset_id} redraw changed its anchor silhouette")
        changed_half = half_zoom_changed_pixels(original, output)
        minimum = int(profile["qa"]["minimum_redraw_half_zoom_changed_pixels"])
        if changed_half < minimum:
            raise ValueError(f"{asset_id} redraw is not visible at half zoom: {changed_half} < {minimum}")
        target = destination / f"{asset_id}.png"
        output.save(target, format="PNG", optimize=True, compress_level=9)
        generated.append(
            {
                "slot": int(vehicles[asset_id]["missionchief_slot"]),
                "id": asset_id,
                "family": family,
                "cue": cue,
                "service": str(vehicles[asset_id]["service"]),
                "source": str(source_path.relative_to(ROOT)),
                "target": str((OUTPUT_DIR / f"{asset_id}.png").relative_to(ROOT)),
                "original_dimensions": {"width": original.width, "height": original.height},
                "master_dimensions": {"width": output.width, "height": output.height},
                "content_offset": {"x": 0, "y": 0},
                "light_transform": {"x_scale": 1.0, "x_offset": 0.0, "y_scale": 1.0, "y_offset": 0.0},
                "half_zoom_added_alpha_pixels": 0,
                "half_zoom_changed_pixels": changed_half,
                "alpha_silhouette_preserved": True,
                "sha256": sha256(target),
            }
        )

    combined = [legacy_details[asset_id] for asset_id in sorted(legacy_details)] + generated
    configured = set(profile["baked_master_cues"])
    actual = {item["id"] for item in combined}
    if actual != configured:
        raise ValueError(
            f"combined master inventory mismatch: missing={sorted(configured - actual)}, unexpected={sorted(actual - configured)}"
        )
    combined.sort(key=lambda item: int(item["slot"]))
    return {
        "release": profile["release"],
        "masters": len(combined),
        "legacy_masters": len(legacy_details),
        "redraw_masters": len(redraws),
        "marine_masters": len(marine),
        "all_redraws_preserve_anchor_silhouettes": True,
        "protected_service_marks_added": False,
        "vehicles": combined,
        "all_passed": len(generated) == len(redraws) + len(marine),
    }


def check() -> None:
    if not REPORT_PATH.is_file():
        raise SystemExit(f"missing committed master report: {REPORT_PATH.relative_to(ROOT)}")
    committed = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="v1.4-masters-") as temp:
        generated = build(Path(temp))
        expected_new = set(json.loads(PROFILE_PATH.read_text(encoding="utf-8"))["redraw_master_cues"]) | set(
            json.loads(PROFILE_PATH.read_text(encoding="utf-8"))["marine_master_cues"]
        )
        actual_new = {path.stem for path in OUTPUT_DIR.glob("*.png")}
        if actual_new != expected_new:
            raise SystemExit(f"committed v1.4 master inventory mismatch: {sorted(actual_new ^ expected_new)}")
        for asset_id in sorted(expected_new):
            if (Path(temp) / f"{asset_id}.png").read_bytes() != (OUTPUT_DIR / f"{asset_id}.png").read_bytes():
                raise SystemExit(f"deterministic v1.4 master mismatch: {asset_id}")
        if generated != committed:
            raise SystemExit("deterministic v1.4 master report mismatch")
    print(json.dumps({"status": "PASS", "masters": committed["masters"]}, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> None:
    if parse_args().check:
        check()
        return
    report = build(OUTPUT_DIR)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
