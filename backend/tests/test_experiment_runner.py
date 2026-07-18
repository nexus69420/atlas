"""Unit tests for the multi-model experiment runner."""

import pandas as pd

from app.ml.training.experiment_runner import run_experiment


def test_run_classification_experiment_ranks_models() -> None:
    # Separable-ish synthetic data so metrics are defined
    rows = []
    for i in range(40):
        rows.append({"age": 20 + i % 10, "income": 20_000 + i * 1000, "churn": 0})
    for i in range(40):
        rows.append({"age": 50 + i % 10, "income": 80_000 + i * 500, "churn": 1})
    frame = pd.DataFrame(rows)

    result = run_experiment(
        frame,
        target_column="churn",
        task_type="classification",
        test_size=0.25,
        random_state=42,
        model_keys=["logistic_regression", "random_forest"],
    )

    assert len(result["models"]) == 2
    assert result["comparison"]["primary_metric"] == "f1_macro"
    assert result["comparison"]["winner"] is not None
    assert result["comparison"]["ranking"]
    assert "tradeoffs" in result["comparison"]
    assert result["data"]["n_features_used"] == 2

    for model in result["models"]:
        assert "accuracy" in model["metrics"]
        assert "f1_macro" in model["metrics"]
        assert model["train_time_seconds"] >= 0


def test_unknown_model_raises() -> None:
    frame = pd.DataFrame({"x": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], "y": [0, 1] * 5})
    try:
        run_experiment(
            frame,
            target_column="y",
            model_keys=["not_a_model"],
        )
        raised = False
    except ValueError:
        raised = True
    assert raised
