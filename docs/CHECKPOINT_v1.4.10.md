# v1.4.10 release checkpoint

## Fixed scope

- Baseline: `v1.4.9`
- Vehicle: slot 23, Community First Responder
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
12. `python scripts/validate_community_first_responder_lighting.py`
13. `python scripts/build_prototypes.py`
14. `python scripts/validate_v1_1_enhanced.py`
15. `python scripts/validate_v1_4_overhaul.py`
16. `python scripts/validate_light_placement.py --report data/v1.4.10-light-placement-report.json`
17. `python scripts/validate_full_fleet_lighting.py`
18. `python scripts/validate_release_png_integrity.py`
19. `python scripts/validate_release_scope.py`
20. `python scripts/build_numbered_upload_package.py --version v1.4.10 --profile command`
21. `python scripts/build_interactive_gallery.py --check --site-output dist/gallery-site`
22. `node --test tests/gallery.test.mjs`

## Fail-closed Community First Responder contract

- Master dimensions: 57×23
- Command dimensions: 65×31
- Master alpha bounds: `(0, 1, 57, 23)`
- Static master roof lenses: exactly `(21, 1)` and `(24, 1)`
- Static command roof lenses: exactly `(25, 5)` and `(28, 5)`
- Maximum connected saturated-blue component in the roof housing: one pixel
- No saturated green cross-box or unexpected saturated-blue pixel anywhere in the audited roof region
- Animated response fixtures: `(25, 5)`, `(28, 5)`, `(59, 16)` and `(7, 15)`
- Both roof emitters visibly change during the 12-frame cycle
- APNG frame zero is byte-for-byte visually identical to the static PNG
- Bottom-centre map anchor remains unchanged
- Exact release scope is two command-profile files for slot 23

The release is deployable only when every gate passes and `data/v1.4.10-scope.json` reports no missing or unexpected export path.
