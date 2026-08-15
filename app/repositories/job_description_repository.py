from uuid import UUID

from sqlalchemy.orm import Session

from app.models.job_description import JobDescription


class JobDescriptionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, job_description: JobDescription) -> JobDescription:
        self.db.add(job_description)
        self.db.commit()
        self.db.refresh(job_description)
        return job_description

    def get_by_id(self, job_description_id: UUID, user_id: UUID | None = None) -> JobDescription | None:
        query = self.db.query(JobDescription).filter(JobDescription.id == job_description_id)
        if user_id is not None:
            query = query.filter(JobDescription.user_id == user_id)
        return query.first()

    def get_all_by_user(self, user_id: UUID) -> list[JobDescription]:
        return (
            self.db.query(JobDescription)
            .filter(JobDescription.user_id == user_id)
            .order_by(JobDescription.created_at.desc())
            .all()
        )

    def update(self, job_description: JobDescription) -> JobDescription:
        self.db.commit()
        self.db.refresh(job_description)
        return job_description

    def delete(self, job_description: JobDescription) -> None:
        self.db.delete(job_description)
        self.db.commit()
