# v1.3.0 release checkpoint

## Baseline

- Repository baseline: tag `v1.2.7`
- MissionChief destination: graphics pack `5897`
- Declared scope: 117 static PNGs and 117 twelve-frame APNGs
- Preserved exception: slot 70 ALB remains 169×84 px

## Required gates

1. `build_mounted_pod_carriers.py --check`
2. `build_helicopter_tail_masters.py --check`
3. `build_v1_3_masters.py --check`
4. `build_v1_1_enhanced.py`
5. `validate_v1_1_enhanced.py`
6. `validate_v1_3_overhaul.py`
7. `validate_light_placement.py --report data/v1.3.0-light-placement-report.json`
8. `validate_release_scope.py`
9. `build_numbered_upload_package.py --version v1.3.0 --profile command`
10. Repeat the deterministic master, export, validation and package gates; require byte-identical output.

## Expected evidence

- `data/v1.3.0-master-report.json`
- `data/v1.3.0-build-report.json`
- `data/v1.3.0-qa-report.json`
- `data/v1.3.0-overhaul-report.json`
- `data/v1.3.0-light-placement-report.json`
- `assets/previews/v1.3.0/`
- numbered v1.3.0 ZIP and SHA-256 checksum

The release is not deployable unless every report states `"all_passed": true`, the exact 234-export scope passes against `v1.2.7`, and the repeated archive hash is identical.
