"""
Module 8 — ATS score repository tests.

These tests exercise the repository layer for AtsScore CRUD operations.
They require a real database session.
"""
import uuid

import pytest

from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models.ats_score import AtsScore
from app.models.resume import Resume
from app.models.user import User
from app.repositories.ats_score_repository import AtsScoreRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.user_repository import UserRepository


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def owner(db):
    user = User(
        full_name="ATS Repo Tester",
        email=f"ats_repo_{uuid.uuid4().hex}@example.com",
        hashed_password=hash_password("Test@123"),
    )
    repo = UserRepository(db)
    saved = repo.create(user)
    yield saved
    db.query(User).filter(User.id == saved.id).delete()
    db.commit()


@pytest.fixture()
def owned_resume(db, owner):
    resume = Resume(
        user_id=owner.id,
        original_name="repo_test.pdf",
        stored_name="repo_test.pdf",
        file_path="uploads/repo_test.pdf",
        file_size=300,
    )
    repo = ResumeRepository(db)
    saved = repo.create(resume)
    yield saved
    db.query(Resume).filter(Resume.id == saved.id).delete()
    db.commit()


class TestAtsScoreRepository:
    def test_get_by_resume_returns_none_when_empty(self, db, owned_resume):
        repo = AtsScoreRepository(db)
        record = repo.get_by_resume(owned_resume.id)
        assert record is None

    def test_create_and_get(self, db, owner, owned_resume):
        repo = AtsScoreRepository(db)
        score = AtsScore(
            resume_id=owned_resume.id,
            user_id=owner.id,
            score=85.0,
            category_scores=[{"name": "test", "score": 15.0, "max_score": 15.0, "weight": 0.15}],
            feedback=["Great resume!"],
            score_breakdown={"test": {"score": 15.0}},
        )
        created = repo.create(score)
        assert created.id is not None
        assert created.score == 85.0

        retrieved = repo.get_by_resume(owned_resume.id)
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_replace_for_resume(self, db, owner, owned_resume):
        repo = AtsScoreRepository(db)
        first = AtsScore(
            resume_id=owned_resume.id,
            user_id=owner.id,
            score=50.0,
            category_scores=[],
            feedback=[],
            score_breakdown={},
        )
        repo.create(first)

        second = AtsScore(
            resume_id=owned_resume.id,
            user_id=owner.id,
            score=90.0,
            category_scores=[],
            feedback=[],
            score_breakdown={},
        )
        replaced = repo.replace_for_resume(owned_resume.id, second)
        assert replaced.score == 90.0

        # Only one record should exist.
        records = (
            db.query(AtsScore)
            .filter(AtsScore.resume_id == owned_resume.id)
            .all()
        )
        assert len(records) == 1
        assert records[0].score == 90.0

    def test_unique_resume_constraint(self, db, owner, owned_resume):
        repo = AtsScoreRepository(db)
        score1 = AtsScore(
            resume_id=owned_resume.id,
            user_id=owner.id,
            score=70.0,
            category_scores=[],
            feedback=[],
            score_breakdown={},
        )
        repo.create(score1)

        score2 = AtsScore(
            resume_id=owned_resume.id,
            user_id=owner.id,
            score=80.0,
            category_scores=[],
            feedback=[],
            score_breakdown={},
        )
# Attempting to create a second record for the same resume should fail
        # due to the unique constraint on resume_id.
        with pytest.raises(Exception):
            repo.create(score2)

        # Roll back the failed transaction so teardown can clean up cleanly.
        db.rollback()
