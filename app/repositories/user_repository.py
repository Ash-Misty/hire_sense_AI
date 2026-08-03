from uuid import UUID

from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """
    Repository for all User database operations.
    """

    def __init__(self, db: Session):
        self.db = db

    def create(self, user: User) -> User:
        """
        Save a new user to the database.
        """
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_by_id(self, user_id: UUID) -> User | None:
        """
        Retrieve a user by UUID.
        """
        return (
            self.db.query(User)
            .filter(User.id == user_id)
            .first()
        )

    def get_by_email(self, email: str) -> User | None:
        """
        Retrieve a user by email.
        """
        return (
            self.db.query(User)
            .filter(User.email == email)
            .first()
        )

    def email_exists(self, email: str) -> bool:
        """
        Check whether a user with the given email exists.
        """
        return self.get_by_email(email) is not None

    def get_all(self) -> list[User]:
        """
        Retrieve all users.
        """
        return self.db.query(User).all()

    def update(self, user: User) -> User:
        """
        Update an existing user.
        """
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user: User) -> None:
        """
        Delete a user.
        """
        self.db.delete(user)
        self.db.commit()