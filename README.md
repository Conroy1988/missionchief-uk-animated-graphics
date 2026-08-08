# TKB UK Emergency Fleet — Animated v1.3.0

A complete, original UK emergency-services vehicle graphics pack for [MissionChief UK](https://www.missionchief.co.uk/), built by **TKB Gaming**.

> **[Use TKB UK Fleet — Animated on MissionChief →](https://www.missionchief.co.uk/vehicle_graphics/5897)**

**[Preview all 117 vehicle graphics](GALLERY.md)** · **[See the automated map tests](#tested-for-real-map-conditions)** · **[MissionChief UK Guide](https://tkb-gaming.scot/games/missionchief/guides/)** · **[Scripts & Tools](https://tkb-gaming.scot/mission-chief-scripts/)**

## Preview the full fleet

<table>
  <tr>
    <td align="center" width="25%"><a href="GALLERY.md"><img src="assets/exports/command/animated/fire-rescue-pump.png" alt="Water Ladder preview" width="160"></a><br><strong>Water Ladder</strong></td>
    <td align="center" width="25%"><a href="GALLERY.md"><img src="assets/exports/command/animated/frontline-ambulance.png" alt="Ambulance preview" width="160"></a><br><strong>Ambulance</strong></td>
    <td align="center" width="25%"><a href="GALLERY.md"><img src="assets/exports/command/animated/police-incident-response-vehicle.png" alt="IRV preview" width="160"></a><br><strong>IRV</strong></td>
    <td align="center" width="25%"><a href="GALLERY.md"><img src="assets/exports/command/animated/hems.png" alt="HEMS preview" width="160"></a><br><strong>HEMS</strong></td>
  </tr>
  <tr>
    <td align="center" width="25%"><a href="GALLERY.md"><img src="assets/exports/command/animated/police-helicopter.png" alt="Police helicopter preview" width="160"></a><br><strong>Police helicopter</strong></td>
    <td align="center" width="25%"><a href="GALLERY.md"><img src="assets/exports/command/animated/coastguard-rescue-helicopter.png" alt="Coastguard Rescue Helicopter preview" width="160"></a><br><strong>Coastguard Rescue Helicopter</strong></td>
    <td align="center" width="25%"><a href="GALLERY.md"><img src="assets/exports/command/animated/control-van-sar.png" alt="Control Van (SAR) preview" width="160"></a><br><strong>Control Van (SAR)</strong></td>
    <td align="center" width="25%"><a href="GALLERY.md"><img src="assets/exports/command/animated/eod-heavy-equipment-vehicle.png" alt="EOD Heavy Equipment Vehicle preview" width="160"></a><br><strong>EOD Heavy Equipment Vehicle</strong></td>
  </tr>
</table>

**[Explore all 117 static and animated vehicle graphics →](GALLERY.md)**

## The complete UK fleet

Release **v1.3.0** covers every one of the **117 current vehicle slots** in MissionChief UK:

- 117 transparent, map-scale static PNGs
- 117 twelve-frame APNGs with a unique timing signature per vehicle
- A fleet-wide **13 px per metre** scale calibration based on each vehicle's real length, with only 0.285% mean rounding error and the approved 169×84 ALB exception preserved
- 97 emergency assets distributed across 11 fleet phase offsets, 58 visible light-activity signatures and independent roof, grille, body and rear rhythms
- 196 fixture-specific emergency-light anchors audited and corrected across 61 vehicles, including left-facing, specialist, carrier and helicopter assets
- Fixture-shaped LED cores and restrained bloom instead of generic flash points, plus subtle steady headlights and rear lamps on 91 response vehicles
- Semi-transparent elliptical main-rotor blur, aviation-light rhythms and moving haze on both preserved Coastguard tail rotors
- Improved red/green navigation lighting, bow spray, stern turbulence and class-weighted wakes for both operational lifeboats
- Selective wheel motion on six suitable cycle, ATV, recovery and airport assets, aligned to declared wheel geometry
- Twenty rebuilt role-specific masters with command, ANPR, medical, drone, CBRN and EOD equipment baked into the source artwork
- A standardised UK high-visibility colour pass across 123,679 livery pixels without introducing copied service marks
- Adaptive compact, standard and large-vehicle outlines that reduce the cut-out effect while retaining satellite-map contrast
- ALB map footprint reduced by approximately 30%, with both its static and twelve-frame navigation/wake variants corrected
- Clean, original rooflines on the 40 vehicles affected by v1.2.0's artificial role and equipment overlays
- A fail-closed 40-asset roofline regression gate that rejects any return of generated top-padding blocks
- A coherent nine-vehicle mounted pod family across slots 42–50: Water, Bulk Foam, Rescue, Command, Welfare, BASU, Misting, Hazardous Materials and OSU
- Every pod role now retains its distinct module on a complete three-axle prime mover with visible cab, chassis, wheels and four-point response lighting
- The HVP at slot 51 now mounts its pump, hose banks and manifolds on the same complete prime-mover platform instead of appearing as a self-propelled module
- Complete, unclipped tail geometry on HEMS, Police and both Coastguard helicopters, protected by both clearance and structural-pixel regression gates
- Reinforced light/dark dual edges on the 15 weakest satellite-map assets; the minimum targeted satellite contrast remains above the v1.2 target
- Fleet-wide contact grounding shadows with five weight-appropriate classes for light vehicles, heavy vehicles, trailers, watercraft and aircraft
- Native half-scale sharpening and artefact cleanup across all 117 assets, with zero isolated alpha pixels remaining
- Lossless APNG delta-frame optimisation: the complete animated fleet is **51.73% smaller** than v1.2.7 while decoding pixel-for-pixel identically
- Fire, ambulance, police, coastguard, water rescue, HEMS, mountain rescue, airport, fire-investigation and EOD coverage
- The original v1.0 True Scale profile remains available and unchanged

Every release asset has passed the production validation suite for decoding, alpha transparency, slot order, unique IDs, relative scale, animation frame count, static/APNG alignment and expected flashing behaviour.

## Visual standard

The pack uses realistic right-facing side elevations, recognisable UK emergency-service colour language and a clean, consistent map presence. The artwork is original: it does not reproduce official service logos, vehicle registrations or third-party branding.

Emergency lighting is deliberately restrained so the fleet remains readable on a busy MissionChief map. Lightbar, grille and rear fixtures run independently, while 11 deterministic phase offsets and 58 activity patterns prevent an entire incident from blinking in lockstep.

## Tested for real map conditions

Every icon is tested automatically at **100%, 75% and 50% scale** against light, dark, grayscale and satellite-style backgrounds. The release gate checks half-zoom survival, edge contrast, corrected rooflines, frame stability and all 117 static/animated slot pairs.

[![Light-map dense fleet test](assets/previews/v1.3.0/busy-map-light.png)](assets/previews/v1.3.0/busy-map-light.png)

**[v1.2.7 → v1.3.0 scale comparison](assets/previews/v1.3.0/fleet-scale-before-after.png)** · **[Twenty rebuilt masters](assets/previews/v1.3.0/baked-role-master-audit.png)** · **[Lighting and motion frames](assets/previews/v1.3.0/lighting-motion-audit.png)** · **[Outline, livery and shadow audit](assets/previews/v1.3.0/adaptive-outline-livery-shadow-audit.png)** · **[Complete helicopter-tail audit](assets/previews/v1.3.0/complete-helicopter-tails-map-scale.png)** · **[Complete mounted specialist-carrier audit](assets/previews/v1.3.0/mounted-specialist-carrier-map-scale.png)** · **[Satellite-style test](assets/previews/v1.3.0/busy-map-satellite.png)** · **[Crowded-response light audit](assets/previews/v1.3.0/desynchronised-lights-crowd.png)**

## Install in MissionChief

1. Open the **[TKB UK Emergency Fleet — Animated](https://www.missionchief.co.uk/vehicle_graphics/5897)** pack.
2. Select the pack for your MissionChief account.
3. Enable animated vehicle graphics in MissionChief if you want the blue-light APNG versions.

For broader gameplay help, missions, vehicles, buildings and operational planning, visit the **[TKB MissionChief UK Guide](https://tkb-gaming.scot/games/missionchief/guides/)**.

For MissionChief enhancements and utilities, visit **[TKB MissionChief Scripts & Tools](https://tkb-gaming.scot/mission-chief-scripts/)**.

## Release downloads

The [v1.3.0 release](https://github.com/Conroy1988/missionchief-uk-animated-graphics/releases/tag/v1.3.0) includes:

- **`TKB-UK-Emergency-Fleet-Modern-Command-Clarity-MissionChief-Numbered-Upload-Ready-v1.3.0.zip`** — recommended ordered deployment package, with separate static and animated folders, an upload guide, manifest and reproducible SHA-256 verification
- **`TKB-MissionChief-UK-Graphics-Bulk-Uploader-v1.3.0.user.js`** — resumable live deployment helper for pack maintainers
- **`v1.3.0-build-report.json`**, **`v1.3.0-qa-report.json`**, **`v1.3.0-overhaul-report.json`**, **`v1.3.0-master-report.json`** and **`v1.3.0-light-placement-report.json`** — machine-readable production evidence

The [v1.0.0 release](https://github.com/Conroy1988/missionchief-uk-animated-graphics/releases/tag/v1.0.0) remains available for players who prefer strict real-world relative scale.

## Repository structure

- `assets/sources/` — representative full-resolution chroma-key source artwork
- `assets/exports/standard/static/` — MissionChief-ready transparent PNGs
- `assets/exports/standard/animated/` — MissionChief-ready six-frame APNGs
- `assets/exports/command/static/` — v1.3.0 Modern Command Clarity PNGs
- `assets/exports/command/animated/` — v1.3.0 twelve-frame APNGs
- `assets/masters/` — deterministic command-profile replacement masters, including the v1.2.4 mounted specialist-carrier/full-tail sources and twenty baked v1.3.0 role masters
- `assets/previews/` — map-scale, animation-frame and selected-artwork QA sheets
- `data/vehicle-slots.json` — authoritative 117-slot MissionChief mapping
- `data/prototypes.json` — production specification and light-placement manifest
- `data/final-pack-validation.json` — release-level validation report
- `scripts/` — repeatable preparation, packaging and QA tools
- `docs/` — production standards, release checkpoints and the parked future roadmap

Large production artwork is supplied through the release archive rather than duplicated throughout Git history.

## Rebuild and validate

```bash
python scripts/build_mounted_pod_carriers.py --check
python scripts/build_helicopter_tail_masters.py --check
python scripts/build_v1_3_masters.py --check
python scripts/build_v1_1_enhanced.py
python scripts/validate_v1_1_enhanced.py
python scripts/validate_v1_3_overhaul.py
python scripts/validate_release_scope.py
python scripts/validate_light_placement.py --report data/v1.3.0-light-placement-report.json
python scripts/build_numbered_upload_package.py --version v1.3.0 --profile command
```

The final validation gate must report `"all_passed": true` before a release is published. The immutable v1.0 source profile remains documented separately in its release and checkpoint.

## Rights and licence

The artwork is original and the pack is not affiliated with or endorsed by MissionChief, any UK emergency service or any vehicle manufacturer.

Code and automation are MIT licensed. Artwork and visual assets are licensed under CC BY-NC-SA 4.0. See [LICENSE.md](LICENSE.md) for the exact scope and attribution requirement.
