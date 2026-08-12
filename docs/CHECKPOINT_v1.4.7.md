# v1.4.7 release checkpoint

## Fixed scope

- Baseline: `v1.4.6`
- Vehicle: slot 20, Joint Response Unit
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
9. `python scripts/validate_arv_lighting.py`
10. `python scripts/validate_joint_response_unit_lighting.py`
11. `python scripts/build_prototypes.py`
12. `python scripts/validate_v1_1_enhanced.py`
13. `python scripts/validate_v1_4_overhaul.py`
14. `python scripts/validate_light_placement.py --report data/v1.4.7-light-placement-report.json`
15. `python scripts/validate_full_fleet_lighting.py`
16. `python scripts/validate_release_scope.py`
17. `python scripts/build_numbered_upload_package.py --version v1.4.7 --profile command`
18. `python scripts/build_interactive_gallery.py --check --site-output dist/gallery-site`
19. `node --test tests/gallery.test.mjs`

## Fail-closed Joint Response Unit contract

- Master dimensions: 64×22
- Command dimensions: 72×30
- Static roof lenses: exactly `(32,5)` and `(37,5)`
- Maximum connected blue component in the roof housing: one pixel
- Animated response fixtures: `(32,5)`, `(37,5)`, `(66,16)` and `(7,15)`
- Both roof emitters visibly change during the 12-frame cycle
- APNG frame zero is byte-for-byte visually identical to the static PNG
- Bottom-centre map anchor remains unchanged
- Exact release scope is two command-profile files for slot 20

The release is deployable only when every gate passes and `data/v1.4.7-scope.json` reports no missing or unexpected export path.
