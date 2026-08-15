from uuid import UUID

from sqlalchemy.orm import Session

from app.models.job_match import JobMatch


class JobMatchRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, match_record: JobMatch) -> JobMatch:
        self.db.add(match_record)
        self.db.commit()
        self.db.refresh(match_record)
        return match_record

    def get_by_id(self, match_id: UUID, user_id: UUID | None = None) -> JobMatch | None:
        query = self.db.query(JobMatch).filter(JobMatch.id == match_id)
        if user_id is not None:
            query = query.filter(JobMatch.user_id == user_id)
        return query.first()

    def get_by_resume(self, resume_id: UUID, user_id: UUID) -> list[JobMatch]:
        return (
            self.db.query(JobMatch)
            .filter(JobMatch.resume_id == resume_id, JobMatch.user_id == user_id)
            .order_by(JobMatch.created_at.desc())
            .all()
        )

    def get_all_by_user(self, user_id: UUID) -> list[JobMatch]:
        return (
            self.db.query(JobMatch)
            .filter(JobMatch.user_id == user_id)
            .order_by(JobMatch.created_at.desc())
            .all()
        )

    def delete(self, match_record: JobMatch) -> None:
        self.db.delete(match_record)
        self.db.commit()
