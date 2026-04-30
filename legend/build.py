"""End-to-end LEGEND builder for one floor PDF + an optional building summary.

The dataset's PDFs contain only axis labels and dimension chains as vector text;
the room-label graphics (Russian) are not present as selectable text. We therefore
extract the *envelope* (axes, grid step, building footprint) deterministically and
fall back gracefully on missing fields. The encyclopedia stays useful for any
downstream LLM that needs a structured spec to reason from.
"""
from __future__ import annotations
from pathlib import Path
from typing import Iterable

from .parse_pdf import extract_text_spans, extract_drawings
from .grid import detect_grid
from .schema import BuildingSpec, FloorSpec, Envelope, Counts


FLOOR_FROM_NAME = {
    "цокольный этаж": "0",
    "1 этаж": "1",
    "2 этаж": "2",
    "3 этаж": "3",
}

ELEVATION_M = {"0": -4.3, "1": 0.0, "2": 4.2, "3": 7.2}


def floor_id_from_path(p: Path) -> str:
    stem = p.stem.lower()
    for k, v in FLOOR_FROM_NAME.items():
        if k in stem:
            return v
    return stem


def build_floor(pdf_path: str | Path) -> FloorSpec:
    p = Path(pdf_path)
    spans = extract_text_spans(p)
    g = detect_grid(spans)

    # Wall-segment proxy: count vector strokes longer than 50 pt
    # (very rough — used only as a feature, not as ground truth).
    draws = extract_drawings(p)
    wall_proxy = 0
    for d in draws:
        for it in d.get("items", []):
            if it[0] in ("l", "re") and "rect" in d:
                r = d["rect"]
                if max(r.width, r.height) > 50:
                    wall_proxy += 1
    step_m = (g.grid_step_mm / 1000.0) if g.grid_step_mm else None
    width_m = (g.width_mm or 0) / 1000.0
    depth_m = (g.depth_mm or 0) / 1000.0
    # Fallback: if a dimension is missing, infer from axis count × grid step.
    if step_m:
        if width_m == 0 and len(g.axes_x) >= 2:
            width_m = (len(g.axes_x) - 1) * step_m
        if depth_m == 0 and len(g.axes_y) >= 2:
            depth_m = (len(g.axes_y) - 1) * step_m
    env = Envelope(
        width_m=width_m,
        depth_m=depth_m,
        axes_x=g.axes_x,
        axes_y=g.axes_y,
        grid_step_m=step_m,
    )
    fid = floor_id_from_path(p)
    return FloorSpec(
        floor_id=fid,
        elevation_m=ELEVATION_M.get(fid),
        envelope=env,
        counts=Counts(walls=wall_proxy),
        notes=[
            f"vector-text spans: {len(spans)}",
            f"vector drawings: {len(draws)}",
        ],
    )


def build_building(pdfs: Iterable[str | Path]) -> BuildingSpec:
    floors = [build_floor(p) for p in pdfs]
    return BuildingSpec(storeys=len(floors), floors=floors)
