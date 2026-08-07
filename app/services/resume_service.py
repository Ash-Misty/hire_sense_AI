import os
from pathlib import Path

from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.config import settings
from app.models.user import User
from app.models.resume import Resume
from app.repositories.resume_repository import ResumeRepository
from app.utils.file_handler import (
    ensure_upload_dir,
    save_upload,
    validate_file,
)


class ResumeService:
    """
    Handles all resume upload and management business logic.
    """

    def __init__(self, db: Session):
        self.repo = ResumeRepository(db)
        self.upload_dir = ensure_upload_dir(settings.UPLOAD_DIR)

    def upload_resume(
        self,
        user: User,
        file: UploadFile,
    ) -> dict:
        """
        Validate and save an uploaded resume, then store its metadata.

        Returns a dict describing the stored file.
        """
        # 1. Validate extension
        validate_file(file)

        # 2. Save the file to disk (also enforces size limit)
        stored_name = save_upload(file, self.upload_dir)

        file_size = os.path.getsize(
            Path(self.upload_dir) / stored_name
        )

        # 3. Persist metadata
        resume = Resume(
            user_id=user.id,
            original_name=file.filename or "",
            stored_name=stored_name,
            file_path=str(Path(settings.UPLOAD_DIR) / stored_name),
            file_size=file_size,
        )

        self.repo.create(resume)

        return {
            "message": "Resume uploaded successfully.",
            "file_name": stored_name,
            "file_size": file_size,
        }

    def get_user_resumes(self, user: User) -> list[Resume]:
        """
        Return all resumes belonging to a user.
        """
        return self.repo.get_by_user(user.id)

    def get_resume_for_user(
        self,
        user: User,
        resume_id: UUID,
    ) -> Resume:
        """
        Retrieve a resume only if it belongs to the user.
        """
        resume = self.repo.get_by_id(resume_id)

        if resume is None or resume.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found.",
            )

        return resume

    def delete_resume(
        self,
        user: User,
        resume_id: UUID,
    ) -> None:
        """
        Delete a resume record and remove its file from disk.
        """
        resume = self.get_resume_for_user(user, resume_id)

        # Remove file from disk (best effort)
        file_path = Path(settings.UPLOAD_DIR) / resume.stored_name
        file_path.unlink(missing_ok=True)

        self.repo.delete(resume)

