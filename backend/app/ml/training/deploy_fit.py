"""Fit a production pipeline on all usable rows (for deployment artifacts)."""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from app.ml.training.models import (
    CLASSIFICATION_MODELS,
    REGRESSION_MODELS,
    build_preprocessor,
    select_feature_columns,
)

TaskType = Literal["classification", "regression"]


def fit_production_pipeline(
    frame: pd.DataFrame,
    *,
    target_column: str,
    model_key: str,
    task_type: TaskType = "classification",
) -> dict[str, Any]:
    """Train on the full dataset for serving (not a train/test split)."""
    registry = (
        CLASSIFICATION_MODELS if task_type == "classification" else REGRESSION_MODELS
    )
    if model_key not in registry:
        raise ValueError(
            f"Unknown model '{model_key}'. Available: {list(registry.keys())}"
        )

    feature_cols, dropped = select_feature_columns(frame, target_column)
    if not feature_cols:
        raise ValueError("No usable feature columns remain after selection")

    x = frame[feature_cols].copy()
    y = frame[target_column].copy()
    mask = y.notna()
    x = x.loc[mask]
    y = y.loc[mask]

    if len(x) < 10:
        raise ValueError("Need at least 10 rows with a non-null target to deploy")

    pipe = Pipeline(
        steps=[
            ("preprocess", build_preprocessor(x)),
            ("model", registry[model_key]["factory"]()),
        ]
    )
    pipe.fit(x, y)

    classes: list[Any] | None = None
    model = pipe.named_steps["model"]
    if hasattr(model, "classes_"):
        classes = [_to_jsonable(c) for c in model.classes_]

    return {
        "pipeline": pipe,
        "model_key": model_key,
        "model_name": registry[model_key]["name"],
        "feature_columns": feature_cols,
        "dropped_columns": dropped,
        "task_type": task_type,
        "n_rows_trained": int(len(x)),
        "classes": classes,
    }


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value
