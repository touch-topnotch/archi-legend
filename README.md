# LEGEND — Lightweight Encyclopedia-Guided ENcoding for Drawings

A deterministic symbolic preprocessor that converts vector PDFs of architectural floor plans
into a compact textual *encyclopedia*. A cheap text-only LLM consuming this encyclopedia
matches frontier multimodal VLMs on parametric floorplan extraction at a fraction of the cost.

- Notebook: `notebooks/legend.ipynb`
- Poster: `poster/poster.pdf`
- Paper: `paper/paper.pdf`
- Pipeline: `legend/`
- Evaluation: `eval/`
- LLM clients: `llm/` (kie.ai aggregator)

## Quick start
```bash
uv sync
cp .env.example .env  # add KIE_API_KEY
jupyter lab notebooks/legend.ipynb
```

Real PDFs (`GardaSources/`) are not committed; `data/gt/gt.json` and pre-computed
encyclopedias under `results/` allow reviewers to reproduce numbers without raw data.
