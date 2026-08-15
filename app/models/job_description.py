from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.base import Base


class JobDescription(Base):
    __tablename__ = "job_descriptions"
    __table_args__ = (
        Index("ix_job_descriptions_user_created", "user_id", "created_at"),
    )

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

    title = Column(
        String(255),
        nullable=False,
        index=True,
    )

    company = Column(
        String(255),
        nullable=True,
        index=True,
    )

    description = Column(
        Text,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
