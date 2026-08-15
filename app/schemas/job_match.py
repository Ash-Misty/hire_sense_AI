from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class JobMatchRequest(BaseModel):
    resume_id: UUID
    job_description_id: UUID


class JobMatchResponse(BaseModel):
    id: UUID
    resume_id: UUID
    job_description_id: UUID
    title: str | None = None
    company: str | None = None
    match_percentage: float
    matched_skills: list[str]
    missing_skills: list[str]
    extra_skills: list[str]
    category_scores: dict[str, float]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MatchedSkill(BaseModel):
    skill: str


class MissingSkill(BaseModel):
    skill: str


class CategoryScore(BaseModel):
    name: str
    score: float
