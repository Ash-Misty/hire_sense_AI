from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.candidate_dashboard import CandidateDashboardResponse
from app.services.candidate_dashboard_service import CandidateDashboardService

router = APIRouter(prefix="/candidate", tags=["Candidate Dashboard"])


@router.get("/dashboard", response_model=CandidateDashboardResponse)
def get_candidate_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CandidateDashboardResponse:
    service = CandidateDashboardService(db)
    dashboard = service.get_dashboard(current_user)
    return CandidateDashboardResponse(**dashboard)
