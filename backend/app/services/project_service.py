"""Project business logic — ownership rules live here, not in routes."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreateRequest, ProjectUpdateRequest


class ProjectService:
    def __init__(self, db: Session) -> None:
        self._projects = ProjectRepository(db)

    def create(self, owner: User, payload: ProjectCreateRequest) -> Project:
        name = payload.name.strip()
        if self._projects.get_by_owner_and_name(owner.id, name) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A project with this name already exists",
            )

        return self._projects.create(
            owner_id=owner.id,
            name=name,
            description=payload.description,
        )

    def list_for_user(self, owner: User) -> list[Project]:
        return self._projects.list_by_owner(owner.id)

    def get_for_user(self, owner: User, project_id: UUID) -> Project:
        project = self._projects.get_by_id(project_id)
        if project is None or project.owner_id != owner.id:
            # Same status whether missing or not yours — avoid leaking existence
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )
        return project

    def update(
        self,
        owner: User,
        project_id: UUID,
        payload: ProjectUpdateRequest,
    ) -> Project:
        project = self.get_for_user(owner, project_id)

        if payload.name is not None:
            name = payload.name.strip()
            existing = self._projects.get_by_owner_and_name(owner.id, name)
            if existing is not None and existing.id != project.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="A project with this name already exists",
                )
            project.name = name

        if payload.description is not None:
            project.description = payload.description

        return self._projects.save(project)

    def delete(self, owner: User, project_id: UUID) -> None:
        project = self.get_for_user(owner, project_id)
        self._projects.delete(project)
