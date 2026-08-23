from datetime import datetime
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ats_score import AtsScore
from app.models.extracted_skill import ExtractedSkill
from app.models.interview_question import InterviewQuestion
from app.models.job_match import JobMatch
from app.models.parsed_resume import ParsedResume
from app.models.resume import Resume
from app.models.user import User
from app.repositories.ats_score_repository import AtsScoreRepository
from app.repositories.extracted_skill_repository import ExtractedSkillRepository
from app.repositories.interview_question_repository import InterviewQuestionRepository
from app.repositories.job_match_repository import JobMatchRepository
from app.repositories.parsed_resume_repository import ParsedResumeRepository
from app.repositories.resume_repository import ResumeRepository


class CandidateDashboardService:
    """
    Aggregates candidate data for the dashboard.

    All queries are scoped to the authenticated user. No data from other
    users is exposed.
    """

    def __init__(self, db: Session):
        self.db = db
        self.resume_repo = ResumeRepository(db)
        self.parsed_repo = ParsedResumeRepository(db)
        self.skill_repo = ExtractedSkillRepository(db)
        self.ats_repo = AtsScoreRepository(db)
        self.job_match_repo = JobMatchRepository(db)
        self.interview_repo = InterviewQuestionRepository(db)

    def get_dashboard(self, user: User) -> dict:
        profile = self._build_profile(user)
        resume_summary = self._build_resume_summary(user.id)
        skills = self._build_skill_summary(user.id)
        ats_summary = self._build_ats_summary(user.id)
        job_matches = self._build_job_match_summary(user.id)
        interview = self._build_interview_summary(user.id)
        recent_activity = self._build_recent_activity(user.id)

        return {
            "profile": profile,
            "resume_summary": resume_summary,
            "skills": skills,
            "ats_summary": ats_summary,
            "job_matches": job_matches,
            "interview": interview,
            "recent_activity": recent_activity,
        }

    def _build_profile(self, user: User) -> dict:
        return {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at,
        }

    def _build_resume_summary(self, user_id: UUID) -> dict:
        total_resumes = (
            self.db.query(func.count(Resume.id))
            .filter(Resume.user_id == user_id)
            .scalar()
            or 0
        )

        parsed_resumes = (
            self.db.query(func.count(func.distinct(ParsedResume.resume_id)))
            .filter(ParsedResume.user_id == user_id)
            .scalar()
            or 0
        )

        latest_resume = (
            self.db.query(Resume.original_name)
            .filter(Resume.user_id == user_id)
            .order_by(Resume.uploaded_at.desc())
            .first()
        )

        latest_parsed = (
            self.db.query(Resume.original_name)
            .join(ParsedResume, ParsedResume.resume_id == Resume.id)
            .filter(ParsedResume.user_id == user_id)
            .order_by(ParsedResume.parsed_at.desc())
            .first()
        )

        resumes_with_skills = (
            self.db.query(func.count(func.distinct(ExtractedSkill.resume_id)))
            .filter(ExtractedSkill.resume_id.in_(
                self.db.query(Resume.id).filter(Resume.user_id == user_id)
            ))
            .scalar()
            or 0
        )

        return {
            "total_resumes": total_resumes,
            "parsed_resumes": parsed_resumes,
            "latest_resume_name": latest_resume.original_name if latest_resume else None,
            "latest_parsed_name": latest_parsed.original_name if latest_parsed else None,
            "resumes_with_skills": resumes_with_skills,
        }

    def _build_skill_summary(self, user_id: UUID) -> dict:
        skills = self.skill_repo.get_by_user_id(user_id)

        total_skills = len(skills)
        top_skills = [s.skill for s in skills[:10]]

        skills_by_category: dict[str, list[str]] = {}
        for skill in skills:
            skills_by_category.setdefault(skill.category, []).append(skill.skill)

        return {
            "total_skills": total_skills,
            "top_skills": top_skills,
            "skills_by_category": skills_by_category,
        }

    def _build_ats_summary(self, user_id: UUID) -> dict | None:
        scores = self.ats_repo.get_by_user_id(user_id)

        if not scores:
            return None

        latest = scores[0] if scores else None
        highest = max(scores, key=lambda s: s.score) if scores else None
        average = sum(s.score for s in scores) / len(scores) if scores else None

        return {
            "latest_score": latest.score if latest else None,
            "highest_score": highest.score if highest else None,
            "average_score": round(average, 2) if average is not None else None,
            "total_analyzed": len(scores),
        }

    def _build_job_match_summary(self, user_id: UUID) -> dict:
        matches = self.job_match_repo.get_all_by_user(user_id)

        total_matches = len(matches)
        highest_match = max((m.match_percentage for m in matches), default=None)
        average_match = (
            round(sum(m.match_percentage for m in matches) / len(matches), 2)
            if matches
            else None
        )

        recent_matches = [
            {
                "id": str(m.id),
                "match_percentage": m.match_percentage,
                "matched_skills": m.matched_skills or [],
                "missing_skills": m.missing_skills or [],
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in matches[:5]
        ]

        return {
            "total_matches": total_matches,
            "highest_match_percentage": highest_match,
            "average_match_percentage": average_match,
            "recent_matches": recent_matches,
        }

    def _build_interview_summary(self, user_id: UUID) -> dict:
        questions = self.interview_repo.get_by_user(user_id)

        recent_questions = [
            {
                "id": str(q.id),
                "question": q.question,
                "category": q.category,
                "skill": q.skill,
                "difficulty": q.difficulty,
                "created_at": q.created_at.isoformat() if q.created_at else None,
            }
            for q in questions[:5]
        ]

        return {
            "total_questions": len(questions),
            "recent_questions": recent_questions,
        }

    def _build_recent_activity(self, user_id: UUID) -> list[dict]:
        activities: list[tuple[datetime, str, str]] = []

        latest_resume = (
            self.db.query(Resume.uploaded_at)
            .filter(Resume.user_id == user_id)
            .order_by(Resume.uploaded_at.desc())
            .first()
        )
        if latest_resume:
            activities.append((latest_resume.uploaded_at, "resume_upload", "Resume uploaded"))

        latest_parsed = (
            self.db.query(ParsedResume.parsed_at)
            .filter(ParsedResume.user_id == user_id)
            .order_by(ParsedResume.parsed_at.desc())
            .first()
        )
        if latest_parsed:
            activities.append((latest_parsed.parsed_at, "resume_parsed", "Resume parsed"))

        latest_skills = (
            self.db.query(ExtractedSkill.created_at)
            .filter(ExtractedSkill.resume_id.in_(
                self.db.query(Resume.id).filter(Resume.user_id == user_id)
            ))
            .order_by(ExtractedSkill.created_at.desc())
            .first()
        )
        if latest_skills:
            activities.append((latest_skills.created_at, "skills_extracted", "Skills extracted"))

        latest_ats = (
            self.db.query(AtsScore.created_at)
            .filter(AtsScore.user_id == user_id)
            .order_by(AtsScore.created_at.desc())
            .first()
        )
        if latest_ats:
            activities.append((latest_ats.created_at, "ats_analysis", "ATS analysis completed"))

        latest_match = (
            self.db.query(JobMatch.created_at)
            .filter(JobMatch.user_id == user_id)
            .order_by(JobMatch.created_at.desc())
            .first()
        )
        if latest_match:
            activities.append((latest_match.created_at, "job_matched", "Job description matched"))

        latest_question = (
            self.db.query(InterviewQuestion.created_at)
            .filter(InterviewQuestion.user_id == user_id)
            .order_by(InterviewQuestion.created_at.desc())
            .first()
        )
        if latest_question:
            activities.append((latest_question.created_at, "interview_prep", "Interview questions generated"))

        activities.sort(key=lambda x: x[0], reverse=True)

        return [
            {
                "activity_type": activity_type,
                "description": description,
                "timestamp": timestamp,
            }
            for timestamp, activity_type, description in activities[:10]
        ]
