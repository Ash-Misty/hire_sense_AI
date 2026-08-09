from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session
from uuid import UUID

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.resume import ResumeListResponse
from app.schemas.resume import ResumeResponse
from app.schemas.resume import ResumeUploadResponse
from app.schemas.parsed_resume import ParsedResumeResponse
from app.schemas.parsed_resume import ResumeParseResponse
from app.schemas.user import MessageResponse
from app.schemas.extracted_skill import SkillExtractionResponse
from app.schemas.extracted_skill import SkillSummaryResponse
from app.schemas.extracted_skill import SkillCategorySummary
from app.services.resume_service import ResumeService
from app.services.resume_parser_service import ResumeParserService
from app.services.skill_extraction_service import SkillExtractionService

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


@router.post(
    "/parse/{resume_id}",
    response_model=ResumeParseResponse,
    status_code=200,
)
def parse_resume(
    resume_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ResumeParserService(db)

    record = service.parse_resume(current_user, resume_id)

    return ResumeParseResponse(
        message="Resume parsed successfully.",
        resume_id=record.resume_id,
        name=record.name,
        email=record.email,
        phone=record.phone,
        skills=record.skills,
        education=record.education,
        experience=record.experience,
        projects=record.projects,
        certifications=record.certifications,
    )


@router.get(
    "/parse/{resume_id}",
    response_model=ParsedResumeResponse,
    status_code=200,
)
def get_parsed_resume(
    resume_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ResumeParserService(db)

    record = service.get_parsed_resume(current_user, resume_id)

    return ParsedResumeResponse(
        id=record.id,
        resume_id=record.resume_id,
        name=record.name,
        email=record.email,
        phone=record.phone,
        summary=record.summary,
        skills=record.skills,
        education=record.education,
        experience=record.experience,
        projects=record.projects,
        certifications=record.certifications,
        parsed_at=record.parsed_at,
    )


@router.post(
    "/{resume_id}/skills/extract",
    response_model=SkillExtractionResponse,
    status_code=200,
)
def extract_skills_endpoint(
    resume_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SkillExtractionService(db)

    records = service.extract_and_store(current_user, resume_id)

    return SkillExtractionResponse(
        message="Skills extracted successfully.",
        resume_id=resume_id,
        total_skills=len(records),
        skills=records,
    )


@router.get(
    "/{resume_id}/skills",
    response_model=SkillExtractionResponse,
    status_code=200,
)
def get_extracted_skills(
    resume_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SkillExtractionService(db)

    records = service.get_skills(current_user, resume_id)

    return SkillExtractionResponse(
        message="Skills retrieved successfully.",
        resume_id=resume_id,
        total_skills=len(records),
        skills=records,
    )


@router.get(
    "/{resume_id}/skills/summary",
    response_model=SkillSummaryResponse,
    status_code=200,
)
def get_skill_summary(
    resume_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SkillExtractionService(db)

    grouped = service.get_category_summary(current_user, resume_id)

    categories = [
        SkillCategorySummary(
            category=category,
            skill_count=len(items),
            skills=[item["skill"] for item in items],
        )
        for category, items in grouped.items()
    ]

    total_skills = sum(len(items) for items in grouped.values())

    categories.sort(key=lambda c: -c.skill_count)

    return SkillSummaryResponse(
        resume_id=resume_id,
        total_skills=total_skills,
        categories=categories,
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
