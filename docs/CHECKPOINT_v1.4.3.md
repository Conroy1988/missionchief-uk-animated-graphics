# v1.4.3 release checkpoint

## Baseline and scope

- Repository baseline: tag `v1.4.2`
- MissionChief destination: graphics pack `5897`
- Changed scope: 87 standard animated APNGs and 97 command animated APNGs
- Static policy: all 234 static PNGs remain visually identical to v1.4.2
- Shape policy: one-pixel point lamps; connected response-light components may not exceed 2×2 pixels
- Encoder policy: every APNG frame must cover the complete canvas with zero offsets and source blending

## Required gates

1. `python scripts/build_mounted_pod_carriers.py --check`
2. `python scripts/build_helicopter_tail_masters.py --check`
3. `python scripts/build_v1_3_masters.py --check`
4. `python scripts/build_v1_4_masters.py --check`
5. `python scripts/validate_point_emitters.py`
6. `python scripts/build_v1_1_enhanced.py`
7. `python scripts/build_prototypes.py`
8. `python scripts/validate_v1_1_enhanced.py`
9. `python scripts/validate_v1_4_overhaul.py`
10. `python scripts/validate_light_placement.py --report data/v1.4.3-light-placement-report.json`
11. `python scripts/validate_full_fleet_lighting.py`
12. `python scripts/validate_release_scope.py`
13. `python scripts/build_interactive_gallery.py --check --site-output dist/gallery-site`
14. `node --test tests/gallery.test.mjs`
15. `node --check gallery/app.mjs`
16. `node --check tools/tkb-missionchief-bulk-uploader.user.js`
17. `python scripts/build_numbered_upload_package.py --version v1.4.3 --profile command`
18. Repeat both export builds and require byte-identical APNG hashes.

## Expected evidence

- `data/v1.4.3-build-report.json`
- `data/v1.4.3-qa-report.json`
- `data/v1.4.3-overhaul-report.json`
- `data/v1.4.3-anchor-report.json`
- `data/v1.4.3-light-placement-report.json`
- `data/v1.4.3-full-fleet-lighting-report.json`
- `assets/previews/v1.4.3/`
- numbered v1.4.3 ZIP and SHA-256 checksum

The release is deployable only when every report passes, the exact 184-APNG scope matches v1.4.2, all 2,178 APNG controls are full canvas, all 602 lamp coordinates are inspected, the maximum connected light component is no larger than 2×2, and the bar, box, oversized, escaped-pixel, and hidden-RGB counts are zero.
