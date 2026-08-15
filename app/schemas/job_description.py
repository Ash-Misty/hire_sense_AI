from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class JobDescriptionCreate(BaseModel):
    title: str
    company: str | None = None
    description: str


class JobDescriptionResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    company: str | None = None
    description: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobDescriptionListResponse(BaseModel):
    job_descriptions: list[JobDescriptionResponse]
