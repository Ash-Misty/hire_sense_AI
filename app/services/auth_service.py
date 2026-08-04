from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserRegisterRequest
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)


class AuthService:
    """
    Handles all authentication business logic.
    """

    def __init__(self, db: Session):
        self.repo = UserRepository(db)

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
        )

        return self.repo.create(new_user)

    def login(
        self,
        email: str,
        password: str,
    ):

        user = self.repo.get_by_email(email)

        if user is None:
            return None

        if not verify_password(
            password,
            user.hashed_password,
        ):
            return None

        token = create_access_token(
            {
                "sub": str(user.id)
            }
        )

        return token