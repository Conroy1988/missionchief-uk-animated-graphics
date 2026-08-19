# v2.0.0 release checkpoint

## Fixed scope

- Baseline: v1.4.14 live pack and authoritative 117-slot mapping.
- New profile: `v2`.
- New exports: 117 static PNGs and 117 animated APNGs.
- Existing `standard` and `command` profiles: unchanged.

## Required gates

1. `python scripts/build_v2_calibration.py`
2. `python scripts/build_v2_animated_fleet.py`
3. `python scripts/validate_v2_static_fleet.py`
4. `python scripts/validate_v2_animated_fleet.py`
5. `python scripts/build_numbered_upload_package.py --version v2.0.0 --profile v2`
6. `python scripts/validate_v2_release_integrity.py`

## Fail-closed contract

- The exact 117 asset IDs in `data/vehicle-slots.json` must exist once in both v2 export folders.
- Every static and animation frame must be 200×200 RGBA with a transparent background.
- Road assets contain 12 full-canvas APNG frames; the four aircraft and two marine assets contain 18.
- Every APNG loops indefinitely and uses SOURCE blending with no partial update tile.
- Every declared lamp core overlaps the subject.
- Every response asset retains a high-contrast change after 50% reduction.
- Full-fleet static and A/B response sheets must decode on light, dark, satellite and grayscale backgrounds.
- The numbered archive must contain 117 static and 117 animated files whose SHA-256 hashes match its manifest.
- `assets/exports/command/` must remain unchanged from v1.4.14.

The release may be staged only when all three v2 QA reports state `"all_passed": true`.
