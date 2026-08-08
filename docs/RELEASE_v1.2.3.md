# v1.2.3 — Complete Mounted Pod Fleet

This release finishes the mounted fire-service pod family. The eight remaining standalone pod bodies at MissionChief slots 42–48 and 50 now travel on complete three-axle prime-mover carriers, matching the Hazardous Materials Pod correction introduced in v1.2.2.

## Corrected graphics

- Water Pod — slot 42
- Bulk Foam Pod — slot 43
- Rescue Pod — slot 44
- Command Pod — slot 45
- Welfare Pod — slot 46
- BASU Pod — slot 47
- Misting Pod — slot 48
- OSU Pod — slot 50

Each static PNG and twelve-frame APNG now includes a clearly visible UK fire-service cab, powered road chassis, three axles and wheels. The original role-specific module remains mounted behind the cab, and every carrier uses the same restrained four-point blue-light response language.

The v1.2.2 Hazardous Materials Pod carrier at slot 49 remains byte-identical in the exported pack, giving all nine pod roles one coherent road-going family.

## Preserved production baseline

- all 117 MissionChief vehicle mappings
- the v1.2.1 clean-roofline hotfix and its 40-asset fail-closed regression gate
- the v1.2.2 Hazardous Materials Pod carrier
- twelve-frame desynchronised emergency lighting
- helicopter rotor and coastguard tail-rotor fixes
- satellite-map contrast and fleet-wide grounding shadows
- deterministic packaging and exact slot ordering
- the immutable v1.0 True Scale container-only sources

## Regression protection

CI rebuilds all nine carrier masters from the established PM chassis and original pod modules. It rejects a missing pod role, changed cab, incomplete module, damaged chassis, insufficient mounted-vehicle width or missing response lights.

The release-scope gate compares against tag `v1.2.2` and fails unless exactly the intended eight static/APNG pairs changed. `data/v1.2.3-qa-report.json` must report nine mounted carriers and `"all_passed": true` before publication.

[View all mounted carriers at 100%, 75% and 50%](../assets/previews/v1.2.3/mounted-pod-carrier-map-scale.png) · [View the dense satellite audit](../assets/previews/v1.2.3/busy-map-satellite.png)

## Use the pack

- [TKB UK Fleet — Animated on MissionChief](https://www.missionchief.co.uk/vehicle_graphics/5897)
- [MissionChief UK Guide](https://tkb-gaming.scot/games/missionchief/guides/)
- [MissionChief Scripts & Tools](https://tkb-gaming.scot/mission-chief-scripts/)
