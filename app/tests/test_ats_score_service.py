"""
Module 8 — ATS score service tests.

These tests exercise the orchestrator service layer (not the scoring engine).
They require a real database session.
"""
import uuid

import pytest

from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models.ats_score import AtsScore
from app.models.parsed_resume import ParsedResume
from app.models.resume import Resume
from app.models.user import User
from app.repositories.ats_score_repository import AtsScoreRepository
from app.repositories.parsed_resume_repository import ParsedResumeRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.user_repository import UserRepository
from app.services.ats_score_service import AtsScoreService


SAMPLE_TEXT = (
    "John Doe\n"
    "john@example.com\n"
    "Experienced Python Developer.\n"
    "Skills: Python, Django, React, PostgreSQL, Docker.\n"
)


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
        full_name="ATS Score Tester",
        email=f"ats_{uuid.uuid4().hex}@example.com",
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
        original_name="ats_candidate.pdf",
        stored_name="ats_candidate.pdf",
        file_path="uploads/ats_candidate.pdf",
        file_size=200,
    )
    repo = ResumeRepository(db)
    saved = repo.create(resume)
    yield saved
    db.query(Resume).filter(Resume.id == saved.id).delete()
    db.commit()


@pytest.fixture()
def parsed(owner, owned_resume, db):
    record = ParsedResume(
        resume_id=owned_resume.id,
        user_id=owner.id,
        raw_text=SAMPLE_TEXT,
        name="John Doe",
        email="john@example.com",
        phone="+1-555-0000",
        summary="Experienced Python Developer.",
        skills=["Python", "Django", "React", "PostgreSQL", "Docker"],
        education=[{"degree": "BSc Computer Science"}],
        experience=[{"role": "Python Developer", "company": "Tech Corp"}],
        projects=[{"name": "Project X"}],
        certifications=["AWS Certified"],
    )
    repo = ParsedResumeRepository(db)
    saved = repo.create(record)
    yield saved
    db.query(ParsedResume).filter(ParsedResume.id == saved.id).delete()
    db.commit()


class TestAtsScoreService:
    def test_compute_and_store_persists_score(self, db, owner, owned_resume, parsed):
        service = AtsScoreService(db)
        record = service.compute_and_store(owner, owned_resume.id)
        assert record.resume_id == owned_resume.id
        assert record.user_id == owner.id
        assert 0.0 <= record.score <= 100.0
        assert record.category_scores is not None
        assert record.feedback is not None
        assert record.score_breakdown is not None

    def test_get_score_returns_stored_score(self, db, owner, owned_resume, parsed):
        service = AtsScoreService(db)
        service.compute_and_store(owner, owned_resume.id)
        retrieved = service.get_score(owner, owned_resume.id)
        assert retrieved.resume_id == owned_resume.id
        assert retrieved.score is not None

    def test_recompute_replaces_previous_score(self, db, owner, owned_resume, parsed):
        service = AtsScoreService(db)
        first = service.compute_and_store(owner, owned_resume.id)
        second = service.compute_and_store(owner, owned_resume.id)
        # Only one record should exist for this resume.
        scores = (
            db.query(AtsScore)
            .filter(AtsScore.resume_id == owned_resume.id)
            .all()
        )
        assert len(scores) == 1

    def test_unauthorized_user_gets_404(self, db, owner, owned_resume, parsed):
        other_user = User(
            full_name="Other",
            email=f"other_{uuid.uuid4().hex}@example.com",
            hashed_password=hash_password("Test@123"),
        )
        other = UserRepository(db).create(other_user)
        try:
            service = AtsScoreService(db)
            with pytest.raises(Exception) as exc:
                service.compute_and_store(other, owned_resume.id)
            assert exc.value.status_code == 403
        finally:
            db.query(User).filter(User.id == other.id).delete()
            db.commit()

    def test_nonexistent_resume_raises_404(self, db, owner):
        service = AtsScoreService(db)
        with pytest.raises(Exception) as exc:
            service.compute_and_store(owner, uuid.uuid4())
        assert exc.value.status_code == 404

    def test_get_score_when_not_computed_raises_404(self, db, owner, owned_resume, parsed):
        service = AtsScoreService(db)
        with pytest.raises(Exception) as exc:
            service.get_score(owner, owned_resume.id)
        assert exc.value.status_code == 404

    def test_unparsed_resume_raises_404(self, db, owner, owned_resume):
        # No parsed resume exists for this resume.
        service = AtsScoreService(db)
        with pytest.raises(Exception) as exc:
            service.compute_and_store(owner, owned_resume.id)
        assert exc.value.status_code == 404
