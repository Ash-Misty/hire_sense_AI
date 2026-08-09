from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CategoryScore(BaseModel):
    name: str
    score: float
    max_score: float
    weight: float
    feedback: list[str] = []


class AtsScoreResponse(BaseModel):
    id: UUID
    resume_id: UUID
    score: float
    category_scores: list[CategoryScore]
    feedback: list[str]
    score_breakdown: dict
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
