#!/usr/bin/env python3
"""Write deterministic APNGs whose every frame covers the complete canvas."""

from __future__ import annotations

import binascii
import io
import struct
from pathlib import Path

from PIL import Image


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def chunk(chunk_type: bytes, payload: bytes) -> bytes:
    checksum = binascii.crc32(chunk_type)
    checksum = binascii.crc32(payload, checksum) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + chunk_type + payload + struct.pack(">I", checksum)


def standalone_png_payload(image: Image.Image, compress_level: int) -> tuple[bytes, bytes]:
    """Return one RGBA PNG's IHDR payload and concatenated IDAT stream."""
    buffer = io.BytesIO()
    image.convert("RGBA").save(
        buffer,
        format="PNG",
        optimize=True,
        compress_level=compress_level,
    )
    data = buffer.getvalue()
    if data[:8] != PNG_SIGNATURE:
        raise ValueError("Pillow did not produce a PNG")
    position = 8
    ihdr = b""
    idat: list[bytes] = []
    while position < len(data):
        length = struct.unpack(">I", data[position : position + 4])[0]
        chunk_type = data[position + 4 : position + 8]
        payload = data[position + 8 : position + 8 + length]
        position += length + 12
        if chunk_type == b"IHDR":
            ihdr = payload
        elif chunk_type == b"IDAT":
            idat.append(payload)
    if len(ihdr) != 13 or not idat:
        raise ValueError("standalone frame is missing IHDR or IDAT data")
    return ihdr, b"".join(idat)


def save_full_frame_apng(
    frames: list[Image.Image],
    durations_ms: list[int],
    target: Path,
    *,
    compress_level: int = 9,
    disposal: int = 0,
    blend: int = 0,
) -> None:
    """Write an APNG without encoder-generated rectangular update frames."""
    if not frames:
        raise ValueError("cannot encode an APNG without frames")
    if len(frames) != len(durations_ms):
        raise ValueError("frame and duration counts differ")
    size = frames[0].size
    if any(frame.size != size for frame in frames):
        raise ValueError("APNG frame dimensions differ")
    if disposal not in {0, 1, 2} or blend not in {0, 1}:
        raise ValueError("invalid APNG disposal or blend operation")

    encoded = [standalone_png_payload(frame, compress_level) for frame in frames]
    ihdr = encoded[0][0]
    if any(frame_ihdr != ihdr for frame_ihdr, _payload in encoded):
        raise ValueError("APNG frame IHDR payloads differ")

    output = bytearray(PNG_SIGNATURE)
    output += chunk(b"IHDR", ihdr)
    output += chunk(b"acTL", struct.pack(">II", len(frames), 0))
    sequence = 0
    width, height = size
    for index, ((_frame_ihdr, compressed), duration) in enumerate(zip(encoded, durations_ms)):
        delay = max(1, min(65535, int(duration)))
        control = struct.pack(
            ">IIIIIHHBB",
            sequence,
            width,
            height,
            0,
            0,
            delay,
            1000,
            disposal,
            blend,
        )
        output += chunk(b"fcTL", control)
        sequence += 1
        if index == 0:
            output += chunk(b"IDAT", compressed)
        else:
            output += chunk(b"fdAT", struct.pack(">I", sequence) + compressed)
            sequence += 1
    output += chunk(b"IEND", b"")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(output)
