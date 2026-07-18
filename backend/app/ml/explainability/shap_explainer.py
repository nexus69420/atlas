"""SHAP-based explainability for fitted sklearn pipelines.

Returns global feature importance (mean |SHAP|) plus optional
per-instance contributions — with plain-language notes.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import shap
from sklearn.pipeline import Pipeline


def _as_2d_shap(shap_values: Any, n_features: int) -> np.ndarray:
    """Normalize SHAP outputs to shape (n_samples, n_features).

    TreeExplainer may return a list (one array per class) or a 3D array.
    For ranking features we use the positive class (index 1) when binary,
    otherwise mean absolute values across classes.
    """
    if isinstance(shap_values, list):
        if len(shap_values) == 2:
            return np.asarray(shap_values[1])
        stacked = np.stack([np.asarray(s) for s in shap_values], axis=0)
        return np.mean(np.abs(stacked), axis=0)

    arr = np.asarray(shap_values)
    if arr.ndim == 3:
        # (samples, features, classes) or (samples, classes, features)
        if arr.shape[1] == n_features:
            return np.mean(np.abs(arr), axis=2)
        if arr.shape[2] == n_features:
            if arr.shape[1] == 2:
                return arr[:, 1, :]
            return np.mean(np.abs(arr), axis=1)
    if arr.ndim == 2:
        return arr
    raise ValueError(f"Unexpected SHAP values shape: {arr.shape}")


def _build_explainer(model: Any, background: np.ndarray) -> Any:
    name = type(model).__name__
    if any(token in name for token in ("Forest", "Boosting", "Tree", "HistGradient")):
        return shap.TreeExplainer(model)
    if any(token in name for token in ("Logistic", "Linear")):
        return shap.LinearExplainer(model, background)
    # Model-agnostic fallback
    return shap.Explainer(model.predict, background)


def explain_pipeline(
    pipeline: Pipeline,
    x_background: pd.DataFrame,
    x_explain: pd.DataFrame,
    *,
    instance_index: int | None = None,
) -> dict[str, Any]:
    """Compute SHAP explanations in the model's transformed feature space."""
    preprocess = pipeline.named_steps["preprocess"]
    model = pipeline.named_steps["model"]

    background = preprocess.transform(x_background)
    explain = preprocess.transform(x_explain)
    # Ensure dense arrays for LinearExplainer / general handling
    if hasattr(background, "toarray"):
        background = background.toarray()
    if hasattr(explain, "toarray"):
        explain = explain.toarray()

    feature_names = [str(n) for n in preprocess.get_feature_names_out()]
    explainer = _build_explainer(model, background)

    raw_values = explainer.shap_values(explain)
    shap_matrix = _as_2d_shap(raw_values, n_features=len(feature_names))

    mean_abs = np.mean(np.abs(shap_matrix), axis=0)
    order = np.argsort(mean_abs)[::-1]

    feature_importances = [
        {
            "feature": feature_names[i],
            "mean_abs_shap": round(float(mean_abs[i]), 6),
            "rank": rank + 1,
        }
        for rank, i in enumerate(order)
    ]

    top = feature_importances[:5]
    summary_bits = [
        f"{item['feature']} (mean |SHAP|={item['mean_abs_shap']:.4f})" for item in top
    ]
    summary = (
        "Global explanation: features ranked by mean absolute SHAP value "
        "on the explained sample. Top drivers: " + "; ".join(summary_bits) + ". "
        "SHAP values are in the model's transformed feature space "
        "(one-hot / scaled columns), not always raw CSV column names."
    )

    instance: dict[str, Any] | None = None
    if instance_index is not None:
        if instance_index < 0 or instance_index >= shap_matrix.shape[0]:
            raise ValueError(
                f"instance_index must be between 0 and {shap_matrix.shape[0] - 1}"
            )
        row = shap_matrix[instance_index]
        contribs = [
            {
                "feature": feature_names[i],
                "shap_value": round(float(row[i]), 6),
            }
            for i in np.argsort(np.abs(row))[::-1][:15]
        ]
        instance = {
            "index": instance_index,
            "top_contributions": contribs,
            "note": (
                "Positive SHAP pushes the prediction toward the positive class "
                "(classification) or higher target (regression); negative pushes opposite."
            ),
        }

    expected_value = getattr(explainer, "expected_value", None)
    if isinstance(expected_value, (list, np.ndarray)):
        expected_value = (
            float(np.asarray(expected_value).reshape(-1)[-1])
            if np.asarray(expected_value).size
            else None
        )
    elif expected_value is not None:
        expected_value = float(expected_value)

    return {
        "method": "shap",
        "explainer": type(explainer).__name__,
        "n_background": int(len(x_background)),
        "n_explained": int(len(x_explain)),
        "feature_importances": feature_importances,
        "top_features": top,
        "summary": summary,
        "base_value": expected_value,
        "instance": instance,
    }
