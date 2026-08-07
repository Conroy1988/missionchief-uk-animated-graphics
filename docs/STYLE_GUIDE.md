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

- Six-frame APNG loop for the True Scale profile; twelve frames for Modern Command Clarity.
- Alternating A/B blue-light groups with deliberate dark intervals.
- Modern Command Clarity distributes blue-light vehicles across all eleven active phase offsets; individual fittings also receive deterministic sub-phases so crowded incidents do not flash in lockstep.
- Short bright core and restrained bloom; no whole-vehicle neon glow.
- Animation geometry is composited onto the approved static master so the vehicle body never shifts between frames.
- Helicopters use per-aircraft hub geometry. Baked source blades are removed before a single edge-on rotor sweep is composited, preventing a static blade from showing underneath the animation.
- Coastguard external tail rotors receive their own rotating layer. Enclosed HEMS and police fenestrons do not receive a second synthetic rotor cross.

## Role clarity and map contrast

- Commonly confused roles use restrained equipment silhouettes—command pods, aerials, ANPR pods, medical modules, EOD cases and marine equipment—rather than colour-only differentiation.
- Added equipment must remain connected to the roof line, preserve the right-facing elevation and avoid official service branding.
- Specialist equipment should communicate capability through shape: command masts, drone cradles, rescue tools, cylinders, pod modules, watercraft frames and evidence equipment. Existing strong ladder, platform and boat silhouettes must not receive duplicate generated equipment.
- The weakest satellite-map assets receive a stronger light inner edge, dark outer edge and shadow while retaining transparent corners.
- Every asset receives a compact contact shadow rather than a full-body floating halo. Road, marine and aerial assets use distinct grounding treatments.
- Role-confusion groups must remain distinguishable at 50% scale and clear the configured silhouette-distance gate.

## Quality gates

- RGBA transparency with fully transparent corners.
- No chroma colour at map scale.
- Correct real-world relative width.
- Exactly six APNG frames in True Scale and twelve in Modern Command Clarity.
- Static and animated files share identical dimensions and vehicle alignment.
- The fleet must occupy all eleven emergency-light phase buckets and clear the configured light-activity diversity gates.
- Profiled specialist equipment and grounding shadows must remain visible at 50% scale.
- All targeted satellite assets clear the boosted edge-contrast threshold.
