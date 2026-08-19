#!/usr/bin/env python3
"""Build the isolated v2 direction-neutral calibration assets and QA sheets."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from v2_emergency_light import Fixture, ROAD_DOUBLE_FLASH, build_animation_frames, save_apng


ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "assets/masters/v2.0.0/fire-rescue-pump.png"
STATIC = ROOT / "assets/exports/v2/static/fire-rescue-pump.png"
ANIMATED = ROOT / "assets/exports/v2/animated/fire-rescue-pump.png"
PREVIEW = ROOT / "assets/previews/v2.0.0/water-ladder-emergency-light-calibration.png"


WATER_LADDER_FIXTURES = (
    # Raised roof bar, divided into perspective-correct LED modules.  The
    # modules share a bloom but retain visible dark gaps between their cores.
    Fixture("a", "polygon", ((128, 106), (134, 104), (138, 106), (132, 109)), bloom_radius=2.2),
    Fixture("a", "polygon", ((139, 103), (145, 101), (149, 103), (143, 106)), bloom_radius=2.2),
    Fixture("b", "polygon", ((151, 100), (157, 98), (161, 100), (155, 103)), bloom_radius=2.2),
    Fixture("b", "polygon", ((163, 97), (169, 95), (174, 98), (167, 100)), bloom_radius=2.2),
    # Front corner/grille repeaters.
    Fixture("a", "ellipse", ((174, 141), (178, 145)), bloom_radius=2.1),
    Fixture("b", "ellipse", ((156, 157), (160, 161)), bloom_radius=2.1),
    # Rear upper-body repeaters maintain visibility when the cab is obscured.
    Fixture("a", "ellipse", ((31, 91), (34, 94)), bloom_radius=1.8, bloom_strength=0.85),
    Fixture("b", "ellipse", ((43, 112), (46, 115)), bloom_radius=1.8, bloom_strength=0.85),
)


def _checkerboard(size: tuple[int, int], cell: int = 10) -> Image.Image:
    image = Image.new("RGB", size, (224, 227, 230))
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], cell):
        for x in range(0, size[0], cell):
            if (x // cell + y // cell) % 2:
                draw.rectangle((x, y, x + cell - 1, y + cell - 1), fill=(194, 199, 204))
    return image


def _label(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str) -> None:
    draw.text(xy, text, fill=(236, 240, 244), font=ImageFont.load_default())


def render_preview(base: Image.Image, frames: list[Image.Image]) -> None:
    width, height = 1040, 1010
    sheet = Image.new("RGB", (width, height), (20, 24, 30))
    draw = ImageDraw.Draw(sheet)
    draw.text((24, 18), "v2 direction-neutral Water Ladder — emergency-light calibration", fill=(255, 255, 255))
    draw.text((24, 38), "Static plus all 12 full-canvas APNG frames; actual-size checks at 100%, 75% and 50%", fill=(168, 180, 194))

    tiles = [(base, "static / lenses off")] + [
        (frame, f"frame {index + 1:02d} / {ROAD_DOUBLE_FLASH[index].duration_ms} ms")
        for index, frame in enumerate(frames)
    ]
    for index, (sprite, label) in enumerate(tiles):
        col = index % 5
        row = index // 5
        x = 20 + col * 204
        y = 74 + row * 224
        tile = _checkerboard((200, 200))
        tile.paste(sprite, (0, 0), sprite)
        sheet.paste(tile, (x, y))
        _label(draw, (x + 4, y + 204), label)

    y = 942
    for scale, label in ((1.0, "100%"), (0.75, "75%"), (0.5, "50%")):
        sprite = frames[0].resize(
            (round(200 * scale), round(200 * scale)), Image.Resampling.LANCZOS
        )
        x = 24 if scale == 1.0 else (270 if scale == 0.75 else 470)
        bg = Image.new("RGB", sprite.size, (238, 241, 235))
        bg.paste(sprite, (0, 0), sprite)
        sheet.paste(bg, (x, y - sprite.height + 42))
        draw.text((x, y + 46), label, fill=(255, 255, 255))

        dark_x = x + sprite.width + 8
        dark = Image.new("RGB", sprite.size, (35, 43, 47))
        dark.paste(sprite, (0, 0), sprite)
        sheet.paste(dark, (dark_x, y - sprite.height + 42))

    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(PREVIEW, optimize=True)


def main() -> None:
    if not MASTER.exists():
        raise FileNotFoundError(f"Missing approved v2 master: {MASTER}")
    base = Image.open(MASTER).convert("RGBA")
    if base.size != (200, 200):
        raise ValueError(f"Expected 200 x 200 master, found {base.size}")

    STATIC.parent.mkdir(parents=True, exist_ok=True)
    ANIMATED.parent.mkdir(parents=True, exist_ok=True)
    base.save(STATIC, optimize=True)
    frames, durations = build_animation_frames(base, WATER_LADDER_FIXTURES)
    save_apng(str(ANIMATED), frames, durations)
    render_preview(base, frames)

    print(f"static={STATIC.relative_to(ROOT)}")
    print(f"animated={ANIMATED.relative_to(ROOT)}")
    print(f"preview={PREVIEW.relative_to(ROOT)}")
    print(f"frames={len(frames)} duration_ms={sum(durations)}")


if __name__ == "__main__":
    main()
