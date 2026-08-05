# CryoSENSE-HK

**An explainable tree-ensemble framework for lead-time snow-state forecasting from ERA5-Land, bounded by station and physical references (Hakkari, Türkiye).**

This repository contains the full source code for the CryoSENSE-HK framework described in the accompanying manuscript. It reproduces every model, figure and table in the paper from a single processed daily ERA5-Land table. The framework is lightweight, runs on a laptop, and exposes its decision structure rather than acting as a black box.

> Scope: CryoSENSE-HK forecasts ERA5-Land snow cover, snow water equivalent and snowmelt at 1-, 7-, 15- and 30-day lead times using only issue-date and lagged information. It is a lead-time forecasting and sensitivity-assessment tool, **not** a glacier mass-balance or ice-melt model.

---

## 1. Framework components

CryoSENSE-HK is a staged pipeline. Each stage is a section of the pipeline notebook, and `docs/REPRODUCIBILITY.md` maps every article figure and table to the section that writes it.

```
ERA5-Land daily data
   -> climate diagnostics
   -> leakage-safe lead-time targets (predictors at t, target at t+h)
   -> physically grouped feature engineering + snow memory (Sets A / B / C)
   -> training-only mutual-information feature selection (top-k on validation)
   -> tree decision layer (XGBoost / Random Forest / Extra Trees, chosen on validation)
   -> feature-group ablation
   -> event-classification layer (high-melt day, snow-covered day)
   -> rolling-origin temporal robustness
   -> TreeSHAP explanation
   -> glacier-area linkage + bias-corrected CMIP6 projection
```

---

## 2. Repository structure

```
cryosense-hk/
├── README.md
├── LICENSE                          # MIT
├── requirements.txt                 # pinned dependencies
├── CryoSENSE_HK_pipeline.ipynb      # reproduces the paper end to end
├── CryoSENSE_HK_glacier_gee.ipynb   # Earth Engine glacier-area export
├── tools/                           # data download helpers (CMIP6, Sentinel-2)
├── data/
│   └── README.md                    # how to obtain the public input data
├── docs/
│   └── REPRODUCIBILITY.md           # figure/table <-> notebook map, seeds, environment
├── outputs/tables/                  # every table the notebook writes
└── figures/
    ├── raw/                         # every panel, under its working name
    └── submission/                  # the eleven the article carries, as Figure_N
```

The analysis lives in the notebook rather than in an importable package, so
there is one place to read and one place to change. Figures and tables are
never edited by hand; both folders above are outputs.

---

## 3. Installation

The framework requires **Python 3.12**. Two equivalent options:

### Option A: uv (recommended)

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Option B: pip

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 4. Data

Per the journal's instruction, **no dataset is bundled** with the code. All inputs are public; `data/README.md` gives the exact source, access route and citation for each:

- ERA5-Land (Copernicus Climate Data Store)
- EC-Earth3-CC CMIP6 SSP2-4.5 / SSP5-8.5 (ESGF)
- Landsat glacier-area series (Google Earth Engine / USGS)
- GLIMS glacier polygons
- Natural Earth administrative boundaries

The single processed input the notebook consumes is `data/hakkari_gunluk_tum_degiskenler.csv` (daily ERA5-Land, 1950-2025). The script `data/README.md` documents its columns and how it is produced from the raw NetCDF inventory.

---

## 5. Reproducing the paper

1. Install the environment (Section 3).
2. Place the input data under `data/` as described in `data/README.md`.
3. Run the notebook top to bottom:

```bash
jupyter lab CryoSENSE_HK_pipeline.ipynb
# or headless:
jupyter nbconvert --to notebook --execute CryoSENSE_HK_pipeline.ipynb
```

Figures are written to `figures/raw/` and tables to `outputs/tables/`; the last section of the notebook copies the eleven article figures to `figures/submission/`. A global seed (`SEED = 42`) is applied to NumPy, mutual-information ranking, the tree models, bootstrap resampling and TreeSHAP sampling, so results are deterministic. `docs/REPRODUCIBILITY.md` maps each figure and table to the cell that writes it and records the environment the reported numbers came from.

Two analyses read beyond the study cell and need the country-wide daily ERA5-Land archive, which is too large to bundle: the leave-one-pixel-out spatial transfer and the elevation matching behind the station comparison. Point the notebook at a local copy with `CRYO_ERA5_ARCHIVE`; `data/README.md` documents the variables and the extraction. Without it the notebook stops at that cell rather than continuing with partial data.

---

## 6. Hyperparameters

Fixed regularizing defaults and the two quantities that are tuned, on the validation period only, are listed in `docs/REPRODUCIBILITY.md`.

---

## 7. How to cite

If you use this code, please cite the paper and the archived release:

```
Gül E. CryoSENSE-HK: An explainable tree-ensemble framework for lead-time
snow-state forecasting from ERA5-Land, bounded by station and physical
references (Hakkari, Türkiye). Manuscript under review.
Code: https://github.com/ertugrul-gul/cryosense-hk-framework ; archived at Zenodo, concept DOI: 10.5281/zenodo.20765680.
```

---

## 8. License and availability

Code is released under the **MIT License** (see `LICENSE`), with no restrictions on reuse, with no venue-specific restrictions. The repository is archived on Zenodo with a versioned DOI for citation.
