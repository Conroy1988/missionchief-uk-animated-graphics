#!/usr/bin/env python3
"""Build or verify all compact v2 static exports from preserved 200px masters."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops

from v2_profile import (
    EXPORT_CANVAS,
    EXPORT_SCALE,
    MASTER_CANVAS,
    MASTER_DIR,
    RELEASE,
    RELEASE_CANDIDATE,
    ROOT,
    STATIC_DIR,
    compact_export,
)


SLOTS = json.loads((ROOT / "data/vehicle-slots.json").read_text())["slots"]
REPORT = ROOT / f"data/{RELEASE}-scale-report.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def images_equal(left: Image.Image, right: Image.Image) -> bool:
    return (
        left.mode == right.mode
        and left.size == right.size
        and ImageChops.difference(left, right).getbbox() is None
    )


def build(check: bool) -> dict:
    expected_ids = {slot["asset_id"] for slot in SLOTS}
    actual_master_ids = {path.stem for path in MASTER_DIR.glob("*.png")}
    entries: list[dict] = []
    errors: list[str] = []

    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    for slot in SLOTS:
        asset_id = slot["asset_id"]
        master_path = MASTER_DIR / f"{asset_id}.png"
        export_path = STATIC_DIR / f"{asset_id}.png"
        if not master_path.exists():
            errors.append(f"missing-master/{asset_id}")
            continue

        with Image.open(master_path) as source_image:
            source = source_image.convert("RGBA")
            source_bbox = source.getchannel("A").getbbox()
            if source.size != MASTER_CANVAS:
                errors.append(f"master-canvas/{asset_id}={source.size}")
                continue
            expected = compact_export(source)

        if check:
            if not export_path.exists():
                errors.append(f"missing-export/{asset_id}")
                continue
            with Image.open(export_path) as actual_image:
                actual = actual_image.convert("RGBA")
            if not images_equal(actual, expected):
                errors.append(f"stale-export/{asset_id}")
        else:
            expected.save(export_path, optimize=True)

        output = expected if not check else actual
        output_bbox = output.getchannel("A").getbbox()
        entries.append(
            {
                "slot": slot["slot"],
                "asset_id": asset_id,
                "master_canvas": list(MASTER_CANVAS),
                "master_bbox": list(source_bbox) if source_bbox else None,
                "export_canvas": list(EXPORT_CANVAS),
                "export_bbox": list(output_bbox) if output_bbox else None,
                "master_sha256": sha256(master_path),
                "export_sha256": sha256(export_path) if export_path.exists() else None,
            }
        )

    actual_export_ids = {path.stem for path in STATIC_DIR.glob("*.png")}
    missing_masters = sorted(expected_ids - actual_master_ids)
    extra_masters = sorted(actual_master_ids - expected_ids)
    missing_exports = sorted(expected_ids - actual_export_ids)
    extra_exports = sorted(actual_export_ids - expected_ids)
    errors.extend(f"missing-master/{item}" for item in missing_masters)
    errors.extend(f"extra-master/{item}" for item in extra_masters)
    errors.extend(f"missing-export/{item}" for item in missing_exports)
    errors.extend(f"extra-export/{item}" for item in extra_exports)

    result = {
        "release": RELEASE_CANDIDATE,
        "master_canvas": list(MASTER_CANVAS),
        "export_canvas": list(EXPORT_CANVAS),
        "scale": EXPORT_SCALE,
        "expected_assets": len(expected_ids),
        "master_assets": len(actual_master_ids),
        "export_assets": len(actual_export_ids),
        "all_passed": not errors and len(entries) == len(expected_ids),
        "errors": sorted(set(errors)),
        "entries": entries,
    }
    if not check:
        REPORT.write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if committed compact exports are stale")
    args = parser.parse_args()

    result = build(args.check)
    print(
        json.dumps(
            {
                key: result[key]
                for key in (
                    "master_canvas",
                    "export_canvas",
                    "scale",
                    "expected_assets",
                    "master_assets",
                    "export_assets",
                    "all_passed",
                    "errors",
                )
            },
            indent=2,
        )
    )
    if not result["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
