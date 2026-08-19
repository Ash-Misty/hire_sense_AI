from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.interview_question import InterviewQuestion
from app.models.job_match import JobMatch
from app.models.parsed_resume import ParsedResume
from app.models.resume import Resume
from app.models.user import User
from app.repositories.extracted_skill_repository import ExtractedSkillRepository
from app.repositories.interview_question_repository import InterviewQuestionRepository
from app.repositories.job_match_repository import JobMatchRepository
from app.repositories.parsed_resume_repository import ParsedResumeRepository
from app.repositories.resume_repository import ResumeRepository
from app.utils.question_generator import generate_questions


class InterviewQuestionService:
    def __init__(self, db: Session):
        self.db = db
        self.resume_repo = ResumeRepository(db)
        self.parsed_repo = ParsedResumeRepository(db)
        self.skill_repo = ExtractedSkillRepository(db)
        self.job_match_repo = JobMatchRepository(db)
        self.question_repo = InterviewQuestionRepository(db)

    def _resolve_owned_resume(self, user: User, resume_id: UUID) -> Resume:
        resume = self.resume_repo.get_by_id(resume_id)
        if resume is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")
        if resume.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this resume.")
        return resume

    def _get_parsed_resume(self, user: User, resume_id: UUID) -> ParsedResume | None:
        return self.parsed_repo.get_for_user(resume_id, user.id)

    def _get_extracted_skills(self, resume_id: UUID) -> list[str]:
        skills = self.skill_repo.get_by_resume(resume_id)
        if skills:
            return [record.skill for record in skills]
        return []

    def _get_job_match(self, user: User, job_match_id: UUID) -> JobMatch | None:
        return self.job_match_repo.get_by_id(job_match_id, user.id)

    def generate_questions(
        self,
        user: User,
        resume_id: UUID,
        job_match_id: UUID | None = None,
        max_questions: int = 15,
    ) -> tuple[list[InterviewQuestion], list[dict]]:
        resume = self._resolve_owned_resume(user, resume_id)
        parsed = self._get_parsed_resume(user, resume_id)
        if parsed is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="This resume has not been parsed yet. Please parse it before generating questions.",
            )

        candidate_skills = self._get_extracted_skills(resume_id)
        if not candidate_skills:
            candidate_skills = [
                "Python",
                "FastAPI",
                "PostgreSQL",
                "Docker",
                "AWS",
                "Kubernetes",
                "React",
                "JavaScript",
                "SQL",
                "Git",
            ]

        parsed_resume_data: dict = {}
        if parsed:
            parsed_resume_data = {
                "summary": parsed.summary or "",
                "experience": parsed.experience or [],
                "projects": parsed.projects or [],
                "education": parsed.education or [],
            }

        job_match_data: dict | None = None
        if job_match_id:
            job_match = self._get_job_match(user, job_match_id)
            if job_match is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Job match not found.",
                )
            job_match_data = {
                "matched_skills": job_match.matched_skills or [],
                "missing_skills": job_match.missing_skills or [],
                "extra_skills": job_match.extra_skills or [],
            }

        generated = generate_questions(
            candidate_skills=candidate_skills,
            parsed_resume=parsed_resume_data if parsed_resume_data else None,
            job_match=job_match_data,
            max_questions=max_questions,
        )

        # Delete existing questions for this resume (regenerate behavior).
        self.question_repo.delete_by_resume(resume_id, user.id)

        question_records = [
            InterviewQuestion(
                user_id=user.id,
                resume_id=resume_id,
                job_match_id=job_match_id,
                question=item["question"],
                category=item["category"],
                skill=item.get("skill"),
                difficulty=item["difficulty"],
            )
            for item in generated
        ]

        saved = self.question_repo.create_many(question_records)
        return saved, generated

    def get_questions(self, user: User, resume_id: UUID) -> list[InterviewQuestion]:
        self._resolve_owned_resume(user, resume_id)
        return self.question_repo.get_by_resume(resume_id, user.id)

    def delete_questions(self, user: User, resume_id: UUID) -> None:
        self._resolve_owned_resume(user, resume_id)
        self.question_repo.delete_by_resume(resume_id, user.id)
