"""Build a polished, UI-ready model comparison from experiment results."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status

from app.models.experiment import Experiment
from app.schemas.comparison import (
    ComparisonBlock,
    ExperimentComparisonResponse,
    ExperimentDataInfo,
    ExperimentResults,
    ModelComparisonCard,
    ModelRunMetrics,
    ModelRunResult,
)


def parse_experiment_results(raw: dict[str, Any] | None) -> ExperimentResults | None:
    if raw is None:
        return None
    return ExperimentResults.model_validate(raw)


def _pros_cons(
    *,
    model: ModelRunResult,
    is_winner: bool,
    is_fastest: bool,
    primary_metric: str | None,
    delta: float | None,
) -> tuple[list[str], list[str]]:
    pros = list(model.notes)
    cons: list[str] = []

    if is_winner and primary_metric:
        pros.insert(
            0,
            f"Best {primary_metric} on this experiment's held-out test set.",
        )
    if is_fastest and not is_winner:
        pros.append("Fastest training time among compared models.")
    if is_fastest and is_winner:
        pros.append("Also the fastest model — strong accuracy/latency balance here.")

    if delta is not None and delta < 0 and primary_metric:
        cons.append(f"{abs(delta):.4f} below the winner on {primary_metric}.")
    if not is_fastest and model.train_time_seconds > 0:
        cons.append("Slower to train than at least one alternative in this run.")

    # Deduplicate while preserving order
    def unique(items: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for item in items:
            if item not in seen:
                seen.add(item)
                out.append(item)
        return out

    return unique(pros), unique(cons)


def build_comparison_response(experiment: Experiment) -> ExperimentComparisonResponse:
    if experiment.status != "completed" or not experiment.results:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Comparison is only available for completed experiments "
                f"(current status: {experiment.status})"
            ),
        )

    results = parse_experiment_results(experiment.results)
    if results is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Experiment has no results to compare",
        )

    comparison: ComparisonBlock = results.comparison
    primary = comparison.primary_metric
    winner_key = comparison.winner.model_key if comparison.winner else None
    winner_score = comparison.winner.score if comparison.winner else None

    rank_by_key = {
        entry.model_key: idx + 1 for idx, entry in enumerate(comparison.ranking)
    }
    fastest_key = min(
        (m.model_key for m in results.models),
        key=lambda k: next(
            m.train_time_seconds for m in results.models if m.model_key == k
        ),
        default=None,
    )

    cards: list[ModelComparisonCard] = []
    for model in results.models:
        primary_score = None
        if primary:
            primary_score = getattr(model.metrics, primary, None)

        delta = None
        if primary_score is not None and winner_score is not None:
            delta = round(float(primary_score) - float(winner_score), 6)

        is_winner = model.model_key == winner_key
        pros, cons = _pros_cons(
            model=model,
            is_winner=is_winner,
            is_fastest=model.model_key == fastest_key,
            primary_metric=primary,
            delta=delta,
        )

        cards.append(
            ModelComparisonCard(
                rank=rank_by_key.get(model.model_key, len(cards) + 1),
                model_key=model.model_key,
                model_name=model.model_name,
                metrics=model.metrics,
                primary_score=primary_score,
                delta_vs_winner=delta,
                train_time_seconds=model.train_time_seconds,
                is_winner=is_winner,
                pros=pros,
                cons=cons,
            )
        )

    cards.sort(key=lambda c: c.rank)

    metric_table: list[dict[str, Any]] = []
    for card in cards:
        row: dict[str, Any] = {
            "rank": card.rank,
            "model_key": card.model_key,
            "model_name": card.model_name,
            "train_time_seconds": card.train_time_seconds,
            "is_winner": card.is_winner,
            "delta_vs_winner": card.delta_vs_winner,
        }
        row.update(card.metrics.model_dump(exclude_none=True))
        metric_table.append(row)

    data: ExperimentDataInfo | None = results.data

    return ExperimentComparisonResponse(
        experiment_id=experiment.id,
        experiment_name=experiment.name,
        task_type=experiment.task_type,
        target_column=experiment.target_column,
        status=experiment.status,
        primary_metric=primary,
        winner=comparison.winner,
        tradeoffs=comparison.tradeoffs,
        models=cards,
        metric_table=metric_table,
        data=data,
    )


# Re-export for type checkers / services
__all__ = [
    "ModelRunMetrics",
    "ModelRunResult",
    "build_comparison_response",
    "parse_experiment_results",
]
