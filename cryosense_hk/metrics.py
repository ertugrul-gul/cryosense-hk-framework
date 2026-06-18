"""Regression and classification metrics used throughout CryoSENSE-HK.

The hydrological efficiency metrics (NSE, KGE) follow the standard
definitions used in the manuscript Methods section.
"""

from __future__ import annotations

from typing import Dict

import numpy as np
from numpy.typing import ArrayLike
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)


def kge(y_true: ArrayLike, y_pred: ArrayLike) -> float:
    """Kling-Gupta efficiency.

    KGE = 1 - sqrt((r - 1)^2 + (alpha - 1)^2 + (beta - 1)^2), where r is the
    Pearson correlation, alpha = std(pred) / std(true) is the variability ratio
    and beta = mean(pred) / mean(true) is the bias ratio.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    r = np.corrcoef(y_true, y_pred)[0, 1]
    alpha = np.std(y_pred) / max(np.std(y_true), 1e-12)
    beta = np.mean(y_pred) / max(np.mean(y_true), 1e-12)
    return float(1 - np.sqrt((r - 1) ** 2 + (alpha - 1) ** 2 + (beta - 1) ** 2))


def regression_metrics(y_true: ArrayLike, y_pred: ArrayLike) -> Dict[str, float]:
    """Return RMSE, MAE, R2, NSE and KGE for a continuous forecast."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    sse = np.sum((y_true - y_pred) ** 2)
    sst = np.sum((y_true - y_true.mean()) ** 2)
    return {
        "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "R2": float(r2_score(y_true, y_pred)),
        "NSE": float(1 - sse / sst) if sst > 0 else float("nan"),
        "KGE": kge(y_true, y_pred),
    }


def classification_metrics(
    y_true: ArrayLike, y_pred: ArrayLike, y_prob: ArrayLike
) -> Dict[str, float]:
    """Return the full event-classification metric suite.

    Includes accuracy, balanced accuracy, precision, recall, specificity, F1,
    AUC and Cohen's kappa.
    """
    y_true = np.asarray(y_true)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    specificity = tn / (tn + fp) if (tn + fp) else float("nan")
    auc = roc_auc_score(y_true, y_prob) if len(np.unique(y_true)) == 2 else float("nan")
    return {
        "Accuracy": float(accuracy_score(y_true, y_pred)),
        "Balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "Precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "Recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "Specificity": float(specificity),
        "F1": float(f1_score(y_true, y_pred, zero_division=0)),
        "AUC": float(auc),
        "Cohen_kappa": float(cohen_kappa_score(y_true, y_pred)),
    }
