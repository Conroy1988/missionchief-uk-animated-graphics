# v1.2.5 — Complete Helicopter Tails

This release repairs the four helicopter tails that remained visibly incomplete after v1.2.4. The earlier hotfix added transparent clearance but did not prevent the main-rotor cleanup mask from deleting real tail pixels.

## Corrected helicopter graphics

- HEMS — slot 10
- Police Helicopter — slot 12
- Coastguard Rescue Helicopter — slot 65
- Coastguard Rescue Helicopter (Large) — slot 66

HEMS and Police Helicopter now retain their complete upper fin and enclosed fenestron structures. Both Coastguard helicopters retain the full external tail-rotor blades and tips instead of losing the upper half of the rotor during main-rotor cleanup.

The fix constrains main-rotor removal to the actual main-rotor sweep. It no longer uses a full-width eraser across the top of the aircraft. All four response APNGs retain twelve frames, complete tails and aligned main-rotor motion.

## Stronger regression protection

The original clearance test remains active, but it is no longer sufficient by itself. CI now also counts structural alpha pixels in the upper-tail region of every static image and every APNG frame. A blank margin cannot pass as a complete tail.

The new minimum upper-tail requirements are:

- HEMS: 550 structural pixels
- Police Helicopter: 500 structural pixels
- Coastguard Rescue Helicopter: 550 structural pixels
- Coastguard Rescue Helicopter (Large): 600 structural pixels

## Preserved production baseline

- all 117 MissionChief vehicle mappings
- all ten mounted specialist carriers, including HVP
- all v1.2.1 clean-roofline protections
- twelve-frame desynchronised emergency lighting
- satellite-map contrast and fleet-wide grounding shadows
- deterministic packaging and exact slot ordering
- the immutable v1.0 True Scale source profile

The release-scope gate compares against tag `v1.2.4` and fails unless exactly four static/APNG pairs change: the four helicopters above. `data/v1.2.5-qa-report.json` must report complete upper-tail structures, safe tail clearance and `"all_passed": true` before publication.

[View helicopter tails at 100%, 75% and 50%](../assets/previews/v1.2.5/complete-helicopter-tails-map-scale.png) · [View the twelve-frame helicopter audit](../assets/previews/v1.2.5/helicopter-rotor-frames.png) · [View the dense satellite audit](../assets/previews/v1.2.5/busy-map-satellite.png)

## Use the pack

- [TKB UK Fleet — Animated on MissionChief](https://www.missionchief.co.uk/vehicle_graphics/5897)
- [MissionChief UK Guide](https://tkb-gaming.scot/games/missionchief/guides/)
- [MissionChief Scripts & Tools](https://tkb-gaming.scot/mission-chief-scripts/)
