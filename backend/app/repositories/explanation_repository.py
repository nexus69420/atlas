"""Explanation persistence."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.explanation import Explanation


class ExplanationRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self, experiment_id: UUID, model_key: str) -> Explanation | None:
        statement = select(Explanation).where(
            Explanation.experiment_id == experiment_id,
            Explanation.model_key == model_key,
        )
        return self._db.scalars(statement).first()

    def upsert(
        self,
        *,
        experiment_id: UUID,
        model_key: str,
        report: dict,
    ) -> Explanation:
        existing = self.get(experiment_id, model_key)
        if existing is None:
            row = Explanation(
                experiment_id=experiment_id,
                model_key=model_key,
                report=report,
            )
            self._db.add(row)
        else:
            existing.report = report
            row = existing
        self._db.commit()
        self._db.refresh(row)
        return row
