# AI usage

The course requires disclosing AI assistance. This project was built with Claude Code
(Anthropic, model Claude Fable 5.1) working from a written brief. What it did:

- **Dataset access.** Found that neither Hugging Face copy of BioMassters hosts loose
  TIFFs (both are multi-part zips, ~150 GB) and that the DrivenData S3 bucket is closed.
  Wrote `biomass/fetch.py`, which reads the zip central directories once and fetches
  single chips by HTTP range request, so the selective download in the brief still works.
- **Data pipeline.** `biomass/load.py`, `features.py`, `split.py`, `carbon.py`: chip
  selection from the tracker CSV, patch cache, tabular features, chip-level split, carbon
  conversion.
- **Models and evaluation.** `biomass/models.py` and `evaluate.py`: ridge, random forest,
  Keras CNN, metrics, residual-by-bin analysis, figures.
- **Export and UI.** `biomass/export.py` and the Vite/React app in `web/`.
- **Tests.** Everything under `tests/`.

Decisions taken by the author, not the assistant, are noted in the README. All numbers
in the report come from running the pipeline; none were typed by hand.
