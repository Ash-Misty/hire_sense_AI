from fastapi import HTTPException, status
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.schemas.auth import UserRegisterRequest
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from app.services.email_service import EmailService
from datetime import datetime, timedelta, timezone


class AuthService:
    """
    Handles all authentication business logic.
    """

    def __init__(self, db: Session):
        self.repo = UserRepository(db)
        self.refresh_repo = RefreshTokenRepository(db)

    def register_user(
        self,
        user_data: UserRegisterRequest,
    ) -> User:

        existing_user = self.repo.get_by_email(
            user_data.email
        )

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered.",
            )

        hashed_password = hash_password(
            user_data.password
        )

        new_user = User(
            full_name=user_data.full_name,
            email=user_data.email,
            hashed_password=hashed_password,
            role="candidate",
        )

        return self.repo.create(new_user)

    def login(
        self,
        email: str,
        password: str,
    ) -> dict | None:

        user = self.repo.get_by_email(email)

        if user is None:
            return None

        if not verify_password(
            password,
            user.hashed_password,
        ):
            return None

        if not user.is_active:
            return None

        access_token = create_access_token(
            {"sub": str(user.id)}
        )

        refresh_token = self._issue_refresh_token(user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    def _issue_refresh_token(self, user_id) -> str:
        """
        Create a new refresh token, hash it and store it in the DB.
        """
        raw_token = create_refresh_token(
            {"sub": str(user_id)}
        )

        token_hash = self._hash_token(raw_token)

        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        db_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        self.refresh_repo.create(db_token)

        return raw_token

    @staticmethod
    def _hash_token(token: str) -> str:
        """
        Hash the raw refresh token before storing in the DB.
        Uses SHA-256 for a fixed-length, one-way fingerprint.
        """
        import hashlib

        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def refresh(self, raw_token: str) -> dict | None:
        """
        Validate a refresh token and issue a new token pair.
        Rotates the refresh token (revokes the old one).
        """
        # 1. Hash the incoming token
        token_hash = self._hash_token(raw_token)

        # 2. Look it up in DB
        db_token = self.refresh_repo.get_by_token_hash(token_hash)

        if db_token is None:
            return None

        # 3. Make sure it's not revoked
        if db_token.revoked:
            return None

        # 4. Make sure it's not expired
        now = datetime.now(timezone.utc)
        expires_at = db_token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at <= now:
            return None

        # 5. Decode the JWT to confirm validity
        try:
            payload = jwt.decode(
                raw_token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
            user_id = payload.get("sub")
        except JWTError:
            return None

        # 6. Ensure the user still exists and is active
        user = self.repo.get_by_id(user_id)
        if user is None or not user.is_active:
            return None

        # 7. Rotate: revoke old refresh token
        self.refresh_repo.revoke(db_token)

        # 8. Issue new pair
        access_token = create_access_token(
            {"sub": str(user.id)}
        )
        new_refresh_token = self._issue_refresh_token(user.id)

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
        }

    def logout(self, raw_token: str) -> None:
        """
        Revoke a refresh token, effectively logging the user out.
        """
        token_hash = self._hash_token(raw_token)
        db_token = self.refresh_repo.get_by_token_hash(token_hash)

        if db_token is None:
            return

        self.refresh_repo.revoke(db_token)

    def logout_all_sessions(self, user_id) -> None:
        """
        Revoke every refresh token for a user (e.g. on password change).
        """
        self.refresh_repo.revoke_all_for_user(user_id)

    def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str,
    ) -> None:
        """
        Change a user's password after verifying their current password.
        Revokes all existing refresh tokens so other sessions must re-login.
        """
        if not verify_password(
            current_password,
            user.hashed_password,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect.",
            )

        user.hashed_password = hash_password(new_password)
        self.repo.update(user)

        # Invalidate all sessions after a password change
        self.logout_all_sessions(user.id)

    def create_verification_token(self, user_id) -> str:
        """
        Create a short-lived JWT for email verification.
        """
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            "sub": str(user_id),
            "type": "email_verification",
            "exp": expire,
        }
        return jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

    def verify_email(self, token: str) -> User:
        """
        Validate the verification token and mark the user as verified.
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token.",
            ) from exc

        token_type = payload.get("type")
        if token_type != "email_verification":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type.",
            )

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token.",
            )

        user = self.repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already verified.",
            )

        user.is_verified = True
        self.repo.update(user)

        return user

    def resend_verification_email(self, email: str) -> None:
        """
        Generate a new verification token and send it to the user.
        """
        user = self.repo.get_by_email(email)
        if user is None:
            return

        if user.is_verified:
            return

        token = self.create_verification_token(user.id)

        verification_url = (
            f"http://localhost:8000/api/v1/auth/verify-email?token={token}"
        )

        EmailService().send_verification_email(
            to_email=user.email,
            name=user.full_name,
            verification_url=verification_url,
            expire_minutes=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES,
        )

    def create_password_reset_token(self, user_id) -> str:
        """
        Create a short-lived JWT for password reset.
        """
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            "sub": str(user_id),
            "type": "password_reset",
            "exp": expire,
        }
        return jwt.encode(
            payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

    def reset_password(self, token: str, new_password: str) -> User:
        """
        Validate the reset token and update the user's password.
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token.",
            ) from exc

        token_type = payload.get("type")
        if token_type != "password_reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type.",
            )

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token.",
            )

        user = self.repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        user.hashed_password = hash_password(new_password)
        self.repo.update(user)

        # Invalidate all sessions after password reset
        self.logout_all_sessions(user.id)

        return user

    def request_password_reset(self, email: str) -> None:
        """
        Generate a password reset token and send it to the user.
        """
        user = self.repo.get_by_email(email)
        if user is None:
            return

        token = self.create_password_reset_token(user.id)

        reset_url = (
            f"http://localhost:3000/reset-password?token={token}"
        )

        EmailService().send_password_reset_email(
            to_email=user.email,
            name=user.full_name,
            reset_url=reset_url,
            expire_minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
        )
    
