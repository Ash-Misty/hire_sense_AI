from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.dependencies.database import get_db

from app.schemas.auth import RegisterResponse
from app.schemas.auth import UserRegisterRequest

from app.schemas.login import LoginRequest
from app.schemas.login import TokenResponse

from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=201,
)
def register(
    user_data: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    return service.register_user(user_data)


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    token = service.login(
        request.email,
        request.password,
    )

    if token is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    return TokenResponse(
        access_token=token,
    )