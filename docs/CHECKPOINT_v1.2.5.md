# Checkpoint v1.2.5 — Complete Helicopter Tails

## Scope completed

- Corrected assets: `hems`, `police-helicopter`, `coastguard-rescue-helicopter`, `coastguard-rescue-helicopter-large`
- MissionChief slots: 10, 12, 65 and 66
- Static/animated pairs changed from v1.2.4: 4
- MissionChief slot mapping changes: none
- Legacy v1.0 source changes: none
- Main-rotor cleanup scope: rotor sweep only, never full canvas width
- HEMS and Police upper fins/fenestrons: complete
- Coastguard external tail rotors: complete
- Safe edge allowance: 10 pixels per helicopter
- Minimum transparent tail margin: 6 pixels

## Preserved production gates

- 117 transparent static PNGs
- 117 twelve-frame APNGs
- frame-one/static identity
- all v1.2.1 clean-roofline protections
- all ten mounted specialist-carrier identities
- helicopter main-rotor underlay protection
- satellite contrast and grounding-shadow thresholds
- 100%, 75% and 50% map-scale evidence

## Structural tail gate

The validation suite measures the upper-left tail region in every static export and every APNG frame. It requires at least 550 strong-alpha pixels for HEMS, 500 for Police Helicopter, 550 for Coastguard Rescue Helicopter and 600 for Coastguard Rescue Helicopter (Large).

This gate detects the actual failure mode from v1.2.4: blank transparent clearance could previously pass even when the tail fin or rotor had been erased. `data/v1.2.5-qa-report.json` must report all four structural thresholds, a minimum six-pixel tail margin and `"all_passed": true`.

The release-scope gate compares the built exports to `v1.2.4` and must report exactly four changed static/APNG pairs with no unrelated fleet drift.
