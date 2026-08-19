# v2.0.0 — Complete direction-neutral fleet rebuild

Version 2.0.0 replaces the previous right-facing side-elevation production artwork with a complete 117-slot raised three-quarter fleet. Every graphic uses one fixed lower-right orientation and remains credible when MissionChief moves it in either horizontal direction.

## Complete release scope

- 117 new 200×200 transparent static PNGs.
- 117 new lossless response APNGs.
- 111 twelve-frame road, pod, trailer, cycle and specialist animations.
- Four eighteen-frame helicopter animations with aviation lighting and rotor traces.
- Two eighteen-frame lifeboat animations with response/navigation lighting and wake motion.
- Exact static/APNG parity with all 117 authoritative MissionChief slots.

## Emergency-light system

The former one-pixel-only renderer is retained for v1.4.14 but is not used by v2. The new 200×200 artwork supports a visible physical lens, compact inner flare and restrained outer bloom without joining separate fixtures into vehicle-sized blue bars.

Road assets use independently alternating A/B double flashes. Recovery and selected airfield assets receive amber profiles, the General Practitioner vehicle receives green, aircraft receive aviation-aware mixed lighting, and both operational lifeboats receive navigation-aware marine profiles.

The validator measures every response asset after native 50% reduction and rejects dim, undersized, oversized or off-subject lighting.

## Validation result

| Gate | Result |
|---|---:|
| Static slot parity | 117/117 |
| Static canvas/transparency/anchor QA | 117/117 |
| Animated slot parity | 117/117 |
| Full-frame APNG control QA | 117/117 |
| Fixture-on-subject QA | 117/117 |
| 50% flash visibility QA | 117/117 |
| Numbered package static files | 117 |
| Numbered package animated files | 117 |
| Current v1.4.14 command exports changed | 0 |

The validated deployment archive SHA-256 is recorded in `data/v2.0.0-release-integrity-report.json` and the adjacent `.zip.sha256` file.

## Deployment

This is a complete-pack replacement rather than an incremental slot patch. Upload both the static and animated file for all 117 rows in numeric order. Do not mix v2 direction-neutral assets with the v1.4 side-elevation profile.
