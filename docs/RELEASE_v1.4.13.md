# v1.4.13 — SAR Drone Vehicle roof-equipment repair

This targeted release corrects the Drone Vehicle (SAR HQ) at MissionChief slot 90. No other vehicle artwork changes.

## Corrected defect

The baked specialist cue added a deep orange-edged launch box and a fully spread drone silhouette above a source vehicle that already carried an emergency lightbar and rear communications mast. At MissionChief scale the generated assembly appeared detached, dominated the roofline and obscured the authentic vehicle equipment in both the static and animated graphics.

## Permanent repair

- Removes the raised launch box and fully spread drone silhouette.
- Preserves the source vehicle's emergency lightbar, rear communications mast, SAR livery and exact map anchor.
- Adds one three-pixel-high attached stowage profile with a compact longitudinally folded airframe and exactly two isolated markers.
- Retains the roof, front and rear response emitters at their audited coordinates.
- Retains the 89×53 command canvas and full-frame 12-frame APNG encoding.
- Adds a dedicated fail-closed gate that permits master changes only on the approved stowage geometry and rejects any raised box, spread rotor silhouette, marker drift, fixed-hardware animation, fixture drift, frame-zero drift or partial APNG frame.

## Release scope

Against v1.4.12, the only changed MissionChief exports are:

- `assets/exports/command/static/drone-vehicle-sar-hq.png`
- `assets/exports/command/animated/drone-vehicle-sar-hq.png`

The standard profile and the other 116 command-profile vehicle pairs remain byte-identical to v1.4.12.

## Deployment

For an incremental update to MissionChief pack `5897`, replace both files at slot 90 (edit index 89), keep animation enabled for the APNG, and leave every other row untouched.
