"""Classification / regression metric helpers."""

from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)


def classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: np.ndarray | None = None,
) -> dict[str, float | None]:
    """Compute a comparable metric set for model ranking."""
    metrics: dict[str, float | None] = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_macro": float(
            precision_score(y_true, y_pred, average="macro", zero_division=0)
        ),
        "recall_macro": float(
            recall_score(y_true, y_pred, average="macro", zero_division=0)
        ),
        "f1_macro": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "roc_auc": None,
    }

    if y_proba is not None:
        try:
            n_classes = len(np.unique(y_true))
            if n_classes == 2 and y_proba.ndim == 2 and y_proba.shape[1] >= 2:
                metrics["roc_auc"] = float(roc_auc_score(y_true, y_proba[:, 1]))
            elif n_classes > 2 and y_proba.ndim == 2:
                metrics["roc_auc"] = float(
                    roc_auc_score(
                        y_true,
                        y_proba,
                        multi_class="ovr",
                        average="macro",
                    )
                )
        except ValueError:
            metrics["roc_auc"] = None

    return metrics


def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    mse = float(mean_squared_error(y_true, y_pred))
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mse)),
        "r2": float(r2_score(y_true, y_pred)),
    }


def to_jsonable_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    """Ensure metric values are JSON-serializable."""
    out: dict[str, Any] = {}
    for key, value in metrics.items():
        if value is None:
            out[key] = None
        else:
            out[key] = float(value)
    return out
