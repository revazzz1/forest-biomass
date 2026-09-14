# Forest biomass from a single Sentinel-2 image

Course project, Aalto introductory machine learning, autumn 2026. Estimates mean
above-ground biomass (t/ha) of 2.56 × 2.56 km patches of Finnish forest from one summer
Sentinel-2 image, compares a small CNN against ridge regression and a random forest, and
states the error in tonnes of CO₂ per patch. A local web UI browses the patches.

Data: [BioMassters](https://huggingface.co/datasets/nascetti-a/BioMassters) (Nascetti et
al., NeurIPS 2023 Datasets & Benchmarks), CC-BY-4.0. Labels are airborne-LiDAR biomass
maps from the Finnish Forest Centre calibrated with field plots.

## Run

```bash
python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt
make data N=200        # smoke run; N=1500 for the real one (~2–3 GB into data/raw/)
make features          # tabular features + chip-level 70/15/15 split
make train             # ridge, random forest, CNN -> models/
make evaluate          # test-set metrics -> models/*_metrics.json, figures/
make export            # -> web/public/data/ for the UI
make test
cd web && npm install && npm run dev
```

`report.ipynb` imports from `biomass/` and produces every figure in the report; run it
top to bottom after `make evaluate`.

## How the download works

Neither Hugging Face copy of BioMassters hosts loose TIFFs: the training features are a
14-part split zip (~150 GB) and the labels a single zip. `biomass/fetch.py` reads the two
central directories once (33 MB, cached) and then fetches one chip at a time by HTTP range
request, inflating and CRC-checking each entry. Chips are chosen from the mirror's
`biomassters_chip_tracker.csv`: training split, a June–August image, no corrupt blocks,
at most 5 % cloudy pixels and a red-band mean in (0, 1000] (zero is an empty image, higher
is snow or a failed atmospheric correction). Per chip the least cloudy image wins, ties
broken by the lowest red mean.

Facts verified against the data rather than assumed: month index 00 is the previous
September and 11 is August; the label raster has no nodata value and zero is a real
value (water, rock, clearcut) that is kept; reflectance is uint16 scaled by 1/10000; the
eleventh band is cloud probability in percent and is dropped from the model input.

## Layout

```
biomass/   fetch.py load.py features.py split.py models.py evaluate.py carbon.py export.py
tests/     pytest; frontend tests live in web/
data/      raw/ and cache/ are gitignored
models/    gitignored
figures/   produced by report.ipynb and make evaluate
web/       Vite + React + TypeScript, static; reads web/public/data/
```

## Limits

One image, one summer, patch means only. Optical reflectance saturates at high biomass,
so all three models under-predict dense stands; the residual-by-bin chart shows this.
Chip coordinates are not public, so there is no map. Root biomass is excluded unless the
root-to-shoot parameter is set in the carbon panel.
