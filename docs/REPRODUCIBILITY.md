# Reproducibility record

## Determinism
A single global seed `SEED = 42` is applied to NumPy, the mutual-information ranking, the tree models, the bootstrap resampling and the TreeSHAP sampling (set in the configuration cell of the notebook). Running the notebook top to bottom reproduces every reported number.

## Chronological protocol
| Split | Target-date window | Role |
|---|---|---|
| Training | 1950-01-01 ... 2002-12-31 | MI ranking + model fitting |
| Validation | 2003-01-01 ... 2014-12-31 | choose top-k and algorithm |
| Test | 2015-01-01 ... 2025-12-31 | held-out, used once |

Predictors are observed at issue date `t` or earlier; targets are at `t + h`, `h in {1, 7, 15, 30}`.

## Hyperparameters (fixed) and what is tuned
**Tuned on the validation period only:** the feature count `k in {4, 6, 8, 10, 12}` and the decision algorithm (XGBoost / Random Forest / Extra Trees). Nothing is tuned on the test period.

**Fixed regularizing defaults (`decision_model` in the notebook):**

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

## Where the figures and tables are written
Every panel is drawn under `figures/raw/` with a working name, and the eleven
that the article carries are copied to `figures/submission/` as `Figure_N` by
the copy step in section 14.1 of the notebook. Tables are written to
`outputs/tables/`. Nothing in either folder is edited by hand: a redrawn panel
reaches the submission set only by re-running the notebook.

## Article figure -> notebook cell map
Cells are identified by the section tag in their first comment line, which is
stable across edits, and by the cell index stored in the `.ipynb`.

| Article item | Notebook section | Index | File written under `figures/raw/` |
|---|---|---|---|
| Figure 1 (study area, CC BY basemaps) | 2.1b | 7 | `fig1_manuscript/figure_01_study_area_map_ccby.png` |
| Figure 2 (workflow) | 5.1 | 14 | `figure_05_cryosense_hk_workflow.png` |
| Figure 3 (annual climate diagnostics) | 3.1 | 9 | `figure_02_historical_climate_diagnostics.png` |
| Figure 4 (feature-group ablation) | 8.1 | 21 | `figure_07_feature_group_ablation.png` |
| Figure 5 (held-out skill and references) | 9.1 | 24 | `figure_08_final_model_baselines.png` |
| Figure 6 (leave-one-pixel-out transfer) | 9e.2 | 33 | `figure_08d_spatial_generalisation.png` |
| Figure 7 (event classification) | 9b.1 | 26 | `figure_08b_event_classification.png` |
| Figure 8 (TreeSHAP by horizon) | 11.1 | 43 | `figure_10_treeshap_feature_importance.png` |
| Figure 9 (station comparison) | 9g.1 | 37 | `figure_08f_station_validation.png` |
| Figure 10 (three-way sensitivity) | 13e.1 | 59 | `figure_12b_sensitivity_three_ways.png` |
| Figure S1 (projection series) | 13d.2 | 57 | `figure_12_projected_snow_scenarios.png` |

## Article table -> notebook cell map
| Article item | Notebook section | Index | Source under `outputs/tables/` |
|---|---|---|---|
| Table 1 (source manifest) | 1.1 | 3 | `table_01_source_manifest.csv` |
| Table 2 (descriptive statistics) | 1.2 | 4 | `table_02_descriptive_statistics.csv` |
| Table 3 (feature-group definitions) | - | - | stated in the text |
| Table 4 (chronological split) | 7.1 | 18 | `table_10_temporal_split_protocol.csv` |
| Table 5 (decision-layer settings) | - | - | stated in the text |
| Table 6 (climate trends) | 3.1 | 9 | `table_04_climate_trends.csv` |
| Table 7 (feature-group ablation) | 8.1 | 21 | `table_11_feature_group_ablation.csv` |
| Table 8 (held-out skill and references) | 9.1 | 24 | `table_16_heldout_model_and_baselines.csv` |
| Table 9 (spatial transfer summary) | 9e.2 | 33 | `table_16o_leave_one_pixel_out.csv` |
| Table 10 (station agreement) | 9g.1 | 37 | `table_16v_station_reanalysis_agreement.csv` |
| Table 11 (reduced emulator skill) | 13.1 | 50 | `table_24_projection_model_skill.csv` |
| Table 12 (three-way sensitivity) | 13e.1 | 59 | `table_26b_sensitivity_three_ways.csv` |

## Analyses that support the article without carrying a numbered item
| Analysis | Notebook section | Index |
|---|---|---|
| Drought-stress context (SPEI) | 3.2 | 10 |
| Glacier-area context from Earth Engine | 4.1 | 12 |
| Precipitation-phase threshold | 6.1 | 16 |
| Classical and temperature-index baselines | 9c.1 | 28 |
| Moving-block bootstrap intervals and paired tests | 9d.1 | 30 |
| Domain mask and multi-cell extraction | 9e.1 | 32 |
| Design-choice and hyperparameter sensitivity | 9f.1 | 35 |
| Conformal intervals and event detection | 9h.1 | 39 |
| Rolling-origin validation | 10.1 | 41 |
| Attribution stability across folds | 11b.1 | 45 |
| Glacier linkage (supplementary) | 12.1-12.2 | 47, 48 |
| Synthetic warming response of the emulator | 13b.1 | 52 |
| CMIP6 ensemble load and bias correction | 13c.1 | 54 |
| Ensemble projection | 13d.1 | 56 |
| Submission figure set and output register | 14.1-14.2 | 61, 62 |

## Environment (reported results)
Python 3.12.10; numpy 2.4.6; pandas 2.3.3; scikit-learn 1.8.0; xgboost 3.1.2; shap 0.51.0; scipy 1.16.3; matplotlib 3.10.8; seaborn 0.13.2; geopandas 1.1.3; rasterio 1.5.0; xarray 2025.12.0. Platform: macOS arm64.
