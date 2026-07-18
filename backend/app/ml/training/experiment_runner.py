"""Run a multi-model experiment and return comparable evidence.

This is the core of Atlas V1: not "train one model" —
train several, score them, and explain the trade-offs.
"""

from __future__ import annotations

import time
from typing import Any, Literal

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app.ml.evaluation.metrics import (
    classification_metrics,
    regression_metrics,
    to_jsonable_metrics,
)
from app.ml.training.models import (
    CLASSIFICATION_MODELS,
    REGRESSION_MODELS,
    build_preprocessor,
    select_feature_columns,
)

TaskType = Literal["classification", "regression"]


def _resolve_models(
    task_type: TaskType,
    model_keys: list[str] | None,
) -> dict[str, Any]:
    registry = (
        CLASSIFICATION_MODELS if task_type == "classification" else REGRESSION_MODELS
    )
    keys = model_keys or list(registry.keys())
    missing = [k for k in keys if k not in registry]
    if missing:
        raise ValueError(
            f"Unknown model(s) for {task_type}: {missing}. "
            f"Available: {list(registry.keys())}"
        )
    return {k: registry[k] for k in keys}


def _build_comparison(
    task_type: TaskType,
    model_results: list[dict[str, Any]],
) -> dict[str, Any]:
    if not model_results:
        return {
            "primary_metric": None,
            "ranking": [],
            "winner": None,
            "tradeoffs": ["No models completed successfully."],
        }

    primary = "f1_macro" if task_type == "classification" else "r2"
    scored: list[dict[str, Any]] = []
    for result in model_results:
        metrics = result.get("metrics") or {}
        score = metrics.get(primary)
        if score is None:
            continue
        scored.append(
            {
                "model_key": result["model_key"],
                "model_name": result["model_name"],
                "score": score,
                "train_time_seconds": result["train_time_seconds"],
            }
        )

    scored.sort(key=lambda r: r["score"], reverse=True)
    winner = scored[0] if scored else None

    tradeoffs: list[str] = []
    if winner:
        tradeoffs.append(
            f"{winner['model_name']} leads on {primary} "
            f"({winner['score']:.4f}) under the current split and seed."
        )

    # Speed vs accuracy note
    if len(scored) >= 2:
        fastest = min(scored, key=lambda r: r["train_time_seconds"])
        if fastest["model_key"] != winner["model_key"]:
            tradeoffs.append(
                f"{fastest['model_name']} trained fastest "
                f"({fastest['train_time_seconds']:.3f}s) but did not win on {primary}. "
                "Prefer it when latency/cost matter more than peak score."
            )

    if task_type == "classification":
        tradeoffs.append(
            "Primary ranking uses macro-F1 so minority classes are not ignored. "
            "Check ROC-AUC and precision/recall before deploying."
        )
    else:
        tradeoffs.append(
            "Primary ranking uses R². Also inspect RMSE/MAE in the units of your target."
        )

    tradeoffs.append(
        "These results are from a single train/test split — not cross-validation. "
        "Treat them as directional evidence, not a final production decision."
    )

    return {
        "primary_metric": primary,
        "ranking": scored,
        "winner": (
            {
                "model_key": winner["model_key"],
                "model_name": winner["model_name"],
                "score": winner["score"],
                "reason": (
                    f"Highest {primary} on the held-out test set "
                    f"with the configured random_state."
                ),
            }
            if winner
            else None
        ),
        "tradeoffs": tradeoffs,
    }


def run_experiment(
    frame: pd.DataFrame,
    *,
    target_column: str,
    task_type: TaskType = "classification",
    test_size: float = 0.2,
    random_state: int = 42,
    model_keys: list[str] | None = None,
) -> dict[str, Any]:
    """Train multiple models and return structured comparison evidence."""
    if target_column not in frame.columns:
        raise ValueError(f"Target column '{target_column}' not found")

    if not 0.05 <= test_size <= 0.5:
        raise ValueError("test_size must be between 0.05 and 0.5")

    feature_cols, dropped = select_feature_columns(frame, target_column)
    if not feature_cols:
        raise ValueError("No usable feature columns remain after selection")

    x = frame[feature_cols].copy()
    y = frame[target_column].copy()

    # Drop rows with missing target
    mask = y.notna()
    x = x.loc[mask]
    y = y.loc[mask]

    if len(x) < 10:
        raise ValueError(
            "Need at least 10 rows with a non-null target to run an experiment"
        )

    stratify = None
    if task_type == "classification":
        # Stratify only when every class has >= 2 samples
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

    registry = _resolve_models(task_type, model_keys)
    model_results: list[dict[str, Any]] = []

    for model_key, spec in registry.items():
        preprocessor = build_preprocessor(x_train)
        pipe = Pipeline(
            steps=[
                ("preprocess", preprocessor),
                ("model", spec["factory"]()),
            ]
        )

        started = time.perf_counter()
        pipe.fit(x_train, y_train)
        elapsed = time.perf_counter() - started

        y_pred = pipe.predict(x_test)
        y_proba = None
        if task_type == "classification" and hasattr(pipe, "predict_proba"):
            try:
                y_proba = pipe.predict_proba(x_test)
            except Exception:
                y_proba = None

        if task_type == "classification":
            metrics = classification_metrics(
                np.asarray(y_test),
                np.asarray(y_pred),
                y_proba=np.asarray(y_proba) if y_proba is not None else None,
            )
        else:
            metrics = regression_metrics(np.asarray(y_test), np.asarray(y_pred))

        model_results.append(
            {
                "model_key": model_key,
                "model_name": spec["name"],
                "metrics": to_jsonable_metrics(metrics),
                "train_time_seconds": round(elapsed, 4),
                "n_train": int(len(x_train)),
                "n_test": int(len(x_test)),
                "notes": list(spec["notes"]),
            }
        )

    class_distribution = None
    if task_type == "classification":
        class_distribution = {
            str(k): int(v) for k, v in y_train.value_counts().to_dict().items()
        }

    return {
        "data": {
            "n_rows_used": int(len(x)),
            "n_features_used": int(len(feature_cols)),
            "feature_columns": feature_cols,
            "dropped_columns": dropped,
            "test_size": test_size,
            "random_state": random_state,
            "stratified": stratify is not None,
            "class_distribution_train": class_distribution,
        },
        "models": model_results,
        "comparison": _build_comparison(task_type, model_results),
    }
