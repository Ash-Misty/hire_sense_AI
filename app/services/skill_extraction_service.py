from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.extracted_skill import ExtractedSkill
from app.models.resume import Resume
from app.models.user import User
from app.repositories.extracted_skill_repository import ExtractedSkillRepository
from app.repositories.parsed_resume_repository import ParsedResumeRepository
from app.repositories.resume_repository import ResumeRepository
from app.utils.skill_extractor import ExtractionResult, extract_skills


class SkillExtractionService:
    """
    Orchestrates the Module 7 skill-extraction workflow.

    The service operates on an already-parsed resume (Module 6). It verifies
    ownership, runs the deterministic extraction engine against the parsed raw
    text, persists the structured results, and exposes retrieval + category
    summary helpers for the API layer.
    """

    def __init__(self, db: Session):
        self.resume_repo = ResumeRepository(db)
        self.parsed_repo = ParsedResumeRepository(db)
        self.skill_repo = ExtractedSkillRepository(db)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _resolve_owned_resume(self, user: User, resume_id: UUID) -> Resume:
        """
        Ensure the resume exists and belongs to the authenticated user.
        """
        resume = self.resume_repo.get_by_id(resume_id)

        if resume is None or resume.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found.",
            )

        return resume

    def _resolve_parsed_text(self, user: User, resume_id: UUID) -> tuple[str, str]:
        """
        Return (raw_text, skills_section_text) from the parsed resume.
        Raises 404/400 if the resume has not been parsed.
        """
        parsed = self.parsed_repo.get_for_user(resume_id, user.id)

        if parsed is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="This resume has not been parsed yet. "
                       "Please parse it before extracting skills.",
            )

        raw_text = parsed.raw_text or ""
        skills_section_text = ""

        # The parsed model stores skills as a JSONB list (flat). Reconstructing
        # a skills-section string is not needed for the extractor, which scans
        # the full raw text. We leave skills_section_text empty to keep the
        # deterministic scoring based purely on full-text frequency.
        return raw_text, skills_section_text

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def extract_and_store(
        self,
        user: User,
        resume_id: UUID,
    ) -> list[ExtractedSkill]:
        """
        Extract skills from a parsed resume, persist them, and return the
        stored records.

        Extraction is idempotent — running it multiple times replaces the
        stored set rather than creating duplicates.
        """
        self._resolve_owned_resume(user, resume_id)

        raw_text, skills_section = self._resolve_parsed_text(user, resume_id)

        result: ExtractionResult = extract_skills(raw_text, skills_section)

        records = [
            ExtractedSkill(
                resume_id=resume_id,
                skill=s.skill,
                normalized_skill=s.normalized_skill,
                category=s.category,
                count=s.count,
                confidence=s.confidence,
            )
            for s in result.skills
        ]

        return self.skill_repo.replace_for_resume(resume_id, records)

    def get_skills(
        self,
        user: User,
        resume_id: UUID,
    ) -> list[ExtractedSkill]:
        """
        Return the stored extracted skills for a user-owned resume.
        Returns an empty list if none have been extracted yet.
        """
        self._resolve_owned_resume(user, resume_id)
        return self.skill_repo.get_by_resume(resume_id)

    def get_category_summary(
        self,
        user: User,
        resume_id: UUID,
    ) -> dict[str, list[dict]]:
        """
        Group stored skills by category for a user-owned resume.
        Returns a dict keyed by category name -> list of skill dicts.
        """
        skills = self.get_skills(user, resume_id)

        grouped: dict[str, list[dict]] = {}
        for skill in skills:
            grouped.setdefault(skill.category, []).append(
                {
                    "skill": skill.skill,
                    "normalized_skill": skill.normalized_skill,
                    "count": skill.count,
                    "confidence": skill.confidence,
                }
            )

        return grouped
