"""Feature engineering, leakage-safe target construction and chronological splits.

This module implements the CryoSENSE-HK predictor/target design: every
predictor is observed at the issue date t or earlier, and every target is the
snow-state value at t + h. The three nested feature sets (A, B, C) control the
dependence of skill on snow memory.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from .config import LAGS

# Mapping of target column -> human-readable label.
TARGETS: Dict[str, str] = {
    "snowc": "Snow cover (%)",
    "sd": "Snow depth (m)",
    "smlt_mm": "Snowmelt (mm/day)",
}

# Nested feature sets (see manuscript Table 3).
FEATURE_SETS: Dict[str, List[str]] = {
    "A_atmosphere_energy": [
        "t2m_C", "d2m_C", "sp_hPa", "ws", "tp_mm", "e_mm",
        "ssrd_W", "strd_W", "slhf_W", "sshf_W", "net_radiation_W",
        "doy_sin", "doy_cos",
    ],
    "B_atmosphere_snowfall_memory": [
        "t2m_C", "d2m_C", "sp_hPa", "ws", "tp_mm", "sf_mm", "e_mm",
        "ssrd_W", "strd_W", "slhf_W", "sshf_W", "net_radiation_W",
        "doy_sin", "doy_cos",
        "t2m_C_lag1", "t2m_C_lag3", "t2m_C_lag7",
        "tp_mm_lag1", "tp_mm_lag3", "tp_mm_lag7",
        "sf_mm_lag1", "sf_mm_lag3", "sf_mm_lag7",
        "snowc_lag0", "snowc_lag1", "snowc_lag3", "snowc_lag7",
        "sd_lag0", "sd_lag1", "sd_lag3", "sd_lag7",
        "smlt_mm_lag1", "smlt_mm_lag3", "smlt_mm_lag7",
    ],
    "C_full_reanalysis_state": [
        "t2m_C", "d2m_C", "tsn_C", "sp_hPa", "ws", "tp_mm", "sf_mm", "e_mm",
        "ssrd_W", "strd_W", "slhf_W", "sshf_W", "net_radiation_W",
        "rsn", "sde_mm", "sro_mm", "ro_mm", "ssro_mm",
        "doy_sin", "doy_cos",
        "t2m_C_lag1", "t2m_C_lag3", "t2m_C_lag7",
        "tp_mm_lag1", "tp_mm_lag3", "tp_mm_lag7",
        "sf_mm_lag1", "sf_mm_lag3", "sf_mm_lag7",
        "snowc_lag0", "snowc_lag1", "snowc_lag3", "snowc_lag7",
        "sd_lag0", "sd_lag1", "sd_lag3", "sd_lag7",
        "smlt_mm_lag1", "smlt_mm_lag3", "smlt_mm_lag7",
    ],
}

# The proposed CryoSENSE-HK forecast input design.
PROPOSED_FEATURES: List[str] = FEATURE_SETS["B_atmosphere_snowfall_memory"]

_LAG_BASE: Tuple[str, ...] = ("t2m_C", "tp_mm", "sf_mm", "snowc", "sd", "smlt_mm")


def target_col(target: str, horizon: int) -> str:
    """Name of the horizon-shifted target column for a given lead time."""
    return f"{target}_h{horizon}"


def build_features(daily: pd.DataFrame) -> pd.DataFrame:
    """Add seasonality harmonics, net radiation and snow-memory lags.

    Args:
        daily: Daily ERA5-Land table indexed by a DatetimeIndex.

    Returns:
        A copy of the input with engineered predictor columns added.
    """
    df = daily.copy()
    day = df.index.dayofyear
    df["doy_sin"] = np.sin(2 * np.pi * day / 365.25)
    df["doy_cos"] = np.cos(2 * np.pi * day / 365.25)
    df["net_radiation_W"] = df["ssr_W"] + df["str_W"]
    for col in _LAG_BASE:
        for lag in LAGS:
            df[f"{col}_lag{lag}"] = df[col].shift(lag)
    for col in ("snowc", "sd"):
        df[f"{col}_lag0"] = df[col]
    return df


def make_forecast_frame(base: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Build the leakage-safe forecast frame for one horizon.

    Targets are shifted backward by ``horizon`` days so that row t carries the
    snow state observed at t + horizon, while all predictors stay at issue date.
    """
    df = base.copy()
    df["issue_date"] = df.index
    df["target_date"] = df.index + pd.to_timedelta(horizon, unit="D")
    df["target_doy"] = df["target_date"].dt.dayofyear
    for target in TARGETS:
        df[target_col(target, horizon)] = df[target].shift(-horizon)
    required = sorted(
        set(sum(FEATURE_SETS.values(), []) + [target_col(t, horizon) for t in TARGETS])
    )
    return df.dropna(subset=required + ["target_date", "target_doy"]).copy()


def split_forecast_frame(
    frame: pd.DataFrame,
    train_end: str = "2002-12-31",
    valid_start: str = "2003-01-01",
    valid_end: str = "2014-12-31",
    test_start: str = "2015-01-01",
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Chronological train/validation/test split keyed on the target date."""
    train = frame.loc[frame["target_date"] <= pd.Timestamp(train_end)].copy()
    valid = frame.loc[
        (frame["target_date"] >= pd.Timestamp(valid_start))
        & (frame["target_date"] <= pd.Timestamp(valid_end))
    ].copy()
    test = frame.loc[frame["target_date"] >= pd.Timestamp(test_start)].copy()
    return train, valid, test
