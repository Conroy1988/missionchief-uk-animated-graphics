# v1.2.2 — Mounted HazMat Carrier Hotfix

This hotfix replaces the standalone Hazardous Materials Pod body at MissionChief slot 49 with a complete road-going carrier. The new graphic retains the original specialist pod module but mounts it on the pack's matching three-axle prime mover, with a clearly visible cab, chassis and wheels.

## Corrected graphic

- Rebuilt both the static PNG and twelve-frame APNG for `hazardous-materials-pod`.
- Added the full UK fire-service prime-mover cab and three-axle road chassis.
- Preserved the original HazMat shelving, equipment and pod colour language.
- Added the matching four-point blue-light response pattern.
- Kept the v1.0 True Scale container-only source immutable; the mounted carrier is a command-profile override.

## Preserved production baseline

- all 117 MissionChief vehicle mappings
- the v1.2.1 clean-roofline hotfix and its 40-asset fail-closed regression gate
- twelve-frame desynchronised emergency lighting
- helicopter rotor and coastguard tail-rotor fixes
- satellite-map contrast and fleet-wide grounding shadows
- deterministic packaging and exact slot ordering

## Regression protection

The carrier master is rebuilt deterministically from the existing PM chassis and Hazardous Materials Pod module. CI fails if the committed master differs from that construction, the cab changes, the pod or three-axle chassis is incomplete, the command sprite loses its minimum mounted-vehicle width, or the four response lights disappear.

`data/v1.2.2-qa-report.json` must report `"all_passed": true` before publication.

[View the mounted carrier at 100%, 75% and 50%](../assets/previews/v1.2.2/mounted-pod-carrier-map-scale.png) · [View the dense satellite audit](../assets/previews/v1.2.2/busy-map-satellite.png)

## Use the pack

- [TKB UK Fleet — Animated on MissionChief](https://www.missionchief.co.uk/vehicle_graphics/5897)
- [MissionChief UK Guide](https://tkb-gaming.scot/games/missionchief/guides/)
- [MissionChief Scripts & Tools](https://tkb-gaming.scot/mission-chief-scripts/)
