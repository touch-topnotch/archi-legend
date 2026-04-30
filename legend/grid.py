"""Stage 2: axis & dimension detection from extracted spans.

Heuristics:
- Latin/Cyrillic single letters that match the axis alphabet → Y axes.
- Pure digits 1..20 → X axes.
- Numbers with thousands-separator (e.g. ``82 500``) → dimension chains in mm.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import List, Tuple

from .parse_pdf import TextSpan

CYR_AXIS_ALPHA = list("АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЭЮЯ")
NUM_RE = re.compile(r"^\d+$")
DIM_RE = re.compile(r"^\d{1,3}(?:[\s ]\d{3})+$")  # 82 500, 7 500


@dataclass
class GridInfo:
    axes_x: List[str]
    axes_y: List[str]
    dimensions_mm: List[int]
    width_mm: int | None
    depth_mm: int | None
    grid_step_mm: int | None


def _parse_dim(t: str) -> int | None:
    if DIM_RE.match(t):
        return int(re.sub(r"[\s ]", "", t))
    return None


def detect_grid(spans: List[TextSpan]) -> GridInfo:
    axes_x: List[Tuple[str, float]] = []  # (label, x_center)
    axes_y: List[Tuple[str, float]] = []  # (label, y_center)
    dims: List[int] = []

    if not spans:
        return GridInfo([], [], [], None, None, None)

    xs = [(s.bbox[0] + s.bbox[2]) / 2 for s in spans]
    ys = [(s.bbox[1] + s.bbox[3]) / 2 for s in spans]
    page_xmax, page_ymax = max(xs), max(ys)
    # Axis labels live near sheet borders: numbers at top/bottom strip,
    # cyrillic letters along the right strip.
    band_top = page_ymax * 0.95
    band_right = page_xmax * 0.85

    for s in spans:
        t = s.text
        cx = (s.bbox[0] + s.bbox[2]) / 2
        cy = (s.bbox[1] + s.bbox[3]) / 2

        if NUM_RE.match(t) and 1 <= int(t) <= 30 and cy >= band_top:
            axes_x.append((t, cx))
        # Handle "Г9" style glued labels along the X strip.
        elif cy >= band_top and len(t) >= 2 and t[0] in CYR_AXIS_ALPHA and t[1:].isdigit():
            n = int(t[1:])
            if 1 <= n <= 30:
                axes_x.append((str(n), cx))
        elif len(t) == 1 and t in CYR_AXIS_ALPHA and cx >= band_right:
            axes_y.append((t, cy))
        else:
            d = _parse_dim(t)
            if d is not None:
                dims.append(d)
            # Plain integer dimensions (no separator) — values like "7500" or "82500".
            elif NUM_RE.match(t) and 3000 <= int(t) <= 200000:
                dims.append(int(t))

    # Combine adjacent numeric spans on the same baseline (e.g. "82" + "500").
    by_y: dict[int, list[tuple[float, str]]] = {}
    for s in spans:
        if NUM_RE.match(s.text) and 0 < int(s.text) < 1000:
            key = int(((s.bbox[1] + s.bbox[3]) / 2) // 3)
            by_y.setdefault(key, []).append(((s.bbox[0] + s.bbox[2]) / 2, s.text))
    for parts in by_y.values():
        parts.sort()
        for i in range(len(parts) - 1):
            (x1, t1), (x2, t2) = parts[i], parts[i + 1]
            if 0 < x2 - x1 < 40:
                try:
                    v = int(t1 + t2)
                    if 3000 <= v <= 200000:
                        dims.append(v)
                except ValueError:
                    pass

    # Deduplicate while preserving sort order.
    axes_x.sort(key=lambda x: x[1])
    axes_y.sort(key=lambda x: -x[1])  # PDF Y is top-down; building convention bottom-up
    seen_x: set[str] = set()
    seen_y: set[str] = set()
    xs = [a for a, _ in axes_x if not (a in seen_x or seen_x.add(a))]
    ys = [a for a, _ in axes_y if not (a in seen_y or seen_y.add(a))]

    big = sorted({d for d in dims if d > 30000}, reverse=True)
    width_mm = big[0] if big else None
    depth_mm = None
    if len(big) >= 2:
        for v in big[1:]:
            if width_mm is None or abs(v - width_mm) > 1000:
                depth_mm = v
                break
        if depth_mm is None:
            depth_mm = big[1]

    # Grid step: most common small dim.
    small = [d for d in dims if 3000 <= d <= 12000]
    step = None
    if small:
        from collections import Counter
        step = Counter(small).most_common(1)[0][0]

    return GridInfo(xs, ys, dims, width_mm, depth_mm, step)
