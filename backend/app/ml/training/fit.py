"""Fit a single sklearn pipeline with the same prep as experiments."""

from __future__ import annotations

from typing import Any, Literal

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app.ml.training.models import (
    CLASSIFICATION_MODELS,
    REGRESSION_MODELS,
    build_preprocessor,
    select_feature_columns,
)

TaskType = Literal["classification", "regression"]


def fit_model_pipeline(
    frame: pd.DataFrame,
    *,
    target_column: str,
    model_key: str,
    task_type: TaskType = "classification",
    test_size: float = 0.2,
    random_state: int = 42,
) -> dict[str, Any]:
    """Train one model; used by explainability to recover a fitted pipeline."""
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
        raise ValueError("Need at least 10 rows with a non-null target")

    stratify = None
    if task_type == "classification":
        counts = y.value_counts()
        if counts.min() >= 2 and counts.shape[0] >= 2:
            stratify = y

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify,
    )

    pipe = Pipeline(
        steps=[
            ("preprocess", build_preprocessor(x_train)),
            ("model", registry[model_key]["factory"]()),
        ]
    )
    pipe.fit(x_train, y_train)

    return {
        "pipeline": pipe,
        "model_key": model_key,
        "model_name": registry[model_key]["name"],
        "feature_columns": feature_cols,
        "dropped_columns": dropped,
        "x_train": x_train,
        "x_test": x_test,
        "y_train": y_train,
        "y_test": y_test,
        "task_type": task_type,
    }
