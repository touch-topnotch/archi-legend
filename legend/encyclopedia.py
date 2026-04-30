"""Stage 8: render the encyclopedia (compact JSON + Markdown)."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Iterable

from .schema import BuildingSpec, FloorSpec


def to_json(spec: BuildingSpec) -> str:
    return spec.model_dump_json(indent=2)


def to_markdown(spec: BuildingSpec) -> str:
    lines: list[str] = []
    lines.append(f"# Building encyclopedia — {spec.project}")
    lines.append(f"Storeys: **{spec.storeys}**\n")
    for f in spec.floors:
        lines.append(f"## Floor {f.floor_id}  (elevation {f.elevation_m} m)")
        e = f.envelope
        lines.append(
            f"- envelope: **{e.width_m:.1f} m × {e.depth_m:.1f} m**, "
            f"axes X = {','.join(e.axes_x) or '?'}, "
            f"axes Y = {','.join(e.axes_y) or '?'}, "
            f"grid step = {e.grid_step_m or '?'} m"
        )
        c = f.counts
        lines.append(
            f"- counts: walls={c.walls}, columns={c.columns}, slabs={c.slabs}, grids={c.grids}"
        )
        if f.notes:
            for n in f.notes:
                lines.append(f"- note: {n}")
        lines.append("")
    return "\n".join(lines)


def write(spec: BuildingSpec, out_dir: str | Path) -> tuple[Path, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    j = out / "encyclopedia.json"
    m = out / "encyclopedia.md"
    j.write_text(to_json(spec))
    m.write_text(to_markdown(spec))
    return j, m
