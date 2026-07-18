"""Unit tests for the pure profiling engine (no HTTP)."""

import pandas as pd

from app.ml.profiling.profiler import profile_dataframe


def test_profile_detects_missing_correlation_and_imbalance() -> None:
    frame = pd.DataFrame(
        {
            "age": [22, 45, 31, 28, None, 40],
            "income": [30_000, 90_000, 55_000, 48_000, 70_000, 85_000],
            # Nearly collinear with income
            "income_copy": [30_100, 89_900, 55_200, 47_800, 70_100, 84_800],
            "id_like": ["a", "b", "c", "d", "e", "f"],
            "churn": [0, 0, 0, 0, 0, 1],
        }
    )

    report = profile_dataframe(frame, target_column="churn")

    assert report["summary"]["row_count"] == 6
    assert report["summary"]["column_count"] == 5

    age = next(c for c in report["columns"] if c["name"] == "age")
    assert age["missing_count"] == 1
    assert age["inferred_type"] == "numeric"
    assert "stats" in age

    codes = {w["code"] for w in report["warnings"]}
    assert "HIGH_MISSING" in codes or age["missing_pct"] > 0
    assert "HIGH_CORRELATION" in codes
    assert "CLASS_IMBALANCE" in codes
    assert "HIGH_CARDINALITY" in codes

    assert report["target_analysis"]["column"] == "churn"
    assert report["target_analysis"]["imbalance_ratio"] is not None
    assert report["target_analysis"]["imbalance_ratio"] >= 3.0


def test_profile_without_target_skips_imbalance() -> None:
    frame = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
    report = profile_dataframe(frame)
    assert report["target_analysis"] is None
    assert "CLASS_IMBALANCE" not in {w["code"] for w in report["warnings"]}
