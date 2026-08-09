#!/usr/bin/env python3
"""Fail closed unless release exports match the declared asset scope."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "data" / "v1.4-overhaul-profile.json"


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def main() -> None:
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    release = str(profile["release"])
    scope_path = ROOT / "data" / f"{release}-scope.json"
    if not scope_path.is_file():
        raise SystemExit(f"missing release scope: {scope_path.relative_to(ROOT)}")
    scope = json.loads(scope_path.read_text(encoding="utf-8"))
    if str(scope.get("release")) != release:
        raise SystemExit("release scope does not match the active profile")
    baseline = str(scope["baseline"])
    declared_ids = scope["changed_asset_ids"]
    mapping = json.loads((ROOT / "data" / "vehicle-slots.json").read_text(encoding="utf-8"))
    all_ids = {str(item["asset_id"]) for item in mapping["slots"]}
    expected_ids = all_ids if declared_ids == "all" else set(declared_ids)
    profile_variants = scope.get("profile_variants")
    if profile_variants is None:
        expected_profiles = tuple(scope.get("changed_profiles", ("command",)))
        expected_variants = tuple(scope.get("changed_variants", ("static", "animated")))
        profile_variants = {profile_name: expected_variants for profile_name in expected_profiles}
    else:
        profile_variants = {
            str(profile_name): tuple(variants)
            for profile_name, variants in profile_variants.items()
        }
    expected_paths = {
        f"assets/exports/{profile_name}/{variant}/{asset_id}.png"
        for profile_name, variants in profile_variants.items()
        for asset_id in expected_ids
        for variant in variants
    }

    try:
        git("rev-parse", "--verify", f"{baseline}^{{commit}}")
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"missing required release baseline tag: {baseline}") from exc

    changed_paths = {
        line
        for line in git(
            "diff",
            "--name-only",
            baseline,
            "--",
            *(f"assets/exports/{profile_name}" for profile_name in profile_variants),
        ).splitlines()
        if line
    }
    if changed_paths != expected_paths:
        raise SystemExit(
            json.dumps(
                {
                    "error": "release export scope mismatch",
                    "missing": sorted(expected_paths - changed_paths),
                    "unexpected": sorted(changed_paths - expected_paths),
                },
                indent=2,
            )
        )

    actual_slots = {
        str(item["asset_id"]): int(item["slot"])
        for item in mapping["slots"]
        if str(item["asset_id"]) in expected_ids
    }
    expected_slots = (
        {str(item["asset_id"]): int(item["slot"]) for item in mapping["slots"]}
        if scope["slots"] == "all"
        else {str(key): int(value) for key, value in scope["slots"].items()}
    )
    if actual_slots != expected_slots:
        raise SystemExit(
            json.dumps(
                {
                    "error": "release slot scope mismatch",
                    "expected": expected_slots,
                    "actual": actual_slots,
                },
                indent=2,
            )
        )

    print(
        json.dumps(
            {
                "status": "PASS",
                "baseline": baseline,
                "profile_variants": profile_variants,
                "changed_assets": len(expected_ids),
                "changed_files": len(changed_paths),
                "asset_ids": sorted(expected_ids),
                "slots": actual_slots,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
