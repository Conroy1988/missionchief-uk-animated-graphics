# Checkpoint v1.0.0 — Complete UK Fleet

## Coverage

- Live MissionChief UK slots: 117
- Finished transparent masters: 117
- Validated static PNGs: 117
- Validated six-frame APNGs: 117
- Assets with visible flashing blue lights: 87
- Non-blue-light assets with aligned static APNG frames: 30
- Remaining production slots: 0

Every slot in the authenticated MissionChief UK vehicle-graphics editor is represented by an original, role-specific asset and mapped to its zero-based upload index.

## Completed service families

1. Fire and rescue appliances, specialist units, pods and airport fire vehicles
2. Ambulance, HEMS, HART, patient transport and critical-care vehicles
3. Police, firearms, public-order, custody, dog and aviation units
4. Coastguard command, mud, rope, flood and decontamination units
5. Lifeboats, rescue watercraft, hovercraft and transport assets
6. Search and rescue, drone, mountain rescue, dog and crew-support units
7. Airfield operations and medical-support assets
8. Recovery, road-rail and British Transport Police intervention units
9. EOD, marine EOD and welfare vehicles

## Quality results

- Complete ordered slot sequence 1–117: passed
- Unique manifest asset IDs: passed
- Source and master PNG decoding: passed
- Transparent RGBA canvas corners: passed
- Real-scale export dimensions: passed
- Static/APNG pixel alignment: passed
- APNG frame count: six per asset
- Visible frame changes on lit assets: passed
- No frame changes on non-blue-light assets: passed
- Static and animated export directories exactly match the manifest: passed
- Full-resolution source contact sheet: passed
- MissionChief map-scale contact sheet: passed
- Six-frame animation contact sheet: passed
- Final release validator: `all_passed: true`

## Production method

Each new vehicle was generated independently in a consistent product-mockup side-elevation style on a uniform `#FF00FF` key. The keyed images are archived under `assets/sources/`; `prepare_chroma_master.py` extracts transparent RGBA masters while protecting red emergency livery and verifying every PNG stream. Map-scale images are then resized at 13 pixels per metre and built into six-frame APNG sequences.

## Animation policy

Emergency response vehicles use restrained alternating blue-light glows with a six-frame cadence. Trailers, standalone boats, non-emergency patient transport, amber-only airfield/recovery vehicles and other assets without appropriate blue warning lights remain visually static across their APNG frames, ensuring exact alignment without inventing incorrect lighting.

## Deployment state

The complete files are ready for the private MissionChief working pack:

- Pack ID: 5897
- Caption: `TKB UK Fleet — Animated WIP`
- Local slot mapping: `data/vehicle-slots.json`

MissionChief live upload remains a separate browser deployment operation because the site requires local file selection for each of its 117 individual slot forms.
