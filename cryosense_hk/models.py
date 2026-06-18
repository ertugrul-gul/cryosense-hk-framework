"""Tree-ensemble decision-layer factories for CryoSENSE-HK.

The regression and event-classification layers are built through small
factory functions so the same three algorithms (XGBoost, Random Forest,
Extra Trees) can be selected on the validation period by name.
"""

from __future__ import annotations

from typing import Tuple

from sklearn.ensemble import (
    ExtraTreesClassifier,
    ExtraTreesRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from xgboost import XGBClassifier, XGBRegressor

from .config import (
    ExtraTreesConfig,
    ForestClassifierConfig,
    RandomForestConfig,
    XGBClassifierConfig,
    XGBRegressorConfig,
)

REGRESSOR_NAMES: Tuple[str, ...] = ("XGBoost", "Random Forest", "Extra Trees")
CLASSIFIER_NAMES: Tuple[str, ...] = ("XGBoost", "Random Forest", "Extra Trees")


def decision_model(name: str):
    """Build a regression decision-layer model by name.

    Args:
        name: One of ``REGRESSOR_NAMES``. Unknown names fall back to Extra Trees.
    """
    if name == "XGBoost":
        return XGBRegressor(**vars(XGBRegressorConfig()))
    if name == "Random Forest":
        return RandomForestRegressor(**vars(RandomForestConfig()))
    return ExtraTreesRegressor(**vars(ExtraTreesConfig()))


def event_classifier(name: str):
    """Build an event-classification decision-layer model by name.

    Args:
        name: One of ``CLASSIFIER_NAMES``. Unknown names fall back to Extra Trees.
    """
    if name == "XGBoost":
        return XGBClassifier(**vars(XGBClassifierConfig()))
    cfg = ForestClassifierConfig()
    if name == "Random Forest":
        return RandomForestClassifier(
            n_estimators=cfg.n_estimators,
            max_depth=cfg.max_depth,
            min_samples_leaf=cfg.min_samples_leaf,
            max_features=cfg.rf_max_features,
            class_weight=cfg.class_weight,
            n_jobs=cfg.n_jobs,
            random_state=cfg.random_state,
        )
    return ExtraTreesClassifier(
        n_estimators=cfg.n_estimators,
        max_depth=cfg.max_depth,
        min_samples_leaf=cfg.min_samples_leaf,
        max_features=cfg.et_max_features,
        class_weight=cfg.class_weight,
        n_jobs=cfg.n_jobs,
        random_state=cfg.random_state,
    )
