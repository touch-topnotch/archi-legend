"""Build ground truth JSON from the IFC model.

The shipped IFC has no IfcSpace / IfcRelSpaceBoundary — typical of an early-stage
structural BIM where space modelling is deferred. We therefore extract a
*structural* GT: storeys, elevations, counts of walls / columns / slabs / grids,
and a per-floor envelope. The envelope read from local IFC placements is
unreliable here (placements are scattered in a global frame), so for the
architectural-envelope fields we trust the architect's title-block values that
are stamped on every PDF sheet (82.5 m × 75 m, axes 1..12 + А..М, grid 7.5 m).
This duality is documented in the notebook.
"""
from __future__ import annotations
import json, math
from collections import Counter
from pathlib import Path
import argparse

import ifcopenshell


FLOOR_NAME_MAP = {
    "-2. Этаж": "B2",
    "-4,300 минус 1 этаж": "0",
    "+0,000 1 этаж": "1",
    "+4,200 2 этаж": "2",
    "+7,200 3 этаж": "3",
}


def storey_envelope(model, storey) -> dict:
    xs, ys = [], []
    for rel in model.by_type("IfcRelContainedInSpatialStructure"):
        if rel.RelatingStructure != storey:
            continue
        for el in rel.RelatedElements:
            try:
                pl = el.ObjectPlacement.RelativePlacement.Location.Coordinates
                xs.append(pl[0]); ys.append(pl[1])
            except Exception:
                pass
    if not xs:
        return {}
    return {
        "x_min": min(xs), "x_max": max(xs),
        "y_min": min(ys), "y_max": max(ys),
        "width_m": (max(xs) - min(xs)) / 1000.0,
        "depth_m": (max(ys) - min(ys)) / 1000.0,
    }


def build_gt(ifc_path: str | Path) -> dict:
    model = ifcopenshell.open(str(ifc_path))
    storeys = sorted(
        model.by_type("IfcBuildingStorey"),
        key=lambda s: (s.Elevation if s.Elevation is not None else 0.0),
    )
    floors = []
    for s in storeys:
        contents = Counter()
        for rel in model.by_type("IfcRelContainedInSpatialStructure"):
            if rel.RelatingStructure == s:
                for el in rel.RelatedElements:
                    contents[el.is_a()] += 1
        # Envelope from architect's title block (anonymised, deterministic).
        env = {
            "width_m": 82.5,
            "depth_m": 75.0,
            "axes_x": ["1","2","3","4","5","6","7","8","9","10","11","12"],
            "axes_y": ["А","Б","В","Г","Д","Е","Ж","И","К","Л","М"],
            "grid_step_m": 7.5,
        }
        floors.append({
            "ifc_name": s.Name,
            "floor_id": FLOOR_NAME_MAP.get(s.Name, s.Name),
            "elevation_m": (s.Elevation or 0.0) / 1000.0,
            "counts": {
                "walls": contents.get("IfcWallStandardCase", 0),
                "columns": contents.get("IfcColumn", 0),
                "slabs": contents.get("IfcSlab", 0),
                "grids": contents.get("IfcGrid", 0),
                "roofs": contents.get("IfcRoof", 0),
                "proxies": contents.get("IfcBuildingElementProxy", 0),
            },
            "envelope": env,
        })

    return {
        "schema": model.schema,
        "project": "industrial MFC, anonymised",
        "n_storeys": len(storeys),
        "totals": {
            "walls": len(model.by_type("IfcWallStandardCase")),
            "columns": len(model.by_type("IfcColumn")),
            "slabs": len(model.by_type("IfcSlab")),
            "grids": len(model.by_type("IfcGrid")),
        },
        "floors": floors,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ifc", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    gt = build_gt(a.ifc)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(gt, indent=2, ensure_ascii=False))
    print(f"wrote {a.out}: {len(gt['floors'])} floors")


if __name__ == "__main__":
    main()
