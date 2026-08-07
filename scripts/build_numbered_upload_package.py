#!/usr/bin/env python3
"""Build a slot-numbered MissionChief upload package without altering image bytes."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Any


INVALID_WINDOWS_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
MULTISPACE = re.compile(r"\s+")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
EXPECTED_SLOTS = 117
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_label(label: str) -> str:
    """Return a readable filename-safe representation of a MissionChief label."""
    cleaned = INVALID_WINDOWS_CHARS.sub("-", label)
    cleaned = MULTISPACE.sub(" ", cleaned).strip().rstrip(". ")
    cleaned = re.sub(r"\s*-\s*", "-", cleaned)
    return cleaned or "Unnamed vehicle"


def require_png(path: Path, description: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Missing {description}: {path}")
    with path.open("rb") as handle:
        if handle.read(len(PNG_SIGNATURE)) != PNG_SIGNATURE:
            raise ValueError(f"Invalid PNG signature for {description}: {path}")


def copy_exact(source: Path, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    source_hash = sha256(source)
    destination_hash = sha256(destination)
    if source_hash != destination_hash:
        raise RuntimeError(f"Byte verification failed: {source} -> {destination}")
    return source_hash


def add_deterministic_zip_member(archive: zipfile.ZipFile, path: Path, archive_name: Path) -> None:
    """Write one file with stable metadata so identical inputs yield an identical archive."""
    info = zipfile.ZipInfo(str(archive_name).replace("\\", "/"), date_time=ZIP_EPOCH)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = (0o100644 & 0xFFFF) << 16
    archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def write_readme(package_root: Path, version: str, profile: str) -> None:
    frame_description = "twelve-frame" if profile == "command" else "six-frame"
    content = f"""# TKB UK Emergency Fleet — Numbered MissionChief Upload Package

Release: {version}
Profile: {profile}
MissionChief pack: 5897 — TKB UK Fleet — Animated
Vehicle slots: {EXPECTED_SLOTS}

## Folder layout

- `01 - Static/` — the normal/non-response PNG for every slot.
- `02 - Animated/` — the {frame_description} response APNG for every slot.
- `UPLOAD-GUIDE.csv` — exact MissionChief label, slot, source asset and upload URL.
- `UPLOAD-MANIFEST.json` — machine-readable equivalent with SHA-256 hashes.

## Upload method

Work from the top of the MissionChief vehicle-graphics editor to the bottom. The three-digit number at the start of every filename is the one-based editor slot:

- `001 - ...` is the first form.
- `002 - ...` is the second form.
- Continue in order through `117 - ...`.

For each MissionChief row, select the file with the same slot number from both folders. The text after the number is the exact live MissionChief label, adjusted only where Windows filename rules prohibit a character. For example, `F/WrC` is stored as `F-WrC`.

The image files are copied byte-for-byte from the validated production exports. No image is resized, recompressed or otherwise modified by this packaging step.
"""
    (package_root / "README-FIRST.txt").write_text(content, encoding="utf-8", newline="\n")


def build(root: Path, version: str, profile: str) -> tuple[Path, Path, int]:
    mapping_path = root / "data" / "vehicle-slots.json"
    static_source = root / "assets" / "exports" / profile / "static"
    animated_source = root / "assets" / "exports" / profile / "animated"

    with mapping_path.open("r", encoding="utf-8") as handle:
        mapping: dict[str, Any] = json.load(handle)

    slots = sorted(mapping.get("slots", []), key=lambda item: int(item["slot"]))
    expected_sequence = list(range(1, EXPECTED_SLOTS + 1))
    actual_sequence = [int(item["slot"]) for item in slots]
    if actual_sequence != expected_sequence:
        raise ValueError(
            f"Slot mapping must be exactly 1-{EXPECTED_SLOTS}; got {actual_sequence[:5]} ... {actual_sequence[-5:]}"
        )

    dist = root / "dist"
    profile_label = "Modern-Command-Clarity-" if profile == "command" else ""
    package_name = f"TKB-UK-Emergency-Fleet-{profile_label}MissionChief-Numbered-Upload-Ready-{version}"
    package_root = dist / package_name
    archive_path = dist / f"{package_name}.zip"
    checksum_path = dist / f"{package_name}.zip.sha256"

    if package_root.exists():
        shutil.rmtree(package_root)
    if archive_path.exists():
        archive_path.unlink()
    if checksum_path.exists():
        checksum_path.unlink()

    static_output = package_root / "01 - Static"
    animated_output = package_root / "02 - Animated"
    static_output.mkdir(parents=True, exist_ok=True)
    animated_output.mkdir(parents=True, exist_ok=True)

    manifest_rows: list[dict[str, Any]] = []
    generated_names: set[str] = set()

    for item in slots:
        slot = int(item["slot"])
        edit_index = int(item["edit_index"])
        label = str(item["label"])
        asset_id = str(item["asset_id"])
        upload_path = str(item["upload_path"])

        filename = f"{slot:03d} - {safe_label(label)}.png"
        if filename.casefold() in generated_names:
            raise ValueError(f"Duplicate output filename: {filename}")
        generated_names.add(filename.casefold())

        source_static = static_source / f"{asset_id}.png"
        source_animated = animated_source / f"{asset_id}.png"
        require_png(source_static, f"static slot {slot}")
        require_png(source_animated, f"animated slot {slot}")

        static_hash = copy_exact(source_static, static_output / filename)
        animated_hash = copy_exact(source_animated, animated_output / filename)

        manifest_rows.append(
            {
                "slot": slot,
                "edit_index": edit_index,
                "exact_missionchief_label": label,
                "filename": filename,
                "asset_id": asset_id,
                "static_sha256": static_hash,
                "animated_sha256": animated_hash,
                "upload_path": upload_path,
            }
        )

    if len(list(static_output.glob("*.png"))) != EXPECTED_SLOTS:
        raise RuntimeError("Static output count is not 117")
    if len(list(animated_output.glob("*.png"))) != EXPECTED_SLOTS:
        raise RuntimeError("Animated output count is not 117")

    write_readme(package_root, version, profile)

    csv_path = package_root / "UPLOAD-GUIDE.csv"
    fieldnames = [
        "slot",
        "edit_index",
        "exact_missionchief_label",
        "filename",
        "asset_id",
        "static_sha256",
        "animated_sha256",
        "upload_path",
    ]
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_rows)

    manifest_path = package_root / "UPLOAD-MANIFEST.json"
    manifest_path.write_text(
        json.dumps(
            {
                "release": version,
                "profile": profile,
                "missionchief_pack_id": 5897,
                "slots": EXPECTED_SLOTS,
                "static_files": EXPECTED_SLOTS,
                "animated_files": EXPECTED_SLOTS,
                "images_copied_byte_for_byte": True,
                "entries": manifest_rows,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(package_root.rglob("*")):
            if path.is_file():
                add_deterministic_zip_member(archive, path, path.relative_to(dist))

    archive_hash = sha256(archive_path)
    checksum_path.write_text(f"{archive_hash}  {archive_path.name}\n", encoding="ascii")

    with zipfile.ZipFile(archive_path, "r") as archive:
        bad_file = archive.testzip()
        if bad_file is not None:
            raise RuntimeError(f"ZIP integrity check failed at {bad_file}")
        names = archive.namelist()
        static_members = [name for name in names if "/01 - Static/" in name and name.endswith(".png")]
        animated_members = [name for name in names if "/02 - Animated/" in name and name.endswith(".png")]
        if len(static_members) != EXPECTED_SLOTS or len(animated_members) != EXPECTED_SLOTS:
            raise RuntimeError("ZIP does not contain 117 static and 117 animated files")

    return archive_path, checksum_path, len(manifest_rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default="v1.0.0", help="Release version used in archive names")
    parser.add_argument(
        "--profile",
        choices=("standard", "command"),
        default="standard",
        help="Validated export profile to package",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        archive, checksum, count = build(args.root.resolve(), args.version, args.profile)
    except Exception as exc:  # noqa: BLE001 - command-line release gate
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Built {archive}")
    print(f"Checksum {checksum}")
    print(f"Validated {count} numbered static/animated slot pairs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
