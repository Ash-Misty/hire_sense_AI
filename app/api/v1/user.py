from fastapi import APIRouter, Depends

from app.models.user import User
from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.schemas.user import UserResponse
from app.schemas.user import UserUpdateRequest
from app.schemas.user import MessageResponse
from app.schemas.auth import ChangePasswordRequest
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.put(
    "/me",
    response_model=UserResponse,
)
def update_my_profile(
    update_data: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = UserService(db)

    return service.update_profile(current_user, update_data)


@router.delete(
    "/me",
    response_model=MessageResponse,
)
def delete_my_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = UserService(db)

    service.delete_account(current_user)

    return MessageResponse(
        message="Account deleted successfully."
    )


@router.put(
    "/change-password",
    response_model=MessageResponse,
)
def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AuthService(db)

    service.change_password(
        current_user,
        request.current_password,
        request.new_password,
    )

    return MessageResponse(
        message="Password changed successfully."
    )
