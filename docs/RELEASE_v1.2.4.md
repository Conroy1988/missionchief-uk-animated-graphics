# v1.2.4 — HVP & Helicopter Tail Hotfix

This release corrects the final fire-service specialist module that appeared to drive independently and removes the residual tail-edge clipping from all four helicopters.

## Corrected graphic

- HVP — slot 51

Both the static PNG and twelve-frame APNG now include a clearly visible UK fire-service cab, powered road chassis, three axles and wheels. The original HVP pump, large-diameter hose banks and water manifolds remain mounted behind the cab, with a restrained four-point blue-light response pattern.

## Corrected helicopter tails

- HEMS — slot 10
- Police Helicopter — slot 12
- Coastguard Rescue Helicopter — slot 65
- Coastguard Rescue Helicopter (Large) — slot 66

HEMS and Police Helicopter now use deterministic full-tail masters rebuilt from the retained high-resolution source artwork, restoring the complete fenestron surround instead of inheriting the clipped left edge from the old map-scale source. All four helicopter exports now have a dedicated ten-pixel edge allowance, and every static/APNG frame must retain at least six transparent pixels behind the tail.

## Preserved production baseline

- all 117 MissionChief vehicle mappings
- all nine mounted pod carriers from v1.2.3
- the v1.2.1 clean-roofline hotfix and its 40-asset fail-closed regression gate
- twelve-frame desynchronised emergency lighting
- helicopter main-rotor and animated coastguard tail-rotor fixes
- satellite-map contrast and fleet-wide grounding shadows
- deterministic packaging and exact slot ordering
- the immutable v1.0 True Scale module-only source

## Regression protection

CI rebuilds all ten specialist carriers from the established PM chassis and their original modules. It rejects a changed cab, incomplete HVP equipment module, damaged chassis, insufficient road-vehicle width or missing response lights.

It also rebuilds the HEMS and Police full-tail masters deterministically, validates the complete four-helicopter rotor set and fails any frame whose tail margin drops below six pixels.

The release-scope gate compares against tag `v1.2.3` and fails unless exactly five static/APNG pairs change: HVP and the four helicopters. `data/v1.2.4-qa-report.json` must report ten mounted carriers, a minimum helicopter tail margin of at least six pixels and `"all_passed": true` before publication.

[View all specialist carriers at 100%, 75% and 50%](../assets/previews/v1.2.4/mounted-specialist-carrier-map-scale.png) · [View all twelve helicopter frames](../assets/previews/v1.2.4/helicopter-rotor-frames.png) · [View the dense satellite audit](../assets/previews/v1.2.4/busy-map-satellite.png)

## Use the pack

- [TKB UK Fleet — Animated on MissionChief](https://www.missionchief.co.uk/vehicle_graphics/5897)
- [MissionChief UK Guide](https://tkb-gaming.scot/games/missionchief/guides/)
- [MissionChief Scripts & Tools](https://tkb-gaming.scot/mission-chief-scripts/)
