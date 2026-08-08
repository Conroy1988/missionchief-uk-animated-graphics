# Checkpoint v1.2.2 — Mounted HazMat Carrier Hotfix

## Scope completed

- Corrected asset: `hazardous-materials-pod`
- MissionChief slot: 49
- Vehicle configuration: mounted pod on three-axle prime mover
- Static/animated pairs changed: 1
- Response lights added: 4
- MissionChief slot mapping changes: none
- Legacy v1.0 source changes: none

## Preserved production gates

- 117 transparent static PNGs
- 117 twelve-frame APNGs
- frame-one/static identity
- all v1.2.1 clean-roofline protections
- helicopter rotor-underlay regression
- satellite contrast and grounding-shadow thresholds
- 100%, 75% and 50% map-scale evidence

## Carrier gate

The deterministic carrier build must preserve the PM cab, mounted pod body and three-axle chassis. `data/v1.2.2-qa-report.json` must report one mounted carrier, four response lights, the expected source override and `"all_passed": true`.

v1.2.1 remains the clean-roofline baseline; v1.2.2 changes only the Hazardous Materials Pod static/APNG pair and its release evidence.
