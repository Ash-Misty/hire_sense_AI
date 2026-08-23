from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ApplicationStatus(str, Enum):
    applied = "applied"
    reviewing = "reviewing"
    shortlisted = "shortlisted"
    interview = "interview"
    selected = "selected"
    rejected = "rejected"


class ApplicationCreate(BaseModel):
    job_id: UUID
    candidate_id: UUID
    resume_id: UUID
    status: ApplicationStatus = ApplicationStatus.applied
    notes: str | None = None


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus
    notes: str | None = None


class ApplicationResponse(BaseModel):
    id: UUID
    recruiter_id: UUID
    job_id: UUID
    candidate_id: UUID
    resume_id: UUID
    status: ApplicationStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationSummary(BaseModel):
    total: int
    applied: int
    reviewing: int
    shortlisted: int
    interview: int
    selected: int
    rejected: int
