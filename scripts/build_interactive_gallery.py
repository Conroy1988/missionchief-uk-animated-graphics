#!/usr/bin/env python3
"""Build and validate the deterministic interactive vehicle-gallery catalogue."""

from __future__ import annotations

import argparse
import json
import shutil
import struct
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GALLERY_DIR = ROOT / "gallery"
CATALOGUE_PATH = GALLERY_DIR / "vehicles.json"
PACK_URL = "https://www.missionchief.co.uk/vehicle_graphics/5897"
REPOSITORY_URL = "https://github.com/Conroy1988/missionchief-uk-animated-graphics"

RELEASES = [
    {
        "id": "v1.4.0",
        "label": "v1.4.0 · Current",
        "profile": "command",
        "summary": "Air, marine and redraw overhaul",
    },
    {
        "id": "v1.3.0",
        "label": "v1.3.0",
        "profile": "command",
        "summary": "Fleet quality overhaul",
    },
    {
        "id": "v1.2.7",
        "label": "v1.2.7",
        "profile": "command",
        "summary": "Pre-overhaul stable baseline",
    },
    {
        "id": "v1.0.0",
        "label": "v1.0.0 · True Scale",
        "profile": "standard",
        "summary": "Original true-scale release",
    },
]

SERVICE_LABELS = {
    "fire": "Fire",
    "ambulance": "Ambulance",
    "police": "Police",
    "coastguard": "Coastguard",
    "lifeboat": "Lifeboat",
    "search-and-rescue": "SAR",
    "recovery": "Recovery",
    "airfield": "Airfield",
    "eod": "EOD",
    "multi-service": "Multi-service",
}

FOCUS_LABELS = {
    "role-differentiation": "Role differentiation",
    "specialist-equipment": "Specialist equipment",
    "lighting": "Lighting changes",
    "grounding-shadow": "Grounding shadows",
    "redraw": "v1.4 redraws",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def png_dimensions(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        signature = handle.read(8)
        if signature != b"\x89PNG\r\n\x1a\n":
            raise ValueError(f"Not a PNG: {path}")
        length = struct.unpack(">I", handle.read(4))[0]
        chunk = handle.read(4)
        if chunk != b"IHDR" or length < 8:
            raise ValueError(f"Missing IHDR: {path}")
        return struct.unpack(">II", handle.read(8))


def png_frame_count(path: Path) -> int:
    count = 0
    with path.open("rb") as handle:
        if handle.read(8) != b"\x89PNG\r\n\x1a\n":
            raise ValueError(f"Not a PNG: {path}")
        while True:
            size_bytes = handle.read(4)
            if not size_bytes:
                break
            if len(size_bytes) != 4:
                raise ValueError(f"Truncated PNG: {path}")
            size = struct.unpack(">I", size_bytes)[0]
            chunk = handle.read(4)
            if chunk == b"fcTL":
                count += 1
            handle.seek(size + 4, 1)
    return max(count, 1)


def humanise_cue(cue: str | None) -> str | None:
    if not cue:
        return None
    return cue.replace("-pass", " detail pass").replace("-", " ").capitalize()


def git_tree(release: str) -> set[str]:
    result = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", release],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return set(result.stdout.splitlines())


def build_catalogue() -> dict:
    slots = load_json(ROOT / "data/vehicle-slots.json")["slots"]
    prototypes = load_json(ROOT / "data/prototypes.json")["vehicles"]
    profile = load_json(ROOT / "data/v1.4-overhaul-profile.json")
    lighting_scope = load_json(ROOT / "data/v1.2.6-scope.json")["changed_asset_ids"]

    prototypes_by_slot = {item["missionchief_slot"]: item for item in prototypes}
    cue_data = profile["baked_master_cues"]
    frame_overrides = profile["animation_frame_overrides"]
    lighting_assets = set(lighting_scope)
    vehicles = []

    for slot in slots:
        prototype = prototypes_by_slot[slot["slot"]]
        asset_id = slot["asset_id"]
        if prototype["id"] != asset_id:
            raise ValueError(
                f"Slot {slot['slot']} asset mismatch: {asset_id} != {prototype['id']}"
            )

        static_path = Path("assets/exports/command/static") / f"{asset_id}.png"
        animated_path = Path("assets/exports/command/animated") / f"{asset_id}.png"
        width, height = png_dimensions(ROOT / static_path)
        animated_width, animated_height = png_dimensions(ROOT / animated_path)
        if (width, height) != (animated_width, animated_height):
            raise ValueError(f"Static/APNG dimensions differ for {asset_id}")

        actual_frames = png_frame_count(ROOT / animated_path)
        expected_frames = frame_overrides.get(asset_id, profile["frames"])
        if actual_frames != expected_frames:
            raise ValueError(
                f"Unexpected frame count for {asset_id}: {actual_frames} != {expected_frames}"
            )

        cue = cue_data.get(asset_id)
        focus = ["grounding-shadow"]
        if cue:
            family = cue["family"]
            if family == "role":
                focus.append("role-differentiation")
            elif family == "equipment":
                focus.append("specialist-equipment")
            elif family == "redraw":
                focus.append("redraw")
        if asset_id in lighting_assets:
            focus.append("lighting")

        service = prototype["service"]
        cue_label = humanise_cue(cue["cue"] if cue else None)
        search_parts = [
            f"{slot['slot']:03}",
            str(slot["slot"]),
            f"slot {slot['slot']}",
            slot["label"],
            slot["id"],
            asset_id,
            prototype["display_name"],
            service,
            SERVICE_LABELS[service],
            slot["production_batch"].replace("-", " "),
            cue_label or "",
            *(FOCUS_LABELS[item] for item in focus),
        ]

        vehicles.append(
            {
                "slot": slot["slot"],
                "edit_index": slot["edit_index"],
                "id": slot["id"],
                "asset_id": asset_id,
                "label": slot["label"],
                "display_name": prototype["display_name"],
                "service": service,
                "service_label": SERVICE_LABELS[service],
                "production_batch": slot["production_batch"],
                "real_length_metres": prototype["real_length_metres"],
                "width": width,
                "height": height,
                "frames": actual_frames,
                "focus": focus,
                "cue": cue_label,
                "static_path": static_path.as_posix(),
                "animated_path": animated_path.as_posix(),
                "missionchief_url": PACK_URL,
                "search_text": " ".join(search_parts).lower(),
            }
        )

    service_counts = {
        service: sum(item["service"] == service for item in vehicles)
        for service in SERVICE_LABELS
    }
    focus_counts = {
        focus: sum(focus in item["focus"] for item in vehicles) for focus in FOCUS_LABELS
    }

    return {
        "schema_version": 1,
        "release": "v1.4.0",
        "title": "TKB UK Emergency Fleet",
        "edition": "Interactive Gallery",
        "pack_id": 5897,
        "pack_url": PACK_URL,
        "repository_url": REPOSITORY_URL,
        "total": len(vehicles),
        "services": [
            {"id": service, "label": label, "count": service_counts[service]}
            for service, label in SERVICE_LABELS.items()
        ],
        "focus_views": [
            {"id": focus, "label": label, "count": focus_counts[focus]}
            for focus, label in FOCUS_LABELS.items()
        ],
        "releases": RELEASES,
        "vehicles": vehicles,
        "generated_from": [
            "data/vehicle-slots.json",
            "data/prototypes.json",
            "data/v1.4-overhaul-profile.json",
            "data/v1.2.6-scope.json",
        ],
    }


def serialise(catalogue: dict) -> str:
    return json.dumps(catalogue, indent=2, ensure_ascii=False) + "\n"


def validate_historical_assets(catalogue: dict) -> None:
    for release in RELEASES:
        tree = git_tree(release["id"])
        profile = release["profile"]
        for vehicle in catalogue["vehicles"]:
            for mode in ("static", "animated"):
                path = f"assets/exports/{profile}/{mode}/{vehicle['asset_id']}.png"
                if path not in tree:
                    raise ValueError(f"Missing {release['id']} comparison asset: {path}")


def stage_site(output: Path) -> None:
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    for filename in ("index.html", "styles.css", "app.mjs", "vehicles.json"):
        shutil.copy2(GALLERY_DIR / filename, output / filename)

    asset_root = output / "assets/exports/command"
    asset_root.mkdir(parents=True)
    for variant in ("static", "animated"):
        shutil.copytree(
            ROOT / "assets/exports/command" / variant,
            asset_root / variant,
        )
    (output / ".nojekyll").write_text("", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Fail if catalogue is stale")
    parser.add_argument("--site-output", type=Path, help="Stage a deployable static site")
    args = parser.parse_args()

    catalogue = build_catalogue()
    rendered = serialise(catalogue)

    if catalogue["total"] != 117:
        raise ValueError(f"Expected 117 vehicles, found {catalogue['total']}")

    if args.check:
        if not CATALOGUE_PATH.exists() or CATALOGUE_PATH.read_text(encoding="utf-8") != rendered:
            raise SystemExit(
                "gallery/vehicles.json is stale; run scripts/build_interactive_gallery.py"
            )
        validate_historical_assets(catalogue)
    else:
        GALLERY_DIR.mkdir(exist_ok=True)
        CATALOGUE_PATH.write_text(rendered, encoding="utf-8")

    if args.site_output:
        stage_site(args.site_output.resolve())
        print(f"Staged gallery site at {args.site_output.resolve()}")

    print(
        f"Interactive gallery catalogue valid: {catalogue['total']} vehicles, "
        f"{len(catalogue['services'])} services, {len(catalogue['focus_views'])} focus views"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
