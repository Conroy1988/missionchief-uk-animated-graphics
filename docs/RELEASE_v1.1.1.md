# v1.1.1 — Helicopter Rotor Refinement

This patch corrects the helicopter rotor presentation in the complete TKB UK Emergency Fleet while preserving all 117 MissionChief vehicle mappings and the v1.1 Modern Command Visibility profile.

## Improvements

- Removes the sharp source blades that previously remained visible underneath the animated main-rotor overlay.
- Aligns the rotor hub independently for HEMS, police and both coastguard helicopter silhouettes.
- Replaces the generic bright blade line with a restrained edge-on high-speed rotor sweep.
- Rebuilds both coastguard external tail rotors as genuinely rotating layers.
- Stops adding a second synthetic cross to the enclosed HEMS and police fenestrons.
- Preserves the existing independent blue-light rhythms, vehicle dimensions and MissionChief slot order.

## Validation

All 117 static/animated pairs are rebuilt and tested at 100%, 75% and 50% scale against light, dark, satellite-style and grayscale backgrounds. The release gate verifies exact slot coverage, transparent corners, frame-one/static identity, animation presence, body stability, timing diversity, half-zoom survival, edge contrast and specialist silhouette separation.

The v1.1.1 gate adds a rotor-underlay regression check. It measures the cleaned blade region on every helicopter and fails if a strong static blade layer returns beneath the animated sweep.

[View the twelve-frame audit for all four helicopters](../assets/previews/v1.1/helicopter-rotor-frames.png).

## Use the pack

- [TKB UK Fleet — Animated on MissionChief](https://www.missionchief.co.uk/vehicle_graphics/5897)
- [MissionChief UK Guide](https://tkb-gaming.scot/games/missionchief/guides/)
- [MissionChief Scripts & Tools](https://tkb-gaming.scot/mission-chief-scripts/)
