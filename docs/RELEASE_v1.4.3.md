# v1.4.3 — Isolated Point-Lamp Emergency Lighting

This release permanently removes the elongated cyan light bars visible in MissionChief from the v1.4.2 fleet.

## Root cause

v1.4.2 fixed APNG update rectangles but retained a shape-based light primitive. A nominal `compact-bar` was a three-pixel horizontal core inside a five-pixel-wide blurred ellipse. At MissionChief sprite scale those pixels became solid luminous strokes, and nearby emitters could visually join.

The v1.4.2 audit also had an invalid acceptance threshold: its own report recorded connected blue components as large as 10×3 pixels and 23 pixels in area, but it rejected only components taller than five pixels or larger than 48 pixels. The release therefore labelled obvious bars as valid compact lights.

## Permanent correction

- Replaced both export profiles with one shared `point-emitter` primitive.
- Each emergency lamp is exactly one bright source pixel: no line, ellipse, rectangle, blur, or synthetic glow is permitted.
- Removed `compact-bar` and `compact-point` from the active fixture data.
- Added a primitive-level regression test that rejects any shape-producing implementation.
- Added exact rendered-frame gates: a connected lamp component may never exceed 2×2 pixels, and no elongated component is allowed.
- Recorded all 602 active lamp coordinates in the command build report so mixed helicopter, wheel, and response animations are audited rather than skipped.

## Full-fleet evidence

- 468 production images inspected.
- 2,178 decoded APNG frames and 2,178 APNG controls inspected.
- 184 lit APNGs changed: 87 true-scale and 97 command-profile assets.
- 234 static PNGs remain visually identical to v1.4.2.
- 602 declared lamp coordinates audited.
- Maximum connected emergency-light component: 1×1 pixel.
- 0 elongated bars, oversized light components, box components, partial APNG updates, escaped blue pixels, or hidden transparent RGB pixels.
- The 26 command assets whose v1.4.2 components were at least five pixels wide are shown in `assets/previews/v1.4.3/point-lamps-before-after.png`.

Machine-readable evidence is in `data/v1.4.3-full-fleet-lighting-report.json`. Four complete fleet sheets are under `assets/previews/v1.4.3/`.

## Deployment

Deploy the 97 corrected command-profile APNGs to MissionChief pack `5897`, keep APNG enabled, and update the pack description to v1.4.3. The remaining 20 command animations and all 117 static images are unchanged from v1.4.2.
