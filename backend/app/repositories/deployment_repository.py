"""Deployment persistence."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.deployment import Deployment


class DeploymentRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, deployment: Deployment) -> Deployment:
        self._db.add(deployment)
        self._db.commit()
        self._db.refresh(deployment)
        return deployment

    def save(self, deployment: Deployment) -> Deployment:
        self._db.add(deployment)
        self._db.commit()
        self._db.refresh(deployment)
        return deployment

    def get_by_id(self, deployment_id: UUID) -> Deployment | None:
        return self._db.get(Deployment, deployment_id)

    def list_by_project(self, project_id: UUID) -> list[Deployment]:
        statement = (
            select(Deployment)
            .where(Deployment.project_id == project_id)
            .order_by(Deployment.created_at.desc())
        )
        return list(self._db.scalars(statement).all())
