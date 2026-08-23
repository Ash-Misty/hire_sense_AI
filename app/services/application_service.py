from fastapi import HTTPException
from fastapi import status as http_status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.roles import is_recruiter
from app.models.application import Application
from app.models.user import User
from app.repositories.application_repository import ApplicationRepository
from app.schemas.application import ApplicationUpdate


class ApplicationService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = ApplicationRepository(db)

    def create_application(
        self,
        recruiter: User,
        job_id: UUID,
        candidate_id: UUID,
        resume_id: UUID,
        application_status: str = "applied",
        notes: str | None = None,
    ) -> Application:
        if not is_recruiter(recruiter):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Recruiter access required.",
            )

        application = Application(
            recruiter_id=recruiter.id,
            job_id=job_id,
            candidate_id=candidate_id,
            resume_id=resume_id,
            status=application_status,
            notes=notes,
        )
        return self.repo.create(application)

    def get_application(self, recruiter: User, application_id: UUID) -> Application:
        application = self.repo.get_by_id(application_id, recruiter.id)
        if application is None:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Application not found.",
            )
        return application

    def update_application_status(
        self,
        recruiter: User,
        application_id: UUID,
        update_data: ApplicationUpdate,
    ) -> Application:
        application = self.get_application(recruiter, application_id)
        return self.repo.update_status(
            application=application,
            status=update_data.status.value,
            notes=update_data.notes,
        )

    def get_candidates_for_job(
        self,
        recruiter: User,
        job_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Application], int]:
        if not is_recruiter(recruiter):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Recruiter access required.",
            )
        return self.repo.get_by_job(job_id, recruiter.id, skip=skip, limit=limit)

    def get_candidate_applications(
        self,
        recruiter: User,
        candidate_id: UUID,
    ) -> list[Application]:
        if not is_recruiter(recruiter):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Recruiter access required.",
            )
        return self.repo.get_by_candidate(candidate_id, recruiter.id)

    def get_statistics(self, recruiter: User) -> dict:
        if not is_recruiter(recruiter):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="Recruiter access required.",
            )
        return self.repo.get_statistics(recruiter.id)

    def delete_application(self, recruiter: User, application_id: UUID) -> None:
        application = self.get_application(recruiter, application_id)
        self.repo.delete(application)
