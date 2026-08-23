from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.dependencies.roles import get_current_recruiter
from app.models.user import User
from app.schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationResponse
from app.schemas.job import JobCreateRequest, JobUpdateRequest, JobResponse, JobListResponse
from app.schemas.recruiter_dashboard import RecruiterDashboardResponse
from app.services.application_service import ApplicationService
from app.services.job_service import JobService
from app.services.recruiter_dashboard_service import RecruiterDashboardService

router = APIRouter(prefix="/recruiter", tags=["Recruiter Dashboard"])


@router.get(
    "/dashboard",
    response_model=RecruiterDashboardResponse,
)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_recruiter),
):
    service = RecruiterDashboardService(db)
    return service.get_dashboard(current_user)


@router.get(
    "/statistics",
    response_model=dict,
)
def get_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_recruiter),
):
    service = ApplicationService(db)
    return service.get_statistics(current_user)


@router.get(
    "/jobs",
    response_model=JobListResponse,
)
def get_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_recruiter),
):
    service = JobService(db)
    jobs = service.get_jobs(current_user)
    return JobListResponse(jobs=jobs)


@router.post(
    "/jobs",
    response_model=JobResponse,
    status_code=201,
)
def create_job(
    payload: JobCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_recruiter),
):
    service = JobService(db)
    return service.create_job(
        recruiter=current_user,
        title=payload.title,
        company=payload.company,
        description=payload.description,
    )


@router.get(
    "/jobs/{job_id}",
    response_model=JobResponse,
)
def get_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_recruiter),
):
    service = JobService(db)
    return service.get_job(current_user, job_id)


@router.put(
    "/jobs/{job_id}",
    response_model=JobResponse,
)
def update_job(
    job_id: UUID,
    payload: JobUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_recruiter),
):
    service = JobService(db)
    return service.update_job(
        recruiter=current_user,
        job_id=job_id,
        title=payload.title,
        company=payload.company,
        description=payload.description,
    )


@router.delete(
    "/jobs/{job_id}",
    status_code=204,
)
def delete_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_recruiter),
):
    service = JobService(db)
    service.delete_job(current_user, job_id)
    return None


@router.get(
    "/jobs/{job_id}/candidates",
    response_model=list[ApplicationResponse],
)
def get_job_candidates(
    job_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_recruiter),
):
    service = ApplicationService(db)
    applications, _ = service.get_candidates_for_job(
        recruiter=current_user,
        job_id=job_id,
        skip=skip,
        limit=limit,
    )
    return applications


@router.get(
    "/candidates/{candidate_id}",
    response_model=dict,
)
def get_candidate_details(
    candidate_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_recruiter),
):
    service = ApplicationService(db)
    applications = service.get_candidate_applications(current_user, candidate_id)
    if not applications:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found.",
        )
    return {"candidate_id": str(candidate_id), "applications": applications}


@router.patch(
    "/applications/{application_id}/status",
    response_model=ApplicationResponse,
)
def update_application_status(
    application_id: UUID,
    payload: ApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_recruiter),
):
    service = ApplicationService(db)
    return service.update_application_status(
        recruiter=current_user,
        application_id=application_id,
        update_data=payload,
    )
