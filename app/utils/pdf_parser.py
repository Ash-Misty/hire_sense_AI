from pathlib import Path

from fastapi import HTTPException, status
from pypdf import PdfReader


def extract_text_from_pdf(file_path: str | Path) -> str:
    """
    Extract plain text from a PDF resume.

    Only the first page is used, since resumes are typically one page.
    Raises HTTPException (422) for corrupted/unreadable PDFs.
    """
    try:
        reader = PdfReader(str(file_path))

        pages = []
        for page in reader.pages[:1]:
            text = page.extract_text() or ""
            pages.append(text)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not read the PDF file. It may be corrupted or "
                   "scanned (image-based).",
        )

    return "\n".join(pages)

