"""Stage 1: vector text extraction from PDFs."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List
import fitz  # pymupdf


@dataclass
class TextSpan:
    text: str
    bbox: tuple  # (x0,y0,x1,y1) in PDF points
    page: int


def extract_text_spans(pdf_path: str | Path) -> List[TextSpan]:
    out: List[TextSpan] = []
    doc = fitz.open(str(pdf_path))
    for pi, page in enumerate(doc):
        for w in page.get_text("words"):
            x0, y0, x1, y1, txt, *_ = w
            t = txt.strip()
            if t:
                out.append(TextSpan(t, (x0, y0, x1, y1), pi))
    return out


def extract_drawings(pdf_path: str | Path):
    """Return list of vector drawings (used as a proxy for wall/door geometry)."""
    doc = fitz.open(str(pdf_path))
    return doc[0].get_drawings()
