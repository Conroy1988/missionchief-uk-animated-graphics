#!/usr/bin/env python3
"""Fail if the shared emergency-light primitive can form a bar or tile."""

from __future__ import annotations

import inspect
import json
from collections import deque

from PIL import Image, ImageChops

import build_prototypes
import build_v1_1_enhanced
import emergency_light


def components(alpha: Image.Image) -> list[dict[str, int]]:
    width, height = alpha.size
    pixels = alpha.load()
    seen: set[tuple[int, int]] = set()
    results: list[dict[str, int]] = []
    for y in range(height):
        for x in range(width):
            if (x, y) in seen or pixels[x, y] == 0:
                continue
            queue = deque([(x, y)])
            seen.add((x, y))
            points: list[tuple[int, int]] = []
            while queue:
                px, py = queue.popleft()
                points.append((px, py))
                for neighbour in ((px - 1, py), (px + 1, py), (px, py - 1), (px, py + 1)):
                    nx, ny = neighbour
                    if not (0 <= nx < width and 0 <= ny < height):
                        continue
                    if neighbour in seen or pixels[nx, ny] == 0:
                        continue
                    seen.add(neighbour)
                    queue.append(neighbour)
            results.append(
                {
                    "pixels": len(points),
                    "width": max(point[0] for point in points) - min(point[0] for point in points) + 1,
                    "height": max(point[1] for point in points) - min(point[1] for point in points) + 1,
                }
            )
    return results


def main() -> None:
    errors: list[str] = []
    source = inspect.getsource(emergency_light.render_point_emitter)
    for forbidden in ("draw.line(", "draw.ellipse(", "draw.rectangle(", "GaussianBlur"):
        if forbidden in source:
            errors.append(f"point emitter contains forbidden shape operation: {forbidden}")
    for module in (build_prototypes, build_v1_1_enhanced):
        wrapper = inspect.getsource(module.blue_flash)
        if "render_point_emitter" not in wrapper:
            errors.append(f"{module.__name__}.blue_flash bypasses the shared primitive")

    samples = 0
    largest = {"pixels": 0, "width": 0, "height": 0}
    size = (9, 9)
    for px, py in ((0, 0), (1, 1), (4, 4), (7, 7), (8, 8)):
        for strength in (0.0, 0.5, 1.0):
            full_mask = Image.new("L", size, 255)
            for variant in (0, 1):
                emitter = emergency_light.render_point_emitter(
                    size, px, py, strength, full_mask, variant
                )
                if emitter.getpixel((px, py))[3] != 255:
                    errors.append(f"centre lens is not fully visible at {(px, py)} strength {strength}")
                for component in components(emitter.getchannel("A")):
                    if component["pixels"] > largest["pixels"]:
                        largest = component
                    if component["width"] > 1 or component["height"] > 1:
                        errors.append(f"primitive produced a joined component: {component}")
                samples += 1

    left = emergency_light.render_point_emitter(size, 4, 4, 1.0)
    right = emergency_light.render_point_emitter(size, 5, 4, 1.0)
    adjacent = Image.alpha_composite(left, right)
    adjacent_largest = max(components(adjacent.getchannel("A")), key=lambda item: item["pixels"])
    if adjacent_largest["width"] > 2 or adjacent_largest["height"] > 2:
        errors.append(f"two adjacent lamps exceed the 2x2 release envelope: {adjacent_largest}")

    clipped = emergency_light.render_point_emitter(size, 4, 4, 1.0, Image.new("L", size, 0))
    if ImageChops.difference(clipped, Image.new("RGBA", size, (0, 0, 0, 0))).getbbox() is not None:
        errors.append("zero clip mask did not suppress the emitter")

    report = {
        "fixture": emergency_light.POINT_EMITTER_FIXTURE,
        "samples": samples,
        "largest_single_emitter_component": largest,
        "largest_two-adjacent-emitter_component": adjacent_largest,
        "forbidden_shape_operations": ["line", "ellipse", "rectangle", "blur"],
        "all_passed": not errors,
        "errors": errors,
    }
    print(json.dumps(report, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
