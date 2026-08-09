from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.ats_score import AtsScore
from app.models.resume import Resume
from app.models.user import User
from app.repositories.ats_score_repository import AtsScoreRepository
from app.repositories.extracted_skill_repository import ExtractedSkillRepository
from app.repositories.parsed_resume_repository import ParsedResumeRepository
from app.repositories.resume_repository import ResumeRepository
from app.utils.ats_scorer import AtsReport, compute_ats_score


class AtsScoreService:
    """
    Orchestrates the Module 8 ATS scoring workflow.

    The service verifies ownership, loads the resume along with its parsed
    data and extracted skills, delegates the actual scoring to the stateless
    engine in ``app/utils/ats_scorer.py``, and persists the resulting report.
    """

    def __init__(self, db: Session):
        self.resume_repo = ResumeRepository(db)
        self.parsed_repo = ParsedResumeRepository(db)
        self.skill_repo = ExtractedSkillRepository(db)
        self.ats_repo = AtsScoreRepository(db)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _resolve_owned_resume(self, user: User, resume_id: UUID) -> Resume:
        """
        Ensure the resume exists and belongs to the authenticated user.
        """
        resume = self.resume_repo.get_by_id(resume_id)

        if resume is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found.",
            )

        if resume.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this resume.",
            )

        return resume

    def _load_scoring_inputs(
        self,
        resume_id: UUID,
    ) -> dict:
        """
        Load the parsed resume and extracted skills needed for scoring.

        Returns a snapshot dict of plain values suitable for the scorer.
        """
        parsed = self.parsed_repo.get_by_resume_id(resume_id)

        if parsed is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="This resume has not been parsed yet. "
                       "Please parse it before computing an ATS score.",
            )

        extracted = self.skill_repo.get_by_resume(resume_id)

        return {
            "name": parsed.name,
            "email": parsed.email,
            "phone": parsed.phone,
            "summary": parsed.summary,
            "skills": parsed.skills,
            "education": parsed.education,
            "experience": parsed.experience,
            "projects": parsed.projects,
            "certifications": parsed.certifications,
            "raw_text": parsed.raw_text,
            "extracted_skills": [
                {
                    "skill": s.skill,
                    "normalized_skill": s.normalized_skill,
                    "category": s.category,
                    "count": s.count,
                    "confidence": s.confidence,
                }
                for s in extracted
            ],
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def compute_and_store(
        self,
        user: User,
        resume_id: UUID,
    ) -> AtsScore:
        """
        Compute the ATS score for a user-owned resume and persist it.

        Recomputing replaces the previously stored score for the resume.
        """
        self._resolve_owned_resume(user, resume_id)

        inputs = self._load_scoring_inputs(resume_id)

        report: AtsReport = compute_ats_score(**inputs)

        return self.ats_repo.replace_for_resume(
            resume_id,
            AtsScore(
                resume_id=resume_id,
                user_id=user.id,
                score=report.overall_score,
                category_scores=[
                    {
                        "name": c.name,
                        "score": c.score,
                        "max_score": c.max_score,
                        "weight": c.weight,
                        "feedback": c.feedback,
                    }
                    for c in report.category_scores
                ],
                feedback=report.feedback,
                score_breakdown=report.score_breakdown,
            ),
        )

    def get_score(
        self,
        user: User,
        resume_id: UUID,
    ) -> AtsScore:
        """
        Return the stored ATS score for a user-owned resume.

        Raises 404 if the resume does not exist or no score has been computed.
        """
        self._resolve_owned_resume(user, resume_id)

        score = self.ats_repo.get_by_resume(resume_id)

        if score is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No ATS score has been generated for this resume yet.",
            )

        return score
