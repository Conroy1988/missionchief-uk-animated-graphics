# v2.2.0 — Low-Lag Performance Fleet

v2.2.0 optimises every one of the 117 MissionChief UK animated vehicle graphics. It removes redundant animation work without shrinking the vehicles, weakening the emergency lighting or changing any approved artwork.

## Complete performance rebuild

- All 111 road, pod, trailer, cycle and specialist APNGs now use two complementary illuminated phases at 3.85 updates per second.
- All four aircraft and both marine APNGs now use four evenly spaced motion phases at 5.56 updates per second.
- Fleet-wide frames fall from 1,440 to 246 per complete asset cycle: **82.9% fewer frames**.
- Encoded APNG data falls from 13,054,362 bytes to 2,267,212 bytes: **82.6% smaller**.
- Full-cycle decoded RGBA frame data falls from 69,696,000 bytes to 11,906,400 bytes.
- At 500 visible road vehicles, estimated animation update ticks fall from roughly 6,186 to 1,923 per second.

## Visual and compatibility safeguards

- Both road phases remain visibly illuminated; there are no blank/reset frames.
- Aircraft retain calibrated main- and tail-rotor motion, aviation lighting and white strobe detail.
- ILB and ALB retain navigation lighting and wake motion.
- Every APNG remains lossless, infinitely looping and encoded as complete 110×110 frames with disposal 0 and blend 0.
- All 117 static exports are SHA-256 identical to v2.1.1.
- Every preserved 200×200 master and retained production source is unchanged.
- All 117 emergency-light, native-scale, family-authenticity, cab, carrier and release-integrity gates pass.

## Deployment scope

All 117 animated slots must be updated together. Static files are included in the numbered package for completeness but are byte-identical to v2.1.1.

## Evidence

- `data/v2.2.0-performance-report.json`
- `data/v2.2.0-animation-build-report.json`
- `data/v2.2.0-animation-qa-report.json`
- `data/v2.2.0-release-integrity-report.json`
- `assets/previews/v2.2.0/full-fleet-response-a-satellite.png`
- `assets/previews/v2.2.0/full-fleet-response-b-dark.png`
- `assets/previews/v2.2.0/helicopter-rotor-fleet.gif`

## Download

`TKB-UK-Emergency-Fleet-Direction-Neutral-MissionChief-Numbered-Upload-Ready-v2.2.0.zip` contains ordered static and animated folders, the authoritative slot guide, an upload manifest and SHA-256 provenance.
