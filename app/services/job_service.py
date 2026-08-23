from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.roles import is_recruiter
from app.models.job_description import JobDescription
from app.models.user import User
from app.repositories.job_description_repository import JobDescriptionRepository


class JobService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = JobDescriptionRepository(db)

    def create_job(self, recruiter: User, title: str, company: str | None, description: str) -> JobDescription:
        if not is_recruiter(recruiter):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Recruiter access required.",
            )
        job = JobDescription(
            user_id=recruiter.id,
            title=title,
            company=company,
            description=description,
        )
        return self.repo.create(job)

    def get_job(self, recruiter: User, job_id: UUID) -> JobDescription:
        job = self.repo.get_by_id(job_id, recruiter.id)
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job not found.",
            )
        return job

    def get_jobs(self, recruiter: User) -> list[JobDescription]:
        return self.repo.get_all_by_user(recruiter.id)

    def update_job(self, recruiter: User, job_id: UUID, title: str | None, company: str | None, description: str | None) -> JobDescription:
        job = self.get_job(recruiter, job_id)
        if title is not None:
            job.title = title
        if company is not None:
            job.company = company
        if description is not None:
            job.description = description
        return self.repo.update(job)

    def delete_job(self, recruiter: User, job_id: UUID) -> None:
        job = self.get_job(recruiter, job_id)
        self.repo.delete(job)
