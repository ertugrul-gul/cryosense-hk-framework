"""Training-only mutual-information feature selection.

Feature ranking is fitted on the training period only and the compact top-k
subset size is chosen on the validation period, never on the held-out test
period, to avoid selection leakage.
"""

from __future__ import annotations

from typing import List, Tuple

import pandas as pd
from sklearn.feature_selection import mutual_info_regression

from .config import SEED, TOPK_GRID
from .metrics import regression_metrics
from .models import decision_model


def rank_features(frame: pd.DataFrame, features: List[str], target: str) -> pd.Series:
    """Rank features by mutual information with the target (descending).

    The mutual information is estimated on the supplied (training) frame only.
    """
    mi = mutual_info_regression(frame[features], frame[target], random_state=SEED)
    return pd.Series(mi, index=features).sort_values(ascending=False)


def tune_top_k(
    train_df: pd.DataFrame,
    valid_df: pd.DataFrame,
    features: List[str],
    target: str,
    algorithm: str = "XGBoost",
) -> Tuple[pd.Series, int, pd.DataFrame]:
    """Choose the top-k subset size on the validation period.

    Returns the training-period MI ranking, the validation-optimal k, and the
    per-k validation RMSE table.
    """
    ranking = rank_features(train_df, features, target)
    candidates = [k for k in sorted(set(TOPK_GRID)) if k <= len(features)]
    scores = []
    for k in candidates:
        selected = ranking.index[:k].tolist()
        model = decision_model(algorithm)
        model.fit(train_df[selected], train_df[target])
        pred = model.predict(valid_df[selected])
        scores.append({"k": k, "RMSE": regression_metrics(valid_df[target], pred)["RMSE"]})
    scores_df = pd.DataFrame(scores)
    best_k = int(scores_df.loc[scores_df["RMSE"].idxmin(), "k"])
    return ranking, best_k, scores_df
