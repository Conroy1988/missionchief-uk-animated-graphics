# v2.0.3 release checkpoint

## Fixed scope

- Immutable base masters: the 117-file `assets/masters/v2.0.0/` set.
- Release master overrides: F/WrC, WrL CAFS and RP CAFS in `assets/masters/v2.0.3/`.
- Production profile: `v2`.
- MissionChief export canvas: 110×110 RGBA.
- Output scope: 117 static PNGs and 117 animated APNGs.
- Cab scope: slots 37, 38 and 39 only.
- Preserved scope: all other vehicle artwork plus the v2.0.2 helicopter rotor geometry and motion.

## Required gates

1. `python scripts/build_v2_cab_legibility_masters.py --check`
2. `python scripts/build_v2_compact_exports.py`
3. `python scripts/validate_v2_static_fleet.py`
4. `python scripts/validate_v2_cab_legibility.py`
5. `python scripts/build_v2_animated_fleet.py`
6. `python scripts/validate_v2_animated_fleet.py`
7. `python scripts/build_v2_calibration.py`
8. `python scripts/build_v2_helicopter_previews.py`
9. `python scripts/build_interactive_gallery.py`
10. `python scripts/build_numbered_upload_package.py --version v2.0.3 --profile v2`
11. `python scripts/validate_v2_release_integrity.py`

## Fail-closed contract

- The immutable v2.0.0 master set remains untouched; release-specific replacements are isolated as v2.0.3 overrides.
- Each corrected appliance retains a complete and immediately recognisable lower-right front cab.
- The validated front region must contain sufficient dark cab structure and glazing pixels to reject the inherited rear/module-only artwork.
- Every declared master remains 200×200 and every production frame is exactly 110×110.
- Every committed static export must match a deterministic single downsample of its resolved master.
- Static/APNG pairs retain identical canvases and the authoritative 117-slot order.
- Road assets contain twelve full-canvas frames; the four aircraft and two marine assets contain eighteen.
- Every APNG loops indefinitely, uses SOURCE blending and has no partial update tile.
- Emergency-light cores overlap the subject and remain visible at native, 75% and 50% display scale.
- The v2.0.2 helicopter main- and tail-rotor geometry remains valid and unchanged.
- The release archive contains exactly 117 static and 117 animated files whose SHA-256 hashes match its manifest.
- `assets/exports/command/` remains unchanged from v1.4.14.

The release and MissionChief deployment may proceed only when cab, scale, static, animation and complete integrity reports all pass and the before/after and live-map cab evidence has been visually accepted.
