# v1.2.0 — Modern Command Clarity

This release makes commonly confused UK fleet roles easier to identify, strengthens specialist capability cues, prevents crowded incidents flashing in lockstep and grounds every icon more naturally on the map while preserving all 117 MissionChief vehicle mappings.

## Role differentiation

Fifteen assets now use restrained, role-specific equipment silhouettes rather than colour-only cues:

- Joint Response Unit and Police IRV
- all three RRV variants, including Specialist Paramedic RRV
- OTL and Community First Responder
- Armed Traffic Car and Armed Response Vehicle
- EOD Commander, response, medium equipment, heavy equipment and both marine EOD variants

The equipment language includes command pods, medical modules, aerials, ANPR pods, equipment cases, canisters and marine-response kit. These cues are built deterministically into both static and animated exports.

## Satellite-map clarity

The 15 weakest satellite performers from v1.1.1 receive a reinforced dual edge and shadow treatment. This covers Rescue Pod, M-RAV, Hazardous Materials Pod, Welfare Pod, ILB, OSU Pod, Mountain Rescue 4x4, Fire-station Drone Vehicle, Firearms Personnel Carrier, Armed Cell Van, Hovercraft Transporter, BASU Pod and three EOD assets.

The minimum targeted satellite edge-contrast score rises from **24.36** to **53.24**.

## Desynchronised emergency lighting

The 87 blue-response assets now occupy all **11** active fleet phase offsets and produce **48** visible light-activity signatures. Roof, grille, body and rear fittings receive their own deterministic sub-phases, so large incidents retain varied emergency-light rhythms while every rebuild remains byte-reproducible.

## Specialist equipment and grounding

Twenty-five further specialist assets gain role-authentic equipment that remains visible at 50% scale: command masts, drone cradles, rescue and rope gear, BA/HazMat cylinders, pod modules, tactical lockers, watercraft frames, mass-casualty cases and evidence-camera equipment. Existing aerial ladders, platforms and boat silhouettes remain unchanged where they were already clear, avoiding duplicated equipment.

All 117 icons now use a compact contact shadow. Road vehicles, watercraft and aircraft receive separate treatments, replacing the old full-silhouette drop-shadow effect that could make icons appear to float.

## Validation

- 117 static PNGs and 117 twelve-frame APNGs
- exact 117-slot MissionChief mapping retained
- 100%, 75% and 50% scale tests
- light, dark, grayscale and satellite-style map tests
- role-group silhouette regression checks
- eleven-bucket fleet phase and light-activity diversity checks
- specialist-equipment and grounding-shadow survival checks at 50% scale
- targeted satellite-contrast release gate
- frame-one/static identity, transparent corners, animation cadence and body-stability checks
- v1.1.1 helicopter rotor-underlay regression checks retained
- deterministic numbered ZIP metadata, so identical validated inputs produce the same release checksum

The generated `data/v1.2-qa-report.json` reports `"all_passed": true`.

[View the crowded-response light audit](../assets/previews/v1.2/desynchronised-lights-crowd.png) · [View the specialist-equipment audit](../assets/previews/v1.2/specialist-equipment-map-scale.png) · [View the grounding-shadow audit](../assets/previews/v1.2/grounding-shadows-map-scale.png) · [View the role-differentiation audit](../assets/previews/v1.2/role-differentiation-map-scale.png) · [View the satellite-contrast audit](../assets/previews/v1.2/satellite-contrast-map-scale.png)

## Use the pack

- [TKB UK Fleet — Animated on MissionChief](https://www.missionchief.co.uk/vehicle_graphics/5897)
- [MissionChief UK Guide](https://tkb-gaming.scot/games/missionchief/guides/)
- [MissionChief Scripts & Tools](https://tkb-gaming.scot/mission-chief-scripts/)
