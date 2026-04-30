"""One callable per approach (A..E).

Each callable returns a dict with: ``pred`` (parsed JSON), ``input_tokens``,
``output_tokens``, ``cost_usd``, ``latency_s``, ``model``, ``approach``.

The functions never raise on a bad LLM output; instead they return ``pred=None``
plus an ``error`` string. Useful for batch evaluation.
"""
from __future__ import annotations
import json, re
from pathlib import Path
from typing import Any

from . import kie_client


PROMPT_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPT_DIR / name).read_text()


def _parse_json(text: str) -> Any:
    # Strip markdown fences if present.
    m = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.S)
    if m:
        text = m.group(1)
    # Try direct.
    try:
        return json.loads(text)
    except Exception:
        pass
    # Take the first {...} balanced span.
    s = text.find("{")
    e = text.rfind("}")
    if s != -1 and e != -1:
        try:
            return json.loads(text[s:e+1])
        except Exception:
            return None
    return None


def _run(prompt: str, model: str, image_path: str | None, approach: str) -> dict:
    out: dict = {"approach": approach, "model": model,
                 "pred": None, "error": None,
                 "input_tokens": 0, "output_tokens": 0,
                 "cost_usd": 0.0, "latency_s": 0.0}
    try:
        r = kie_client.chat(model=model, prompt=prompt, image_path=image_path)
        out["input_tokens"] = r.input_tokens
        out["output_tokens"] = r.output_tokens
        out["latency_s"] = r.latency_s
        out["cost_usd"] = kie_client.estimate_cost(model, r.input_tokens, r.output_tokens)
        out["pred"] = _parse_json(r.text)
        if out["pred"] is None:
            out["error"] = "could not parse JSON"
            out["raw_text"] = r.text[:500]
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"
    return out


# --- Approaches ---------------------------------------------------------------

def approach_A(model: str, image_path: str) -> dict:
    return _run(_load_prompt("A_vlm_zeroshot.md"), model, image_path, "A")


def approach_B(model: str, image_path: str) -> dict:
    return _run(_load_prompt("B_vlm_fewshot.md"), model, image_path, "B")


def approach_C(model: str, image_path: str) -> dict:
    return _run(_load_prompt("C_cheap_vlm.md"), model, image_path, "C")


def approach_D(model: str, encyclopedia_md: str) -> dict:
    p = _load_prompt("D_encyclopedia.md").replace("{{ENCYCLOPEDIA}}", encyclopedia_md)
    return _run(p, model, None, "D")


def approach_E(model: str, encyclopedia_md: str) -> dict:
    p = _load_prompt("E_encyclopedia_frontier.md").replace("{{ENCYCLOPEDIA}}", encyclopedia_md)
    return _run(p, model, None, "E")
