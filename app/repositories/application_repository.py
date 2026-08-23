from uuid import UUID

from sqlalchemy import func
from sqlalchemy import Integer
from sqlalchemy.orm import Session

from app.models.application import Application


class ApplicationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, application: Application) -> Application:
        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)
        return application

    def get_by_id(self, application_id: UUID, recruiter_id: UUID | None = None) -> Application | None:
        query = self.db.query(Application).filter(Application.id == application_id)
        if recruiter_id is not None:
            query = query.filter(Application.recruiter_id == recruiter_id)
        return query.first()

    def get_by_job(self, job_id: UUID, recruiter_id: UUID, skip: int = 0, limit: int = 100) -> tuple[list[Application], int]:
        base_query = self.db.query(Application).filter(
            Application.job_id == job_id,
            Application.recruiter_id == recruiter_id,
        )
        total = base_query.count()
        items = base_query.order_by(Application.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def get_by_candidate(self, candidate_id: UUID, recruiter_id: UUID) -> list[Application]:
        return (
            self.db.query(Application)
            .filter(Application.candidate_id == candidate_id, Application.recruiter_id == recruiter_id)
            .order_by(Application.created_at.desc())
            .all()
        )

    def get_by_recruiter(self, recruiter_id: UUID, skip: int = 0, limit: int = 100) -> tuple[list[Application], int]:
        base_query = self.db.query(Application).filter(Application.recruiter_id == recruiter_id)
        total = base_query.count()
        items = base_query.order_by(Application.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def update_status(self, application: Application, status: str, notes: str | None = None) -> Application:
        application.status = status
        if notes is not None:
            application.notes = notes
        self.db.commit()
        self.db.refresh(application)
        return application

    def delete(self, application: Application) -> None:
        self.db.delete(application)
        self.db.commit()

    def get_statistics(self, recruiter_id: UUID) -> dict:
        result = (
            self.db.query(
                func.count(Application.id).label("total"),
                func.sum(func.cast(Application.status == "applied", Integer)).label("applied"),
                func.sum(func.cast(Application.status == "reviewing", Integer)).label("reviewing"),
                func.sum(func.cast(Application.status == "shortlisted", Integer)).label("shortlisted"),
                func.sum(func.cast(Application.status == "interview", Integer)).label("interview"),
                func.sum(func.cast(Application.status == "selected", Integer)).label("selected"),
                func.sum(func.cast(Application.status == "rejected", Integer)).label("rejected"),
            )
            .filter(Application.recruiter_id == recruiter_id)
            .first()
        )
        return {
            "total": result.total or 0,
            "applied": result.applied or 0,
            "reviewing": result.reviewing or 0,
            "shortlisted": result.shortlisted or 0,
            "interview": result.interview or 0,
            "selected": result.selected or 0,
            "rejected": result.rejected or 0,
        }
