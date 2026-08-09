# v1.4.5 release checkpoint

## Fixed scope

- Baseline: `v1.4.4`
- Vehicle: slot 11, Rapid Response Vehicle
- Export changes: command static PNG and command animated APNG only
- Standard profile changes: none

## Required gates

1. `python scripts/build_mounted_pod_carriers.py --check`
2. `python scripts/build_helicopter_tail_masters.py --check`
3. `python scripts/build_v1_3_masters.py --check`
4. `python scripts/build_v1_4_masters.py --check`
5. `python scripts/validate_point_emitters.py`
6. `python scripts/build_v1_1_enhanced.py`
7. `python scripts/validate_irv_lighting.py`
8. `python scripts/validate_rrv_lighting.py`
9. `python scripts/build_prototypes.py`
10. `python scripts/validate_v1_1_enhanced.py`
11. `python scripts/validate_v1_4_overhaul.py`
12. `python scripts/validate_light_placement.py --report data/v1.4.5-light-placement-report.json`
13. `python scripts/validate_full_fleet_lighting.py`
14. `python scripts/validate_release_scope.py`
15. `python scripts/build_numbered_upload_package.py --version v1.4.5 --profile command`
16. `python scripts/build_interactive_gallery.py --check --site-output dist/gallery-site`
17. `node --test tests/gallery.test.mjs`

## Fail-closed RRV contract

- Master dimensions: 64×23
- Command dimensions: 72×31
- Static roof lenses: exactly `(29, 5)` and `(32, 5)`
- Maximum connected blue component in the roof housing: one pixel
- Animated response fixtures: `(29, 5)`, `(32, 5)` and `(65, 18)`
- Both roof emitters visibly change during the 12-frame cycle
- APNG frame zero is byte-for-byte visually identical to the static PNG
- Bottom-centre map anchor remains unchanged
- Exact release scope is two command-profile files for slot 11

The release is deployable only when every gate passes and `data/v1.4.5-scope.json` reports no missing or unexpected export path.
