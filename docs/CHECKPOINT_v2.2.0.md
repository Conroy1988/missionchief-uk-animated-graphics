# v2.2.0 release checkpoint

## Release scope

- Artwork baseline: all v2.1.1 masters and sources preserved without modification.
- Live deployment scope: all 117 animated MissionChief slots.
- Outputs: 117 static PNGs and 117 infinitely looping response APNGs on the 110×110 canvas.
- Animation distribution: 111 × 2-frame road assets and 6 × 4-frame aircraft/marine assets.
- Compatibility: complete-frame APNG controls, disposal 0, blend 0 and infinite looping.

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
11. `python scripts/validate_v2_performance.py`
12. `python scripts/build_v2_calibration.py`
13. `python scripts/build_v2_helicopter_previews.py`
14. `python scripts/build_interactive_gallery.py`
15. `node --test tests/gallery.test.mjs`
16. `python scripts/build_numbered_upload_package.py --version v2.2.0 --profile v2`
17. `python scripts/validate_v2_release_integrity.py`

## Performance gates

- Frame reduction: at least 80% against v2.1.1.
- Encoded APNG reduction: at least 75%.
- Road update-rate reduction: at least 65%.
- Road update rate: no more than 4 Hz.
- Aircraft/marine update rate: no more than 6 Hz.
- Static files preserved: 117/117 exact SHA-256 matches.
- Master/source artwork drift: none.

## Verified local result

- Static QA: 117/117 passed.
- Animation QA: 117/117 passed.
- Family hero gate: 117/117 passed across 18 families.
- Frame distribution: 111 × 2 frames and 6 × 4 frames.
- Total frames: 1,440 → 246 (**82.9% reduction**).
- Encoded APNG data: 13,054,362 → 2,267,212 bytes (**82.6% reduction**).
- Full-cycle decoded RGBA data: 69,696,000 → 11,906,400 bytes.
- Road update rate: 12.371 → 3.846 Hz (**68.9% reduction**).
- Static SHA-256 preservation: 117/117.
- Numbered package: 117 static plus 117 animated files.
- Release archive SHA-256: `293f94c5b5fb4268c572157145220757704ae595feb978a2e3d6be6ee4c9dbc1`.
- Release-integrity errors: none.

The MissionChief live pack is updated only from the numbered archive produced by the exact release commit. The v2.1.1 tag and package remain the rollback baseline.
