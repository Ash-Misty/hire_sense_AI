from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User
from app.repositories.job_description_repository import JobDescriptionRepository
from app.schemas.job_description import JobDescriptionCreate, JobDescriptionListResponse, JobDescriptionResponse
from app.schemas.job_match import JobMatchResponse
from app.services.job_matching_service import JobMatchingService
from app.models.job_description import JobDescription
from app.models.job_match import JobMatch

router = APIRouter(prefix="/job", tags=["Job Matching"])


@router.post("/descriptions", response_model=JobDescriptionResponse, status_code=201)
def create_job_description(
    payload: JobDescriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = JobDescriptionRepository(db)
    record = JobDescription(
        user_id=current_user.id,
        title=payload.title,
        company=payload.company,
        description=payload.description,
    )
    saved = repo.create(record)
    return saved


@router.get("/descriptions", response_model=JobDescriptionListResponse)
def get_job_descriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = JobDescriptionRepository(db)
    records = repo.get_all_by_user(current_user.id)
    return JobDescriptionListResponse(job_descriptions=records)


@router.get("/descriptions/{job_id}", response_model=JobDescriptionResponse)
def get_job_description(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = JobDescriptionRepository(db)
    record = repo.get_by_id(job_id, current_user.id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found.")
    return record


@router.delete("/descriptions/{job_id}", status_code=204)
def delete_job_description(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = JobDescriptionRepository(db)
    record = repo.get_by_id(job_id, current_user.id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found.")
    repo.delete(record)
    return None


@router.post("/resumes/{resume_id}/match/{job_id}", response_model=JobMatchResponse)
def match_resume_against_job(
    resume_id: UUID,
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = JobMatchingService(db)
    result = service.match_resume_to_job_description(current_user, resume_id, job_id)
    return JobMatchResponse(**result)


@router.get("/matches", response_model=list[JobMatchResponse])
def get_all_matches(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = JobMatchingService(db)
    matches = service.get_match_history(current_user)
    return [JobMatchResponse(**{
        "id": str(item.id),
        "resume_id": str(item.resume_id),
        "job_description_id": str(item.job_description_id),
        "match_percentage": item.match_percentage,
        "matched_skills": item.matched_skills,
        "missing_skills": item.missing_skills,
        "extra_skills": item.extra_skills,
        "category_scores": item.category_scores,
        "created_at": item.created_at,
    }) for item in matches]
