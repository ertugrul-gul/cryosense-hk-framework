"""Bootstrap uncertainty estimation for CryoSENSE-HK forecasts.

Provides metric confidence intervals and the paired bootstrap test of the
RMSE difference between the model and a baseline.
"""

from __future__ import annotations

from typing import Dict

import numpy as np
from numpy.typing import ArrayLike

from .config import N_BOOT_METRIC, N_BOOT_PAIRED, SEED
from .metrics import regression_metrics


def bootstrap_regression_ci(
    y_true: ArrayLike, y_pred: ArrayLike, n_boot: int = N_BOOT_METRIC, seed: int = SEED
) -> Dict[str, float]:
    """Percentile bootstrap 95% confidence intervals for RMSE and R2."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    rng = np.random.RandomState(seed)
    rmse, r2 = [], []
    for _ in range(n_boot):
        idx = rng.randint(0, len(y_true), len(y_true))
        met = regression_metrics(y_true[idx], y_pred[idx])
        rmse.append(met["RMSE"])
        r2.append(met["R2"])
    return {
        "RMSE_ci_low": float(np.quantile(rmse, 0.025)),
        "RMSE_ci_high": float(np.quantile(rmse, 0.975)),
        "R2_ci_low": float(np.quantile(r2, 0.025)),
        "R2_ci_high": float(np.quantile(r2, 0.975)),
    }


def paired_rmse_bootstrap(
    y_true: ArrayLike,
    model_pred: ArrayLike,
    baseline_pred: ArrayLike,
    n_boot: int = N_BOOT_PAIRED,
    seed: int = SEED,
) -> Dict[str, float]:
    """Paired bootstrap test of the RMSE difference (model minus baseline).

    A negative delta favours the model. The two-sided p value is the doubled
    smaller tail mass of the bootstrap distribution of the RMSE difference.
    """
    y_true = np.asarray(y_true, dtype=float)
    model_pred = np.asarray(model_pred, dtype=float)
    baseline_pred = np.asarray(baseline_pred, dtype=float)
    rng = np.random.RandomState(seed)

    def _rmse(a: np.ndarray, b: np.ndarray) -> float:
        return float(np.sqrt(np.mean((a - b) ** 2)))

    observed_delta = _rmse(y_true, model_pred) - _rmse(y_true, baseline_pred)
    boot_delta = np.empty(n_boot, dtype=float)
    for i in range(n_boot):
        idx = rng.randint(0, len(y_true), len(y_true))
        boot_delta[i] = _rmse(y_true[idx], model_pred[idx]) - _rmse(
            y_true[idx], baseline_pred[idx]
        )
    p_two_sided = min(1.0, 2 * min(np.mean(boot_delta <= 0), np.mean(boot_delta >= 0)))
    return {
        "delta_RMSE_model_minus_baseline": float(observed_delta),
        "delta_RMSE_ci_low": float(np.quantile(boot_delta, 0.025)),
        "delta_RMSE_ci_high": float(np.quantile(boot_delta, 0.975)),
        "bootstrap_p_two_sided": float(p_two_sided),
    }
