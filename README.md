# CryoSENSE-HK

**An explainable tree-ensemble framework for lead-time snow forecasting from ERA5-Land in the Cilo-Sat cryosphere, Hakkari (Türkiye).**

This repository contains the full source code for the CryoSENSE-HK framework described in the manuscript submitted to *PLOS ONE* (PONE-D-26-28266). It reproduces every model, figure and table in the paper from a single processed daily ERA5-Land table. The framework is lightweight, runs on a laptop, and exposes its decision structure rather than acting as a black box.

> Scope: CryoSENSE-HK forecasts ERA5-Land snow cover, snow depth and snowmelt at 1-, 7-, 15- and 30-day lead times using only issue-date and lagged information. It is a lead-time forecasting and sensitivity-assessment tool, **not** a glacier mass-balance or ice-melt model.

---

## 1. Framework components

CryoSENSE-HK is a staged pipeline. Each stage maps to a module function and to a notebook section.

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

| Component | Module | Key functions |
|---|---|---|
| Configuration & hyperparameters | `cryosense_hk/config.py` | frozen dataclasses, `SEED`, split dates |
| Feature engineering & targets | `cryosense_hk/features.py` | `build_features`, `make_forecast_frame`, `split_forecast_frame`, `FEATURE_SETS` |
| Feature selection | `cryosense_hk/selection.py` | `rank_features` (MI), `tune_top_k` |
| Decision layer | `cryosense_hk/models.py` | `decision_model`, `event_classifier` |
| Metrics | `cryosense_hk/metrics.py` | `regression_metrics`, `kge`, `classification_metrics` |
| Uncertainty | `cryosense_hk/uncertainty.py` | `bootstrap_regression_ci`, `paired_rmse_bootstrap` |
| End-to-end analysis | `notebooks/Hakkari_ERA5_Land.ipynb` | all figures and tables |

---

## 2. Repository structure

```
cryosense-hk/
├── README.md
├── LICENSE                       # MIT
├── requirements.txt              # pinned dependencies (Table S1)
├── pyproject.toml                # installable package metadata (uv / pip)
├── cryosense_hk/                 # importable framework module
│   ├── __init__.py
│   ├── config.py
│   ├── features.py
│   ├── selection.py
│   ├── models.py
│   ├── metrics.py
│   └── uncertainty.py
├── notebooks/
│   └── Hakkari_ERA5_Land.ipynb   # reproduces the paper
├── data/
│   └── README.md                 # how to obtain the public input data
├── docs/
│   └── REPRODUCIBILITY.md        # figure/table <-> notebook map, seeds, environment
└── tests/
    └── test_smoke.py             # fast synthetic end-to-end check
```

---

## 3. Installation

The framework requires **Python 3.12**. Two equivalent options:

### Option A: uv (recommended)

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt
uv pip install -e .          # makes `import cryosense_hk` available
```

### Option B: pip

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
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
2. Place the input data under `data/` and `nc_cilo_sat/` as described in `data/README.md`.
3. Run the notebook top to bottom:

```bash
jupyter lab notebooks/Hakkari_ERA5_Land.ipynb
# or headless:
jupyter nbconvert --to notebook --execute notebooks/Hakkari_ERA5_Land.ipynb
```

All figures are written to `outputs/figures/` and all tables to `outputs/tables/`. A global seed (`SEED = 42`) is applied to NumPy, mutual-information ranking, the tree models, bootstrap resampling and TreeSHAP sampling, so results are deterministic. See `docs/REPRODUCIBILITY.md` for the figure/table-to-cell map.

### Quick API example

```python
from cryosense_hk import (
    set_seed, build_features, make_forecast_frame, split_forecast_frame,
    tune_top_k, decision_model, regression_metrics, PROPOSED_FEATURES, target_col,
)
import pandas as pd

set_seed(42)
daily = pd.read_csv("data/hakkari_gunluk_tum_degiskenler.csv",
                    sep=";", parse_dates=["time"]).set_index("time")

feat = build_features(daily)
frame = make_forecast_frame(feat, horizon=7)
train, valid, test = split_forecast_frame(frame)

ycol = target_col("smlt_mm", 7)
ranking, best_k, _ = tune_top_k(train, valid, PROPOSED_FEATURES, ycol)
selected = ranking.index[:best_k].tolist()

model = decision_model("XGBoost")
model.fit(pd.concat([train, valid])[selected], pd.concat([train, valid])[ycol])
print(regression_metrics(test[ycol], model.predict(test[selected])))
```

---

## 6. Smoke test

A fast synthetic check that the pipeline wires together (no real data needed):

```bash
pip install pytest
pytest -q
```

---

## 7. Hyperparameters

All hyperparameters are fixed, conservative defaults stored in `cryosense_hk/config.py`; model capacity is controlled only by the validation-selected feature count *k* and the validation-selected algorithm, never on the test period. The full table and tuning protocol are in `docs/REPRODUCIBILITY.md` and in the manuscript Methods section.

---

## 8. How to cite

If you use this code, please cite the paper and the archived release:

```
Gül E. CryoSENSE-HK: An explainable tree-ensemble framework for lead-time snow
forecasting from ERA5-Land in the Cilo-Sat cryosphere, Hakkari (Türkiye). PLOS ONE (under review).
Code: https://github.com/ertugrul-gul/cryosense-hk-framework ; archived at Zenodo, concept DOI: 10.5281/zenodo.20765680.
```

---

## 9. License and availability

Code is released under the **MIT License** (see `LICENSE`), with no restrictions on reuse, in line with PLOS code-sharing policy. The repository is archived on Zenodo with a versioned DOI for citation.
