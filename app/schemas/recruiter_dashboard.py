from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class DashboardStats(BaseModel):
    total_jobs: int
    active_jobs: int
    total_candidates: int
    candidates_under_review: int
    shortlisted: int
    interviews: int
    selected: int


class JobSummary(BaseModel):
    id: str
    title: str
    company: str | None
    candidate_count: int
    avg_match_score: float | None
    shortlisted_count: int
    interview_count: int
    selected_count: int
    created_at: datetime


class RecentCandidate(BaseModel):
    id: str
    full_name: str
    email: str
    resume_id: str
    match_percentage: float | None
    status: str | None
    applied_at: datetime | None


class TopCandidate(BaseModel):
    id: str
    full_name: str
    email: str
    resume_id: str
    match_percentage: float | None
    matched_skills: list[str] | None
    missing_skills: list[str] | None
    status: str | None


class RecruiterDashboardResponse(BaseModel):
    statistics: DashboardStats
    jobs: list[JobSummary]
    recent_candidates: list[RecentCandidate]
    top_candidates: list[TopCandidate]
