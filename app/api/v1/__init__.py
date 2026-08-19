from .auth import router as auth_router
from .interview import router as interview_router
from .job_matching import router as job_matching_router
from .resume import router as resume_router
from .user import router as user_router

__all__ = [
    "auth_router",
    "user_router",
    "resume_router",
    "job_matching_router",
    "interview_router",
]
