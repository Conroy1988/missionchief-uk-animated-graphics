# v2.1.0 release checkpoint

## Release scope

- Base masters: 117 preserved v2.0.0 direction-neutral vehicles.
- Inherited overrides: all 13 v2.0.4 cab and mounted-carrier corrections, byte-preserved in `assets/masters/v2.1.0/`.
- New overrides: 11 UK family-authentic conversions built from retained sources in `assets/sources/v2.1.0/`.
- Outputs: 117 static PNGs and 117 infinitely looping response APNGs on the 110×110 MissionChief canvas.
- Hero standard: 117/117 ready across 18 families, zero conversion backlog and zero cross-family conflicts.

## Required build and validation order

1. `python scripts/build_v2_uk_family_conversions.py --check`
2. `python scripts/build_v2_cab_legibility_masters.py --check`
3. `python scripts/build_v2_mounted_pod_carriers.py --check`
4. `python scripts/build_v2_compact_exports.py`
5. `python scripts/validate_v2_static_fleet.py`
6. `python scripts/validate_v2_cab_legibility.py`
7. `python scripts/validate_v2_mounted_pod_carriers.py`
8. `python scripts/validate_v2_uk_family_hero_gate.py`
9. `python scripts/build_v2_animated_fleet.py`
10. `python scripts/validate_v2_animated_fleet.py`
11. `python scripts/build_v2_calibration.py`
12. `python scripts/build_v2_helicopter_previews.py`
13. `python scripts/build_interactive_gallery.py`
14. `node --test tests/gallery.test.mjs`
15. `python scripts/build_numbered_upload_package.py --version v2.1.0 --profile v2`
16. `python scripts/validate_v2_release_integrity.py`

## Verified local result

- Static: 117/117 passed.
- Animation: 117/117 passed.
- Hero gate: 117/117 passed in enforcement mode.
- Package: 117 numbered static plus 117 numbered animated assets.
- Frame distribution: 111 × 12 frames; 6 × 18 frames.
- Gallery tests: 7/7 passed.
- Release archive SHA-256: `ec8dcf607ee53661395063208a7020b025603a126e4a2ac588465f8d806c84b2`.
- Release-integrity errors: none.

The MissionChief live pack is updated only after the exact release commit lands and the generated archive is reverified against this checkpoint.
