# v2 Direction-Neutral Fleet Standard

Status: compact production standard. The approved 200×200 v2.0.0 masters remain immutable base artwork; later releases may add narrowly scoped, deterministic master overrides without rewriting that historical baseline. MissionChief-facing exports use the map-calibrated canvas below.

## Visual contract

- Every asset uses a raised three-quarter view with enough roof visibility to read equipment and emergency lighting.
- Every subject points diagonally toward the lower-right. MissionChief may move the same sprite left or right, so no asset relies on the travel direction for its meaning.
- Every approved master is a 200×200 RGBA PNG. Every MissionChief upload is a uniformly downsampled 110×110 RGBA PNG or APNG with a transparent background and stable full-canvas anchoring.
- The 55% whole-canvas transform preserves bottom-centre placement, the raised camera, real-world class relationships and every animation frame. Production exports are never recursively resized.
- Vehicle scale is based on real-world length, then optically corrected within its class so cycles, cars, appliances, heavy units, trailers, watercraft and aircraft remain legible together.
- Distinguishing role equipment, body type and UK livery must remain readable at the 110×110 native map size and at 75% and 50% display scale.
- Every self-propelled road appliance must expose an immediately recognisable front cab. Windscreen or driver glazing, a cab roof, front wheel/arch and front-end structure must remain visually distinct from the equipment body at native map scale.
- Purpose-built pods, trailers and independently transported equipment are exempt from the front-cab rule, but must retain the correct towing or transport identity for their MissionChief slot.

## Emergency-light contract

- Response assets use a visible physical lens, a compact inner flare and a faint outer bloom.
- The lens is the brightest component. Bloom may support it but may not merge separate fixtures into a bar-shaped or vehicle-sized blue mass.
- Normal road response uses a 12-frame alternating double-flash cycle. Groups A and B alternate, with a short reset pause and subtle opposite-side spill on selected pulses.
- Roof bars are split into independently flashing perspective-correct sections. Front, rear and body repeaters are added where the real vehicle category supports them.
- Blue is the default UK emergency response colour. Amber-only, mixed-colour command, aircraft-navigation and marine-navigation patterns receive category-specific profiles.
- The response state must be unmistakable at 50% scale on light, dark, grayscale and satellite-like map backgrounds.

## Release gate

The live pack cannot be replaced until all 117 static assets and all 117 response assets pass:

1. exact slot and filename parity;
2. exact 200×200 master provenance, deterministic 110×110 export and valid transparency;
3. stable subject anchoring across every animation frame;
4. visible on/off emergency-light separation at map scale;
5. no clipped apparatus, rotor, wake, trailer or light bloom;
6. visual inspection on light, dark, grayscale and satellite-like fleet sheets;
7. lossless, infinitely looping APNG structure with the category-approved frame count.
8. explicit cab-legibility validation for every release that changes a self-propelled road appliance.
