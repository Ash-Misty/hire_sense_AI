from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.extracted_skill import ExtractedSkill
from app.models.job_description import JobDescription
from app.models.job_match import JobMatch
from app.models.parsed_resume import ParsedResume
from app.models.resume import Resume
from app.models.user import User
from app.repositories.extracted_skill_repository import ExtractedSkillRepository
from app.repositories.job_description_repository import JobDescriptionRepository
from app.repositories.job_match_repository import JobMatchRepository
from app.repositories.parsed_resume_repository import ParsedResumeRepository
from app.repositories.resume_repository import ResumeRepository
from app.services.skill_extraction_service import SkillExtractionService
from app.utils.job_skill_extractor import extract_job_skills
from app.utils.matching_engine import calculate_match


class JobMatchingService:
    def __init__(self, db: Session):
        self.db = db
        self.resume_repo = ResumeRepository(db)
        self.parsed_repo = ParsedResumeRepository(db)
        self.skill_repo = ExtractedSkillRepository(db)
        self.job_description_repo = JobDescriptionRepository(db)
        self.job_match_repo = JobMatchRepository(db)
        self.skill_service = SkillExtractionService(db)

    def _resolve_owned_resume(self, user: User, resume_id: UUID) -> Resume:
        resume = self.resume_repo.get_by_id(resume_id)
        if resume is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")
        if resume.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this resume.")
        return resume

    def _resolve_owned_job_description(self, user: User, job_id: UUID) -> JobDescription:
        job = self.job_description_repo.get_by_id(job_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found.")
        if job.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this job description.")
        return job

    def _get_resume_skill_names(self, user: User, resume_id: UUID) -> list[str]:
        skills = self.skill_repo.get_by_resume(resume_id)
        if skills:
            return [record.skill for record in skills]
        parsed = self.parsed_repo.get_by_resume_id(resume_id)
        if parsed is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This resume has not been parsed yet.")
        extracted = self.skill_service.extract_and_store(user, resume_id)
        return [record.skill for record in extracted]

    def match_resume_to_job_description(self, user: User, resume_id: UUID, job_id: UUID) -> dict:
        resume = self._resolve_owned_resume(user, resume_id)
        job_description = self._resolve_owned_job_description(user, job_id)

        parsed = self.parsed_repo.get_by_resume_id(resume_id)
        if parsed is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This resume has not been parsed yet.")

        candidate_skills = self._get_resume_skill_names(user, resume_id)
        required_skills = extract_job_skills(job_description.description)

        if not required_skills and not candidate_skills:
            result = {"matched_skills": [], "missing_skills": [], "extra_skills": [], "match_percentage": 0.0, "category_scores": {}}
        else:
            result = calculate_match(candidate_skills, required_skills)

        match_record = JobMatch(
            user_id=user.id,
            resume_id=resume_id,
            job_description_id=job_id,
            match_percentage=result["match_percentage"],
            matched_skills=result["matched_skills"],
            missing_skills=result["missing_skills"],
            extra_skills=result["extra_skills"],
            category_scores=result["category_scores"],
        )
        self.db.add(match_record)
        self.db.commit()
        self.db.refresh(match_record)

        return {
            "id": str(match_record.id),
            "resume_id": str(resume.id),
            "job_description_id": str(job_description.id),
            "title": job_description.title,
            "company": job_description.company,
            "match_percentage": result["match_percentage"],
            "matched_skills": result["matched_skills"],
            "missing_skills": result["missing_skills"],
            "extra_skills": result["extra_skills"],
            "category_scores": result["category_scores"],
            "created_at": match_record.created_at,
        }

    def get_match_history(self, user: User, resume_id: UUID | None = None) -> list[JobMatch]:
        if resume_id is not None:
            self._resolve_owned_resume(user, resume_id)
            return self.job_match_repo.get_by_resume(resume_id, user.id)
        return self.job_match_repo.get_all_by_user(user.id)

    def get_match_by_id(self, user: User, match_id: UUID) -> JobMatch:
        match = self.job_match_repo.get_by_id(match_id, user.id)
        if match is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match result not found.")
        return match
