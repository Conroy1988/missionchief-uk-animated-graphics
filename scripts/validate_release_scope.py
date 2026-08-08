#!/usr/bin/env python3
"""Fail closed unless v1.2.3 changes exactly the eight intended pod pairs."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCOPE_PATH = ROOT / "data" / "v1.2.3-scope.json"


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
    scope = json.loads(SCOPE_PATH.read_text(encoding="utf-8"))
    baseline = str(scope["baseline"])
    expected_ids = set(scope["changed_asset_ids"])
    expected_paths = {
        f"assets/exports/command/{variant}/{asset_id}.png"
        for asset_id in expected_ids
        for variant in ("static", "animated")
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
            "assets/exports/command/static",
            "assets/exports/command/animated",
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

    mapping = json.loads((ROOT / "data" / "vehicle-slots.json").read_text(encoding="utf-8"))
    actual_slots = {
        str(item["asset_id"]): int(item["slot"])
        for item in mapping["slots"]
        if str(item["asset_id"]) in expected_ids
    }
    expected_slots = {str(key): int(value) for key, value in scope["slots"].items()}
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
                "changed_pairs": len(expected_ids),
                "changed_files": len(changed_paths),
                "asset_ids": sorted(expected_ids),
                "slots": actual_slots,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
