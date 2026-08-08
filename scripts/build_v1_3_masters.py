#!/usr/bin/env python3
"""Build deterministic baked v1.3 role-specific vehicle masters."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from pathlib import Path

from PIL import Image, ImageChops, ImageEnhance, ImageFilter

from build_v1_1_enhanced import (
    add_profiled_equipment,
    add_role_differentiation,
    crop_to_alpha,
)


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "data" / "v1.3-overhaul-profile.json"
STANDARD_DIR = ROOT / "assets" / "exports" / "standard" / "static"
OUTPUT_DIR = ROOT / "assets" / "masters" / "v1.3.0"
REPORT_PATH = ROOT / "data" / "v1.3.0-master-report.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def master_tone(image: Image.Image) -> Image.Image:
    """Recover crisp source detail before baking the role-specific silhouette."""
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    rgb = rgba.convert("RGB")
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=0.55, percent=105, threshold=2))
    rgb = ImageEnhance.Contrast(rgb).enhance(1.025)
    result = rgb.convert("RGBA")
    result.putalpha(alpha)
    return result


def final_crop(
    image: Image.Image,
    content_offset: tuple[int, int],
    original_size: tuple[int, int],
) -> tuple[Image.Image, tuple[int, int]]:
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        raise ValueError("generated master is empty")
    left, top, right, bottom = bbox
    left = max(0, left - 1)
    top = max(0, top - 1)
    right = min(image.width, right + 1)
    bottom = min(image.height, bottom + 1)
    cropped = image.crop((left, top, right, bottom))
    adjusted = (content_offset[0] - left, content_offset[1] - top)
    if adjusted[0] < 0 or adjusted[1] < 0:
        raise ValueError("master crop removed original vehicle content")
    if adjusted[0] + original_size[0] > cropped.width:
        raise ValueError("master crop clipped original vehicle width")
    if adjusted[1] + original_size[1] > cropped.height:
        raise ValueError("master crop clipped original vehicle height")
    return cropped, adjusted


def half_zoom_added_pixels(
    master: Image.Image,
    original: Image.Image,
    offset: tuple[int, int],
) -> int:
    original_alpha = Image.new("L", master.size, 0)
    original_alpha.paste(original.getchannel("A"), offset)
    added = ImageChops.subtract(master.getchannel("A"), original_alpha)
    reduced = added.resize(
        (max(1, round(master.width * 0.5)), max(1, round(master.height * 0.5))),
        Image.Resampling.LANCZOS,
    )
    return sum(1 for value in reduced.get_flattened_data() if value >= 48)


def build(destination: Path) -> dict:
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "data" / "prototypes.json").read_text(encoding="utf-8"))
    vehicles = {item["id"]: item for item in manifest["vehicles"]}
    cues = profile["baked_master_cues"]
    destination.mkdir(parents=True, exist_ok=True)
    for old in destination.glob("*.png"):
        old.unlink()

    results = []
    for asset_id in sorted(cues):
        specification = cues[asset_id]
        source_path = STANDARD_DIR / f"{asset_id}.png"
        with Image.open(source_path) as source:
            original = master_tone(crop_to_alpha(source, padding=1))

        family = str(specification["family"])
        cue = str(specification["cue"])
        service = str(vehicles[asset_id]["service"])
        if family == "role":
            generated, offset = add_role_differentiation(original, cue, service)
        elif family == "equipment":
            generated, offset, _metrics = add_profiled_equipment(original, cue, service)
        else:
            raise ValueError(f"unknown baked master family for {asset_id}: {family}")

        generated, offset = final_crop(generated, offset, original.size)
        target = destination / f"{asset_id}.png"
        generated.save(target, format="PNG", optimize=True, compress_level=9)
        added_half = half_zoom_added_pixels(generated, original, offset)
        if added_half < int(profile["qa"]["minimum_baked_master_half_zoom_pixels"]):
            raise ValueError(f"{asset_id} baked cue disappears at half zoom: {added_half}")

        results.append(
            {
                "slot": int(vehicles[asset_id]["missionchief_slot"]),
                "id": asset_id,
                "family": family,
                "cue": cue,
                "service": service,
                "source": str(source_path.relative_to(ROOT)),
                "target": str((OUTPUT_DIR / f"{asset_id}.png").relative_to(ROOT)),
                "original_dimensions": {"width": original.width, "height": original.height},
                "master_dimensions": {"width": generated.width, "height": generated.height},
                "content_offset": {"x": offset[0], "y": offset[1]},
                "light_transform": {
                    "x_scale": (original.width - 1) / max(1, generated.width - 1),
                    "x_offset": offset[0] / max(1, generated.width - 1),
                    "y_scale": (original.height - 1) / max(1, generated.height - 1),
                    "y_offset": offset[1] / max(1, generated.height - 1),
                },
                "half_zoom_added_alpha_pixels": added_half,
                "sha256": sha256(target),
            }
        )

    return {
        "release": profile["release"],
        "masters": len(results),
        "all_cues_baked_into_source_masters": True,
        "runtime_generated_roof_overlays": False,
        "vehicles": results,
        "all_passed": len(results) == len(cues),
    }


def check() -> None:
    if not REPORT_PATH.is_file():
        raise SystemExit(f"missing committed master report: {REPORT_PATH.relative_to(ROOT)}")
    committed = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="v1.3-masters-") as temp:
        generated = build(Path(temp))
        expected_ids = {item["id"] for item in generated["vehicles"]}
        actual_ids = {path.stem for path in OUTPUT_DIR.glob("*.png")}
        if actual_ids != expected_ids:
            raise SystemExit(
                json.dumps(
                    {
                        "error": "committed v1.3 master inventory mismatch",
                        "missing": sorted(expected_ids - actual_ids),
                        "unexpected": sorted(actual_ids - expected_ids),
                    },
                    indent=2,
                )
            )
        for item in generated["vehicles"]:
            generated_path = Path(temp) / f"{item['id']}.png"
            committed_path = OUTPUT_DIR / f"{item['id']}.png"
            if generated_path.read_bytes() != committed_path.read_bytes():
                raise SystemExit(f"deterministic master mismatch: {item['id']}")
        if generated != committed:
            raise SystemExit("deterministic v1.3 master report mismatch")
    print(json.dumps({"status": "PASS", "masters": len(committed["vehicles"])}, indent=2))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="rebuild in a temporary directory and compare bytes")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.check:
        check()
        return
    report = build(OUTPUT_DIR)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
