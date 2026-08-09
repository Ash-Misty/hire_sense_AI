"""
Module 8 — ATS score API endpoint tests.

These tests exercise the FastAPI endpoints for ATS scoring.
They require a real database session and a TestClient.
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.database.session import SessionLocal
from app.main import app
from app.models.parsed_resume import ParsedResume
from app.models.resume import Resume
from app.models.user import User
from app.repositories.parsed_resume_repository import ParsedResumeRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.user_repository import UserRepository

client = TestClient(app)


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
        full_name="ATS API Tester",
        email=f"ats_api_{uuid.uuid4().hex}@example.com",
        hashed_password=hash_password("Test@123"),
    )
    repo = UserRepository(db)
    saved = repo.create(user)
    yield saved
    db.query(User).filter(User.id == saved.id).delete()
    db.commit()


@pytest.fixture()
def token(owner):
    return create_access_token(data={"sub": str(owner.id)})


@pytest.fixture()
def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def owned_resume(db, owner):
    resume = Resume(
        user_id=owner.id,
        original_name="api_test.pdf",
        stored_name="api_test.pdf",
        file_path="uploads/api_test.pdf",
        file_size=400,
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


class TestAtsScoreApi:
    def test_post_ats_score_returns_score(self, db, owned_resume, parsed, auth_header):
        response = client.post(
            f"/api/v1/resume/{owned_resume.id}/ats-score",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["resume_id"] == str(owned_resume.id)
        assert 0.0 <= data["score"] <= 100.0
        assert "category_scores" in data
        assert "feedback" in data
        assert "score_breakdown" in data

    def test_get_ats_score_returns_stored_score(self, db, owned_resume, parsed, auth_header):
        # First compute the score.
        client.post(
            f"/api/v1/resume/{owned_resume.id}/ats-score",
            headers=auth_header,
        )
        # Then retrieve it.
        response = client.get(
            f"/api/v1/resume/{owned_resume.id}/ats-score",
            headers=auth_header,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["resume_id"] == str(owned_resume.id)

    def test_get_ats_score_not_found(self, db, owned_resume, parsed, auth_header):
        response = client.get(
            f"/api/v1/resume/{owned_resume.id}/ats-score",
            headers=auth_header,
        )
        assert response.status_code == 404

    def test_unauthorized_access_returns_401(self, db, owned_resume, parsed):
        response = client.post(
            f"/api/v1/resume/{owned_resume.id}/ats-score",
        )
        assert response.status_code == 401

    def test_wrong_owner_returns_403(self, db, owned_resume, parsed):
        other_user = User(
            full_name="Other API",
            email=f"other_api_{uuid.uuid4().hex}@example.com",
            hashed_password=hash_password("Test@123"),
        )
        other = UserRepository(db).create(other_user)
        other_token = create_access_token(data={"sub": str(other.id)})
        try:
            response = client.post(
                f"/api/v1/resume/{owned_resume.id}/ats-score",
                headers={"Authorization": f"Bearer {other_token}"},
            )
            assert response.status_code == 403
        finally:
            db.query(User).filter(User.id == other.id).delete()
            db.commit()

    def test_nonexistent_resume_returns_404(self, auth_header):
        fake_id = uuid.uuid4()
        response = client.post(
            f"/api/v1/resume/{fake_id}/ats-score",
            headers=auth_header,
        )
        assert response.status_code == 404

    def test_recompute_replaces_score(self, db, owned_resume, parsed, auth_header):
        # First compute.
        resp1 = client.post(
            f"/api/v1/resume/{owned_resume.id}/ats-score",
            headers=auth_header,
        )
        score1 = resp1.json()["score"]

        # Recompute — should replace rather than create duplicate.
        resp2 = client.post(
            f"/api/v1/resume/{owned_resume.id}/ats-score",
            headers=auth_header,
        )
        score2 = resp2.json()["score"]

        # The score should be deterministic for the same input.
        assert score1 == score2
