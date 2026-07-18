"""Dataset profiling — pure pandas logic, no FastAPI/DB.

Why this lives under `app/ml/`:
- Profiling is an ML engineering capability, not HTTP plumbing
- Services orchestrate; this module computes evidence
"""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
import pandas as pd

InferredType = Literal["numeric", "categorical", "boolean", "datetime", "text"]

HIGH_MISSING_PCT = 0.2
HIGH_CORR_ABS = 0.7
CONSTANT_UNIQUE = 1
IMBALANCE_RATIO_WARN = 3.0  # majority/minority


def _to_native(value: Any) -> Any:
    """Convert numpy/pandas scalars to JSON-safe Python types."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    return value


def infer_column_type(series: pd.Series) -> InferredType:
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    # Try datetime parse on object columns (sample)
    if series.dtype == object:
        sample = series.dropna().head(50)
        if not sample.empty:
            parsed = pd.to_datetime(sample, errors="coerce", utc=True)
            if parsed.notna().mean() >= 0.8:
                return "datetime"
        nunique = series.nunique(dropna=True)
        if nunique <= max(20, int(0.05 * max(len(series), 1))):
            return "categorical"
        return "text"

    return "categorical"


def _profile_column(name: str, series: pd.Series) -> dict[str, Any]:
    inferred = infer_column_type(series)
    missing_count = int(series.isna().sum())
    n = len(series)
    missing_pct = float(missing_count / n) if n else 0.0
    unique_count = int(series.nunique(dropna=True))

    column: dict[str, Any] = {
        "name": name,
        "dtype": str(series.dtype),
        "inferred_type": inferred,
        "missing_count": missing_count,
        "missing_pct": round(missing_pct, 4),
        "unique_count": unique_count,
    }

    non_null = series.dropna()
    if inferred == "numeric" and not non_null.empty:
        column["stats"] = {
            "mean": _to_native(non_null.mean()),
            "std": _to_native(non_null.std()),
            "min": _to_native(non_null.min()),
            "median": _to_native(non_null.median()),
            "max": _to_native(non_null.max()),
        }
    elif inferred in {"categorical", "boolean", "text"} and not non_null.empty:
        top = non_null.astype(str).value_counts().head(5)
        column["top_values"] = [
            {"value": str(idx), "count": int(count)} for idx, count in top.items()
        ]

    return column


def _correlation_pairs(frame: pd.DataFrame) -> list[dict[str, Any]]:
    numeric = frame.select_dtypes(include=[np.number])
    if numeric.shape[1] < 2:
        return []

    corr = numeric.corr(method="pearson")
    pairs: list[dict[str, Any]] = []
    cols = list(corr.columns)
    for i, left in enumerate(cols):
        for right in cols[i + 1 :]:
            value = corr.loc[left, right]
            if pd.isna(value):
                continue
            abs_value = abs(float(value))
            if abs_value < HIGH_CORR_ABS:
                continue
            direction = "positive" if value > 0 else "negative"
            pairs.append(
                {
                    "column_a": left,
                    "column_b": right,
                    "coefficient": round(float(value), 4),
                    "abs_coefficient": round(abs_value, 4),
                    "note": (
                        f"Strong {direction} correlation (|r|≥{HIGH_CORR_ABS}). "
                        "Review for multicollinearity or leakage before modeling."
                    ),
                }
            )

    pairs.sort(key=lambda p: p["abs_coefficient"], reverse=True)
    return pairs[:20]


def _target_analysis(
    frame: pd.DataFrame,
    target_column: str,
) -> dict[str, Any]:
    if target_column not in frame.columns:
        raise ValueError(f"Target column '{target_column}' not found in dataset")

    series = frame[target_column]
    counts = series.value_counts(dropna=False)
    class_counts = [
        {"value": str(_to_native(idx)), "count": int(count)}
        for idx, count in counts.items()
    ]

    non_null_counts = series.value_counts(dropna=True)
    imbalance_ratio: float | None = None
    warning: str | None = None
    if len(non_null_counts) >= 2:
        imbalance_ratio = float(
            non_null_counts.iloc[0] / max(non_null_counts.iloc[-1], 1)
        )
        if imbalance_ratio >= IMBALANCE_RATIO_WARN:
            warning = (
                f"Class imbalance detected (majority/minority ≈ {imbalance_ratio:.2f}). "
                "Consider stratified splits, class weights, or resampling — "
                "accuracy alone will be misleading."
            )

    return {
        "column": target_column,
        "class_counts": class_counts,
        "n_classes": int(series.nunique(dropna=True)),
        "imbalance_ratio": (
            round(imbalance_ratio, 4) if imbalance_ratio is not None else None
        ),
        "warning": warning,
    }


def _build_warnings(
    columns: list[dict[str, Any]],
    duplicate_row_count: int,
    row_count: int,
) -> list[dict[str, str]]:
    warnings: list[dict[str, str]] = []

    if row_count and duplicate_row_count / row_count >= 0.05:
        warnings.append(
            {
                "code": "DUPLICATE_ROWS",
                "column": "",
                "severity": "medium",
                "message": (
                    f"{duplicate_row_count} duplicate rows "
                    f"({duplicate_row_count / row_count:.1%}). "
                    "Duplicates can inflate metrics; decide whether to drop them."
                ),
            }
        )

    for col in columns:
        if col["missing_pct"] >= HIGH_MISSING_PCT:
            warnings.append(
                {
                    "code": "HIGH_MISSING",
                    "column": col["name"],
                    "severity": "high",
                    "message": (
                        f"Column '{col['name']}' is missing "
                        f"{col['missing_pct']:.1%} of values. "
                        "Impute carefully or drop — missingness may itself be signal."
                    ),
                }
            )
        if col["unique_count"] == CONSTANT_UNIQUE and col["missing_count"] < row_count:
            warnings.append(
                {
                    "code": "CONSTANT_COLUMN",
                    "column": col["name"],
                    "severity": "medium",
                    "message": (
                        f"Column '{col['name']}' has a single unique value. "
                        "It adds no predictive signal; consider dropping it."
                    ),
                }
            )
        if col["inferred_type"] in {"categorical", "text"} and row_count > 0:
            non_null_count = row_count - col["missing_count"]
            if non_null_count >= 5 and col["unique_count"] == non_null_count:
                warnings.append(
                    {
                        "code": "HIGH_CARDINALITY",
                        "column": col["name"],
                        "severity": "low",
                        "message": (
                            f"Column '{col['name']}' looks like an identifier "
                            "(all unique values). Using it as a feature often causes leakage."
                        ),
                    }
                )

    return warnings


def profile_dataframe(
    frame: pd.DataFrame,
    *,
    target_column: str | None = None,
) -> dict[str, Any]:
    """Build an Atlas Report (structured evidence about a dataset)."""
    row_count = int(len(frame))
    column_count = int(len(frame.columns))
    duplicate_row_count = int(frame.duplicated().sum())

    columns = [_profile_column(str(name), frame[name]) for name in frame.columns]
    corr_pairs = _correlation_pairs(frame)
    warnings = _build_warnings(columns, duplicate_row_count, row_count)

    for pair in corr_pairs:
        warnings.append(
            {
                "code": "HIGH_CORRELATION",
                "column": f"{pair['column_a']}~{pair['column_b']}",
                "severity": "medium",
                "message": pair["note"],
            }
        )

    target: dict[str, Any] | None = None
    if target_column:
        target = _target_analysis(frame, target_column)
        if target.get("warning"):
            warnings.append(
                {
                    "code": "CLASS_IMBALANCE",
                    "column": target_column,
                    "severity": "high",
                    "message": target["warning"],
                }
            )

    return {
        "summary": {
            "row_count": row_count,
            "column_count": column_count,
            "duplicate_row_count": duplicate_row_count,
            "duplicate_row_pct": (
                round(duplicate_row_count / row_count, 4) if row_count else 0.0
            ),
            "memory_bytes_approx": int(frame.memory_usage(deep=True).sum()),
        },
        "columns": columns,
        "correlations": {
            "method": "pearson",
            "threshold_abs": HIGH_CORR_ABS,
            "pairs": corr_pairs,
        },
        "target_analysis": target,
        "warnings": warnings,
    }
