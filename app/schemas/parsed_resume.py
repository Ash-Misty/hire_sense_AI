from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ParsedResumeResponse(BaseModel):
    id: UUID
    resume_id: UUID
    name: str | None
    email: str | None
    phone: str | None
    summary: str | None
    skills: list[str] | None
    education: list[dict] | None
    experience: list[dict] | None
    projects: list[dict] | None
    certifications: list[str] | None
    parsed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeParseResponse(BaseModel):
    message: str
    resume_id: UUID
    name: str | None
    email: str | None
    phone: str | None
    skills: list[str] | None
    education: list[dict] | None
    experience: list[dict] | None
    projects: list[dict] | None
    certifications: list[str] | None
