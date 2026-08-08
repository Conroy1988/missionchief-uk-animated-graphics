# TKB UK Emergency Fleet — Roadmap

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

Status: delivered on 8 August 2026. The gallery is presentation-only and does not alter the live v1.4.0 MissionChief pack.

Release contract:

- `gallery/vehicles.json` is generated from the canonical slot, prototype, lighting and v1.4 profile data
- every current static/APNG pair and every v1.0.0, v1.2.7 and v1.3.0 comparison path is fail-closed in CI
- pure browser-state tests cover search, filters, sorting, release routing and shareable URLs
- the TKB website owns the public route and Games-directory banner while this repository remains authoritative for fleet assets
