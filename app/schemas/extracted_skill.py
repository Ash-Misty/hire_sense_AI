from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ExtractedSkillResponse(BaseModel):
    id: UUID
    resume_id: UUID
    skill: str
    normalized_skill: str
    category: str
    count: int
    confidence: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SkillExtractionResponse(BaseModel):
    message: str
    resume_id: UUID
    total_skills: int
    skills: list[ExtractedSkillResponse]


class SkillCategorySummary(BaseModel):
    category: str
    skill_count: int
    skills: list[str]


class SkillSummaryResponse(BaseModel):
    resume_id: UUID
    total_skills: int
    categories: list[SkillCategorySummary]
