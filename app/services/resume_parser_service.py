from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.config import settings
from app.models.parsed_resume import ParsedResume
from app.models.resume import Resume
from app.models.user import User
from app.repositories.resume_repository import ResumeRepository
from app.repositories.parsed_resume_repository import ParsedResumeRepository
from app.utils.docx_parser import extract_text_from_docx
from app.utils.pdf_parser import extract_text_from_pdf
from app.utils.resume_section_parser import parse_resume_text
from app.utils.file_handler import ALLOWED_EXTENSIONS
import os


class ResumeParserService:
    """
    Orchestrates resume text extraction and rule-based parsing.

    This is the Version 1 parser. It is intentionally decoupled from the
    upload flow so it can be swapped for a more advanced NLP/LLM parser
    later without affecting the rest of the application.
    """

    def __init__(self, db: Session):
        self.resume_repo = ResumeRepository(db)
        self.parsed_repo = ParsedResumeRepository(db)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _resolve_resume(self, user: User, resume_id: UUID) -> Resume:
        resume = self.resume_repo.get_by_id(resume_id)

        if resume is None or resume.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found.",
            )

        return resume

    def _extract_text(self, resume: Resume) -> str:
        """
        Extract plain text from the resume by file extension.
        """
        stored_name = resume.stored_name or ""
        ext = os.path.splitext(stored_name)[1].lower()

        file_path = Path(settings.UPLOAD_DIR) / stored_name

        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume file missing from storage.",
            )

        if ext == ".pdf":
            return extract_text_from_pdf(file_path)

        if ext == ".docx":
            return extract_text_from_docx(file_path)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported resume format.",
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def parse_resume(
        self,
        user: User,
        resume_id: UUID,
    ) -> ParsedResume:
        """
        Parse a resume owned by the user and persist the structured result.

        If an existing parsed record exists for that resume, it will be
        returned without re-parsing (idempotent by design).
        """
        resume = self._resolve_resume(user, resume_id)

        existing = self.parsed_repo.get_for_user(resume_id, user.id)
        if existing is not None:
            return existing

        raw_text = self._extract_text(resume)

        # Guard against pathological input sizes.
        raw_text = raw_text[: settings.MAX_RESUME_TEXT_CHARS]

        parsed = parse_resume_text(raw_text)

        record = ParsedResume(
            resume_id=resume.id,
            user_id=user.id,
            name=parsed.name or None,
            email=parsed.email or None,
            phone=parsed.phone or None,
            summary=parsed.summary or None,
            skills=parsed.skills or None,
            education=parsed.education or None,
            experience=parsed.experience or None,
            projects=parsed.projects or None,
            certifications=parsed.certifications or None,
            raw_text=raw_text or None,
        )

        return self.parsed_repo.create(record)

    def get_parsed_resume(
        self,
        user: User,
        resume_id: UUID,
    ) -> ParsedResume:
        """
        Retrieve an already-parsed resume for a user-owned resume.
        """
        self._resolve_resume(user, resume_id)

        record = self.parsed_repo.get_for_user(resume_id, user.id)

        if record is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="This resume has not been parsed yet.",
            )

        return record
