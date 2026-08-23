from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class JobCreateRequest(BaseModel):
    title: str
    company: str | None = None
    description: str


class JobUpdateRequest(BaseModel):
    title: str | None = None
    company: str | None = None
    description: str | None = None


class JobResponse(BaseModel):
    id: UUID
    recruiter_id: UUID
    title: str
    company: str | None
    description: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobListResponse(BaseModel):
    jobs: list[JobResponse]
