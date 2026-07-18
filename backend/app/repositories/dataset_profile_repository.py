"""Dataset profile persistence."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dataset_profile import DatasetProfile


class DatasetProfileRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_dataset_id(self, dataset_id: UUID) -> DatasetProfile | None:
        statement = select(DatasetProfile).where(
            DatasetProfile.dataset_id == dataset_id
        )
        return self._db.scalars(statement).first()

    def upsert(
        self,
        *,
        dataset_id: UUID,
        target_column: str | None,
        report: dict,
    ) -> DatasetProfile:
        existing = self.get_by_dataset_id(dataset_id)
        if existing is None:
            profile = DatasetProfile(
                dataset_id=dataset_id,
                target_column=target_column,
                report=report,
            )
            self._db.add(profile)
        else:
            existing.target_column = target_column
            existing.report = report
            profile = existing

        self._db.commit()
        self._db.refresh(profile)
        return profile
