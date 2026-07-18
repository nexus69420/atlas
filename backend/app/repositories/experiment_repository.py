"""Experiment persistence."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.experiment import Experiment


class ExperimentRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, experiment: Experiment) -> Experiment:
        self._db.add(experiment)
        self._db.commit()
        self._db.refresh(experiment)
        return experiment

    def save(self, experiment: Experiment) -> Experiment:
        self._db.add(experiment)
        self._db.commit()
        self._db.refresh(experiment)
        return experiment

    def get_by_id(self, experiment_id: UUID) -> Experiment | None:
        return self._db.get(Experiment, experiment_id)

    def list_by_project(self, project_id: UUID) -> list[Experiment]:
        statement = (
            select(Experiment)
            .where(Experiment.project_id == project_id)
            .order_by(Experiment.created_at.desc())
        )
        return list(self._db.scalars(statement).all())
