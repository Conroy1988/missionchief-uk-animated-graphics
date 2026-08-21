#!/usr/bin/env python3
"""Audit or enforce the UK-family authenticity and hero-grade v2 gate.

The gate combines deterministic image checks with a curated family brief.  It
does not pretend that pixel statistics can replace art direction: family
affinity and cross-family silhouette reuse are measured against explicitly
selected hero references, and the report exposes every decision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import textwrap
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageStat

from v2_profile import (
    EXPORT_CANVAS,
    MASTER_CANVAS,
    PREVIEW_DIR,
    RELEASE,
    RELEASE_CANDIDATE,
    ROOT,
    STATIC_DIR,
    compact_export,
    master_path,
)
from v2_uk_family_standard import (
    ASSIGNMENTS,
    FAMILIES,
    FORBIDDEN_SHORTCUTS,
    SCHEMA_VERSION,
)


SLOTS = json.loads((ROOT / "data/vehicle-slots.json").read_text())["slots"]
PROTOTYPES = {
    vehicle["id"]: vehicle
    for vehicle in json.loads((ROOT / "data/prototypes.json").read_text())["vehicles"]
}
REPORT = ROOT / f"data/{RELEASE}-uk-family-hero-report.json"
AUDIT_BOARD = PREVIEW_DIR / "uk-family-hero-audit.png"
REFERENCE_BOARD = PREVIEW_DIR / "uk-family-reference-board.png"
HERO_SCORE_THRESHOLD = 100
CROSS_FAMILY_SILHOUETTE_THRESHOLD = 0.977
FORBIDDEN_BRIEF_WORDS = ("generic", "recolour", "color-only", "colour-only")
ROAD_PROPULSION = {"self-propelled-road", "towed-road", "cycle"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def alpha_signature(image: Image.Image, size: int = 64) -> Image.Image:
    """Normalise a subject without destroying its width/height relationship."""

    alpha = image.convert("RGBA").getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        return Image.new("L", (size, size), 0)
    subject = alpha.crop(bbox)
    usable = size - 4
    scale = min(usable / subject.width, usable / subject.height)
    resized = subject.resize(
        (max(1, round(subject.width * scale)), max(1, round(subject.height * scale))),
        Image.Resampling.BILINEAR,
    )
    signature = Image.new("L", (size, size), 0)
    signature.paste(resized, ((size - resized.width) // 2, size - 2 - resized.height))
    return signature


def silhouette_similarity(left: Image.Image, right: Image.Image) -> float:
    difference = ImageChops.difference(left, right)
    distance = sum(difference.get_flattened_data()) / (255 * left.width * left.height)
    return round(1.0 - distance, 4)


def image_metrics(image: Image.Image) -> dict:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        return {
            "bbox": None,
            "opaque_pixels": 0,
            "quantized_colours": 0,
            "luminance_stddev": 0.0,
            "edge_density": 0.0,
            "dark_structure_pixels": 0,
        }

    opaque_mask = alpha.point(lambda value: 255 if value >= 160 else 0)
    opaque_pixels = sum(value == 255 for value in opaque_mask.get_flattened_data())
    quantized_colours = {
        (red // 16, green // 16, blue // 16)
        for red, green, blue, opacity in rgba.get_flattened_data()
        if opacity >= 160
    }
    luminance = rgba.convert("L")
    luminance_stddev = ImageStat.Stat(luminance, opaque_mask).stddev[0]
    edges = luminance.filter(ImageFilter.FIND_EDGES)
    edge_pixels = sum(
        edge >= 36 and mask == 255
        for edge, mask in zip(
            edges.get_flattened_data(), opaque_mask.get_flattened_data(), strict=True
        )
    )

    left, top, right, bottom = bbox
    structural_region = rgba.crop(
        (
            left + (right - left) // 2,
            top + (bottom - top) // 3,
            right,
            bottom,
        )
    )
    dark_structure_pixels = sum(
        opacity >= 160 and red < 86 and green < 96 and blue < 108
        for red, green, blue, opacity in structural_region.get_flattened_data()
    )
    return {
        "bbox": list(bbox),
        "bbox_width": right - left,
        "bbox_height": bottom - top,
        "opaque_pixels": opaque_pixels,
        "quantized_colours": len(quantized_colours),
        "luminance_stddev": round(luminance_stddev, 2),
        "edge_density": round(edge_pixels / opaque_pixels, 4) if opaque_pixels else 0.0,
        "dark_structure_pixels": dark_structure_pixels,
    }


def score_checks(
    *,
    master: Image.Image,
    export: Image.Image,
    metrics: dict,
    family: dict,
) -> tuple[int, list[dict], list[str]]:
    """Return a transparent ten-part score and fail-closed technical errors."""

    alpha = master.getchannel("A") if "A" in master.getbands() else None
    bbox = tuple(metrics["bbox"]) if metrics["bbox"] else None
    minimum_width, minimum_height = family["minimum_master_bbox"]
    propulsion = family["propulsion"]
    expected_export = compact_export(master.convert("RGBA")) if master.size == MASTER_CANVAS else None
    checks: list[dict] = []
    errors: list[str] = []

    def record(name: str, passed: bool, evidence: str, *, hard: bool = False) -> None:
        checks.append({"name": name, "passed": passed, "points": 10 if passed else 0, "evidence": evidence})
        if hard and not passed:
            errors.append(name)

    record(
        "master-contract",
        master.mode == "RGBA" and master.size == MASTER_CANVAS,
        f"mode={master.mode},canvas={master.size}",
        hard=True,
    )
    alpha_extrema = alpha.getextrema() if alpha else None
    record(
        "genuine-transparency",
        alpha_extrema == (0, 255),
        f"alpha_extrema={alpha_extrema}",
        hard=True,
    )
    record(
        "safe-canvas-bounds",
        bool(bbox) and bbox[0] >= 3 and bbox[1] >= 3 and bbox[2] <= 197 and bbox[3] <= 191,
        f"bbox={bbox}",
        hard=True,
    )
    record(
        "family-scale-envelope",
        bool(bbox)
        and metrics["bbox_width"] >= minimum_width
        and metrics["bbox_height"] >= minimum_height,
        f"bbox={metrics.get('bbox_width')}x{metrics.get('bbox_height')},minimum={minimum_width}x{minimum_height}",
        hard=True,
    )
    baseline_passed = bool(bbox) and 178 <= bbox[3] <= 190
    record("grounded-baseline", baseline_passed, f"bottom={bbox[3] if bbox else None}", hard=True)
    export_matches = (
        export.mode == "RGBA"
        and export.size == EXPORT_CANVAS
        and expected_export is not None
        and ImageChops.difference(export, expected_export).getbbox() is None
    )
    record(
        "deterministic-native-export",
        export_matches,
        f"mode={export.mode},canvas={export.size},matches_master={export_matches}",
        hard=True,
    )
    record(
        "tonal-separation",
        metrics["luminance_stddev"] >= 34,
        f"luminance_stddev={metrics['luminance_stddev']},minimum=34",
    )
    record(
        "colour-and-material-separation",
        metrics["quantized_colours"] >= 24,
        f"quantized_colours={metrics['quantized_colours']},minimum=24",
    )
    record(
        "structural-edge-density",
        metrics["edge_density"] >= 0.045,
        f"edge_density={metrics['edge_density']},minimum=0.045",
    )
    structure_minimum = 18 if propulsion in ROAD_PROPULSION else 0
    record(
        "readable-structure-at-front-or-running-gear",
        metrics["dark_structure_pixels"] >= structure_minimum,
        f"dark_structure_pixels={metrics['dark_structure_pixels']},minimum={structure_minimum}",
    )
    return sum(check["points"] for check in checks), checks, errors


def validate_specification() -> list[str]:
    errors: list[str] = []
    expected_ids = [slot["asset_id"] for slot in SLOTS]
    actual_ids = list(ASSIGNMENTS)
    if actual_ids != expected_ids:
        errors.append(
            "assignment-order-or-parity="
            f"missing:{sorted(set(expected_ids) - set(actual_ids))},"
            f"extra:{sorted(set(actual_ids) - set(expected_ids))}"
        )
    if set(PROTOTYPES) != set(expected_ids):
        errors.append("prototype-parity")

    referenced_assets: set[str] = set()
    for family_id, family in FAMILIES.items():
        reference = family["reference_asset"]
        referenced_assets.add(reference)
        if reference not in ASSIGNMENTS:
            errors.append(f"family/{family_id}/missing-reference={reference}")
        elif ASSIGNMENTS[reference][0] != family_id:
            errors.append(f"family/{family_id}/foreign-reference={reference}")
        if len(family["required_cues"]) < 5:
            errors.append(f"family/{family_id}/insufficient-required-cues")
        if len(family["visual_lineage"].split()) < 8:
            errors.append(f"family/{family_id}/weak-visual-lineage")

    for asset_id, (family_id, brief) in ASSIGNMENTS.items():
        if family_id not in FAMILIES:
            errors.append(f"asset/{asset_id}/unknown-family={family_id}")
        if len(brief.split()) < 7:
            errors.append(f"asset/{asset_id}/weak-role-brief")
        lowered = brief.lower()
        for word in FORBIDDEN_BRIEF_WORDS:
            if word in lowered:
                errors.append(f"asset/{asset_id}/forbidden-brief-word={word}")

    unused_families = set(FAMILIES) - {family for family, _ in ASSIGNMENTS.values()}
    if unused_families:
        errors.append(f"unused-families={sorted(unused_families)}")
    duplicate_references = len(referenced_assets) != len(FAMILIES)
    if duplicate_references:
        errors.append("family-reference-assets-not-unique")
    return errors


def render_audit_board(entries: list[dict]) -> None:
    columns = 6
    tile_width, tile_height = 186, 172
    header_height = 68
    rows = (len(entries) + columns - 1) // columns
    board = Image.new("RGB", (columns * tile_width, header_height + rows * tile_height), (30, 35, 40))
    draw = ImageDraw.Draw(board)
    font = ImageFont.load_default()
    draw.text((12, 10), f"{RELEASE} · UK vehicle-family authenticity × hero-grade gate", fill=(255, 255, 255), font=font)
    draw.text((12, 29), "Green = hero-ready · amber = family conversion required · red = technical failure", fill=(197, 207, 215), font=font)
    draw.text((12, 47), "Every sprite is shown on its actual 110×110 MissionChief canvas.", fill=(148, 162, 173), font=font)

    for index, entry in enumerate(entries):
        x = (index % columns) * tile_width
        y = header_height + (index // columns) * tile_height
        if entry["technical_errors"]:
            border = (224, 71, 68)
            status = "TECH FAIL"
        elif entry["hero_ready"]:
            border = (68, 190, 118)
            status = "HERO"
        else:
            border = (232, 167, 54)
            status = "CONVERT"
        tile = Image.new("RGB", (tile_width, tile_height), (48, 54, 60))
        tile_draw = ImageDraw.Draw(tile)
        sprite_path = STATIC_DIR / f"{entry['asset_id']}.png"
        if sprite_path.exists():
            sprite = Image.open(sprite_path).convert("RGBA")
            tile.paste(sprite, ((tile_width - EXPORT_CANVAS[0]) // 2, 23), sprite)
        else:
            tile_draw.line((38, 35, tile_width - 38, 125), fill=(224, 71, 68), width=4)
            tile_draw.line((tile_width - 38, 35, 38, 125), fill=(224, 71, 68), width=4)
        tile_draw.rectangle((0, 0, tile_width - 1, tile_height - 1), outline=border, width=2)
        tile_draw.text((6, 5), f"{entry['slot']:03d} · {entry['label'][:24]}", fill=(246, 248, 250), font=font)
        tile_draw.text((6, 137), entry["family"], fill=(168, 181, 191), font=font)
        tile_draw.text((6, 153), f"{status} · {entry['quality_score']}/100 · affinity {entry['reference_similarity']:.3f}", fill=border, font=font)
        board.paste(tile, (x, y))

    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    board.save(AUDIT_BOARD, compress_level=6)


def render_reference_board(entries_by_id: dict[str, dict]) -> None:
    columns = 3
    tile_width, tile_height = 390, 186
    header_height = 64
    family_items = list(FAMILIES.items())
    rows = (len(family_items) + columns - 1) // columns
    board = Image.new("RGB", (columns * tile_width, header_height + rows * tile_height), (25, 30, 35))
    draw = ImageDraw.Draw(board)
    font = ImageFont.load_default()
    draw.text((12, 10), "UK family hero references · one morphology target per platform family", fill=(255, 255, 255), font=font)
    draw.text((12, 29), "Original, logo-free designs; manufacturer cues are proportion-level only.", fill=(185, 196, 205), font=font)
    draw.text((12, 46), f"{len(FAMILIES)} families · {len(ASSIGNMENTS)} mapped MissionChief slots", fill=(143, 158, 169), font=font)

    for index, (family_id, family) in enumerate(family_items):
        x = (index % columns) * tile_width
        y = header_height + (index // columns) * tile_height
        reference = family["reference_asset"]
        entry = entries_by_id[reference]
        tile = Image.new("RGB", (tile_width, tile_height), (45, 51, 57))
        tile_draw = ImageDraw.Draw(tile)
        sprite_path = STATIC_DIR / f"{reference}.png"
        if sprite_path.exists():
            sprite = Image.open(sprite_path).convert("RGBA")
            tile.paste(sprite, (10, 35), sprite)
        else:
            tile_draw.line((15, 40, 115, 140), fill=(224, 71, 68), width=4)
            tile_draw.line((115, 40, 15, 140), fill=(224, 71, 68), width=4)
        tile_draw.rectangle((0, 0, tile_width - 1, tile_height - 1), outline=(78, 157, 209), width=2)
        tile_draw.text((8, 7), family["name"], fill=(248, 250, 252), font=font)
        tile_draw.text((8, 21), family_id, fill=(128, 181, 217), font=font)
        tile_draw.text((128, 46), f"REFERENCE · slot {entry['slot']:03d}", fill=(84, 202, 137), font=font)
        tile_draw.text((128, 64), entry["label"], fill=(245, 247, 249), font=font)
        tile_draw.text((128, 84), f"quality {entry['quality_score']}/100", fill=(185, 196, 205), font=font)
        for line_number, line in enumerate(textwrap.wrap(family["visual_lineage"], width=42)[:3]):
            tile_draw.text((128, 108 + line_number * 15), line, fill=(167, 178, 187), font=font)
        board.paste(tile, (x, y))

    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    board.save(REFERENCE_BOARD, compress_level=6)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--audit",
        action="store_true",
        help="write full evidence but do not fail solely because family conversions remain",
    )
    args = parser.parse_args()

    specification_errors = validate_specification()
    signatures: dict[str, Image.Image] = {}
    preliminary: dict[str, dict] = {}

    for slot in SLOTS:
        asset_id = slot["asset_id"]
        family_id, role_brief = ASSIGNMENTS[asset_id]
        family = FAMILIES[family_id]
        source_path = master_path(asset_id)
        export_path = STATIC_DIR / f"{asset_id}.png"
        local_errors: list[str] = []
        if not source_path.exists():
            local_errors.append("missing-master")
        if not export_path.exists():
            local_errors.append("missing-static-export")
        if local_errors:
            preliminary[asset_id] = {
                "slot": slot["slot"],
                "asset_id": asset_id,
                "label": slot["label"],
                "family": family_id,
                "role_brief": role_brief,
                "quality_score": 0,
                "quality_checks": [],
                "technical_errors": local_errors,
            }
            continue

        master = Image.open(source_path)
        export = Image.open(export_path)
        metrics = image_metrics(master)
        try:
            quality_score, quality_checks, scoring_errors = score_checks(
                master=master,
                export=export,
                metrics=metrics,
                family=family,
            )
        except Exception as exc:
            quality_score = 0
            quality_checks = []
            scoring_errors = [f"scoring-exception:{exc}"]
        signatures[asset_id] = alpha_signature(master)
        prototype = PROTOTYPES[asset_id]
        preliminary[asset_id] = {
            "slot": slot["slot"],
            "asset_id": asset_id,
            "label": slot["label"],
            "service": prototype["service"],
            "real_length_metres": prototype["real_length_metres"],
            "family": family_id,
            "family_name": family["name"],
            "role_brief": role_brief,
            "is_family_reference": family["reference_asset"] == asset_id,
            "master": source_path.relative_to(ROOT).as_posix(),
            "master_sha256": sha256(source_path),
            "export": export_path.relative_to(ROOT).as_posix(),
            "export_sha256": sha256(export_path),
            "metrics": metrics,
            "quality_score": quality_score,
            "quality_checks": quality_checks,
            "technical_errors": scoring_errors,
        }
        master.close()
        export.close()

    cross_family_conflicts: list[dict] = []
    conflict_assets: set[str] = set()
    asset_ids = [slot["asset_id"] for slot in SLOTS if slot["asset_id"] in signatures]
    for index, left_id in enumerate(asset_ids):
        for right_id in asset_ids[index + 1 :]:
            left_family = ASSIGNMENTS[left_id][0]
            right_family = ASSIGNMENTS[right_id][0]
            if left_family == right_family:
                continue
            similarity = silhouette_similarity(signatures[left_id], signatures[right_id])
            if similarity >= CROSS_FAMILY_SILHOUETTE_THRESHOLD:
                conflict_assets.update((left_id, right_id))
                cross_family_conflicts.append(
                    {
                        "left_asset": left_id,
                        "left_family": left_family,
                        "right_asset": right_id,
                        "right_family": right_family,
                        "silhouette_similarity": similarity,
                        "reason": "cross-family morphology is too similar for a hero-grade distinction",
                    }
                )

    entries: list[dict] = []
    for slot in SLOTS:
        asset_id = slot["asset_id"]
        entry = preliminary[asset_id]
        family = FAMILIES[entry["family"]]
        reference_id = family["reference_asset"]
        if asset_id in signatures and reference_id in signatures:
            reference_similarity = silhouette_similarity(signatures[asset_id], signatures[reference_id])
        else:
            reference_similarity = 0.0
        family_errors: list[str] = []
        if reference_similarity < family["minimum_reference_similarity"]:
            family_errors.append(
                f"family-affinity={reference_similarity},minimum={family['minimum_reference_similarity']}"
            )
        if asset_id in conflict_assets:
            family_errors.append("cross-family-silhouette-conflict")
        if entry["quality_score"] < HERO_SCORE_THRESHOLD:
            family_errors.append(
                f"quality-score={entry['quality_score']},minimum={HERO_SCORE_THRESHOLD}"
            )
        hero_ready = not entry["technical_errors"] and not family_errors
        entry.update(
            {
                "family_reference": reference_id,
                "reference_similarity": reference_similarity,
                "minimum_reference_similarity": family["minimum_reference_similarity"],
                "family_errors": family_errors,
                "hero_ready": hero_ready,
            }
        )
        entries.append(entry)

    reference_failures = [
        family["reference_asset"]
        for family in FAMILIES.values()
        if not next(
            entry["hero_ready"]
            for entry in entries
            if entry["asset_id"] == family["reference_asset"]
        )
    ]
    if reference_failures:
        specification_errors.append(f"hero-reference-failures={reference_failures}")

    render_audit_board(entries)
    entries_by_id = {entry["asset_id"]: entry for entry in entries}
    render_reference_board(entries_by_id)

    family_summary: list[dict] = []
    for family_id, family in FAMILIES.items():
        members = [entry for entry in entries if entry["family"] == family_id]
        family_summary.append(
            {
                "family": family_id,
                "name": family["name"],
                "visual_lineage": family["visual_lineage"],
                "propulsion": family["propulsion"],
                "reference_asset": family["reference_asset"],
                "required_cues": family["required_cues"],
                "members": len(members),
                "hero_ready": sum(entry["hero_ready"] for entry in members),
                "conversion_required": [
                    entry["asset_id"] for entry in members if not entry["hero_ready"]
                ],
            }
        )

    technical_failures = [entry["asset_id"] for entry in entries if entry["technical_errors"]]
    conversion_backlog = [entry["asset_id"] for entry in entries if not entry["hero_ready"]]
    result = {
        "release": RELEASE_CANDIDATE,
        "schema_version": SCHEMA_VERSION,
        "mode": "audit" if args.audit else "enforce",
        "hero_score_threshold": HERO_SCORE_THRESHOLD,
        "cross_family_silhouette_threshold": CROSS_FAMILY_SILHOUETTE_THRESHOLD,
        "expected_assets": len(SLOTS),
        "mapped_assets": len(ASSIGNMENTS),
        "families": len(FAMILIES),
        "technical_passed": len(SLOTS) - len(technical_failures),
        "technical_failures": technical_failures,
        "hero_ready": len(SLOTS) - len(conversion_backlog),
        "conversion_required": len(conversion_backlog),
        "conversion_backlog": conversion_backlog,
        "specification_errors": specification_errors,
        "hero_reference_failures": reference_failures,
        "cross_family_conflicts": cross_family_conflicts,
        "forbidden_shortcuts": list(FORBIDDEN_SHORTCUTS),
        "previews": [
            AUDIT_BOARD.relative_to(ROOT).as_posix(),
            REFERENCE_BOARD.relative_to(ROOT).as_posix(),
        ],
        "technical_all_passed": not technical_failures and not specification_errors,
        "fleet_hero_ready": not conversion_backlog and not specification_errors,
        "family_summary": family_summary,
        "entries": entries,
    }
    REPORT.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "release",
                    "mode",
                    "expected_assets",
                    "mapped_assets",
                    "families",
                    "technical_passed",
                    "hero_ready",
                    "conversion_required",
                    "technical_all_passed",
                    "fleet_hero_ready",
                    "specification_errors",
                )
            },
            indent=2,
        )
    )
    print(f"report={REPORT.relative_to(ROOT)}")
    print(f"audit_board={AUDIT_BOARD.relative_to(ROOT)}")
    print(f"reference_board={REFERENCE_BOARD.relative_to(ROOT)}")

    if specification_errors or technical_failures:
        raise SystemExit(1)
    if conversion_backlog and not args.audit:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
