"""Prediction log persistence."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.prediction_log import PredictionLog


class PredictionLogRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, row: PredictionLog) -> PredictionLog:
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row

    def list_by_deployment(
        self,
        deployment_id: UUID,
        *,
        limit: int = 50,
    ) -> list[PredictionLog]:
        statement = (
            select(PredictionLog)
            .where(PredictionLog.deployment_id == deployment_id)
            .order_by(PredictionLog.created_at.desc())
            .limit(limit)
        )
        return list(self._db.scalars(statement).all())
