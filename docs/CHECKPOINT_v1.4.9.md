# v1.4.9 release checkpoint

## Fixed scope

- Baseline: `v1.4.8`
- Vehicle: slot 21, Operational Team Leader
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
11. `python scripts/validate_otl_lighting.py`
12. `python scripts/build_prototypes.py`
13. `python scripts/validate_v1_1_enhanced.py`
14. `python scripts/validate_v1_4_overhaul.py`
15. `python scripts/validate_light_placement.py --report data/v1.4.9-light-placement-report.json`
16. `python scripts/validate_full_fleet_lighting.py`
17. `python scripts/validate_release_scope.py`
18. `python scripts/build_numbered_upload_package.py --version v1.4.9 --profile command`
19. `python scripts/build_interactive_gallery.py --check --site-output dist/gallery-site`
20. `node --test tests/gallery.test.mjs`

## Fail-closed OTL contract

- Master dimensions: 65×27
- Command dimensions: 73×35
- Master alpha bounds: `(0, 1, 65, 27)`
- Static master roof lenses: exactly `(27, 1)` and `(30, 1)`
- Static command roof lenses: exactly `(31, 5)` and `(34, 5)`
- Maximum connected saturated-blue component in the roof housing: one pixel
- No saturated green mast or unexpected saturated-blue pixel anywhere in the audited roof region
- Animated response fixtures: `(31, 5)`, `(34, 5)`, `(67, 19)` and `(7, 16)`
- Both roof emitters visibly change during the 12-frame cycle
- APNG frame zero is byte-for-byte visually identical to the static PNG
- Bottom-centre map anchor remains unchanged
- Exact release scope is two command-profile files for slot 21

The release is deployable only when every gate passes and `data/v1.4.9-scope.json` reports no missing or unexpected export path.
