#!/usr/bin/env python3
"""Build the v2.1.0 UK-family conversion master layer.

The release inherits every approved v2.0.4 cab and mounted-carrier repair
byte-for-byte, then replaces only the eleven assets identified by the family
hero audit. Generated source art is deliberately retained on a magenta key so
the alpha extraction, scaling and native export remain reproducible.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

from process_v2_generated import (
    extract_chroma,
    fit_to_canvas,
    validate_chroma_screen,
    vehicle_record,
)
from v2_profile import (
    CAB_OVERRIDE_IDS,
    EXPECTED_OVERRIDE_IDS,
    FAMILY_CONVERSION_IDS,
    MASTER_DIR,
    MASTER_OVERRIDE_DIR,
    MOUNTED_CARRIER_IDS,
    PREVIOUS_OVERRIDE_DIR,
    PREVIEW_DIR,
    RELEASE_CANDIDATE,
    ROOT,
    compact_export,
)


SOURCE_DIR = ROOT / "assets" / "sources" / "v2.1.0"
REPORT = ROOT / "data" / "v2.1.0-family-conversion-report.json"
PREVIEW = PREVIEW_DIR / "family-conversions-before-after.png"
INHERITED_IDS = CAB_OVERRIDE_IDS | frozenset(MOUNTED_CARRIER_IDS)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def source_path(asset_id: str) -> Path:
    return SOURCE_DIR / f"{asset_id}-chroma.png"


def expected_master(asset_id: str) -> tuple[Image.Image, tuple[int, int, int, int]]:
    source = source_path(asset_id)
    if not source.exists():
        raise FileNotFoundError(f"Missing conversion source: {relative(source)}")
    extracted = extract_chroma(Image.open(source))
    validate_chroma_screen(extracted)
    record = vehicle_record(asset_id)
    return fit_to_canvas(extracted, asset_id, float(record["real_length_metres"]))


def inherit_previous_overrides(*, check: bool) -> list[dict]:
    records: list[dict] = []
    MASTER_OVERRIDE_DIR.mkdir(parents=True, exist_ok=True)
    for asset_id in sorted(INHERITED_IDS):
        source = PREVIOUS_OVERRIDE_DIR / f"{asset_id}.png"
        target = MASTER_OVERRIDE_DIR / f"{asset_id}.png"
        if not source.exists():
            raise FileNotFoundError(f"Missing inherited override: {relative(source)}")
        if check:
            if not target.exists() or sha256(target) != sha256(source):
                raise RuntimeError(f"Inherited override drift: {asset_id}")
        else:
            shutil.copyfile(source, target)
        records.append(
            {
                "asset_id": asset_id,
                "source": relative(source),
                "master": relative(target),
                "sha256": sha256(source),
                "byte_preserved": target.exists() and sha256(target) == sha256(source),
            }
        )
    return records


def build_conversions(*, check: bool) -> list[dict]:
    records: list[dict] = []
    MASTER_OVERRIDE_DIR.mkdir(parents=True, exist_ok=True)
    for asset_id in FAMILY_CONVERSION_IDS:
        canvas, bbox = expected_master(asset_id)
        target = MASTER_OVERRIDE_DIR / f"{asset_id}.png"
        if check:
            if not target.exists():
                raise RuntimeError(f"Missing conversion master: {asset_id}")
            actual = Image.open(target).convert("RGBA")
            if ImageChops.difference(actual, canvas).getbbox() is not None:
                raise RuntimeError(f"Conversion master drift: {asset_id}")
        else:
            canvas.save(target, optimize=True)
        records.append(
            {
                "asset_id": asset_id,
                "source": relative(source_path(asset_id)),
                "source_sha256": sha256(source_path(asset_id)),
                "master": relative(target),
                "master_sha256": sha256(target),
                "master_bbox": list(bbox),
                "native_export_bbox": list(compact_export(canvas).getchannel("A").getbbox()),
            }
        )
    return records


def render_preview(records: list[dict]) -> None:
    columns = 3
    tile_width, tile_height = 260, 158
    rows = (len(records) + columns - 1) // columns
    board = Image.new("RGB", (columns * tile_width, rows * tile_height), (28, 32, 37))
    draw = ImageDraw.Draw(board)
    for index, record in enumerate(records):
        asset_id = record["asset_id"]
        left = (index % columns) * tile_width
        top = (index // columns) * tile_height
        draw.text((left + 10, top + 8), asset_id, fill=(235, 240, 244))
        draw.text((left + 12, top + 28), "v2.0.4", fill=(146, 154, 164))
        draw.text((left + 142, top + 28), "v2.1.0", fill=(91, 205, 142))
        before = compact_export(Image.open(MASTER_DIR / f"{asset_id}.png").convert("RGBA"))
        after = compact_export(Image.open(MASTER_OVERRIDE_DIR / f"{asset_id}.png").convert("RGBA"))
        board.paste(before, (left + 5, top + 42), before)
        board.paste(after, (left + 135, top + 42), after)
    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    board.save(PREVIEW, optimize=True)


def validate_override_scope() -> None:
    actual = {path.stem for path in MASTER_OVERRIDE_DIR.glob("*.png")}
    if actual != EXPECTED_OVERRIDE_IDS:
        raise RuntimeError(
            "Override scope mismatch: "
            f"missing={sorted(EXPECTED_OVERRIDE_IDS - actual)},"
            f"extra={sorted(actual - EXPECTED_OVERRIDE_IDS)}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    inherited = inherit_previous_overrides(check=args.check)
    conversions = build_conversions(check=args.check)
    validate_override_scope()

    if not args.check:
        render_preview(conversions)
        payload = {
            "release": RELEASE_CANDIDATE,
            "all_passed": True,
            "inherited_override_count": len(inherited),
            "conversion_count": len(conversions),
            "override_count": len(EXPECTED_OVERRIDE_IDS),
            "inherited_overrides": inherited,
            "conversions": conversions,
            "previews": [relative(PREVIEW)],
        }
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps(payload, indent=2) + "\n")

    print(
        f"release={RELEASE_CANDIDATE} inherited={len(inherited)} "
        f"converted={len(conversions)} overrides={len(EXPECTED_OVERRIDE_IDS)} "
        f"mode={'check' if args.check else 'build'}"
    )


if __name__ == "__main__":
    main()
