"""Central, immutable configuration for the CryoSENSE-HK framework.

Every protocol constant and model hyperparameter lives here as a frozen
dataclass or module-level constant, so an experiment is fully reproducible
from a single auditable source. The values mirror those reported in the
manuscript reproducibility record (Table S1).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

# --- Global reproducibility -------------------------------------------------
SEED: int = 42

# --- Chronological split (boundaries refer to the TARGET date t + h) --------
TRAIN_END: str = "2002-12-31"
VALID_START: str = "2003-01-01"
VALID_END: str = "2014-12-31"
TEST_START: str = "2015-01-01"

# --- Lead-time forecasting protocol -----------------------------------------
FORECAST_HORIZONS: Tuple[int, ...] = (1, 7, 15, 30)
TOPK_GRID: Tuple[int, ...] = (4, 6, 8, 10, 12)
LAGS: Tuple[int, ...] = (1, 3, 7)

# --- Uncertainty estimation -------------------------------------------------
N_BOOT_METRIC: int = 500
N_BOOT_PAIRED: int = 1000
HIGH_MELT_PERCENTILE: float = 0.90
SNOW_COVERED_THRESHOLD: float = 50.0


@dataclass(frozen=True)
class XGBRegressorConfig:
    """Hyperparameters for the XGBoost regression decision layer (fixed)."""

    n_estimators: int = 180
    max_depth: int = 4
    learning_rate: float = 0.06
    subsample: float = 0.85
    colsample_bytree: float = 0.85
    objective: str = "reg:squarederror"
    tree_method: str = "hist"
    n_jobs: int = 4
    random_state: int = SEED


@dataclass(frozen=True)
class RandomForestConfig:
    """Hyperparameters for the Random Forest regression decision layer (fixed)."""

    n_estimators: int = 100
    max_depth: int = 12
    min_samples_leaf: int = 2
    max_features: float = 0.8
    n_jobs: int = 4
    random_state: int = SEED


@dataclass(frozen=True)
class ExtraTreesConfig:
    """Hyperparameters for the Extra Trees regression decision layer (fixed)."""

    n_estimators: int = 100
    max_depth: int = 12
    min_samples_leaf: int = 2
    max_features: float = 0.9
    n_jobs: int = 4
    random_state: int = SEED


@dataclass(frozen=True)
class XGBClassifierConfig:
    """Hyperparameters for the XGBoost event-classification layer (fixed)."""

    n_estimators: int = 180
    max_depth: int = 4
    learning_rate: float = 0.06
    subsample: float = 0.85
    colsample_bytree: float = 0.85
    tree_method: str = "hist"
    eval_metric: str = "logloss"
    n_jobs: int = 4
    random_state: int = SEED


@dataclass(frozen=True)
class ForestClassifierConfig:
    """Shared hyperparameters for the RF / ET event-classification layers (fixed)."""

    n_estimators: int = 200
    max_depth: int = 12
    min_samples_leaf: int = 2
    rf_max_features: float = 0.8
    et_max_features: float = 0.9
    class_weight: str = "balanced"
    n_jobs: int = 4
    random_state: int = SEED


@dataclass(frozen=True)
class ProjectionConfig:
    """Hyperparameters for the reduced monthly projection model (fixed)."""

    n_estimators: int = 300
    max_depth: int = 4
    learning_rate: float = 0.05
    subsample: float = 0.85
    colsample_bytree: float = 0.85
    objective: str = "reg:squarederror"
    tree_method: str = "hist"
    n_jobs: int = 4
    random_state: int = SEED


# Bias-correction guard rails for CMIP6 -> ERA5 multiplicative scaling.
BIAS_RATIO_CLIP: Tuple[float, float] = (0.2, 5.0)
