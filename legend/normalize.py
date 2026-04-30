"""Stage 3: label normalisation (RU → canonical type).

Used when room labels are present as text. The MFC dataset's PDFs do not include
room-label text (labels are graphics), so this module is exercised on a synthetic
label set in the notebook to demonstrate its behaviour.
"""
from __future__ import annotations
from typing import Dict

try:
    import pymorphy3
    _MORPH = pymorphy3.MorphAnalyzer()
except Exception:  # pragma: no cover
    _MORPH = None


CANONICAL: Dict[str, str] = {
    "ритейл": "retail",
    "магазин": "retail",
    "торговый": "retail",
    "тех": "tech",
    "технический": "tech",
    "санузел": "wc",
    "туалет": "wc",
    "уборная": "wc",
    "вход": "entrance",
    "тамбур": "vestibule",
    "коридор": "corridor",
    "лестница": "stair",
    "лифт": "elevator",
    "атриум": "atrium",
    "офис": "office",
    "склад": "storage",
    "загрузка": "loading",
    "служебный": "service",
    "кухня": "kitchen",
    "зал": "hall",
    "холл": "lobby",
}


def normalize(label: str) -> str:
    """Map a Russian room label to a canonical type, or `unknown`."""
    s = label.lower().strip()
    s = s.replace(".", " ").replace(",", " ").replace("/", " ")
    tokens = [t for t in s.split() if t]
    for t in tokens:
        lemma = t
        if _MORPH is not None:
            try:
                lemma = _MORPH.parse(t)[0].normal_form
            except Exception:
                pass
        for key, canon in CANONICAL.items():
            if lemma.startswith(key) or t.startswith(key):
                return canon
    return "unknown"
