from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class GenerateQuestionsRequest(BaseModel):
    resume_id: UUID
    job_match_id: UUID | None = None
    max_questions: int = 15


class QuestionResponse(BaseModel):
    id: UUID
    question: str
    category: str
    skill: str | None = None
    difficulty: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuestionCategorySummary(BaseModel):
    category: str
    count: int


class GenerateQuestionsResponse(BaseModel):
    message: str
    resume_id: UUID
    job_match_id: UUID | None = None
    total_questions: int
    questions: list[QuestionResponse]
    categories: list[QuestionCategorySummary]
