# v1.4.14 release checkpoint

## Fixed scope

- Baseline: `v1.4.13`
- Vehicles: slots 62, 68, 71, 72, 75, 82, 85, 88 and 89
- Export changes: command static PNG and command animated APNG for those nine vehicles only
- Standard profile changes: none

## Required gates

1. `python scripts/build_mounted_pod_carriers.py --check`
2. `python scripts/build_helicopter_tail_masters.py --check`
3. `python scripts/build_v1_3_masters.py --check`
4. `python scripts/build_v1_4_masters.py --check`
5. `python scripts/build_trailer_tow_masters.py --check`
6. `python scripts/validate_point_emitters.py`
7. `python scripts/build_v1_1_enhanced.py`
8. Run all ten existing vehicle-specific lighting and roof-equipment validators.
9. `python scripts/validate_trailer_tow_composites.py`
10. `python scripts/build_prototypes.py`
11. `python scripts/validate_v1_1_enhanced.py`
12. `python scripts/validate_v1_4_overhaul.py`
13. `python scripts/validate_light_placement.py --report data/v1.4.14-light-placement-report.json`
14. `python scripts/validate_full_fleet_lighting.py`
15. `python scripts/validate_release_png_integrity.py`
16. `python scripts/validate_release_scope.py`
17. `python scripts/build_numbered_upload_package.py --version v1.4.14 --profile command`
18. `python scripts/build_interactive_gallery.py --check --site-output dist/gallery-site`
19. `node --test tests/gallery.test.mjs`

## Fail-closed complete towing-unit contract

- Exactly nine IDs appear in `towed_units`, `motion.trailer`, `trailer_marker_geometry` and the deterministic tow-master report.
- Every release-specific master contains both a declared tow vehicle and trailer, retains at least 500 strong-alpha pixels from each component and has a connected hitch.
- The master report declares `bare_trailers_remaining: 0` and `all_passed: true`.
- Production source overrides point to `assets/masters/v1.4.14/<asset-id>.png` for all nine units.
- Command body widths equal each declared combined road length at 13 pixels per metre.
- Eight blue-response units expose exactly three fixture-aligned point emitters; the airfield unit exposes zero blue emitters and uses amber motion.
- Rear marker geometry is on the left for right-facing towing units and on the right for left-facing towing units.
- Static/APNG dimensions match, APNG frame zero equals the static PNG, at least three later frames visibly change and all frames remain full canvas.
- Static and animated bottom-centre map anchors do not move.

The release is deployable only when every gate passes and `data/v1.4.14-scope.json` reports exactly 18 command-profile files for the nine declared slots, with no missing or unexpected export path.
