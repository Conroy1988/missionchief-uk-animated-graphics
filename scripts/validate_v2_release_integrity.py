#!/usr/bin/env python3
"""Fail-closed integrity gate for the complete v2.0.0 candidate."""

from __future__ import annotations

import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
EXPECTED = 117
PACKAGE_NAME = "TKB-UK-Emergency-Fleet-Direction-Neutral-MissionChief-Numbered-Upload-Ready-v2.0.0"
PACKAGE_ROOT = ROOT / "dist" / PACKAGE_NAME
ARCHIVE = ROOT / "dist" / f"{PACKAGE_NAME}.zip"
CHECKSUM = ROOT / "dist" / f"{PACKAGE_NAME}.zip.sha256"
REPORT = ROOT / "data/v2.0.0-release-integrity-report.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decode(path: Path) -> int:
    with Image.open(path) as image:
        frame_count = int(getattr(image, "n_frames", 1))
        for index in range(frame_count):
            image.seek(index)
            image.load()
    return frame_count


def main() -> None:
    errors: list[str] = []
    static_paths = sorted((ROOT / "assets/exports/v2/static").glob("*.png"))
    animated_paths = sorted((ROOT / "assets/exports/v2/animated").glob("*.png"))
    preview_paths = sorted((ROOT / "assets/previews/v2.0.0").glob("*.png"))

    if len(static_paths) != EXPECTED:
        errors.append(f"static-count={len(static_paths)}")
    if len(animated_paths) != EXPECTED:
        errors.append(f"animated-count={len(animated_paths)}")
    if len(preview_paths) < 13:
        errors.append(f"preview-count={len(preview_paths)}")

    decoded_frames = 0
    frame_distribution: dict[str, int] = {}
    for path in static_paths:
        try:
            count = decode(path)
            decoded_frames += count
            if count != 1:
                errors.append(f"static-frames/{path.name}={count}")
        except Exception as exc:
            errors.append(f"static-decode/{path.name}: {exc}")
    for path in animated_paths:
        try:
            count = decode(path)
            decoded_frames += count
            frame_distribution[str(count)] = frame_distribution.get(str(count), 0) + 1
            if count not in {12, 18}:
                errors.append(f"animated-frames/{path.name}={count}")
        except Exception as exc:
            errors.append(f"animated-decode/{path.name}: {exc}")
    for path in preview_paths:
        try:
            decoded_frames += decode(path)
        except Exception as exc:
            errors.append(f"preview-decode/{path.name}: {exc}")

    for report_name in ("v2.0.0-static-qa-report.json", "v2.0.0-animation-qa-report.json"):
        report_path = ROOT / "data" / report_name
        try:
            qa = json.loads(report_path.read_text())
            if not qa.get("all_passed"):
                errors.append(f"qa-failed/{report_name}")
        except Exception as exc:
            errors.append(f"qa-read/{report_name}: {exc}")

    command_diff = subprocess.run(
        ["git", "diff", "--quiet", "v1.4.14", "--", "assets/exports/command"],
        cwd=ROOT,
        check=False,
    ).returncode
    command_status = subprocess.check_output(
        ["git", "status", "--short", "--", "assets/exports/command"],
        cwd=ROOT,
        text=True,
    ).strip()
    if command_diff != 0 or command_status:
        errors.append("current-command-exports-changed")

    package_manifest_path = PACKAGE_ROOT / "UPLOAD-MANIFEST.json"
    try:
        package_manifest = json.loads(package_manifest_path.read_text())
        entries = package_manifest["entries"]
        if len(entries) != EXPECTED:
            errors.append(f"package-manifest-entries={len(entries)}")
        for entry in entries:
            filename = entry["filename"]
            static = PACKAGE_ROOT / "01 - Static" / filename
            animated = PACKAGE_ROOT / "02 - Animated" / filename
            if sha256(static) != entry["static_sha256"]:
                errors.append(f"package-static-hash/{filename}")
            if sha256(animated) != entry["animated_sha256"]:
                errors.append(f"package-animated-hash/{filename}")
    except Exception as exc:
        errors.append(f"package-manifest: {exc}")

    archive_hash = None
    try:
        archive_hash = sha256(ARCHIVE)
        declared_hash = CHECKSUM.read_text().split()[0]
        if archive_hash != declared_hash:
            errors.append("archive-checksum")
        with zipfile.ZipFile(ARCHIVE) as archive:
            bad_member = archive.testzip()
            if bad_member:
                errors.append(f"archive-member/{bad_member}")
            names = archive.namelist()
            if sum("/01 - Static/" in name and name.endswith(".png") for name in names) != EXPECTED:
                errors.append("archive-static-count")
            if sum("/02 - Animated/" in name and name.endswith(".png") for name in names) != EXPECTED:
                errors.append("archive-animated-count")
    except Exception as exc:
        errors.append(f"archive: {exc}")

    result = {
        "release": "v2.0.0-candidate",
        "static_pngs": len(static_paths),
        "animated_apngs": len(animated_paths),
        "frame_distribution": frame_distribution,
        "preview_pngs": len(preview_paths),
        "decoded_images_and_frames": decoded_frames,
        "numbered_static_files": len(list((PACKAGE_ROOT / "01 - Static").glob("*.png"))),
        "numbered_animated_files": len(list((PACKAGE_ROOT / "02 - Animated").glob("*.png"))),
        "archive_sha256": archive_hash,
        "current_v1_command_exports_unchanged": command_diff == 0 and not command_status,
        "all_passed": not errors,
        "errors": errors,
    }
    REPORT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
