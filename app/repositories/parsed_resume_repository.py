from uuid import UUID

from sqlalchemy.orm import Session

from app.models.parsed_resume import ParsedResume


class ParsedResumeRepository:
    """
    Repository for all ParsedResume database operations.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, parsed_resume: ParsedResume) -> ParsedResume:
        """
        Save a new parsed resume record to the database.
        """
        self.db.add(parsed_resume)
        self.db.commit()
        self.db.refresh(parsed_resume)
        return parsed_resume

    def get_by_resume_id(self, resume_id: UUID) -> ParsedResume | None:
        """
        Retrieve the parsed resume record for a given resume.
        """
        return (
            self.db.query(ParsedResume)
            .filter(ParsedResume.resume_id == resume_id)
            .first()
        )

    def get_for_user(
        self,
        resume_id: UUID,
        user_id: UUID,
    ) -> ParsedResume | None:
        """
        Retrieve a parsed resume only if it belongs to the user.
        """
        return (
            self.db.query(ParsedResume)
            .filter(
                ParsedResume.resume_id == resume_id,
                ParsedResume.user_id == user_id,
            )
            .first()
        )

    def delete_for_resume(self, resume_id: UUID) -> None:
        """
        Delete the parsed resume record associated with a resume.
        """
        self.db.query(ParsedResume).filter(
            ParsedResume.resume_id == resume_id
        ).delete()
        self.db.commit()
