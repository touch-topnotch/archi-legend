# Nano-Banana-Pro prompts for LEGEND diagrams

Paste each prompt as-is. Output target: 16:9 PNG, ~1600×900 px, vector-clean
flat illustration, palette `#11365b` (deep blue), `#3aa17a` (green accent),
`#cc6600` (orange accent), white background, no photorealistic textures, no
shadows, thin black outlines.

---

## 1. `encyclopedia_diagram.png` — main pipeline

> A horizontal four-stage pipeline diagram on a clean white background, flat
> infographic style, palette deep navy `#11365b` + green accent `#3aa17a` +
> orange accent `#cc6600`. Stage 1: a stack-of-paper icon labelled "Vector PDF
> (1 этаж.pdf, 9964 drawings, 91 text spans)". Arrow → Stage 2: a small
> magnifying glass over a dotted grid icon labelled "LEGEND preprocessor —
> pymupdf → axes A..M, 1..12 → grid step 7.5 m → envelope 82.5 × 75 m".
> Arrow → Stage 3: a small markdown-document icon labelled "Encyclopedia (~290
> chars / 75 tokens)" in green. Arrow → Stage 4: a tiny robot head icon
> labelled "Cheap text LLM (Gemini 2.5 Flash, \$0.0001/floor)". Below the
> chain a thin label "deterministic | LLM-free | one API key". Crisp 1600×900
> px, no shadows, thin black outlines, sans-serif typography.

## 2. `cost_curve.png` — motivation curve

> A 16:9 line+bar chart on white. X axis: number of pages (1, 100, 1k, 10k,
> 100k) log scale. Y axis: project cost USD log scale. Three lines: red
> "Frontier VLM zero-shot (\$0.04/page)", orange "Cheap VLM (\$0.003/page)",
> green and bold "LEGEND + cheap text LLM (\$0.0001/page)". Axis labels in
> dark navy. Subtitle: "1500 sheets/site is industrial baseline". Big dot at
> the LEGEND/1500 intersection annotated "≈\$0.15". Big dot at frontier-VLM/1500
> annotated "≈\$60". Flat infographic style, no gridlines, clean.

## 3. `failure_mode.png` — omission vs hallucination

> A two-column comparison illustration. Left column titled "Cheap VLM"
> with a thinking robot emitting a wrong but confident JSON `{ "grid_step_m": 6.0 }`
> over a red ✗ icon, caption "hallucinates plausible-but-wrong value".
> Right column titled "LEGEND + cheap text LLM" with the same robot reading
> a markdown encyclopedia, emitting `{ "grid_step_m": null }` over a green
> ✓ icon, caption "returns null when encyclopedia lacks field".
> Below: "Omission > hallucination — practical reason BIM pipelines can use D".
> Flat infographic, navy + green + red accents, white background.

## 4. `legend_anatomy.png` — what's inside the encyclopedia

> A single-page mockup of a Markdown document on the left and an annotated
> floor plan on the right, joined by labelled coloured arrows showing
> correspondences: axes (А–М, 1–12) ↔ grid lines on the plan; "82.5 m × 75 m"
> ↔ outer rectangle dimensions; "grid step 7.5 m" ↔ a single grid bay;
> "walls=1030" ↔ a wall stroke. Hand-drawn architectural plan style on the
> right (thin black lines), clean digital markdown rendering on the left,
> coloured connector arrows in #3aa17a and #cc6600.

---

When generated, save the PNGs into `results/` (the poster references them by
relative path).
