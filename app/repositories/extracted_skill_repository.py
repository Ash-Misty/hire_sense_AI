from uuid import UUID

from sqlalchemy.orm import Session

from app.models.extracted_skill import ExtractedSkill
from app.models.resume import Resume


class ExtractedSkillRepository:
    """
    Repository for all ExtractedSkill database operations.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, skill: ExtractedSkill) -> ExtractedSkill:
        """
        Save a new extracted skill record.
        """
        self.db.add(skill)
        self.db.commit()
        self.db.refresh(skill)
        return skill

    def get_by_resume(self, resume_id: UUID) -> list[ExtractedSkill]:
        """
        Retrieve all extracted skills for a resume,
        ordered by count descending then skill name.
        """
        return (
            self.db.query(ExtractedSkill)
            .filter(ExtractedSkill.resume_id == resume_id)
            .order_by(
                ExtractedSkill.count.desc(),
                ExtractedSkill.skill.asc(),
            )
            .all()
        )

    def get_by_resume_and_skill(
        self,
        resume_id: UUID,
        normalized_skill: str,
    ) -> ExtractedSkill | None:
        """
        Retrieve a single extracted skill for a resume by normalized name.
        """
        return (
            self.db.query(ExtractedSkill)
            .filter(
                ExtractedSkill.resume_id == resume_id,
                ExtractedSkill.normalized_skill == normalized_skill,
            )
            .first()
        )

    def get_by_user_id(self, user_id: UUID) -> list[ExtractedSkill]:
        """
        Retrieve all extracted skills for a given user across all their resumes.
        """
        return (
            self.db.query(ExtractedSkill)
            .filter(ExtractedSkill.resume_id.in_(
                self.db.query(Resume.id).filter(Resume.user_id == user_id)
            ))
            .order_by(ExtractedSkill.count.desc(), ExtractedSkill.skill.asc())
            .all()
        )

    def delete_for_resume(self, resume_id: UUID) -> None:
        """
        Delete all extracted skills associated with a resume.
        """
        self.db.query(ExtractedSkill).filter(
            ExtractedSkill.resume_id == resume_id
        ).delete(synchronize_session=False)
        self.db.commit()

    def replace_for_resume(
        self,
        resume_id: UUID,
        skills: list[ExtractedSkill],
    ) -> list[ExtractedSkill]:
        """
        Replace the extracted skills for a resume with a fresh set.
        Deletes existing rows, bulk-inserts the new set, and returns them.
        """
        # Delete existing rows first (handles the unique constraint).
        self.delete_for_resume(resume_id)

        if not skills:
            return []

        self.db.add_all(skills)
        self.db.commit()

        return self.get_by_resume(resume_id)
