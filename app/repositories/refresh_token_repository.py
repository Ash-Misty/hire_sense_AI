from uuid import UUID

from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    """
    Repository for all RefreshToken database operations.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, refresh_token: RefreshToken) -> RefreshToken:
        """
        Save a new refresh token to the database.
        """
        self.db.add(refresh_token)
        self.db.commit()
        self.db.refresh(refresh_token)
        return refresh_token

    def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        """
        Retrieve a refresh token by its hashed value.
        """
        return (
            self.db.query(RefreshToken)
            .filter(RefreshToken.token_hash == token_hash)
            .first()
        )

    def get_active_by_user(self, user_id: UUID) -> RefreshToken | None:
        """
        Retrieve an active (non-revoked, non-expired) token for a user.
        """
        from datetime import datetime, timezone

        return (
            self.db.query(RefreshToken)
            .filter(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked.is_(False),
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
            .first()
        )

    def revoke(self, refresh_token: RefreshToken) -> RefreshToken:
        """
        Mark a refresh token as revoked.
        """
        refresh_token.revoked = True
        self.db.commit()
        self.db.refresh(refresh_token)
        return refresh_token

    def revoke_all_for_user(self, user_id: UUID) -> None:
        """
        Revoke all refresh tokens belonging to a user.
        """
        self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id
        ).update(
            {RefreshToken.revoked: True}
        )
        self.db.commit()

    def delete(self, refresh_token: RefreshToken) -> None:
        """
        Delete a refresh token.
        """
        self.db.delete(refresh_token)
        self.db.commit()
