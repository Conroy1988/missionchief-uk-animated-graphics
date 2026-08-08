# v1.4.1 release checkpoint

## Baseline and scope

- Repository baseline: tag `v1.4.0`
- MissionChief destination: graphics pack `5897`
- Declared scope: 15 animated APNGs only; all 117 static PNGs remain byte-identical
- Frame policy: unchanged — 105 twelve-frame assets and 12 selected eighteen-frame motion assets
- Master artwork: unchanged v1.4.0 baked masters

## Required gates

1. `python scripts/build_mounted_pod_carriers.py --check`
2. `python scripts/build_helicopter_tail_masters.py --check`
3. `python scripts/build_v1_3_masters.py --check`
4. `python scripts/build_v1_4_masters.py --check`
5. `python scripts/build_v1_1_enhanced.py`
6. `python scripts/validate_v1_1_enhanced.py`
7. `python scripts/validate_v1_4_overhaul.py`
8. `python scripts/validate_light_placement.py --report data/v1.4.1-light-placement-report.json`
9. `python scripts/validate_fixture_accuracy.py`
10. `python scripts/validate_release_scope.py`
11. `python scripts/build_interactive_gallery.py --check --site-output dist/gallery-site`
12. `node --test tests/gallery.test.mjs`
13. `python scripts/build_numbered_upload_package.py --version v1.4.1 --profile command`
14. Repeat the export and package sequence; require byte-identical APNG and archive hashes.

## Expected evidence

- `data/v1.4.1-build-report.json`
- `data/v1.4.1-qa-report.json`
- `data/v1.4.1-overhaul-report.json`
- `data/v1.4.1-anchor-report.json`
- `data/v1.4.1-light-placement-report.json`
- `data/v1.4.1-fixture-accuracy-report.json`
- `assets/previews/v1.4.1/`
- numbered v1.4.1 ZIP and SHA-256 checksum

The release is deployable only when every report states `"all_passed": true`, the exact 15-APNG scope passes against v1.4.0, all 117 map anchors remain fixed, all 228 audited emergency-light anchors pass, every specialist equipment exclusion passes, and two complete release builds produce the same archive hash.
