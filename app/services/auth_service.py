from fastapi import HTTPException
from fastapi import status

from app.core.security import hash_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserRegisterRequest


class AuthService:

    def __init__(self, repository: UserRepository):
        self.repository = repository

    def register_user(
        self,
        user_data: UserRegisterRequest,
    ) -> User:

        existing_user = self.repository.get_by_email(
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

        return self.repository.create(new_user)