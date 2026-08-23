# TKB UK Emergency Fleet — Roadmap

## Delivered: full-fleet map performance overhaul

Version 2.2.0 rebuilds all 117 animated graphics under a low-redraw budget: two constantly illuminated A/B frames for 111 road assets and four motion frames for six aircraft/marine assets. The full-frame APNG compatibility contract, 110×110 anchoring, all static exports and every v2.1.1 master remain intact.

The enforced performance report records 82.9% fewer animation frames, 82.6% less encoded APNG data and 68.9% fewer road animation updates. See the [v2.2.0 release checkpoint](CHECKPOINT_v2.2.0.md).

## Delivered: unified mounted pod carriers

Version 2.1.1 rebuilds slots 42–51 as ten coherent three-axle appliances. Their role bodies now sit directly behind the cab on one continuous powered chassis, removing the detached trailer-like gap and duplicate underframe cues from the earlier composite method.

The new fail-closed gate measures cab-to-body coupling, continuous chassis structure, connected-subject coverage and three axle witness regions before a mounted carrier can pass. See the [v2.1.1 release checkpoint](CHECKPOINT_v2.1.1.md).

## Delivered: UK vehicle-family authenticity

Version 2.1.0 completes the 18-family hero standard across all 117 slots. The release retains 117/117 technical compliance, converts the 11 targeted vehicles and clears the enforcement gate with zero remaining cross-family silhouette conflicts.

Delivered conversion groups:

- van and secure-carrier distinction: Crew Carrier, SRV, PSU Carrier, Armed Cell Van, Mountain Rescue Control Van, Marine EOD Equipment Van and Cell Van;
- ambulance body distinction: Patient Transport Service and Critical Care Transfer Ambulances;
- utility 4x4 distinction: SAR 4x4 and EOD Response Vehicle.

The enforcement command now reports 117/117 hero-ready. See [V2_UK_FAMILY_HERO_STANDARD.md](V2_UK_FAMILY_HERO_STANDARD.md) and the [v2.1.0 release checkpoint](CHECKPOINT_v2.1.0.md).

## Delivered: interactive vehicle gallery

The Markdown gallery has been expanded into a polished interactive gallery for all 117 MissionChief UK vehicle slots. Its public home is the [TKB MissionChief UK Guide](https://tkb-gaming.scot/games/missionchief/guides/fleet-gallery/), with the deterministic source and validation contract retained in this repository.

Planned capabilities:

- instant search by MissionChief name, slot number and vehicle role
- service filters for fire, ambulance, police, coastguard, lifeboat, SAR, recovery, airfield and EOD
- static/animated toggle with animation playback controls
- 100%, 75% and 50% scale previews on light, dark, grayscale and satellite-style maps
- before/after comparison between stable releases
- focused views for role-differentiation, specialist-equipment, lighting and grounding-shadow changes
- direct links to the matching static/APNG asset and MissionChief pack
- responsive desktop, tablet and mobile layout

Status: delivered on 8 August 2026. The gallery is presentation-only, tracks the current validated release and does not itself alter the live MissionChief pack.

Release contract:

- `gallery/vehicles.json` is generated from the canonical slot, prototype, lighting and v1.4 profile data
- every current static/APNG pair and every v1.0.0, v1.2.7 and v1.3.0 comparison path is fail-closed in CI
- pure browser-state tests cover search, filters, sorting, release routing and shareable URLs
- the TKB website owns the public route and Games-directory banner while this repository remains authoritative for fleet assets
