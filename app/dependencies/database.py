from typing import Generator

from sqlalchemy.orm import Session

from app.database.session import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Creates a new database session for each request
    and automatically closes it afterwards.
    """
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()