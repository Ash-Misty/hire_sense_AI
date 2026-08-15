from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.base import Base


class JobMatch(Base):
    __tablename__ = "job_matches"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    resume_id = Column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    job_description_id = Column(
        UUID(as_uuid=True),
        ForeignKey("job_descriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    match_percentage = Column(
        Float,
        nullable=False,
        default=0.0,
    )

    matched_skills = Column(
        JSONB,
        nullable=False,
        default=list,
    )

    missing_skills = Column(
        JSONB,
        nullable=False,
        default=list,
    )

    extra_skills = Column(
        JSONB,
        nullable=False,
        default=list,
    )

    category_scores = Column(
        JSONB,
        nullable=False,
        default=dict,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
