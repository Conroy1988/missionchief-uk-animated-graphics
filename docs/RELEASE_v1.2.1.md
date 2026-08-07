# v1.2.1 — Clean Roofline Hotfix

This hotfix removes the artificial coloured roof bars introduced by v1.2.0 while preserving the rest of Modern Command Clarity across all 117 MissionChief vehicle mappings.

## Corrected graphics

- Removed all 15 generated role-differentiation overlays.
- Removed all 25 generated specialist-equipment overlays.
- Rebuilt both the static PNG and animated APNG for every slot from the clean source profile.
- Prevented the 40 corrected vehicles from falling back to the older generic roof-cue treatment.

The affected inventory includes the JRU/IRV and RRV groups, OTL/CFR, Armed Traffic/ARV, the EOD fleet, command and control units, specialist pods, drone vehicles, coastguard assets, rescue-watercraft trailers, RRU and EIU.

## Preserved v1.2 improvements

- twelve-frame desynchronised emergency lighting
- all 11 fleet phase offsets and 48 visible light-activity signatures
- helicopter rotor fixes and coastguard tail-rotor animation
- satellite-map contrast treatment
- road, marine and aerial grounding shadows
- Command Visibility sizing and exact 117-slot mapping

## Regression protection

The release gate now fails if generated role or specialist overlay maps are re-enabled, if the retired inventory is not exactly 15 + 25 assets, or if any of those 40 vehicles gains synthetic top padding. Dedicated 100%, 75% and 50% roofline sheets provide visual evidence for both corrected groups.

`data/v1.2.1-qa-report.json` must report `"all_passed": true` before publication.

[View corrected role rooflines](../assets/previews/v1.2.1/corrected-role-rooflines-map-scale.png) · [View corrected specialist rooflines](../assets/previews/v1.2.1/corrected-specialist-rooflines-map-scale.png) · [View the crowded-response audit](../assets/previews/v1.2.1/desynchronised-lights-crowd.png)

## Use the pack

- [TKB UK Fleet — Animated on MissionChief](https://www.missionchief.co.uk/vehicle_graphics/5897)
- [MissionChief UK Guide](https://tkb-gaming.scot/games/missionchief/guides/)
- [MissionChief Scripts & Tools](https://tkb-gaming.scot/mission-chief-scripts/)
