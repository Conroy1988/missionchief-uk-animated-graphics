# v1.4.13 release checkpoint

## Fixed scope

- Baseline: `v1.4.12`
- Vehicle: slot 90, edit index 89, Drone Vehicle (SAR HQ)
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
16. `python scripts/validate_drone_vehicle_sar_hq_lighting.py`
17. `python scripts/build_prototypes.py`
18. `python scripts/validate_v1_1_enhanced.py`
19. `python scripts/validate_v1_4_overhaul.py`
20. `python scripts/validate_light_placement.py --report data/v1.4.13-light-placement-report.json`
21. `python scripts/validate_full_fleet_lighting.py`
22. `python scripts/validate_release_png_integrity.py`
23. `python scripts/validate_release_scope.py`
24. `python scripts/build_numbered_upload_package.py --version v1.4.13 --profile command`
25. `python scripts/build_interactive_gallery.py --check --site-output dist/gallery-site`
26. `node --test tests/gallery.test.mjs`

## Fail-closed SAR Drone Vehicle contract

- Master dimensions: 81×45; command dimensions: 89×53
- Master alpha bounds: `(0, 1, 81, 45)`; command alpha bounds: `(3, 4, 86, 53)`
- The master differs from the toned source only at `(40, 13)`, `(35, 14)` through `(45, 14)`, and `(30, 15)` through `(51, 15)`
- Added stowage alpha is exactly `(40, 13)`, `(35, 14)` through `(45, 14)`, and `(30, 15)` through `(48, 15)`; no raised launch-box or spread-rotor pixels are permitted
- Static master stowage markers: exactly `(35, 14)` and `(45, 14)`
- Static command stowage markers: exactly `(39, 18)` and `(49, 18)`
- Folded airframe pixels: exactly `(40, 13)` and `(38, 14)` through `(42, 14)`
- Animated response fixtures: `(38, 20)`, `(6, 34)` and `(80, 34)`
- Each response emitter flashes during at least one frame
- The folded-drone rail and its two markers remain static throughout the animation
- APNG frame zero is visually identical to the static PNG; all 12 frames are full canvas
- The original emergency lightbar, rear communications mast and bottom-centre map anchor remain unchanged

The release is deployable only when every gate passes and `data/v1.4.13-scope.json` reports exactly two command-profile files for slot 90, with no missing or unexpected export path.
