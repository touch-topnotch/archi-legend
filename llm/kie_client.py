"""Minimal kie.ai HTTP wrapper.

kie.ai exposes vendor-native endpoints under one API key. The Anthropic-shape
endpoint at ``/claude/v1/messages`` is used for Claude models; OpenAI-shape
chat completions are used for GPT/Gemini families. We keep one ``chat()``
function that auto-routes by model id prefix.
"""
from __future__ import annotations
import base64, os, time, json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx


BASE = os.environ.get("KIE_BASE_URL", "https://api.kie.ai")
KEY = os.environ.get("KIE_API_KEY", "")


@dataclass
class LLMResponse:
    text: str
    input_tokens: int
    output_tokens: int
    latency_s: float
    raw: dict
    model: str


def _b64_image(path: str | Path) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode()


def _claude_payload(model: str, prompt: str, image_b64: str | None) -> dict:
    if image_b64 is None:
        content: Any = prompt
    else:
        content = [
            {"type": "image", "source": {"type": "base64",
                                          "media_type": "image/png",
                                          "data": image_b64}},
            {"type": "text", "text": prompt},
        ]
    return {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": 4096,
        "stream": False,
    }


def _openai_payload(model: str, prompt: str, image_b64: str | None) -> dict:
    if image_b64 is None:
        msg = {"role": "user", "content": prompt}
    else:
        msg = {"role": "user", "content": [
            {"type": "image_url",
             "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
            {"type": "text", "text": prompt},
        ]}
    return {"model": model, "messages": [msg], "max_tokens": 4096, "stream": False}


def chat(model: str, prompt: str, image_path: str | Path | None = None,
         timeout: float = 120.0) -> LLMResponse:
    if not KEY:
        raise RuntimeError("KIE_API_KEY not set; cannot call live API.")
    img = _b64_image(image_path) if image_path else None
    is_claude = model.lower().startswith("claude")
    if is_claude:
        url = f"{BASE}/claude/v1/messages"
        payload = _claude_payload(model, prompt, img)
    else:
        # kie.ai exposes per-model OpenAI-shape endpoints under
        # /<model-id-with-dashes>/v1/chat/completions
        slug = model.replace(".", "-")
        url = f"{BASE}/{slug}/v1/chat/completions"
        payload = _openai_payload(model, prompt, img)
    headers = {"Authorization": f"Bearer {KEY}",
               "Content-Type": "application/json"}
    t0 = time.time()
    with httpx.Client(timeout=timeout) as c:
        r = c.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
    dt = time.time() - t0
    if data.get("code") and data.get("code") != 200:
        raise RuntimeError(f"kie.ai upstream error: {data.get('msg', data)}")
    if is_claude:
        text = "".join(b.get("text", "") for b in data.get("content", []))
        u = data.get("usage", {})
        in_tok, out_tok = u.get("input_tokens", 0), u.get("output_tokens", 0)
    else:
        text = data["choices"][0]["message"]["content"]
        u = data.get("usage", {})
        in_tok, out_tok = u.get("prompt_tokens", 0), u.get("completion_tokens", 0)
    return LLMResponse(text, in_tok, out_tok, dt, data, model)


# Approx pricing in USD per 1M tokens (input/output) — for cost estimation only.
PRICING = {
    "claude-sonnet-4-5":   (3.0, 15.0),
    "claude-sonnet-4-6":   (3.0, 15.0),
    "claude-opus-4-5":     (15.0, 75.0),
    "gpt-5.2":             (1.0, 5.0),
    "gemini-2.5-flash":    (0.10, 0.40),
    "gemini-3-flash":      (0.10, 0.40),
    "gemini-3-pro":        (1.25, 10.0),
}


def estimate_cost(model: str, in_tok: int, out_tok: int) -> float:
    pi, po = PRICING.get(model, (1.0, 3.0))
    return (in_tok * pi + out_tok * po) / 1_000_000
