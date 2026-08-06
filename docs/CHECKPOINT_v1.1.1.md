# Checkpoint v1.1.1 — Helicopter Rotor Refinement

## Scope completed

- Baked main-rotor removal: 4/4 helicopters
- Per-aircraft main-hub geometry: 4/4 helicopters
- Edge-on main-rotor sweep: 4/4 helicopters
- Coastguard external tail-rotor animation: 2/2 helicopters
- HEMS and police fenestron preservation: 2/2 helicopters
- Static-under-moving rotor regression gate: enabled

## Production totals

- Static transparent PNGs: 117
- Animated APNGs: 117
- Frames per APNG: 12
- MissionChief slots changed: 4 helicopter rows only
- MissionChief slot mapping changes: none

## Automated QA

The full Modern Command Visibility release gate must report `"all_passed": true`. In addition to the existing map, animation, timing, alpha, alignment and silhouette checks, every helicopter now has an explicit maximum for strong pixels inside the cleaned source-blade region.

## Reversibility

The immutable v1.0 True Scale files remain unchanged. The four prior v1.1.0 helicopter pairs can be restored independently if rollback is ever required.
