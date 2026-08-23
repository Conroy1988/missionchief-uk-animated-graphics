# v2 UK vehicle-family authenticity and hero-grade gate

Status: enforced production standard, completed in v2.1.0 and revalidated in v2.2.0.

The fleet already has one of the strongest visual systems available for MissionChief: a shared raised camera, reliable direction-neutral motion, exact slot parity, compact map-scale exports and purpose-built response animation. The next quality step is not more bloom or more pixels. It is making each vehicle read as the correct British *kind* of vehicle before the livery is considered.

## The standard

Every slot is assigned to one of 18 platform families. Each family has one current hero reference, a proportion-level UK visual lineage, five non-negotiable cues, a minimum live-scale envelope and a measurable silhouette-affinity floor. Every individual slot also has a role-specific body/equipment brief.

The family system is deliberately manufacturer-neutral. British fleet types may inform the proportions, but production artwork must not copy a badge, grille, registration, fleet number, service crest or protected livery mark. The result should feel immediately British and remain wholly original.

| Family | Hero reference | Core visual distinction |
| --- | --- | --- |
| British forward-control fire appliance | Water Ladder | cab-over crew cab, roller shutters, ladder gantry |
| British specialist emergency HGV | Rescue Support Unit | heavy chassis plus a role-specific tank, locker or command body |
| British aerial fire appliance | Aerial Appliance | boom, turntable, stabilisers and long multi-axle chassis |
| UK hooklift carrier | Hazardous Materials Pod | complete three-axle prime mover and mounted demountable module |
| UK ambulance conversion | Ambulance | tall clinical body, ambulance doors/windows and corner light housings |
| UK response estate or fastback | IRV | recognisable passenger cell, road-car stance and physical response fixtures |
| UK emergency SUV or 4x4 | Coastguard Commander | raised stance, utility volume, wheel arches and operational roof equipment |
| UK operational van or crew carrier | Operational Support Van | readable cab/door rhythm and task-specific rear-body furniture |
| UK secure police carrier | M-RAV | protected custody/firearms body rather than a normal panel-van reskin |
| UK airport crash appliance | RIV | wide, low tank body, heavy tyres and firefighting monitor |
| UK airfield operations vehicle | Airfield Operations Supervisor | amber operational fit and airfield high-visibility treatment |
| UK recovery platform | HGV Recovery Vehicle | open working deck, winch, boom or underlift |
| UK towed specialist equipment | Boat Trailer | drawbar, trailer wheels and an unmistakable carried load |
| UK emergency rotorcraft | Large Coastguard Rescue Helicopter | cockpit, rotor system, tail relationship and landing gear |
| UK rescue watercraft | ALB | hull sheer, bow, cabin/console and marine equipment |
| UK cycle response unit | Medical Cycle Responder | two wheels, bicycle frame and medical panniers |
| UK specialist transporter | ATV Carrier | complete powered carrier plus a visibly mounted operational load |
| UK heavy EOD equipment vehicle | EOD Heavy Equipment Vehicle | multi-axle secure body and deployment-compartment cues |

The executable source of truth is [`scripts/v2_uk_family_standard.py`](../scripts/v2_uk_family_standard.py). It maps all 117 slots in canonical order and is validated against both `vehicle-slots.json` and `prototypes.json`.

## UK evidence basis

The family briefs use official fleet and operational material as a reality check, never as artwork to trace:

- [Devon and Somerset Fire and Rescue Service's Medium Rescue Pump](https://www.dsfire.gov.uk/fleet/medium-rescue-pump) documents a crewed UK pump's chassis classes, dimensions, water/foam systems, ladders and rescue equipment;
- [London Fire Brigade's aerial-appliance guide](https://www.london-fire.gov.uk/about-us/services-and-facilities/vehicles-and-equipment/aerial-appliances/) confirms the turntable ladder, cage and elevated water-delivery role;
- [London Fire Brigade's Terrain Support Vehicles](https://www.london-fire.gov.uk/about-us/services-and-facilities/vehicles-and-equipment/terrain-support-vehicles/) and [Devon and Somerset's 4x4 Light Vehicle](https://www.dsfire.gov.uk/fleet/4x4-light-vehicle) ground the raised 4x4 stance, carried water/pump equipment and specialist trailer role;
- [East Midlands Ambulance Service fleet material](https://www.emas.nhs.uk/join-team-emas/ambulance-service-roles/fleet-services-and-vehicle-logistics) distinguishes emergency ambulances, fast-response cars, specialist vehicles and patient transport, while [NHS England's critical-care transfer specification](https://www.england.nhs.uk/publication/adult-critical-care-transfer-services/) confirms a dedicated critical-care ambulance vehicle brief;
- [North Yorkshire Police's disclosed fleet mix](https://www.northyorkshire.police.uk/foi-ai/north-yorkshire-police/foi-disclosure-2021-22/february-2025/foi-sold-fleet-vehicles-0723-202425/) confirms the real use of estates/fastbacks, SUVs, pickups and several van sizes rather than one universal police silhouette;
- [UK CAA rescue and firefighting guidance](https://www.caa.co.uk/commercial-industry/aerodromes/aerodrome-safety/rescue-and-firefighting-services/) requires airport RFFS to hold adequate equipment and extinguishing agents, supporting the separate high-capacity crash-appliance family.

These sources justify platform and equipment categories only. Production sprites remain original, badge-free and service-neutral enough to avoid claiming affiliation.

## Hero-grade gate

The validator awards ten transparent, binary ten-point checks. A hero-grade asset needs **100/100**; 90 is not silently rounded up.

1. 200×200 RGBA master contract;
2. genuine alpha transparency;
3. safe canvas bounds with no clipped body, rotor, apparatus or equipment;
4. the family-specific size envelope;
5. a stable grounded baseline;
6. byte-equivalent deterministic 110×110 export provenance;
7. sufficient tonal separation at native scale;
8. sufficient colour and material separation;
9. sufficient structural edge density;
10. readable front/running-gear structure for road subjects.

An asset must also meet its family-reference silhouette floor. Cross-family silhouettes at or above the strict conflict threshold are rejected because a colour-only reskin cannot establish a new vehicle family.

The gate has two intentional modes:

- `--audit` validates the entire technical and specification contract, writes the report and boards, and returns success while known family conversions remain;
- enforcement mode omits `--audit` and exits non-zero until all 117 slots are hero-ready.

```bash
python scripts/validate_v2_uk_family_hero_gate.py --audit
python scripts/validate_v2_uk_family_hero_gate.py
```

The first command is used while migrating the preserved v2.0.4 artwork. The second is mandatory before the next family-authentic fleet release can be cut or deployed to MissionChief.

## Initial full-fleet audit and completed migration

The v2.0.4 baseline was audited on 21 August 2026:

- slot mapping: 117/117;
- technical contract: 117/117;
- platform families: 18/18 with unique hero references;
- current hero-ready assets: 106/117;
- targeted conversion queue: 11/117.

The conversion queue was intentionally narrow. It caught platform-family conflicts such as an EOD 4x4 reading like an operational van or an ambulance/custody body sharing too much morphology, plus any asset that missed the family reference or full 100-point visual bar. The baseline reasons remain in `data/v2.0.4-uk-family-hero-report.json`.

Version 2.1.0 completes all 11 targeted conversions. The enforced report in `data/v2.1.0-uk-family-hero-report.json` records 117/117 hero-ready, 117/117 technical compliance, zero remaining conversions and zero cross-family silhouette conflicts. The retained production-source provenance and before/after evidence are recorded in `data/v2.1.0-family-conversion-report.json` and `assets/previews/v2.1.0/family-conversions-before-after.png`.

Version 2.1.1 keeps that complete family migration and rebuilds the ten loaded hooklift roles as unified three-axle carriers. The current enforced evidence is recorded in `data/v2.1.1-uk-family-hero-report.json`, `data/v2.1.1-mounted-carrier-report.json` and `assets/previews/v2.1.1/mounted-carrier-live-map.png`.

Version 2.2.0 preserves every v2.1.1 master and source byte while rebuilding all 117 APNGs under the low-redraw performance contract. The current enforced evidence is recorded in `data/v2.2.0-uk-family-hero-report.json`, `data/v2.2.0-performance-report.json` and `assets/previews/v2.2.0/uk-family-hero-audit.png`.

## Non-negotiable shortcuts

- No pod, container or trailer may move as if it were a powered vehicle.
- No new family may be represented by a livery-only reskin.
- No manufacturer badge, copied grille, registration, fleet number or protected service crest.
- No light bloom may hide an unreadable cab or role body.
- No detail may count toward approval if it disappears at the native 110×110 map scale.
