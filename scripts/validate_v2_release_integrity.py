#!/usr/bin/env python3
"""Fail-closed integrity gate for the complete compact v2 candidate."""

from __future__ import annotations

import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

from PIL import Image

from v2_profile import (
    ANIMATED_DIR,
    EXPECTED_OVERRIDE_IDS,
    EXPORT_CANVAS,
    FAMILY_CONVERSION_IDS,
    MASTER_OVERRIDE_DIR,
    MOUNTED_CARRIER_IDS,
    PREVIEW_DIR,
    RELEASE,
    RELEASE_CANDIDATE,
    ROOT,
    STATIC_DIR,
)


EXPECTED = 117
PACKAGE_NAME = f"TKB-UK-Emergency-Fleet-Direction-Neutral-MissionChief-Numbered-Upload-Ready-{RELEASE}"
PACKAGE_ROOT = ROOT / "dist" / PACKAGE_NAME
ARCHIVE = ROOT / "dist" / f"{PACKAGE_NAME}.zip"
CHECKSUM = ROOT / "dist" / f"{PACKAGE_NAME}.zip.sha256"
REPORT = ROOT / f"data/{RELEASE}-release-integrity-report.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def decode(path: Path, expected_canvas: tuple[int, int] | None = None) -> int:
    with Image.open(path) as image:
        frame_count = int(getattr(image, "n_frames", 1))
        for index in range(frame_count):
            image.seek(index)
            if expected_canvas is not None and image.size != expected_canvas:
                raise ValueError(f"canvas={image.size}, expected={expected_canvas}")
            image.load()
    return frame_count


def main() -> None:
    errors: list[str] = []
    static_paths = sorted(STATIC_DIR.glob("*.png"))
    animated_paths = sorted(ANIMATED_DIR.glob("*.png"))
    temporary_preview_paths = sorted(PREVIEW_DIR.glob("*.tmp.png"))
    preview_paths = sorted(
        path for path in PREVIEW_DIR.glob("*.png") if not path.name.endswith(".tmp.png")
    )

    if temporary_preview_paths:
        errors.extend(f"temporary-preview/{path.name}" for path in temporary_preview_paths)

    if len(static_paths) != EXPECTED:
        errors.append(f"static-count={len(static_paths)}")
    if len(animated_paths) != EXPECTED:
        errors.append(f"animated-count={len(animated_paths)}")
    if len(preview_paths) < 18:
        errors.append(f"preview-count={len(preview_paths)}")

    override_ids = {path.stem for path in MASTER_OVERRIDE_DIR.glob("*.png")}
    if override_ids != EXPECTED_OVERRIDE_IDS:
        errors.append(
            "release-overrides="
            f"missing:{sorted(EXPECTED_OVERRIDE_IDS - override_ids)},"
            f"extra:{sorted(override_ids - EXPECTED_OVERRIDE_IDS)}"
        )

    expected_v2_asset_changes = {
        f"assets/exports/v2/{variant}/{asset_id}.png"
        for variant in ("static", "animated")
        for asset_id in (*MOUNTED_CARRIER_IDS, *FAMILY_CONVERSION_IDS)
    }
    actual_v2_asset_changes = set(
        subprocess.check_output(
            [
                "git",
                "diff",
                "--name-only",
                "v2.0.3",
                "--",
                "assets/exports/v2/static",
                "assets/exports/v2/animated",
            ],
            cwd=ROOT,
            text=True,
        ).splitlines()
    )
    if actual_v2_asset_changes != expected_v2_asset_changes:
        errors.append(
            "v2-asset-scope="
            f"missing:{sorted(expected_v2_asset_changes - actual_v2_asset_changes)},"
            f"extra:{sorted(actual_v2_asset_changes - expected_v2_asset_changes)}"
        )

    decoded_frames = 0
    frame_distribution: dict[str, int] = {}
    for path in static_paths:
        try:
            count = decode(path, EXPORT_CANVAS)
            decoded_frames += count
            if count != 1:
                errors.append(f"static-frames/{path.name}={count}")
        except Exception as exc:
            errors.append(f"static-decode/{path.name}: {exc}")
    for path in animated_paths:
        try:
            count = decode(path, EXPORT_CANVAS)
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

    for report_name in (
        f"{RELEASE}-scale-report.json",
        f"{RELEASE}-static-qa-report.json",
        f"{RELEASE}-animation-qa-report.json",
        f"{RELEASE}-cab-legibility-report.json",
        f"{RELEASE}-mounted-carrier-report.json",
        f"{RELEASE}-family-conversion-report.json",
    ):
        report_path = ROOT / "data" / report_name
        try:
            qa = json.loads(report_path.read_text())
            if not qa.get("all_passed"):
                errors.append(f"qa-failed/{report_name}")
        except Exception as exc:
            errors.append(f"qa-read/{report_name}: {exc}")

    family_audit_summary = None
    family_audit_path = ROOT / "data" / f"{RELEASE}-uk-family-hero-report.json"
    try:
        family_audit = json.loads(family_audit_path.read_text())
        family_audit_summary = {
            "mapped_assets": family_audit.get("mapped_assets"),
            "families": family_audit.get("families"),
            "technical_passed": family_audit.get("technical_passed"),
            "hero_ready": family_audit.get("hero_ready"),
            "conversion_required": family_audit.get("conversion_required"),
        }
        if family_audit.get("mapped_assets") != EXPECTED:
            errors.append(f"family-audit-mapped={family_audit.get('mapped_assets')}")
        if not family_audit.get("technical_all_passed"):
            errors.append("family-audit-technical-failure")
        if family_audit.get("hero_ready") != EXPECTED:
            errors.append(f"family-audit-hero-ready={family_audit.get('hero_ready')}")
        if family_audit.get("conversion_required") != 0:
            errors.append(
                f"family-audit-conversion-required={family_audit.get('conversion_required')}"
            )
        if not family_audit.get("fleet_hero_ready"):
            errors.append("family-audit-enforcement-failure")
    except Exception as exc:
        errors.append(f"family-audit: {exc}")

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
        if package_manifest.get("release") != RELEASE:
            errors.append(f"package-release={package_manifest.get('release')}")
        expected_canvas = {
            "width": EXPORT_CANVAS[0],
            "height": EXPORT_CANVAS[1],
        }
        if package_manifest.get("canvas") != expected_canvas:
            errors.append(f"package-canvas={package_manifest.get('canvas')}")
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
            static_members = sum(
                "/01 - Static/" in name and name.endswith(".png")
                for name in names
            )
            animated_members = sum(
                "/02 - Animated/" in name and name.endswith(".png")
                for name in names
            )
            if static_members != EXPECTED:
                errors.append("archive-static-count")
            if animated_members != EXPECTED:
                errors.append("archive-animated-count")
    except Exception as exc:
        errors.append(f"archive: {exc}")

    result = {
        "release": RELEASE_CANDIDATE,
        "export_canvas": list(EXPORT_CANVAS),
        "static_pngs": len(static_paths),
        "animated_apngs": len(animated_paths),
        "frame_distribution": frame_distribution,
        "preview_pngs": len(preview_paths),
        "decoded_images_and_frames": decoded_frames,
        "numbered_static_files": len(list((PACKAGE_ROOT / "01 - Static").glob("*.png"))),
        "numbered_animated_files": len(list((PACKAGE_ROOT / "02 - Animated").glob("*.png"))),
        "archive_sha256": archive_hash,
        "current_v1_command_exports_unchanged": command_diff == 0 and not command_status,
        "v2_asset_changes_against_v2.0.3": sorted(actual_v2_asset_changes),
        "uk_family_hero_audit": family_audit_summary,
        "all_passed": not errors,
        "errors": errors,
    }
    REPORT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
