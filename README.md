# TKB UK Emergency Fleet — Animated

A complete, original UK emergency-services vehicle graphics pack for [MissionChief UK](https://www.missionchief.co.uk/), built by **TKB Gaming**.

**[Use the live graphics pack](https://www.missionchief.co.uk/vehicle_graphics/5897)** · **[MissionChief UK Guide](https://tkb-gaming.scot/games/missionchief/guides/)** · **[Scripts & Tools](https://tkb-gaming.scot/mission-chief-scripts/)**

## The complete UK fleet

Release **v1.0.0** covers every one of the **117 current vehicle slots** in MissionChief UK:

- 117 transparent, map-scale static PNGs
- 117 six-frame APNGs
- 87 emergency assets with restrained alternating blue-light animation
- 30 trailers, boats, support assets and non-blue-light vehicles with stable APNG frames
- Fire, ambulance, police, coastguard, water rescue, HEMS, mountain rescue, airport, fire-investigation and EOD coverage
- Consistent real-world relative scale across the entire fleet

Every release asset has passed the production validation suite for decoding, alpha transparency, slot order, unique IDs, relative scale, animation frame count, static/APNG alignment and expected flashing behaviour.

## Visual standard

The pack uses realistic right-facing side elevations, recognisable UK emergency-service colour language and a clean, consistent map presence. The artwork is original: it does not reproduce official service logos, vehicle registrations or third-party branding.

Emergency lighting is deliberately restrained so the fleet remains readable on a busy MissionChief map. Vehicles that should not flash remain stable.

## Install in MissionChief

1. Open the **[TKB UK Emergency Fleet — Animated](https://www.missionchief.co.uk/vehicle_graphics/5897)** pack.
2. Select the pack for your MissionChief account.
3. Enable animated vehicle graphics in MissionChief if you want the blue-light APNG versions.

For broader gameplay help, missions, vehicles, buildings and operational planning, visit the **[TKB MissionChief UK Guide](https://tkb-gaming.scot/games/missionchief/guides/)**.

For MissionChief enhancements and utilities, visit **[TKB MissionChief Scripts & Tools](https://tkb-gaming.scot/mission-chief-scripts/)**.

## Release downloads

The [v1.0.0 release](https://github.com/Conroy1988/missionchief-uk-animated-graphics/releases/tag/v1.0.0) includes:

- **`TKB-UK-Emergency-Fleet-MissionChief-Numbered-Upload-Ready-v1.0.0.zip`** — recommended ordered deployment package, with separate static and animated folders, an upload guide, manifest and SHA-256 verification
- **`TKB-UK-Emergency-Fleet-MissionChief-Upload-Ready-v1.0.0.zip`** — compact deployment package using production asset IDs
- **`TKB-UK-Emergency-Fleet-v1.0.0.zip`** — complete production archive containing sources, transparent masters, exports, previews, mappings, documentation and build tools

## Repository structure

- `assets/sources/` — representative full-resolution chroma-key source artwork
- `assets/exports/standard/static/` — MissionChief-ready transparent PNGs
- `assets/exports/standard/animated/` — MissionChief-ready six-frame APNGs
- `assets/previews/` — map-scale, animation-frame and selected-artwork QA sheets
- `data/vehicle-slots.json` — authoritative 117-slot MissionChief mapping
- `data/prototypes.json` — production specification and light-placement manifest
- `data/final-pack-validation.json` — release-level validation report
- `scripts/` — repeatable preparation, packaging and QA tools
- `docs/` — production standards and release checkpoints

Large production artwork is supplied through the release archive rather than duplicated throughout Git history.

## Rebuild and validate

```bash
python scripts/build_prototypes.py
python scripts/build_source_qa.py
python scripts/validate_final_pack.py
python scripts/build_numbered_upload_package.py --version v1.0.0
```

The final validation gate must report `"all_passed": true` before a release is published.

## Rights and licence

The artwork is original and the pack is not affiliated with or endorsed by MissionChief, any UK emergency service or any vehicle manufacturer.

Code and automation are MIT licensed. Artwork and visual assets are licensed under CC BY-NC-SA 4.0. See [LICENSE.md](LICENSE.md) for the exact scope and attribution requirement.
