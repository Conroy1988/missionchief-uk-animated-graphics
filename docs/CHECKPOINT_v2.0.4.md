# v2.0.4 release checkpoint

## Scope

- Release master overrides: the three inherited v2.0.3 cab repairs plus ten complete mounted carriers in `assets/masters/v2.0.4/`.
- Mounted-carrier scope: MissionChief slots 42–51 only.
- Slot 41 remains the unloaded PM.
- All other vehicle artwork must remain unchanged from v2.0.3.

## Required build sequence

1. `python scripts/build_v2_cab_legibility_masters.py --check`
2. `python scripts/build_v2_mounted_pod_carriers.py --check`
3. `python scripts/build_v2_compact_exports.py`
4. `python scripts/validate_v2_static_fleet.py`
5. `python scripts/validate_v2_cab_legibility.py`
6. `python scripts/validate_v2_mounted_pod_carriers.py`
7. `python scripts/build_v2_animated_fleet.py`
8. `python scripts/validate_v2_animated_fleet.py`
9. `python scripts/build_v2_calibration.py`
10. `python scripts/build_v2_helicopter_previews.py`
11. `python scripts/build_interactive_gallery.py`
12. `python scripts/build_numbered_upload_package.py --version v2.0.4 --profile v2`
13. `python scripts/validate_v2_release_integrity.py`
14. `node --test tests/gallery.test.mjs`

## Fail-closed conditions

- Exactly thirteen release overrides must exist: three driven-appliance cabs and ten mounted carriers.
- Every carrier must preserve the approved PM front, retain its distinct role module and span enough width to contain a cab and powered road chassis.
- Cab glazing, dark structure, front wheel, grille and bumper must remain measurable at master and native map scale.
- Static exports must be exact 55% derivatives of their resolved 200×200 masters.
- APNGs must remain full-canvas, lossless, looping twelve-frame assets with visible calibrated lights at 100%, 75% and 50%.
- Only the ten intended static/APNG pairs may change against v2.0.3.
- The deployment archive must contain exactly 117 static and 117 animated files and pass SHA-256 and ZIP integrity checks.
- `assets/exports/command/` must remain unchanged from v1.4.14.

The release and MissionChief deployment may proceed only when every report returns `all_passed: true` and the mounted-carrier before/after and live-map evidence has been visually accepted.
