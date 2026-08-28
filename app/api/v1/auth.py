from fastapi import APIRouter
from fastapi import BackgroundTasks
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.dependencies.database import get_db

from app.schemas.auth import RegisterResponse
from app.schemas.auth import UserRegisterRequest
from app.schemas.auth import RefreshTokenRequest

from app.schemas.login import LoginRequest
from app.schemas.login import TokenResponse

from app.schemas.email import ForgotPasswordRequest
from app.schemas.email import ResetPasswordRequest
from app.schemas.email import VerificationResendRequest
from app.schemas.email import VerificationResponse
from app.schemas.email import ResetPasswordResponse

from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.core.config import settings

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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    user = service.register_user(user_data)

    token = service.create_verification_token(user.id)
    verification_url = (
        f"http://localhost:8000/api/v1/auth/verify-email?token={token}"
    )

    background_tasks.add_task(
        EmailService().send_verification_email,
        to_email=user.email,
        name=user.full_name,
        verification_url=verification_url,
        expire_minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES,
    )

    return user


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


@router.get(
    "/verify-email",
    response_model=VerificationResponse,
)
def verify_email(
    token: str,
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    service.verify_email(token)
    return VerificationResponse(message="Email verified successfully.")


@router.post(
    "/resend-verification",
    response_model=VerificationResponse,
)
def resend_verification(
    request: VerificationResendRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    background_tasks.add_task(
        EmailService().send_verification_email,
        to_email=request.email,
        name="User",
        verification_url="",
        expire_minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES,
    )

    if service.repo.get_by_email(request.email) is None:
        return VerificationResponse(
            message="If an account with that email exists, a verification email has been sent.",
        )

    return VerificationResponse(
        message="If an account with that email exists, a verification email has been sent.",
    )


@router.post(
    "/forgot-password",
    response_model=VerificationResponse,
)
def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    background_tasks.add_task(
        EmailService().send_password_reset_email,
        to_email=request.email,
        name="User",
        reset_url="",
        expire_minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
    )

    return VerificationResponse(
        message="If an account with that email exists, a password reset link has been sent.",
    )


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
)
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    service.reset_password(request.token, request.new_password)
    return ResetPasswordResponse(message="Password reset successfully.")
