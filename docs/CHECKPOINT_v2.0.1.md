# v2.0.1 release checkpoint

## Fixed scope

- Source masters: the immutable 117-file `assets/masters/v2.0.0/` set.
- Production profile: `v2`.
- MissionChief export canvas: 110×110 RGBA.
- Uniform master-to-export transform: 55% whole-canvas Lanczos downsampling.
- Output scope: 117 static PNGs and 117 animated APNGs.

## Required gates

1. `python scripts/build_v2_compact_exports.py`
2. `python scripts/validate_v2_static_fleet.py`
3. `python scripts/build_v2_animated_fleet.py`
4. `python scripts/validate_v2_animated_fleet.py`
5. `python scripts/build_v2_calibration.py`
6. `python scripts/build_interactive_gallery.py`
7. `python scripts/build_numbered_upload_package.py --version v2.0.1 --profile v2`
8. `python scripts/validate_v2_release_integrity.py`

## Fail-closed contract

- Every declared master remains 200×200 and every production frame is exactly 110×110.
- Every committed static export must match a deterministic single downsample of its corresponding master.
- Static/APNG pairs retain identical canvases and the authoritative 117-slot order.
- Road assets contain twelve full-canvas frames; the four aircraft and two marine assets contain eighteen.
- Every APNG loops indefinitely, uses SOURCE blending and has no partial update tile.
- Emergency-light cores overlap the 200×200 subject and remain visible at native, 75% and 50% compact display scale.
- The actual-pixel representative comparison must include cars, vans, heavy appliances, aircraft, marine, towing and cycle classes.
- The release archive contains exactly 117 static and 117 animated files whose SHA-256 hashes match its manifest.
- `assets/exports/command/` remains unchanged from v1.4.14.

The release and MissionChief deployment may proceed only when the scale, static, animation and complete integrity reports all pass.
