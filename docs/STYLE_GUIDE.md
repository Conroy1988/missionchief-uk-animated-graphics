# TKB UK Emergency Fleet — Visual Standard

## Master view

- Perfect right-facing side elevation.
- Level wheel baseline with no three-quarter perspective.
- Original generic UK fleet designs: no manufacturer marks, registration numbers, service crests, or copied photographs.
- Neutral daylight rendering with realistic materials and crisp technical edges.
- Emergency lights remain visibly blue when inactive but emit no glow in static graphics.

## Service language

- Fire: red bodywork, fluorescent yellow-red conspicuity, operational equipment appropriate to the vehicle role.
- Police: white base, blue-fluorescent-yellow Battenburg, low-profile blue warning equipment.
- Ambulance: fluorescent yellow base, green-yellow markings, blue warning equipment.
- Specialist services will retain their recognisable UK colour and conspicuity conventions without reproducing protected service crests.

## Scale

The standard map profile uses 13 pixels per metre of real vehicle length. This keeps a typical rescue pump close to 110 px wide while preserving the correct visual relationship between cars, vans, heavy appliances, boats, and aircraft.

Large masters are retained independently from exports. All map assets are rebuilt from the masters so the standard can be adjusted later without damaging source artwork.

## Animation

- Six-frame APNG loop.
- Alternating A/B blue-light groups with deliberate dark intervals.
- Short bright core and restrained bloom; no whole-vehicle neon glow.
- Animation geometry is composited onto the approved static master so the vehicle body never shifts between frames.

## Quality gates

- RGBA transparency with fully transparent corners.
- No chroma colour at map scale.
- Correct real-world relative width.
- Exactly six APNG frames in the standard response animation.
- Static and animated files share identical dimensions and vehicle alignment.
