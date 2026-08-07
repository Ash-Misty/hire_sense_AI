from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ResumeResponse(BaseModel):
    id: UUID
    original_name: str
    stored_name: str
    file_size: int
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumeUploadResponse(BaseModel):
    message: str
    file_name: str
    file_size: int


class ResumeListResponse(BaseModel):
    resumes: list[ResumeResponse]
