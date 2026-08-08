# v1.4.0 release checkpoint

## Baseline and scope

- Repository baseline: tag `v1.3.0`
- MissionChief destination: graphics pack `5897`
- Declared scope: all 117 static PNGs and all 117 APNGs
- Frame policy: 105 twelve-frame assets and 12 selected eighteen-frame motion assets
- Preserved exception: slot 70 ALB remains exactly 169×84 px

## Required gates

1. `python scripts/build_mounted_pod_carriers.py --check`
2. `python scripts/build_helicopter_tail_masters.py --check`
3. `python scripts/build_v1_3_masters.py --check`
4. `python scripts/build_v1_4_masters.py --check`
5. `python scripts/build_v1_1_enhanced.py`
6. `python scripts/validate_v1_1_enhanced.py`
7. `python scripts/validate_v1_4_overhaul.py`
8. `python scripts/validate_light_placement.py --report data/v1.4.0-light-placement-report.json`
9. `python scripts/validate_release_scope.py`
10. `python scripts/build_numbered_upload_package.py --version v1.4.0 --profile command`
11. Repeat the deterministic master, export, validation and package sequence; require byte-identical output.

## Expected evidence

- `data/v1.4.0-master-report.json`
- `data/v1.4.0-build-report.json`
- `data/v1.4.0-qa-report.json`
- `data/v1.4.0-overhaul-report.json`
- `data/v1.4.0-anchor-report.json`
- `data/v1.4.0-light-placement-report.json`
- `assets/previews/v1.4.0/`
- numbered v1.4.0 ZIP and SHA-256 checksum

The release is deployable only when every report states `"all_passed": true`, the exact 234-export scope passes against `v1.3.0`, all 117 map anchors remain fixed, all 196 emergency-light anchors pass, and two complete release builds produce the same archive hash.
