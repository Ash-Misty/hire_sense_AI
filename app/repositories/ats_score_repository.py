from uuid import UUID

from sqlalchemy.orm import Session

from app.models.ats_score import AtsScore


class AtsScoreRepository:
    """
    Repository for all AtsScore database operations.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_resume(self, resume_id: UUID) -> AtsScore | None:
        """
        Retrieve the ATS score for a given resume.
        """
        return (
            self.db.query(AtsScore)
            .filter(AtsScore.resume_id == resume_id)
            .first()
        )

    def get_by_user_id(self, user_id: UUID) -> list[AtsScore]:
        """
        Retrieve all ATS scores for a given user.
        """
        return (
            self.db.query(AtsScore)
            .filter(AtsScore.user_id == user_id)
            .order_by(AtsScore.created_at.desc())
            .all()
        )

    def create(self, ats_score: AtsScore) -> AtsScore:
        """
        Save a new ATS score record.
        """
        self.db.add(ats_score)
        self.db.commit()
        self.db.refresh(ats_score)
        return ats_score

    def replace_for_resume(
        self,
        resume_id: UUID,
        ats_score: AtsScore,
    ) -> AtsScore:
        """
        Replace the ATS score for a resume with a fresh one.

        Deletes any existing row for the resume (respecting the unique
        constraint on resume_id) before inserting the new record.
        """
        self.db.query(AtsScore).filter(
            AtsScore.resume_id == resume_id
        ).delete(synchronize_session=False)

        self.db.add(ats_score)
        self.db.commit()
        self.db.refresh(ats_score)
        return ats_score
