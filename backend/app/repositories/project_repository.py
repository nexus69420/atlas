"""Project persistence — SQL only."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.project import Project


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        *,
        owner_id: UUID,
        name: str,
        description: str | None,
    ) -> Project:
        project = Project(owner_id=owner_id, name=name, description=description)
        self._db.add(project)
        self._db.commit()
        self._db.refresh(project)
        return project

    def list_by_owner(self, owner_id: UUID) -> list[Project]:
        statement = (
            select(Project)
            .where(Project.owner_id == owner_id)
            .order_by(Project.created_at.desc())
        )
        return list(self._db.scalars(statement).all())

    def get_by_id(self, project_id: UUID) -> Project | None:
        return self._db.get(Project, project_id)

    def get_by_owner_and_name(self, owner_id: UUID, name: str) -> Project | None:
        statement = select(Project).where(
            Project.owner_id == owner_id,
            Project.name == name,
        )
        return self._db.scalars(statement).first()

    def save(self, project: Project) -> Project:
        self._db.add(project)
        self._db.commit()
        self._db.refresh(project)
        return project

    def delete(self, project: Project) -> None:
        self._db.delete(project)
        self._db.commit()
