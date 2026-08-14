# v1.4.11 release checkpoint

## Fixed scope

- Baseline: `v1.4.10`
- Vehicles: slot 26, Armed Traffic Car; slot 33, CBRN Vehicle
- Export changes: command static PNG and command animated APNG for both vehicles only
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
15. `python scripts/build_prototypes.py`
16. `python scripts/validate_v1_1_enhanced.py`
17. `python scripts/validate_v1_4_overhaul.py`
18. `python scripts/validate_light_placement.py --report data/v1.4.11-light-placement-report.json`
19. `python scripts/validate_full_fleet_lighting.py`
20. `python scripts/validate_release_png_integrity.py`
21. `python scripts/validate_release_scope.py`
22. `python scripts/build_numbered_upload_package.py --version v1.4.11 --profile command`
23. `python scripts/build_interactive_gallery.py --check --site-output dist/gallery-site`
24. `node --test tests/gallery.test.mjs`

## Fail-closed Armed Traffic Car contract

- Master dimensions: 66×26
- Command dimensions: 74×34; v1.4.10 defective baseline: 74×36
- Master alpha bounds: `(0, 1, 66, 26)`
- Command alpha bounds: `(3, 4, 71, 34)`
- Static master roof lenses: exactly `(26, 1)` and `(32, 1)`
- Static command roof lenses: exactly `(30, 5)` and `(36, 5)`
- Maximum connected saturated-blue component in the roof housing: one pixel
- No unexpected saturated-blue pixel anywhere in the audited roof region
- Animated response fixtures: `(30, 5)`, `(36, 5)`, `(67, 17)` and `(7, 17)`
- Each roof emitter flashes during at least one frame while the other remains static
- APNG frame zero is visually identical to the static PNG; all 12 frames are full canvas
- Bottom-centre map anchor remains unchanged

## Fail-closed CBRN Vehicle contract

- Master dimensions: 88×46
- Command dimensions: 96×54; v1.4.10 defective baseline: 96×57
- Master alpha bounds: `(0, 1, 88, 46)`
- Command alpha bounds: `(3, 6, 93, 54)`
- Added detector geometry: exactly one row spanning `(35, 4)` through `(53, 4)`, with no cabinet or mast pixels above it
- Static master detector indicators: exactly `(37, 4)`, `(43, 4)` and `(49, 4)`
- Static command detector indicators: exactly `(41, 8)`, `(47, 8)` and `(53, 8)`
- Animated response fixtures: `(13, 13)`, `(16, 13)`, `(43, 13)`, `(57, 13)`, `(91, 34)` and `(8, 32)`
- All six response emitters flash; both roof pairs demonstrate independent activity
- Detector indicator pixels remain static throughout the animation
- APNG frame zero is visually identical to the static PNG; all 12 frames are full canvas
- Bottom-centre map anchor remains unchanged

The release is deployable only when every gate passes and `data/v1.4.11-scope.json` reports exactly four command-profile files for slots 26 and 33, with no missing or unexpected export path.
