from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.dependencies.database import get_db

from app.schemas.auth import RegisterResponse
from app.schemas.auth import UserRegisterRequest
from app.schemas.auth import RefreshTokenRequest

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

    tokens = service.login(
        request.email,
        request.password,
    )

    if tokens is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    tokens = service.refresh(request.refresh_token)

    if tokens is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token",
        )

    return TokenResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
    )


@router.post(
    "/logout",
    status_code=204,
)
def logout(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    service.logout(request.refresh_token)

    return None
