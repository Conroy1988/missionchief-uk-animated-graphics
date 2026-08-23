#!/usr/bin/env python3
"""Render fleet and tail-rotor QA previews for the current compact release."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageFont, ImageSequence

from v2_helicopter_rotors import HELICOPTER_GEOMETRY
from v2_profile import (
    AIR_MARINE_FRAME_COUNT,
    ANIMATED_DIR,
    EXPORT_SCALE,
    PREVIEW_DIR,
    RELEASE,
    ROOT,
)


FLEET_GIF = PREVIEW_DIR / "helicopter-rotor-fleet.gif"
TAIL_GIF = PREVIEW_DIR / "helicopter-tail-rotor-alignment.gif"
FRAME_SHEET = PREVIEW_DIR / "helicopter-rotor-frame-audit.png"
POLICE_COMPARISON = PREVIEW_DIR / "police-helicopter-rotor-comparison.gif"
BASELINE_RELEASE = "v2.0.1"

ORDER = (
    "hems",
    "police-helicopter",
    "coastguard-rescue-helicopter",
    "coastguard-rescue-helicopter-large",
)
LABELS = {
    "hems": "HEMS",
    "police-helicopter": "Police helicopter",
    "coastguard-rescue-helicopter": "Coastguard rescue helicopter",
    "coastguard-rescue-helicopter-large": "Large coastguard helicopter",
}
FLEET_LABELS = {
    "hems": "HEMS",
    "police-helicopter": "Police helicopter",
    "coastguard-rescue-helicopter": "Coastguard rescue",
    "coastguard-rescue-helicopter-large": "Large coastguard",
}


def _font(size: int) -> ImageFont.ImageFont:
    for candidate in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ):
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def _decode(asset_id: str) -> tuple[list[Image.Image], list[int]]:
    frames: list[Image.Image] = []
    durations: list[int] = []
    with Image.open(ANIMATED_DIR / f"{asset_id}.png") as image:
        for index, frame in enumerate(ImageSequence.Iterator(image)):
            image.seek(index)
            frames.append(frame.convert("RGBA"))
            durations.append(round(float(image.info.get("duration", 0))))
    if len(frames) != AIR_MARINE_FRAME_COUNT:
        raise RuntimeError(
            f"Expected {AIR_MARINE_FRAME_COUNT} frames for {asset_id}, found {len(frames)}"
        )
    return frames, durations


def _decode_police_baseline() -> list[Image.Image]:
    path = "assets/exports/v2/animated/police-helicopter.png"
    result = subprocess.run(
        ["git", "show", f"{BASELINE_RELEASE}:{path}"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    frames: list[Image.Image] = []
    with Image.open(BytesIO(result.stdout)) as image:
        for frame in ImageSequence.Iterator(image):
            frames.append(frame.convert("RGBA"))
    if len(frames) != 18:
        raise RuntimeError(
            f"Expected 18 Police frames at {BASELINE_RELEASE}, found {len(frames)}"
        )
    return frames


def _grid(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], spacing: int = 40) -> None:
    left, top, right, bottom = box
    for x in range(left, right + 1, spacing):
        draw.line((x, top, x, bottom), fill=(39, 52, 64), width=1)
    for y in range(top, bottom + 1, spacing):
        draw.line((left, y, right, y), fill=(39, 52, 64), width=1)


def fleet_preview(decoded: dict[str, list[Image.Image]], durations: list[int]) -> None:
    title_font = _font(28)
    label_font = _font(18)
    note_font = _font(14)
    rendered: list[Image.Image] = []
    for frame_index in range(AIR_MARINE_FRAME_COUNT):
        canvas = Image.new("RGB", (960, 760), (13, 20, 28))
        draw = ImageDraw.Draw(canvas)
        draw.text((24, 18), f"{RELEASE} helicopter rotor standard", font=title_font, fill=(244, 248, 251))
        draw.text(
            (24, 55),
            "Baked blades removed · continuous main rotor · component-aligned tail motion",
            font=note_font,
            fill=(166, 190, 207),
        )
        for index, asset_id in enumerate(ORDER):
            column, row = index % 2, index // 2
            left, top = 24 + column * 468, 86 + row * 326
            box = (left, top, left + 444, top + 302)
            draw.rounded_rectangle(box, radius=18, fill=(30, 42, 53), outline=(54, 71, 84), width=1)
            _grid(draw, (left + 1, top + 42, left + 443, top + 301))
            draw.text((left + 14, top + 10), FLEET_LABELS[asset_id], font=label_font, fill=(235, 242, 247))
            tail_kind = HELICOPTER_GEOMETRY[asset_id].tail.kind
            draw.text(
                (left + 430, top + 16),
                tail_kind.upper(),
                font=note_font,
                fill=(111, 210, 255) if tail_kind == "fenestron" else (255, 161, 124),
                anchor="ra",
            )
            sprite = decoded[asset_id][frame_index].resize((286, 286), Image.Resampling.LANCZOS)
            canvas.paste(sprite, (left + 79, top + 28), sprite)
        draw.text(
            (708, 732),
            f"Frame {frame_index + 1:02d}/{AIR_MARINE_FRAME_COUNT:02d} · production assets 110×110",
            font=note_font,
            fill=(180, 193, 205),
        )
        rendered.append(canvas)
    rendered[0].save(
        FLEET_GIF,
        save_all=True,
        append_images=rendered[1:],
        duration=durations,
        loop=0,
        disposal=2,
        optimize=False,
    )


def tail_preview(decoded: dict[str, list[Image.Image]], durations: list[int]) -> None:
    title_font = _font(26)
    label_font = _font(15)
    note_font = _font(13)
    rendered: list[Image.Image] = []
    crop_size = 28
    scale = 8
    for frame_index in range(AIR_MARINE_FRAME_COUNT):
        canvas = Image.new("RGB", (1000, 330), (13, 20, 28))
        draw = ImageDraw.Draw(canvas)
        draw.text((24, 16), "Tail-rotor alignment audit", font=title_font, fill=(244, 248, 251))
        draw.text(
            (24, 50),
            "Every effect is centred on the physical rotor opening or hub before 110×110 export.",
            font=note_font,
            fill=(166, 190, 207),
        )
        for column, asset_id in enumerate(ORDER):
            geometry = HELICOPTER_GEOMETRY[asset_id].tail
            centre_x = round(geometry.centre[0] * EXPORT_SCALE)
            centre_y = round(geometry.centre[1] * EXPORT_SCALE)
            left = max(0, min(110 - crop_size, centre_x - crop_size // 2))
            top = max(0, min(110 - crop_size, centre_y - crop_size // 2))
            sprite = Image.new("RGBA", (110, 110), (31, 44, 55, 255))
            sprite.alpha_composite(decoded[asset_id][frame_index])
            crop = sprite.crop((left, top, left + crop_size, top + crop_size))
            crop = crop.resize((crop_size * scale, crop_size * scale), Image.Resampling.NEAREST)
            panel_x = 18 + column * 246
            draw.rounded_rectangle((panel_x, 78, panel_x + 228, 312), radius=14, fill=(30, 42, 53))
            canvas.paste(crop.convert("RGB"), (panel_x + 2, 80))
            label = LABELS[asset_id].replace(" helicopter", "")
            draw.text((panel_x + 10, 286), label, font=label_font, fill=(235, 242, 247))
        draw.text((897, 310), f"F{frame_index + 1:02d}", font=note_font, fill=(180, 193, 205))
        rendered.append(canvas)
    rendered[0].save(
        TAIL_GIF,
        save_all=True,
        append_images=rendered[1:],
        duration=durations,
        loop=0,
        disposal=2,
        optimize=False,
    )


def frame_sheet(decoded: dict[str, list[Image.Image]]) -> None:
    selected = tuple(range(AIR_MARINE_FRAME_COUNT))
    font = _font(16)
    cell_width, cell_height = 330, 360
    sheet = Image.new("RGB", (cell_width * len(selected), cell_height * len(ORDER)), (17, 25, 34))
    draw = ImageDraw.Draw(sheet)
    for row, asset_id in enumerate(ORDER):
        for column, frame_index in enumerate(selected):
            tile = Image.new("RGBA", (110, 110), (31, 44, 55, 255))
            tile.alpha_composite(decoded[asset_id][frame_index])
            x, y = column * cell_width, row * cell_height
            sheet.paste(tile.convert("RGB").resize((330, 330), Image.Resampling.NEAREST), (x, y))
            draw.text(
                (x + 8, y + 334),
                f"{LABELS[asset_id]} · F{frame_index + 1}",
                font=font,
                fill=(235, 242, 247),
            )
    sheet.save(FRAME_SHEET, optimize=True)


def police_comparison(current: list[Image.Image], durations: list[int]) -> None:
    baseline = _decode_police_baseline()
    title_font = _font(25)
    label_font = _font(17)
    note_font = _font(13)
    rendered: list[Image.Image] = []
    for frame_index in range(AIR_MARINE_FRAME_COUNT):
        canvas = Image.new("RGB", (760, 430), (13, 20, 28))
        draw = ImageDraw.Draw(canvas)
        draw.text(
            (24, 17),
            "Police helicopter rotor correction",
            font=title_font,
            fill=(244, 248, 251),
        )
        labels = (
            (24, f"{BASELINE_RELEASE} stopped-blade overlay", (255, 161, 124)),
            (400, f"{RELEASE} calibrated rotor motion", (111, 210, 255)),
        )
        for left, label, colour in labels:
            draw.text((left, 54), label, font=label_font, fill=colour)
            draw.rounded_rectangle(
                (left, 82, left + 336, 394),
                radius=16,
                fill=(30, 42, 53),
                outline=(54, 71, 84),
            )
            _grid(draw, (left + 1, 83, left + 335, 393), spacing=56)
        baseline_index = round(frame_index * (len(baseline) - 1) / (AIR_MARINE_FRAME_COUNT - 1))
        for left, frame in ((24, baseline[baseline_index]), (400, current[frame_index])):
            sprite = frame.resize((308, 308), Image.Resampling.LANCZOS)
            canvas.paste(sprite, (left + 14, 84), sprite)
        draw.text(
            (736, 408),
            f"Frame {frame_index + 1:02d}/{AIR_MARINE_FRAME_COUNT:02d} · production assets 110×110",
            font=note_font,
            fill=(180, 193, 205),
            anchor="ra",
        )
        rendered.append(canvas)
    rendered[0].save(
        POLICE_COMPARISON,
        save_all=True,
        append_images=rendered[1:],
        duration=durations,
        loop=0,
        disposal=2,
        optimize=False,
    )


def main() -> None:
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    decoded: dict[str, list[Image.Image]] = {}
    durations: list[int] | None = None
    for asset_id in ORDER:
        asset_frames, asset_durations = _decode(asset_id)
        decoded[asset_id] = asset_frames
        if durations is None:
            durations = asset_durations
        elif durations != asset_durations:
            raise RuntimeError(f"Helicopter duration mismatch for {asset_id}")
    if durations is None:
        raise RuntimeError("No helicopter frames decoded")

    fleet_preview(decoded, durations)
    tail_preview(decoded, durations)
    frame_sheet(decoded)
    police_comparison(decoded["police-helicopter"], durations)
    print(f"fleet={FLEET_GIF.relative_to(ROOT)}")
    print(f"tail={TAIL_GIF.relative_to(ROOT)}")
    print(f"frames={FRAME_SHEET.relative_to(ROOT)}")
    print(f"police_comparison={POLICE_COMPARISON.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
