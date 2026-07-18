"""Typed schemas for experiment results and model comparison.

Why typed (not raw dict):
- OpenAPI docs become usable for a future UI
- Frontend gets a stable contract
- Invalid result shapes fail loudly instead of silently
"""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ExperimentDataInfo(BaseModel):
    n_rows_used: int
    n_features_used: int
    feature_columns: list[str]
    dropped_columns: list[str]
    test_size: float
    random_state: int
    stratified: bool
    class_distribution_train: dict[str, int] | None = None


class ModelRunMetrics(BaseModel):
    # Classification
    accuracy: float | None = None
    precision_macro: float | None = None
    recall_macro: float | None = None
    f1_macro: float | None = None
    roc_auc: float | None = None
    # Regression
    mae: float | None = None
    rmse: float | None = None
    r2: float | None = None


class ModelRunResult(BaseModel):
    model_key: str
    model_name: str
    metrics: ModelRunMetrics
    train_time_seconds: float
    n_train: int
    n_test: int
    notes: list[str] = Field(default_factory=list)


class RankingEntry(BaseModel):
    model_key: str
    model_name: str
    score: float
    train_time_seconds: float


class WinnerInfo(BaseModel):
    model_key: str
    model_name: str
    score: float
    reason: str


class ComparisonBlock(BaseModel):
    primary_metric: str | None
    ranking: list[RankingEntry]
    winner: WinnerInfo | None
    tradeoffs: list[str]


class ExperimentResults(BaseModel):
    data: ExperimentDataInfo
    models: list[ModelRunResult]
    comparison: ComparisonBlock


class ModelComparisonCard(BaseModel):
    """UI-friendly card for one model in a comparison view."""

    rank: int
    model_key: str
    model_name: str
    metrics: ModelRunMetrics
    primary_score: float | None
    delta_vs_winner: float | None = Field(
        description="primary_score - winner_score (0 for winner, negative if worse)"
    )
    train_time_seconds: float
    is_winner: bool
    pros: list[str]
    cons: list[str]


class ExperimentComparisonResponse(BaseModel):
    """Dedicated comparison payload — what a Model Comparison screen should render."""

    experiment_id: UUID
    experiment_name: str
    task_type: str
    target_column: str
    status: str
    primary_metric: str | None
    winner: WinnerInfo | None
    tradeoffs: list[str]
    models: list[ModelComparisonCard]
    metric_table: list[dict[str, Any]] = Field(
        description="Rows suitable for a side-by-side metrics table"
    )
    data: ExperimentDataInfo | None = None
