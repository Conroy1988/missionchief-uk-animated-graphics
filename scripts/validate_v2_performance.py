#!/usr/bin/env python3
"""Measure and fail closed on the v2.2.0 low-redraw animation contract."""

from __future__ import annotations

from io import BytesIO
import hashlib
import json
import subprocess

from PIL import Image

from v2_profile import (
    AIR_MARINE_FRAME_COUNT,
    ANIMATED_DIR,
    EXPORT_CANVAS,
    PERFORMANCE_BASELINE_RELEASE,
    RELEASE,
    RELEASE_CANDIDATE,
    ROAD_FRAME_COUNT,
    ROOT,
    STATIC_DIR,
)


SLOTS = json.loads((ROOT / "data/vehicle-slots.json").read_text())["slots"]
FIXTURES = json.loads((ROOT / f"data/{RELEASE}-light-fixtures.json").read_text())["vehicles"]
REPORT = ROOT / f"data/{RELEASE}-performance-report.json"
RGBA_BYTES_PER_FRAME = EXPORT_CANVAS[0] * EXPORT_CANVAS[1] * 4


def ref_bytes(ref: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=ROOT)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def animation_metrics(data: bytes) -> dict[str, float | int | list[int]]:
    durations: list[int] = []
    with Image.open(BytesIO(data)) as image:
        frame_count = int(getattr(image, "n_frames", 1))
        canvas = image.size
        for index in range(frame_count):
            image.seek(index)
            image.load()
            durations.append(round(float(image.info.get("duration", 0))))
    cycle_ms = sum(durations)
    return {
        "bytes": len(data),
        "frames": frame_count,
        "canvas": list(canvas),
        "durations_ms": durations,
        "cycle_ms": cycle_ms,
        "update_rate_hz": round(frame_count * 1000 / cycle_ms, 3) if cycle_ms else 0.0,
    }


def reduction(before: float, after: float) -> float:
    return round((1 - after / before) * 100, 1) if before else 0.0


def main() -> None:
    errors: list[str] = []
    entries: list[dict] = []
    unchanged_static = 0

    for slot in SLOTS:
        asset_id = slot["asset_id"]
        animated_path = f"assets/exports/v2/animated/{asset_id}.png"
        static_path = f"assets/exports/v2/static/{asset_id}.png"
        current_data = (ANIMATED_DIR / f"{asset_id}.png").read_bytes()
        baseline_data = ref_bytes(PERFORMANCE_BASELINE_RELEASE, animated_path)
        current = animation_metrics(current_data)
        baseline = animation_metrics(baseline_data)
        kind = FIXTURES[asset_id]["kind"]
        group = "aircraft-marine" if kind in {"aircraft", "marine"} else "road"
        expected_frames = AIR_MARINE_FRAME_COUNT if group == "aircraft-marine" else ROAD_FRAME_COUNT

        if current["frames"] != expected_frames:
            errors.append(f"frames/{asset_id}={current['frames']}")
        if current["canvas"] != list(EXPORT_CANVAS):
            errors.append(f"canvas/{asset_id}={current['canvas']}")
        if group == "road" and current["update_rate_hz"] > 4.0:
            errors.append(f"road-update-rate/{asset_id}={current['update_rate_hz']}")
        if group == "aircraft-marine" and current["update_rate_hz"] > 6.0:
            errors.append(f"motion-update-rate/{asset_id}={current['update_rate_hz']}")

        current_static = (STATIC_DIR / f"{asset_id}.png").read_bytes()
        baseline_static = ref_bytes(PERFORMANCE_BASELINE_RELEASE, static_path)
        static_preserved = sha256(current_static) == sha256(baseline_static)
        unchanged_static += int(static_preserved)
        if not static_preserved:
            errors.append(f"static-drift/{asset_id}")

        entries.append(
            {
                "slot": slot["slot"],
                "asset_id": asset_id,
                "group": group,
                "baseline": baseline,
                "optimized": current,
                "frame_reduction_percent": reduction(
                    float(baseline["frames"]), float(current["frames"])
                ),
                "encoded_reduction_percent": reduction(
                    float(baseline["bytes"]), float(current["bytes"])
                ),
                "static_sha256_preserved": static_preserved,
            }
        )

    baseline_frames = sum(int(entry["baseline"]["frames"]) for entry in entries)
    optimized_frames = sum(int(entry["optimized"]["frames"]) for entry in entries)
    baseline_bytes = sum(int(entry["baseline"]["bytes"]) for entry in entries)
    optimized_bytes = sum(int(entry["optimized"]["bytes"]) for entry in entries)
    road_entries = [entry for entry in entries if entry["group"] == "road"]
    motion_entries = [entry for entry in entries if entry["group"] == "aircraft-marine"]
    baseline_road_rate = sum(
        float(entry["baseline"]["update_rate_hz"]) for entry in road_entries
    ) / len(road_entries)
    optimized_road_rate = sum(
        float(entry["optimized"]["update_rate_hz"]) for entry in road_entries
    ) / len(road_entries)
    frame_reduction = reduction(baseline_frames, optimized_frames)
    encoded_reduction = reduction(baseline_bytes, optimized_bytes)
    road_rate_reduction = reduction(baseline_road_rate, optimized_road_rate)
    artwork_unchanged = subprocess.run(
        [
            "git",
            "diff",
            "--quiet",
            PERFORMANCE_BASELINE_RELEASE,
            "--",
            "assets/masters",
            "assets/sources",
        ],
        cwd=ROOT,
        check=False,
    ).returncode == 0

    if len(entries) != 117:
        errors.append(f"asset-count={len(entries)}")
    if len(road_entries) != 111 or len(motion_entries) != 6:
        errors.append(f"profile-counts=road:{len(road_entries)},motion:{len(motion_entries)}")
    if baseline_frames != 1440:
        errors.append(f"baseline-frames={baseline_frames}")
    if optimized_frames != 246:
        errors.append(f"optimized-frames={optimized_frames}")
    if frame_reduction < 80.0:
        errors.append(f"frame-reduction={frame_reduction}")
    if encoded_reduction < 75.0:
        errors.append(f"encoded-reduction={encoded_reduction}")
    if road_rate_reduction < 65.0:
        errors.append(f"road-update-reduction={road_rate_reduction}")
    if unchanged_static != 117:
        errors.append(f"unchanged-static={unchanged_static}")
    if not artwork_unchanged:
        errors.append("master-or-source-artwork-drift")

    report = {
        "release": RELEASE_CANDIDATE,
        "baseline": PERFORMANCE_BASELINE_RELEASE,
        "profile": "full-frame low-redraw APNG",
        "assets": len(entries),
        "road_assets": len(road_entries),
        "aircraft_marine_assets": len(motion_entries),
        "baseline_total_frames": baseline_frames,
        "optimized_total_frames": optimized_frames,
        "frame_reduction_percent": frame_reduction,
        "baseline_animated_bytes": baseline_bytes,
        "optimized_animated_bytes": optimized_bytes,
        "encoded_reduction_percent": encoded_reduction,
        "baseline_decoded_rgba_cycle_bytes": baseline_frames * RGBA_BYTES_PER_FRAME,
        "optimized_decoded_rgba_cycle_bytes": optimized_frames * RGBA_BYTES_PER_FRAME,
        "decoded_cycle_reduction_percent": reduction(baseline_frames, optimized_frames),
        "baseline_road_update_rate_hz": round(baseline_road_rate, 3),
        "optimized_road_update_rate_hz": round(optimized_road_rate, 3),
        "road_update_rate_reduction_percent": road_rate_reduction,
        "estimated_road_updates_per_second_at_500_visible": {
            "baseline": round(baseline_road_rate * 500),
            "optimized": round(optimized_road_rate * 500),
        },
        "static_exports_sha256_preserved": unchanged_static,
        "master_and_source_artwork_unchanged": artwork_unchanged,
        "thresholds": {
            "minimum_frame_reduction_percent": 80.0,
            "minimum_encoded_reduction_percent": 75.0,
            "minimum_road_update_rate_reduction_percent": 65.0,
            "maximum_road_update_rate_hz": 4.0,
            "maximum_aircraft_marine_update_rate_hz": 6.0,
        },
        "all_passed": not errors,
        "errors": sorted(errors),
        "entries": entries,
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "assets",
                    "baseline_total_frames",
                    "optimized_total_frames",
                    "frame_reduction_percent",
                    "baseline_animated_bytes",
                    "optimized_animated_bytes",
                    "encoded_reduction_percent",
                    "road_update_rate_reduction_percent",
                    "static_exports_sha256_preserved",
                    "all_passed",
                    "errors",
                )
            },
            indent=2,
        )
    )
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
