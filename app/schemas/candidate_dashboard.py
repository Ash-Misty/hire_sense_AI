from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CandidateProfileSummary(BaseModel):
    id: UUID
    full_name: str
    email: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeDashboardSummary(BaseModel):
    total_resumes: int
    parsed_resumes: int
    latest_resume_name: str | None = None
    latest_parsed_name: str | None = None
    resumes_with_skills: int = 0


class SkillDashboardSummary(BaseModel):
    total_skills: int
    top_skills: list[str] = []
    skills_by_category: dict[str, list[str]] = {}


class AtsDashboardSummary(BaseModel):
    latest_score: float | None = None
    highest_score: float | None = None
    average_score: float | None = None
    total_analyzed: int = 0


class JobMatchDashboardSummary(BaseModel):
    total_matches: int
    highest_match_percentage: float | None = None
    average_match_percentage: float | None = None
    recent_matches: list[dict] = []


class InterviewDashboardSummary(BaseModel):
    total_questions: int
    recent_questions: list[dict] = []


class RecentActivity(BaseModel):
    activity_type: str
    description: str
    timestamp: datetime


class CandidateDashboardResponse(BaseModel):
    profile: CandidateProfileSummary
    resume_summary: ResumeDashboardSummary
    skills: SkillDashboardSummary
    ats_summary: AtsDashboardSummary | None = None
    job_matches: JobMatchDashboardSummary
    interview: InterviewDashboardSummary
    recent_activity: list[RecentActivity] = []
