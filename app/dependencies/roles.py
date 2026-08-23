from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.core.config import settings
from app.core.roles import has_recruiter_access
from app.dependencies.auth import get_current_user
from app.models.user import User


def get_current_recruiter(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not has_recruiter_access(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Recruiter access required.",
        )
    return current_user
