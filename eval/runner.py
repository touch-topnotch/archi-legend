"""Drive approaches × floors and write results.csv. Caches LLM responses on disk."""
from __future__ import annotations
import argparse, hashlib, json, os, sys
from pathlib import Path
from typing import Iterable

import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from legend.build import build_floor  # noqa: E402
from legend.encyclopedia import to_markdown  # noqa: E402
from legend.schema import BuildingSpec  # noqa: E402
from llm import approaches  # noqa: E402
from eval.metrics import all_metrics, quality_score  # noqa: E402


CACHE = ROOT / "results" / "cache"
CACHE.mkdir(parents=True, exist_ok=True)


def render_floor_md(floor_spec) -> str:
    bs = BuildingSpec(storeys=1, floors=[floor_spec])
    return to_markdown(bs)


def png_for(pdf_path: Path, dpi: int = 150) -> Path:
    out = CACHE / f"{pdf_path.stem}.{dpi}.png"
    if out.exists():
        return out
    import fitz
    page = fitz.open(str(pdf_path))[0]
    pix = page.get_pixmap(dpi=dpi)
    pix.save(str(out))
    return out


def cache_key(approach: str, model: str, payload: str) -> Path:
    h = hashlib.sha256(f"{approach}|{model}|{payload}".encode()).hexdigest()[:24]
    return CACHE / f"{approach}_{model}_{h}.json"


def cached_call(approach: str, model: str, payload: str, fn):
    p = cache_key(approach, model, payload)
    if p.exists():
        return json.loads(p.read_text())
    r = fn()
    p.write_text(json.dumps(r, default=str))
    return r


def floor_id_for_pdf(stem: str) -> str:
    s = stem.lower()
    if "цокольный" in s: return "0"
    if "1 этаж" in s: return "1"
    if "2 этаж" in s: return "2"
    if "3 этаж" in s: return "3"
    return stem


def gt_for_floor(gt: dict, floor_id: str) -> dict | None:
    for f in gt.get("floors", []):
        if str(f.get("floor_id")) == str(floor_id):
            return f
    return None


def run(pdf_dir: Path, gt_path: Path, models_vlm: list[str], models_text: list[str],
        approaches_to_run: list[str]) -> pd.DataFrame:
    load_dotenv(ROOT / ".env")
    gt = json.loads(gt_path.read_text())
    pdfs = sorted([p for p in pdf_dir.glob("*.pdf") if "разрез" not in p.stem.lower()
                   and "наложением" not in p.stem.lower()
                   and "все_планы" not in p.stem.lower()])

    rows: list[dict] = []
    for pdf in pdfs:
        floor_id = floor_id_for_pdf(pdf.stem)
        gt_floor = gt_for_floor(gt, floor_id) or {}
        floor_spec = build_floor(pdf)
        enc_md = render_floor_md(floor_spec)
        png = png_for(pdf)

        # Always log the deterministic LEGEND prediction (zero LLM cost) as a baseline row.
        det_pred = json.loads(floor_spec.model_dump_json())
        m = all_metrics(det_pred, gt_floor)
        rows.append({"approach": "L0_legend_only", "model": "deterministic",
                     "floor": floor_id, "cost_usd": 0.0,
                     "input_tokens": 0, "output_tokens": 0, "latency_s": 0.0,
                     **m, "quality": quality_score(m)})

        if "A" in approaches_to_run:
            for model in models_vlm:
                r = cached_call("A", model, str(png),
                                lambda: approaches.approach_A(model, str(png)))
                m = all_metrics(r.get("pred") or {}, gt_floor)
                rows.append({"approach": "A_vlm_zeroshot", "model": model,
                             "floor": floor_id, **{k: r[k] for k in
                             ("cost_usd","input_tokens","output_tokens","latency_s")},
                             **m, "quality": quality_score(m), "error": r.get("error")})
        if "B" in approaches_to_run:
            for model in models_vlm:
                r = cached_call("B", model, str(png),
                                lambda: approaches.approach_B(model, str(png)))
                m = all_metrics(r.get("pred") or {}, gt_floor)
                rows.append({"approach": "B_vlm_fewshot", "model": model,
                             "floor": floor_id, **{k: r[k] for k in
                             ("cost_usd","input_tokens","output_tokens","latency_s")},
                             **m, "quality": quality_score(m), "error": r.get("error")})
        if "C" in approaches_to_run:
            for model in models_text:
                r = cached_call("C", model, str(png),
                                lambda: approaches.approach_C(model, str(png)))
                m = all_metrics(r.get("pred") or {}, gt_floor)
                rows.append({"approach": "C_cheap_vlm", "model": model,
                             "floor": floor_id, **{k: r[k] for k in
                             ("cost_usd","input_tokens","output_tokens","latency_s")},
                             **m, "quality": quality_score(m), "error": r.get("error")})
        if "D" in approaches_to_run:
            for model in models_text:
                r = cached_call("D", model, enc_md,
                                lambda: approaches.approach_D(model, enc_md))
                m = all_metrics(r.get("pred") or {}, gt_floor)
                rows.append({"approach": "D_legend_text", "model": model,
                             "floor": floor_id, **{k: r[k] for k in
                             ("cost_usd","input_tokens","output_tokens","latency_s")},
                             **m, "quality": quality_score(m), "error": r.get("error")})
        if "E" in approaches_to_run:
            for model in models_vlm:
                r = cached_call("E", model, enc_md,
                                lambda: approaches.approach_E(model, enc_md))
                m = all_metrics(r.get("pred") or {}, gt_floor)
                rows.append({"approach": "E_legend_frontier", "model": model,
                             "floor": floor_id, **{k: r[k] for k in
                             ("cost_usd","input_tokens","output_tokens","latency_s")},
                             **m, "quality": quality_score(m), "error": r.get("error")})

    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf-dir", default="data/raw")
    ap.add_argument("--gt", default="data/gt/gt.json")
    ap.add_argument("--out", default="results/results.csv")
    ap.add_argument("--vlm-models", nargs="*",
                    default=["claude-sonnet-4-5", "gemini-2.5-flash"])
    ap.add_argument("--text-models", nargs="*",
                    default=["gemini-2.5-flash", "claude-sonnet-4-5"])
    ap.add_argument("--approaches", nargs="*", default=["A", "D"])
    a = ap.parse_args()
    df = run(Path(a.pdf_dir), Path(a.gt), a.vlm_models, a.text_models, a.approaches)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(a.out, index=False)
    print(df)


if __name__ == "__main__":
    main()
