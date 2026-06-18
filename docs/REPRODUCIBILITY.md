# Reproducibility record

## Determinism
A single global seed `SEED = 42` is applied to NumPy, the mutual-information ranking, the tree models, the bootstrap resampling and the TreeSHAP sampling (`cryosense_hk.set_seed`). Running the notebook top to bottom reproduces every reported number.

## Chronological protocol
| Split | Target-date window | Role |
|---|---|---|
| Training | 1950-01-01 ... 2002-12-31 | MI ranking + model fitting |
| Validation | 2003-01-01 ... 2014-12-31 | choose top-k and algorithm |
| Test | 2015-01-01 ... 2025-12-31 | held-out, used once |

Predictors are observed at issue date `t` or earlier; targets are at `t + h`, `h in {1, 7, 15, 30}`.

## Hyperparameters (fixed) and what is tuned
**Tuned on the validation period only:** the feature count `k in {4, 6, 8, 10, 12}` and the decision algorithm (XGBoost / Random Forest / Extra Trees). Nothing is tuned on the test period.

**Fixed regularizing defaults (`cryosense_hk/config.py`):**

| Model | Settings |
|---|---|
| XGBoost regressor | n_estimators=180, max_depth=4, learning_rate=0.06, subsample=0.85, colsample_bytree=0.85, tree_method=hist |
| Random Forest regressor | n_estimators=100, max_depth=12, min_samples_leaf=2, max_features=0.8 |
| Extra Trees regressor | n_estimators=100, max_depth=12, min_samples_leaf=2, max_features=0.9 |
| Event classifiers | XGB: 180 trees, depth 4, lr 0.06; RF/ET: 200 trees, depth 12, class_weight=balanced |
| Projection XGBoost (monthly) | n_estimators=300, max_depth=4, learning_rate=0.05, subsample=0.85, colsample_bytree=0.85 |

**Uncertainty:** 500 bootstrap resamples for metric CIs; 1000 paired resamples for the RMSE-difference test (two-sided p).
**Event thresholds:** high-melt day = training 90th percentile of horizon-shifted snowmelt; snow-covered day = snow cover >= 50%.
**Bias correction (CMIP6 -> ERA5, per calendar month):** additive mean shift for temperature; multiplicative mean ratio (clipped to [0.2, 5.0]) for precipitation and snowfall.

## Figure / table -> notebook cell map
| Output | Notebook cell |
|---|---|
| Table 1-2 (manifest, descriptive) | cells 3-4 |
| Figure 1 (study-area map) | cell 6 |
| Table 3-4, Figure 2-3 (climate diagnostics, SPEI) | cells 8-9 |
| Figure 4 (glacier context) | cell 11 |
| Figure 5 (workflow) | cell 13 |
| Table 6, Figure 6 (phase threshold) | cell 15 |
| Split protocol + functions | cells 17-18 |
| Table 7-8, Figure 7 (ablation, selection effect) | cells 20-21 |
| Table 9-10, Figure 8 (held-out skill, skill tests) | cell 23 |
| Table 11, Figure 8b (event classification) | cell 25 |
| Table 12, Figure 9 (rolling-origin) | cell 27 |
| Table 13, Figure 10, S1 Fig (TreeSHAP) | cell 29 |
| Table 14, Figure 11 (glacier linkage) | cells 31-32 |
| Table 15-16, Figure 12 (projection) | cells 34-35 |
| Output register | cell 37 |

## Environment (reported results)
Python 3.12.10; numpy 2.4.6; pandas 2.3.3; scikit-learn 1.8.0; xgboost 3.1.2; shap 0.51.0; scipy 1.16.3; matplotlib 3.10.8; seaborn 0.13.2; geopandas 1.1.3; rasterio 1.5.0; xarray 2025.12.0. Platform: macOS arm64.
