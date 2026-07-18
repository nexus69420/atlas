"""Dataset persistence — SQL only."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dataset import Dataset


class DatasetRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, dataset: Dataset) -> Dataset:
        self._db.add(dataset)
        self._db.commit()
        self._db.refresh(dataset)
        return dataset

    def list_by_project(self, project_id: UUID) -> list[Dataset]:
        statement = (
            select(Dataset)
            .where(Dataset.project_id == project_id)
            .order_by(Dataset.created_at.desc())
        )
        return list(self._db.scalars(statement).all())

    def get_by_id(self, dataset_id: UUID) -> Dataset | None:
        return self._db.get(Dataset, dataset_id)

    def get_by_project_and_name(self, project_id: UUID, name: str) -> Dataset | None:
        statement = select(Dataset).where(
            Dataset.project_id == project_id,
            Dataset.name == name,
        )
        return self._db.scalars(statement).first()

    def delete(self, dataset: Dataset) -> None:
        self._db.delete(dataset)
        self._db.commit()
