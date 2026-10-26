"""Custom 失帧 outlines for the focus-002 title study.

Songti and UMing are only structure donors. A vertical missing column is cut
through both characters before tracing, so the dropped frame is part of the
letter, not a later animation preset.

Called by render_study.py in this same directory. No production module imports it.
graphics_focus.py only fades Noto Serif TextRuns and cannot cut a frame out of a glyph.
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFont

SERIF = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"
UMING = "/usr/share/fonts/truetype/arphic/uming.ttc"

# Left rain field of the close-up. Clears the AI badge and her face.
BOXES = ((210, 118, 560, 430), (210, 548, 560, 400))
# One shared column, where both characters actually have ink.
# 帧's radical gap sits near 0.40–0.45, so a cut there only nicks the edge.
SLIT_START = 0.50


def _segments(mask: np.ndarray) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    image = np.pad(mask.astype(np.uint8), 1)
    top = image[:-1, :-1]
    right = image[:-1, 1:]
    bottom = image[1:, 1:]
    left = image[1:, :-1]
    code = (top << 3) | (right << 2) | (bottom << 1) | left
    north, east, south, west = (0.5, 0.0), (1.0, 0.5), (0.5, 1.0), (0.0, 0.5)
    table = {
        1: ((west, south),),
        2: ((east, south),),
        3: ((west, east),),
        4: ((north, east),),
        5: ((north, west), (east, south)),
        6: ((north, south),),
        7: ((north, west),),
        8: ((north, west),),
        9: ((north, south),),
        10: ((north, east), (west, south)),
        11: ((north, east),),
        12: ((west, east),),
        13: ((east, south),),
        14: ((west, south),),
    }
    rows, cols = np.nonzero((code != 0) & (code != 15))
    segments = []
    for row, col in zip(rows.tolist(), cols.tolist()):
        for a, b in table.get(int(code[row, col]), ()):
            segments.append(((col + a[0], row + a[1]), (col + b[0], row + b[1])))
    return segments


def _loops(segments: list[tuple[tuple[float, float], tuple[float, float]]]) -> list[np.ndarray]:
    def key(point: tuple[float, float]) -> tuple[float, float]:
        return (round(point[0], 3), round(point[1], 3))

    adjacency: dict[tuple[float, float], list[tuple[float, float]]] = {}
    for start, end in segments:
        adjacency.setdefault(key(start), []).append(key(end))
        adjacency.setdefault(key(end), []).append(key(start))
    used: set[tuple[tuple[float, float], tuple[float, float]]] = set()
    loops = []
    for origin, neighbors in adjacency.items():
        for nxt in neighbors:
            edge = tuple(sorted((origin, nxt)))
            if edge in used:
                continue
            loop = [origin]
            previous, current = origin, nxt
            for _ in range(len(segments) + 2):
                used.add(tuple(sorted((previous, current))))
                loop.append(current)
                if current == origin:
                    break
                choices = []
                for candidate in adjacency[current]:
                    if candidate == previous:
                        continue
                    mark = tuple(sorted((current, candidate)))
                    if mark not in used:
                        choices.append(candidate)
                if not choices:
                    break
                previous, current = current, choices[0]
            if len(loop) > 3 and loop[0] == loop[-1]:
                loops.append(np.asarray(loop[:-1], dtype=float))
    return loops


def _simplify(points: np.ndarray, epsilon: float) -> np.ndarray:
    if len(points) < 4:
        return points

    def rdp(path: np.ndarray) -> np.ndarray:
        if len(path) < 3:
            return path
        start, end = path[0], path[-1]
        line = end - start
        length = float(np.hypot(*line))
        if length == 0:
            distance = np.hypot(*(path - start).T)
        else:
            distance = np.abs(line[0] * (start[1] - path[:, 1]) - line[1] * (start[0] - path[:, 0])) / length
        index = int(np.argmax(distance))
        if distance[index] <= epsilon:
            return np.vstack((start, end))
        left, right = rdp(path[: index + 1]), rdp(path[index:])
        return np.vstack((left[:-1], right))

    closed = np.vstack((points, points[0]))
    simplified = rdp(closed)
    if len(simplified) < 4:
        return points
    return simplified[:-1]


def _mask(font_path: str, face: int, character: str, slit_width: float, slit_start: float) -> np.ndarray:
    size = 900
    font = ImageFont.truetype(font_path, size, index=face)
    image = Image.new("L", (size + 80, size + 80), 0)
    draw = ImageDraw.Draw(image)
    draw.text((40, 20), character, font=font, fill=255)
    mask = np.asarray(image) >= 128
    ys, xs = np.nonzero(mask)
    mask = mask[ys.min() : ys.max() + 1, xs.min() : xs.max() + 1]
    if slit_width > 0:
        width = mask.shape[1]
        x0 = int(round(width * slit_start))
        x1 = min(width, x0 + max(6, int(round(width * slit_width))))
        mask[:, x0:x1] = False
    return mask


def _place(
    mask: np.ndarray, box: tuple[int, int, int, int], epsilon: float, uniform: bool = False
) -> list[np.ndarray]:
    x, y, width, height = box
    loops = []
    if uniform:
        fit = min(width / mask.shape[1], height / mask.shape[0])
        offset_x = x + (width - mask.shape[1] * fit) / 2
        offset_y = y + (height - mask.shape[0] * fit) / 2
        scale_x = scale_y = fit
    else:
        offset_x, offset_y = x, y
        scale_x = width / mask.shape[1]
        scale_y = height / mask.shape[0]
    for loop in _loops(_segments(mask)):
        if len(loop) < 3:
            continue
        loop = loop - 1.0
        simplified = _simplify(loop, epsilon)
        if len(simplified) < 3:
            continue
        placed = np.column_stack((
            offset_x + simplified[:, 0] * scale_x, offset_y + simplified[:, 1] * scale_y
        ))
        area = float(np.dot(placed[:, 0], np.roll(placed[:, 1], -1)) - np.dot(placed[:, 1], np.roll(placed[:, 0], -1)))
        if abs(area) < 80:
            continue
        loops.append(placed)
    return loops


def _signed_area(loop: np.ndarray) -> float:
    return 0.5 * float(
        np.dot(loop[:, 0], np.roll(loop[:, 1], -1)) - np.dot(loop[:, 1], np.roll(loop[:, 0], -1))
    )


def _contains(loop: np.ndarray, point: tuple[float, float]) -> bool:
    x, y = point
    inside = False
    for index in range(len(loop)):
        x0, y0 = loop[index]
        x1, y1 = loop[(index + 1) % len(loop)]
        if (y0 > y) != (y1 > y):
            cross = (x1 - x0) * (y - y0) / (y1 - y0) + x0
            if x < cross:
                inside = not inside
    return inside


def _interior_point(loop: np.ndarray) -> tuple[float, float]:
    center = loop.mean(axis=0)
    if _contains(loop, (float(center[0]), float(center[1]))):
        return (float(center[0]), float(center[1]))
    mid = (loop[0] + loop[1]) / 2
    direction = center - mid
    length = float(np.hypot(direction[0], direction[1])) or 1.0
    nudged = mid + direction / length * 2.0
    return (float(nudged[0]), float(nudged[1]))


def _orient(loops: list[np.ndarray], outer_negative: bool) -> list[np.ndarray]:
    """Give outer contours one winding and each nested counter the other.

    SVG nonzero fill then keeps counters. A positive full-frame veil with
    negative letter contours opens the photograph only inside the strokes.
    """
    areas = [_signed_area(loop) for loop in loops]
    points = [_interior_point(loop) for loop in loops]
    oriented = []
    for index, loop in enumerate(loops):
        depth = sum(
            1
            for other, other_area in zip(loops, areas)
            if other is not loop and abs(other_area) > abs(areas[index]) and _contains(other, points[index])
        )
        want_negative = outer_negative if depth % 2 == 0 else not outer_negative
        if (areas[index] < 0) != want_negative:
            loop = loop[::-1]
        oriented.append(loop)
    return oriented


def _path(loops: list[np.ndarray], reverse: bool) -> str:
    commands = []
    for loop in loops:
        points = loop[::-1] if reverse else loop
        head = points[0]
        commands.append(f"M{head[0]:.1f} {head[1]:.1f}")
        commands.extend(f"L{point[0]:.1f} {point[1]:.1f}" for point in points[1:])
        commands.append("Z")
    return " ".join(commands)


def letter_loops(kind: str) -> list[np.ndarray]:
    # UKai's 车 collapses toward 中 once it is cut and set on the rain.
    # UMing keeps 帧 readable. The slit stays in the right half, off 车.
    if kind == "exposure":
        font_path, face, epsilon, slit, start = SERIF, 2, 0.85, 0.030, 0.50
    elif kind == "inscription":
        font_path, face, epsilon, slit, start = UMING, 0, 0.90, 0.036, 0.64
    else:
        raise ValueError(kind)
    loops = []
    for character, box in zip("失帧", BOXES):
        loops.extend(_place(
            _mask(font_path, face, character, slit, start), box, epsilon, uniform=(kind == "inscription")
        ))
    # Exposure holes must wind against the positive veil. Inscription ink winds positive.
    return _orient(loops, outer_negative=(kind == "exposure"))


def exposure_path() -> str:
    """Near-black field; the surviving rain is the ink of 失帧."""
    veil = np.array([[0, 0], [1920, 0], [1920, 1080], [0, 1080]], dtype=float)
    return _path([veil, *letter_loops("exposure")], reverse=False)


def inscription_path() -> str:
    """Dark writing on the glass. The picture stays; one column of the writing does not."""
    return _path(letter_loops("inscription"), reverse=False)
