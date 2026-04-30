"""Metrics that compare a predicted floor spec against ground truth."""
from __future__ import annotations
from typing import Any

import math


def _safe(x):
    try:
        return float(x)
    except Exception:
        return None


def envelope_l1(pred: dict, gt: dict) -> float | None:
    pe = (pred or {}).get("envelope", {}) or {}
    ge = (gt or {}).get("envelope", {}) or {}
    pw, pd = _safe(pe.get("width_m")), _safe(pe.get("depth_m"))
    gw, gd = _safe(ge.get("width_m")), _safe(ge.get("depth_m"))
    if None in (pw, pd, gw, gd):
        return None
    return abs(pw - gw) + abs(pd - gd)


def axes_jaccard(pred: dict, gt: dict, axis: str = "axes_x") -> float | None:
    pe = (pred or {}).get("envelope", {}) or {}
    pa = {str(x).strip() for x in (pe.get(axis, []) or [])}
    ga = {str(x).strip() for x in ((gt.get("envelope", {}) or {}).get(axis, []) or [])}
    if not (pa or ga):
        return None
    return len(pa & ga) / max(1, len(pa | ga))


def counts_mape(pred: dict, gt: dict) -> float | None:
    pc = (pred or {}).get("counts", {}) or {}
    gc = (gt or {}).get("counts", {}) or {}
    keys = set(pc) & set(gc)
    if not keys:
        return None
    errs = []
    for k in keys:
        gv = float(gc.get(k) or 0)
        pv = float(pc.get(k) or 0)
        if gv == 0:
            continue
        errs.append(abs(pv - gv) / gv)
    return (sum(errs) / len(errs)) if errs else None


def grid_step_err(pred: dict, gt: dict) -> float | None:
    pg = (pred or {}).get("envelope", {}).get("grid_step_m")
    gg = (gt or {}).get("envelope", {}).get("grid_step_m")
    if pg is None or gg is None:
        return None
    return abs(float(pg) - float(gg))


def all_metrics(pred: dict, gt: dict) -> dict:
    return {
        "envelope_l1_m": envelope_l1(pred, gt),
        "axes_x_jaccard": axes_jaccard(pred, gt, "axes_x"),
        "axes_y_jaccard": axes_jaccard(pred, gt, "axes_y"),
        "counts_mape": counts_mape(pred, gt),
        "grid_step_err_m": grid_step_err(pred, gt),
    }


def quality_score(m: dict) -> float:
    """Composite 0..1 quality on the envelope/grid axes that both LEGEND and the
    GT extractor target. Counts MAPE is reported separately because the
    encyclopedia's wall *proxy* (vector strokes) and the IFC's wall *element*
    count measure different physical things."""
    parts: list[float] = []
    if m["envelope_l1_m"] is not None:
        parts.append(max(0.0, 1.0 - m["envelope_l1_m"] / 50.0))
    for k in ("axes_x_jaccard", "axes_y_jaccard"):
        if m[k] is not None:
            parts.append(m[k])
    if m["grid_step_err_m"] is not None:
        parts.append(max(0.0, 1.0 - m["grid_step_err_m"] / 5.0))
    if not parts:
        return 0.0
    return sum(parts) / len(parts)
