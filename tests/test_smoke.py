"""Fast synthetic end-to-end smoke test for the CryoSENSE-HK pipeline.

No real data is required. The test builds a synthetic daily table with the
expected ERA5-Land columns and checks that feature engineering, leakage-safe
target construction, the chronological split, training-only feature selection,
the decision layer, the metric suite and the bootstrap all wire together.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from cryosense_hk import (
    PROPOSED_FEATURES,
    bootstrap_regression_ci,
    build_features,
    classification_metrics,
    decision_model,
    event_classifier,
    make_forecast_frame,
    paired_rmse_bootstrap,
    regression_metrics,
    set_seed,
    split_forecast_frame,
    target_col,
    tune_top_k,
)

RAW_COLUMNS = [
    "t2m_C", "d2m_C", "tsn_C", "sp_hPa", "ws", "tp_mm", "sf_mm", "e_mm",
    "ssrd_W", "strd_W", "ssr_W", "str_W", "slhf_W", "sshf_W",
    "snowc", "sd", "sde_mm", "smlt_mm", "rsn", "sro_mm", "ro_mm", "ssro_mm",
]


def _synthetic_daily() -> pd.DataFrame:
    """Daily table spanning all three chronological splits."""
    set_seed(0)
    idx = pd.date_range("1995-01-01", "2020-12-31", freq="D")
    n = len(idx)
    doy = idx.dayofyear.to_numpy()
    season = np.cos(2 * np.pi * doy / 365.25)
    rng = np.random.RandomState(0)
    df = pd.DataFrame(index=idx)
    df.index.name = "time"
    for col in RAW_COLUMNS:
        df[col] = rng.normal(size=n) * 0.1
    # Give a few variables a seasonal, autocorrelated signal so MI is meaningful.
    df["t2m_C"] = 5 + 10 * -season + rng.normal(scale=1.0, size=n)
    df["snowc"] = np.clip(50 + 50 * season + rng.normal(scale=5, size=n), 0, 100)
    df["sd"] = np.clip(0.2 + 0.2 * season + rng.normal(scale=0.02, size=n), 0, None)
    df["smlt_mm"] = np.clip(2 - 2 * season + rng.normal(scale=0.5, size=n), 0, None)
    return df


def test_pipeline_end_to_end() -> None:
    daily = _synthetic_daily()
    feat = build_features(daily)
    frame = make_forecast_frame(feat, horizon=7)
    train, valid, test = split_forecast_frame(frame)
    assert len(train) > 0 and len(valid) > 0 and len(test) > 0

    ycol = target_col("smlt_mm", 7)
    ranking, best_k, scores = tune_top_k(train, valid, PROPOSED_FEATURES, ycol)
    assert best_k in (4, 6, 8, 10, 12)
    selected = ranking.index[:best_k].tolist()

    fit = pd.concat([train, valid])
    model = decision_model("XGBoost")
    model.fit(fit[selected], fit[ycol])
    pred = model.predict(test[selected])

    met = regression_metrics(test[ycol], pred)
    assert set(met) == {"RMSE", "MAE", "R2", "NSE", "KGE"}
    assert np.isfinite(met["RMSE"])

    ci = bootstrap_regression_ci(test[ycol], pred, n_boot=50)
    assert ci["RMSE_ci_low"] <= ci["RMSE_ci_high"]

    persistence = test["smlt_mm"].to_numpy()
    paired = paired_rmse_bootstrap(test[ycol], pred, persistence, n_boot=50)
    assert 0.0 <= paired["bootstrap_p_two_sided"] <= 1.0


def test_event_layer() -> None:
    daily = _synthetic_daily()
    frame = make_forecast_frame(build_features(daily), horizon=7)
    train, valid, test = split_forecast_frame(frame)
    ycol = target_col("snowc", 7)
    thr = 50.0
    y_train = (train[ycol] >= thr).astype(int)
    y_test = (test[ycol] >= thr).astype(int)
    clf = event_classifier("Random Forest")
    clf.fit(train[PROPOSED_FEATURES[:10]], y_train)
    pred = clf.predict(test[PROPOSED_FEATURES[:10]])
    prob = clf.predict_proba(test[PROPOSED_FEATURES[:10]])[:, 1]
    met = classification_metrics(y_test, pred, prob)
    assert 0.0 <= met["F1"] <= 1.0
    assert 0.0 <= met["AUC"] <= 1.0
