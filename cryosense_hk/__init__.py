"""CryoSENSE-HK: an explainable tree-ensemble framework for lead-time snow forecasting.

Public API for the reusable components of the framework. The end-to-end
analysis (figures, tables, projection) is driven by the accompanying notebook,
which imports these functions so that the logic is auditable and importable.
"""

from __future__ import annotations

import os
import random

import numpy as np

from .config import (
    FORECAST_HORIZONS,
    SEED,
    TOPK_GRID,
)
from .features import (
    FEATURE_SETS,
    PROPOSED_FEATURES,
    TARGETS,
    build_features,
    make_forecast_frame,
    split_forecast_frame,
    target_col,
)
from .metrics import classification_metrics, kge, regression_metrics
from .models import (
    CLASSIFIER_NAMES,
    REGRESSOR_NAMES,
    decision_model,
    event_classifier,
)
from .selection import rank_features, tune_top_k
from .uncertainty import bootstrap_regression_ci, paired_rmse_bootstrap

__version__ = "1.0.0"


def set_seed(seed: int = SEED) -> None:
    """Seed Python, NumPy and the hashing salt for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


__all__ = [
    "SEED",
    "FORECAST_HORIZONS",
    "TOPK_GRID",
    "TARGETS",
    "FEATURE_SETS",
    "PROPOSED_FEATURES",
    "build_features",
    "make_forecast_frame",
    "split_forecast_frame",
    "target_col",
    "kge",
    "regression_metrics",
    "classification_metrics",
    "decision_model",
    "event_classifier",
    "REGRESSOR_NAMES",
    "CLASSIFIER_NAMES",
    "rank_features",
    "tune_top_k",
    "bootstrap_regression_ci",
    "paired_rmse_bootstrap",
    "set_seed",
    "__version__",
]
