# v1.1.0 — Modern Command Visibility

This release upgrades the complete 117-slot TKB UK Fleet for clearer, more natural gameplay on busy MissionChief maps while preserving the original v1.0 True Scale exports.

## In-game improvements

- Independent roof-bar, grille, body and rear blue-light rhythms replace the original two-group pulse.
- Every vehicle has a deterministic timing signature, preventing a dense fleet from flashing in lockstep.
- Twelve-frame APNG animation provides smoother light and motion changes.
- Command Visibility sizing lifts small and rare units without flattening the fleet into one uniform size.
- A restrained two-tone visibility edge keeps pale, yellow and dark vehicles readable across light, dark, grayscale and satellite-style map backgrounds.
- HEMS, police and coastguard helicopters now include rotor movement.
- Appropriate non-blue-light units use amber beacons, wheel movement, navigation/wake motion or marker lights.
- Thirty-three specialist and rare assets receive stronger equipment and service cues.
- All 117 vehicles receive the modern colour, contrast, sharpness and visibility treatment.
- The medical cycle responder has been rebuilt from a new high-resolution source.

## Automated validation

The release gate covers all 117 static/animated pairs at 100%, 75% and 50% scale across four simulated map themes. It verifies transparent corners, frame-1/static identity, body stability, 12-frame APNGs, timing diversity, visible animation, half-zoom survival, outline contrast, specialist silhouette separation and exact slot coverage.

The generated `data/v1.1-qa-report.json` must contain `"all_passed": true` before the numbered MissionChief package is produced.

## Use the pack

- [TKB UK Fleet — Animated on MissionChief](https://www.missionchief.co.uk/vehicle_graphics/5897)
- [MissionChief UK Guide](https://tkb-gaming.scot/games/missionchief/guides/)
- [MissionChief Scripts & Tools](https://tkb-gaming.scot/mission-chief-scripts/)
