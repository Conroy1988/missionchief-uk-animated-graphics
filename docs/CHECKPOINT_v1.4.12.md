# v1.4.12 release checkpoint

## Fixed scope

- Baseline: `v1.4.11`
- Vehicle: slot 86, edit index 85, Control Van (SAR)
- Export changes: command static PNG and command animated APNG for this vehicle only
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
13. `python scripts/validate_armed_traffic_car_lighting.py`
14. `python scripts/validate_cbrn_vehicle_lighting.py`
15. `python scripts/validate_control_van_sar_lighting.py`
16. `python scripts/build_prototypes.py`
17. `python scripts/validate_v1_1_enhanced.py`
18. `python scripts/validate_v1_4_overhaul.py`
19. `python scripts/validate_light_placement.py --report data/v1.4.12-light-placement-report.json`
20. `python scripts/validate_full_fleet_lighting.py`
21. `python scripts/validate_release_png_integrity.py`
22. `python scripts/validate_release_scope.py`
23. `python scripts/build_numbered_upload_package.py --version v1.4.12 --profile command`
24. `python scripts/build_interactive_gallery.py --check --site-output dist/gallery-site`
25. `node --test tests/gallery.test.mjs`

## Fail-closed SAR Control Van contract

- Master dimensions: 94×57; command dimensions: 102×65
- Master alpha bounds: `(0, 1, 94, 57)`; command alpha bounds: `(3, 4, 99, 65)`
- The master differs from the toned source only at `(34, 18)` through `(54, 18)`
- Added rail alpha is exactly `(36, 18)` through `(54, 18)`; no cabinet or duplicate mast pixels are permitted
- Static master indicators: exactly `(38, 18)`, `(44, 18)` and `(50, 18)`
- Static command indicators: exactly `(42, 22)`, `(48, 22)` and `(54, 22)`
- Animated response fixtures: `(33, 23)`, `(36, 23)`, `(8, 46)` and `(92, 40)`
- Each roof emitter flashes during at least one frame while the other remains static
- The three amber command-rail indicators remain static throughout the animation
- APNG frame zero is visually identical to the static PNG; all 12 frames are full canvas
- The original front lightbar, single rear communications mast and bottom-centre map anchor remain unchanged

The release is deployable only when every gate passes and `data/v1.4.12-scope.json` reports exactly two command-profile files for slot 86, with no missing or unexpected export path.
