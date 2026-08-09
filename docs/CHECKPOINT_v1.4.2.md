# v1.4.2 release checkpoint

## Baseline and scope

- Repository baseline: tag `v1.4.1`
- MissionChief destination: graphics pack `5897`
- Declared scope: all 234 animated APNGs across standard and command profiles
- Static policy: all 234 static PNGs remain visually identical to v1.4.1
- Frame policy: standard remains six frames; command remains 105 twelve-frame and 12 eighteen-frame assets
- Encoder policy: every APNG frame must cover the complete canvas with zero offsets and source blending

## Required gates

1. `python scripts/build_mounted_pod_carriers.py --check`
2. `python scripts/build_helicopter_tail_masters.py --check`
3. `python scripts/build_v1_3_masters.py --check`
4. `python scripts/build_v1_4_masters.py --check`
5. `python scripts/build_v1_1_enhanced.py`
6. `python scripts/build_prototypes.py`
7. `python scripts/validate_v1_1_enhanced.py`
8. `python scripts/validate_v1_4_overhaul.py`
9. `python scripts/validate_light_placement.py --report data/v1.4.2-light-placement-report.json`
10. `python scripts/validate_full_fleet_lighting.py`
11. `python scripts/validate_release_scope.py`
12. `python scripts/build_interactive_gallery.py --check --site-output dist/gallery-site`
13. `node --test tests/gallery.test.mjs`
14. `node --check gallery/app.mjs`
15. `node --check tools/tkb-missionchief-bulk-uploader.user.js`
16. `python scripts/build_numbered_upload_package.py --version v1.4.2 --profile command`
17. Repeat both export builds and require byte-identical APNG hashes.

## Expected evidence

- `data/v1.4.2-build-report.json`
- `data/v1.4.2-qa-report.json`
- `data/v1.4.2-overhaul-report.json`
- `data/v1.4.2-anchor-report.json`
- `data/v1.4.2-light-placement-report.json`
- `data/v1.4.2-full-fleet-lighting-report.json`
- `assets/previews/v1.4.2/`
- numbered v1.4.2 ZIP and SHA-256 checksum

The release is deployable only when every report states `"all_passed": true`, the exact 234-APNG scope passes against v1.4.1, all 2,178 APNG controls are full canvas, the box-component count is zero, every static remains visually unchanged and the four full-fleet contact sheets have been visually inspected.
