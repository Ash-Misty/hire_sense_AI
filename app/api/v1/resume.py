from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session
from uuid import UUID

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.resume import ResumeListResponse
from app.schemas.resume import ResumeResponse
from app.schemas.resume import ResumeUploadResponse
from app.schemas.user import MessageResponse
from app.services.resume_service import ResumeService

router = APIRouter(
    prefix="/resume",
    tags=["Resume"],
)


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=201,
)
def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ResumeService(db)

    return service.upload_resume(current_user, file)


@router.get(
    "",
    response_model=ResumeListResponse,
)
def list_my_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ResumeService(db)

    resumes = service.get_user_resumes(current_user)

    return ResumeListResponse(
        resumes=[
            ResumeResponse(
                id=r.id,
                original_name=r.original_name,
                stored_name=r.stored_name,
                file_size=r.file_size,
                uploaded_at=r.uploaded_at,
            )
            for r in resumes
        ]
    )


@router.delete(
    "/{resume_id}",
    response_model=MessageResponse,
)
def delete_resume(
    resume_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ResumeService(db)

    service.delete_resume(current_user, resume_id)

    return MessageResponse(
        message="Resume deleted successfully."
    )
