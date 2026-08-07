from uuid import UUID

from sqlalchemy.orm import Session

from app.models.resume import Resume


class ResumeRepository:
    """
    Repository for all Resume database operations.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, resume: Resume) -> Resume:
        """
        Save a new resume record to the database.
        """
        self.db.add(resume)
        self.db.commit()
        self.db.refresh(resume)
        return resume

    def get_by_id(self, resume_id: UUID) -> Resume | None:
        """
        Retrieve a resume by its UUID.
        """
        return (
            self.db.query(Resume)
            .filter(Resume.id == resume_id)
            .first()
        )

    def get_by_user(self, user_id: UUID) -> list[Resume]:
        """
        Retrieve all resumes belonging to a user,
        ordered newest-first.
        """
        return (
            self.db.query(Resume)
            .filter(Resume.user_id == user_id)
            .order_by(Resume.uploaded_at.desc())
            .all()
        )

    def delete(self, resume: Resume) -> None:
        """
        Delete a resume record.
        """
        self.db.delete(resume)
        self.db.commit()

