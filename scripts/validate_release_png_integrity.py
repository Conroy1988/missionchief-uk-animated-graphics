#!/usr/bin/env python3
"""Fail closed when release PNG/APNG assets are empty, truncated or corrupt."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "data" / "v1.4-overhaul-profile.json"
EXPECTED_VEHICLES = 117


def verify_png(path: Path) -> int:
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError("missing or empty file")

    with Image.open(path) as image:
        frames = int(getattr(image, "n_frames", 1))
        for index in range(frames):
            image.seek(index)
            image.load()
    return frames


def main() -> None:
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    release = str(profile["release"])
    groups = {
        "command_static": sorted(
            (ROOT / "assets" / "exports" / "command" / "static").glob("*.png")
        ),
        "command_animated": sorted(
            (ROOT / "assets" / "exports" / "command" / "animated").glob("*.png")
        ),
        "release_previews": sorted(
            (ROOT / "assets" / "previews" / release).glob("*.png")
        ),
    }

    errors: list[str] = []
    if len(groups["command_static"]) != EXPECTED_VEHICLES:
        errors.append(
            f"command_static: expected {EXPECTED_VEHICLES} files, "
            f"found {len(groups['command_static'])}"
        )
    if len(groups["command_animated"]) != EXPECTED_VEHICLES:
        errors.append(
            f"command_animated: expected {EXPECTED_VEHICLES} files, "
            f"found {len(groups['command_animated'])}"
        )
    if not groups["release_previews"]:
        errors.append(f"release_previews: no PNGs found for {release}")

    decoded_frames = 0
    for group, paths in groups.items():
        for path in paths:
            try:
                decoded_frames += verify_png(path)
            except Exception as exc:  # Pillow exposes format-specific failures.
                errors.append(f"{group}/{path.name}: {exc}")

    report = {
        "release": release,
        "command_static_pngs": len(groups["command_static"]),
        "command_animated_apngs": len(groups["command_animated"]),
        "release_preview_pngs": len(groups["release_previews"]),
        "decoded_images_and_frames": decoded_frames,
        "all_passed": not errors,
        "errors": errors,
    }
    print(json.dumps(report, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
