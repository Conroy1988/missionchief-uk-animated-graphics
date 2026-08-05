#!/usr/bin/env python3
"""Register and prepare the final MissionChief UK production block (slots 52-117)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SLOTS_PATH = ROOT / "data" / "vehicle-slots.json"
MANIFEST_PATH = ROOT / "data" / "prototypes.json"
PREPARE = ROOT / "scripts" / "prepare_chroma_master.py"
GENERATED_ROOT = ROOT.parent / "generated_images"


GENERATED = {
    52: "exec-92daec2c-495e-4840-b0f0-bb7641d3049e.png",
    53: "exec-d1b2dfff-f232-41a9-adda-a112407c30c2.png",
    54: "exec-b1858294-8719-49a5-bed5-2a4752fa4e70.png",
    55: "exec-d7ce3158-907a-4c42-b0e6-b4d220ec1777.png",
    56: "exec-aa7de9c2-5926-40da-b013-0bb5bd30e2aa.png",
    57: "exec-d9520359-ea69-4d34-9e9b-6ab398daad5f.png",
    58: "exec-27f01708-df05-447e-a3ce-ab2794c7282c.png",
    59: "exec-3dd734b6-d4e8-4ec4-bf3b-805c5d8c3fd4.png",
    60: "exec-61ad7c6c-d5c8-41f9-874b-c5dc4ff51cd2.png",
    61: "exec-f09c76f3-bdfc-474b-8e55-a46b6496b8b7.png",
    62: "exec-9ef51c55-5837-4c70-9a41-abc8b7def3a8.png",
    63: "exec-1df9aa2f-ca36-4a60-9945-36da099c8de8.png",
    64: "exec-b8eab007-f31d-4be0-95b2-1c2ffa7869f4.png",
    65: "exec-75d5bdf3-28fb-4f3c-8927-209d4f81df80.png",
    66: "exec-046ad441-047c-4fec-b1cb-ecec2648fd9c.png",
    67: "exec-16a2ece4-4ab1-4ded-9719-8e268222dfce.png",
    68: "exec-5bd5921a-7d91-422f-bca5-544c93719952.png",
    69: "exec-7baef1fd-f734-40d6-922a-80b014bbf6bf.png",
    70: "exec-cd215d61-747c-4633-bd1b-0c753ddd6b52.png",
    71: "exec-0b25bb3a-7ca4-458e-95e1-233b7e6f54a4.png",
    72: "exec-552adb7c-893a-41f0-840a-0e743fc36cc5.png",
    73: "exec-b899b1ba-cd4f-4c7c-95da-611788325231.png",
    74: "exec-f9a46a12-c0c6-41b3-8c0c-3bec30011b8f.png",
    75: "exec-29d1af04-a30b-4cc5-aaf9-b6197f0b27f2.png",
    76: "exec-5d7d474d-457e-4d8d-bb3f-5727e660200a.png",
    77: "exec-b91c6afb-8466-403f-8fbc-4e5d3d8affec.png",
    78: "exec-802804dd-6548-47f6-9a0b-c68f04de6062.png",
    79: "exec-f2c83f81-2488-46e4-8cea-f7a1aaf5dd2c.png",
    80: "exec-83eb8082-67e1-4193-9893-2caaac7e4c3d.png",
    81: "exec-aea34da3-b84e-43e4-8458-130bc50e0491.png",
    82: "exec-3f95e83d-a251-4f9a-92da-09966212ee71.png",
    83: "exec-bd77721e-037a-4a03-b31c-25c33ffc1fc8.png",
    84: "exec-ea926386-14df-458e-abff-5d62ba86b78d.png",
    85: "exec-cca189aa-7990-42bf-9118-8e9170785b6d.png",
    86: "exec-c9de65ad-dfa0-4729-9121-fa86349ad6f0.png",
    87: "exec-ea3f53c8-8a7f-47e0-8e35-b69d3a418d1a.png",
    88: "exec-d43476a2-d3bd-4d67-95b3-3ed295511281.png",
    89: "exec-209a6399-2cae-40fe-8457-b42828cb31e6.png",
    90: "exec-5da31482-3d2d-44a4-abf1-71d9a1bce9f3.png",
    91: "exec-b6926ed1-6b9d-416b-93c1-4d63e8fb076a.png",
    92: "exec-70a30b67-6a46-4c93-857a-d14db119b0ba.png",
    93: "exec-1b868f6a-0677-4d30-b1a9-bac4b31eee00.png",
    94: "exec-217d8dd1-e363-45a8-a3d2-f7a888163d8d.png",
    95: "exec-17312c3e-b926-46c2-9ca0-1719b7ed5918.png",
    96: "exec-6a2cffae-b6d8-427b-890c-d15d8cc5b27e.png",
    97: "exec-4f4fbe30-4169-404c-996c-db50b51b1779.png",
    98: "exec-dec14183-edc7-4937-add9-9f735f4ee3f2.png",
    99: "exec-4b2e9d6a-104f-452c-b221-287831a5dc0d.png",
    100: "exec-c69ce3e7-840a-429b-8d61-1d15244f0f78.png",
    101: "exec-7b5a9481-3db6-4e76-9de9-b82e5dee3370.png",
    102: "exec-ccf736ba-b404-4eeb-985b-705327928050.png",
    103: "exec-a106cd7b-742b-4295-9928-49a1c3f19ac0.png",
    104: "exec-50a9e5c8-dbd2-43fb-827d-85df23f63341.png",
    105: "exec-ab31b2d0-b00e-40bf-8c5f-b7c55207ce3a.png",
    106: "exec-57eb79b4-87d5-4878-9721-61a1e727d495.png",
    107: "exec-07bc39bd-0ad9-41b5-82f8-ae1ecfbf7338.png",
    108: "exec-852a39bd-6eff-42cd-9c9b-280850dbbbc1.png",
    109: "exec-88fcaac8-0109-4339-934e-cbe46da2f7a7.png",
    110: "exec-71a7d978-a89f-40f7-87f8-880ab5fc2dd3.png",
    111: "exec-9e45bb79-e084-4204-aea5-708c50fa4b80.png",
    112: "exec-1bbbf5df-b0d6-4023-914f-88b71f6480d6.png",
    113: "exec-f3db386e-49ef-497a-b2eb-2e5e28ddf729.png",
    114: "exec-5e7379b4-58d5-4aa0-80d3-eec184294a7b.png",
    115: "exec-a243f6b8-ca56-44a6-90c5-550df87668c5.png",
    116: "exec-7edca37d-66ff-4055-9a37-93b71301f599.png",
    117: "exec-051f364d-6989-481a-8a16-b6c6b0e360a9.png",
}


LENGTHS = {
    slot: length
    for slot, length in enumerate(
        [
            6.9, 7.2, 7.3, 7.0, 9.0, 6.5, 5.2, 7.0, 7.0, 5.6, 6.8,
            6.8, 7.2, 17.6, 20.9, 5.0, 7.5, 7.6, 16.5, 7.0, 8.0, 6.2,
            5.0, 7.2, 12.0, 7.5, 5.8, 12.0, 5.2, 5.6, 6.0, 7.0, 2.0,
            4.5, 7.2, 7.0, 6.5, 6.8, 6.2, 6.2, 6.2, 4.8, 5.2, 4.9, 4.7,
            5.0, 6.8, 7.2, 5.0, 7.0, 5.8, 5.8, 7.0, 7.0, 8.5, 10.0,
            8.5, 5.5, 5.5, 6.5, 7.0, 10.0, 6.0, 7.0, 7.0, 6.8,
        ],
        start=52,
    )
}


NO_BLUE_LIGHTS = {
    62, 63, 68, 69, 70, 71, 72, 75, 79, 80, 81, 82, 85, 88, 89,
    96, 98, 105, 106, 107,
}


def service_for_slot(slot: int) -> str:
    if 52 <= slot <= 57 or slot in {83, 92, 109, 117}:
        return "police"
    if 58 <= slot <= 68:
        return "coastguard"
    if 69 <= slot <= 73:
        return "lifeboat"
    if 74 <= slot <= 79 or slot in {91, 108}:
        return "fire"
    if 80 <= slot <= 82:
        return "airfield"
    if slot == 84 or 95 <= slot <= 99:
        return "ambulance"
    if 85 <= slot <= 94 or 100 <= slot <= 104:
        return "search-and-rescue"
    if 105 <= slot <= 107:
        return "recovery"
    if 110 <= slot <= 115:
        return "eod"
    return "multi-service"


def lights_for_slot(slot: int) -> list[dict]:
    if slot in NO_BLUE_LIGHTS:
        return []
    if slot in {65, 66}:
        return [
            {"x": 0.70, "y": 0.42, "group": "a", "size": 0.70},
            {"x": 0.12, "y": 0.30, "group": "b", "size": 0.60},
            {"x": 0.86, "y": 0.62, "group": "b", "size": 0.55},
        ]
    if slot == 84:
        return [
            {"x": 0.29, "y": 0.30, "group": "a", "size": 0.55},
            {"x": 0.90, "y": 0.43, "group": "b", "size": 0.55},
        ]
    return [
        {"x": 0.36, "y": 0.075, "group": "a", "size": 0.88},
        {"x": 0.025, "y": 0.60, "group": "b", "size": 0.55},
        {"x": 0.965, "y": 0.43, "group": "a", "size": 0.48},
    ]


def main() -> None:
    slot_data = json.loads(SLOTS_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    slots = {int(item["slot"]): item for item in slot_data["slots"]}
    vehicles = {
        int(item["missionchief_slot"]): item
        for item in manifest["vehicles"]
        if int(item["missionchief_slot"]) < 52
    }

    for slot in range(52, 118):
        slot_item = slots[slot]
        asset_id = slot_item["id"]
        source = ROOT / "assets" / "sources" / f"{asset_id}-chroma.png"
        master = ROOT / "assets" / "masters" / "static" / f"{asset_id}-selected.png"
        generated = GENERATED_ROOT / GENERATED[slot]

        source.parent.mkdir(parents=True, exist_ok=True)
        if generated.exists():
            shutil.copy2(generated, source)
        elif not source.exists():
            raise FileNotFoundError(f"missing generated and archived source for slot {slot}: {generated}")

        subprocess.run([sys.executable, str(PREPARE), str(source), str(master)], check=True)
        vehicles[slot] = {
            "id": asset_id,
            "display_name": slot_item["label"],
            "missionchief_slot": slot,
            "service": service_for_slot(slot),
            "source": str(master.relative_to(ROOT)),
            "real_length_metres": LENGTHS[slot],
            "lights": lights_for_slot(slot),
        }
        slot_item["asset_status"] = "approved-golden"
        slot_item["asset_id"] = asset_id

    manifest["pack"]["working_status"] = "production-complete"
    manifest["vehicles"] = [vehicles[slot] for slot in sorted(vehicles)]
    slot_data["totals"] = {"slots": 117, "approved_golden": 117, "planned": 0}
    slot_data["pack"]["status"] = "private-production-complete"

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    SLOTS_PATH.write_text(json.dumps(slot_data, indent=2) + "\n", encoding="utf-8")
    print("registered slots 52-117; production manifest now contains 117 vehicles")


if __name__ == "__main__":
    main()
