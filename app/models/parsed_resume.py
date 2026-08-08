from uuid import uuid4

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.base import Base


class ParsedResume(Base):
    __tablename__ = "parsed_resumes"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    resume_id = Column(
        UUID(as_uuid=True),
        ForeignKey("resumes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name = Column(
        String(255),
        nullable=True,
    )

    email = Column(
        String(255),
        nullable=True,
    )

    phone = Column(
        String(64),
        nullable=True,
    )

    summary = Column(
        Text,
        nullable=True,
    )

    skills = Column(
        JSONB,
        nullable=True,
    )

    education = Column(
        JSONB,
        nullable=True,
    )

    experience = Column(
        JSONB,
        nullable=True,
    )

    projects = Column(
        JSONB,
        nullable=True,
    )

    certifications = Column(
        JSONB,
        nullable=True,
    )

    raw_text = Column(
        Text,
        nullable=True,
    )

    parsed_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
