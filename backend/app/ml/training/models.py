"""Model registry and preprocessing for V1 experiments.

Why sklearn first:
- Free, reproducible, widely understood
- Enough to demonstrate evidence-driven model comparison
- XGBoost / PyTorch land when we need them — not before
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

EstimatorFactory = Callable[[], BaseEstimator]

CLASSIFICATION_MODELS: dict[str, dict[str, Any]] = {
    "logistic_regression": {
        "name": "Logistic Regression",
        "factory": lambda: LogisticRegression(max_iter=1000),
        "notes": [
            "Linear, fast, highly interpretable coefficients.",
            "Strong baseline when relationships are roughly linear.",
        ],
    },
    "random_forest": {
        "name": "Random Forest",
        "factory": lambda: RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            n_jobs=-1,
        ),
        "notes": [
            "Non-linear ensemble; robust to feature scale.",
            "Usually stronger than linear models; less interpretable.",
        ],
    },
    "gradient_boosting": {
        "name": "Gradient Boosting",
        "factory": lambda: GradientBoostingClassifier(random_state=42),
        "notes": [
            "Often best tabular accuracy in V1 baselines.",
            "Slower to train; watch for overfitting on small data.",
        ],
    },
}

REGRESSION_MODELS: dict[str, dict[str, Any]] = {
    "linear_regression": {
        "name": "Linear Regression",
        "factory": LinearRegression,
        "notes": [
            "Fast linear baseline with clear coefficient interpretation.",
        ],
    },
    "random_forest": {
        "name": "Random Forest",
        "factory": lambda: RandomForestRegressor(
            n_estimators=100,
            random_state=42,
            n_jobs=-1,
        ),
        "notes": [
            "Captures non-linear relationships; less interpretable.",
        ],
    },
    "gradient_boosting": {
        "name": "Gradient Boosting",
        "factory": lambda: GradientBoostingRegressor(random_state=42),
        "notes": [
            "Strong tabular regressor; tune carefully on small datasets.",
        ],
    },
}


def select_feature_columns(
    frame: pd.DataFrame,
    target_column: str,
) -> tuple[list[str], list[str]]:
    """Return (feature_columns, dropped_columns) with simple leakage heuristics."""
    dropped: list[str] = []
    features: list[str] = []

    for col in frame.columns:
        if col == target_column:
            continue
        series = frame[col]
        if pd.api.types.is_datetime64_any_dtype(series):
            dropped.append(col)
            continue
        if series.dtype == object or pd.api.types.is_string_dtype(series):
            non_null = series.dropna()
            if len(non_null) >= 5 and non_null.nunique() == len(non_null):
                dropped.append(col)
                continue
        features.append(col)

    return features, dropped


def build_preprocessor(x: pd.DataFrame) -> ColumnTransformer:
    numeric_cols = [c for c in x.columns if pd.api.types.is_numeric_dtype(x[c])]
    categorical_cols = [c for c in x.columns if c not in numeric_cols]

    transformers: list[tuple] = []
    if numeric_cols:
        transformers.append(
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_cols,
            )
        )
    if categorical_cols:
        transformers.append(
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        (
                            "onehot",
                            OneHotEncoder(
                                handle_unknown="ignore",
                                max_categories=20,
                            ),
                        ),
                    ]
                ),
                categorical_cols,
            )
        )

    if not transformers:
        raise ValueError("No usable feature columns after preprocessing selection")

    return ColumnTransformer(transformers=transformers)
