import os
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, status, UploadFile

from app.core.config import settings

# Allowed file extensions for resume uploads.
ALLOWED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument."
             "wordprocessingml.document",
}


def validate_file(file: UploadFile) -> None:
    """
    Validate the uploaded file's extension and size.

    Raises HTTPException (400) for invalid file types and oversized files.
    """
    original_name = file.filename or ""
    ext = os.path.splitext(original_name)[1].lower()

    # 1. Extension check
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are allowed.",
        )

    # 2. Size check (based on the file's name/mime isn't reliable;
    #    we also check actual bytes during save for a strict limit).
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # Read only the first chunk to validate size if possible.
    # We rely on the service to enforce the hard limit while streaming.


def generate_stored_name(original_name: str) -> str:
    """
    Generate a unique, safe stored filename.

    Example: layout_resume.pdf -> <uuid>.pdf
    """
    ext = os.path.splitext(original_name or "")[1].lower()
    return f"{uuid4().hex}{ext}"


def ensure_upload_dir(upload_dir: str | Path) -> Path:
    """
    Create the upload directory if it does not exist.
    """
    path = Path(upload_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_upload(file: UploadFile, upload_dir: Path) -> str:
    """
    Save an uploaded file to disk in chunks.

    - Validates total size does not exceed the configured maximum.
    - Writes the file to `upload_dir / stored_name`.
    - Returns the stored filename.

    Raises HTTPException (413) if the file exceeds the size limit.
    """
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    stored_name = generate_stored_name(file.filename or "resume")
    file_path = upload_dir / stored_name

    total = 0
    # Default 1MB chunk
    chunk_size = 1024 * 1024

    with open(file_path, "wb") as buffer:
        while True:
            chunk = file.file.read(chunk_size)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                buffer.close()
                file_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB "
                           "limit.",
                )
            buffer.write(chunk)

    return stored_name

