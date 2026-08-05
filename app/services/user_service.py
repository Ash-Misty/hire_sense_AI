from fastapi import HTTPException, status

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.schemas.user import UserUpdateRequest


class UserService:
    """
    Handles all user profile business logic.
    """

    def __init__(self, db):
        self.repo = UserRepository(db)
        self.refresh_repo = RefreshTokenRepository(db)

    def get_profile(self, user: User) -> User:
        """
        Return the authenticated user's profile.
        """
        return user

    def update_profile(
        self,
        user: User,
        update_data: UserUpdateRequest,
    ) -> User:
        """
        Update a user's profile fields.
        """
        data = update_data.model_dump(exclude_unset=True)

        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided to update.",
            )

        if "email" in data:
            existing = self.repo.get_by_email(data["email"])

            if existing is not None and existing.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered.",
                )

        if "full_name" in data:
            user.full_name = data["full_name"]

        if "email" in data:
            user.email = data["email"]

        return self.repo.update(user)

    def delete_account(self, user: User) -> None:
        """
        Soft-delete a user account by marking it inactive.
        Revokes all refresh tokens so they cannot log back in.
        """
        user.is_active = False
        self.repo.update(user)
        self.refresh_repo.revoke_all_for_user(user.id)

