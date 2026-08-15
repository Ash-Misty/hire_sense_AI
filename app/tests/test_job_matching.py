import uuid

import pytest
from fastapi import HTTPException

from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models.job_description import JobDescription
from app.models.resume import Resume
from app.models.user import User
from app.repositories.job_description_repository import JobDescriptionRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.user_repository import UserRepository
from app.services.job_matching_service import JobMatchingService


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
        full_name="Owner",
        email=f"owner_{uuid.uuid4().hex}@example.com",
        hashed_password=hash_password("Test@123"),
    )
    saved = UserRepository(db).create(user)
    yield saved
    db.query(User).filter(User.id == saved.id).delete()
    db.commit()


@pytest.fixture()
def other_user(db):
    user = User(
        full_name="Other User",
        email=f"other_{uuid.uuid4().hex}@example.com",
        hashed_password=hash_password("Test@123"),
    )
    saved = UserRepository(db).create(user)
    yield saved
    db.query(User).filter(User.id == saved.id).delete()
    db.commit()


@pytest.fixture()
def owned_resume(db, owner):
    resume = Resume(
        user_id=owner.id,
        original_name="cv.pdf",
        stored_name="cv.pdf",
        file_path="uploads/cv.pdf",
        file_size=100,
    )
    saved = ResumeRepository(db).create(resume)
    yield saved
    db.query(Resume).filter(Resume.id == saved.id).delete()
    db.commit()


@pytest.fixture()
def job_description(db, owner):
    description = JobDescription(
        user_id=owner.id,
        title="Python Backend Developer",
        company="ABC Tech",
        description="We need Python, FastAPI, PostgreSQL, Docker, AWS and Kubernetes experience.",
    )
    saved = JobDescriptionRepository(db).create(description)
    yield saved
    db.query(JobDescription).filter(JobDescription.id == saved.id).delete()
    db.commit()


class TestModule9Matching:
    def test_perfect_match(self, db, owner, owned_resume, job_description):
        from app.models.parsed_resume import ParsedResume
        parsed = ParsedResume(
            resume_id=owned_resume.id,
            user_id=owner.id,
            raw_text="Python developer with FastAPI, PostgreSQL, Docker, AWS and Kubernetes experience.",
        )
        db.add(parsed)
        db.commit()
        service = JobMatchingService(db)
        result = service.match_resume_to_job_description(owner, owned_resume.id, job_description.id)
        assert result["match_percentage"] == 100.0
        assert set(result["matched_skills"]) >= {"Python", "FastAPI", "PostgreSQL"}

    def test_partial_match(self, db, owner, owned_resume, job_description):
        service = JobMatchingService(db)
        from app.models.parsed_resume import ParsedResume
        parsed = ParsedResume(
            resume_id=owned_resume.id,
            user_id=owner.id,
            raw_text="Python Developer with FastAPI and PostgreSQL experience.",
        )
        db.add(parsed)
        db.commit()
        service.skill_service.extract_and_store(owner, owned_resume.id)
        # use a simpler matching set by updating the JD with a partial set
        job_description.description = "We need Python, FastAPI, PostgreSQL, Docker, AWS."
        db.commit()

        result = service.match_resume_to_job_description(owner, owned_resume.id, job_description.id)
        assert result["match_percentage"] == 60.0

    def test_zero_match(self, db, owner, owned_resume, job_description):
        from app.models.parsed_resume import ParsedResume
        parsed = ParsedResume(
            resume_id=owned_resume.id,
            user_id=owner.id,
            raw_text="Java and Spring developer.",
        )
        db.add(parsed)
        db.commit()
        service = JobMatchingService(db)
        result = service.match_resume_to_job_description(owner, owned_resume.id, job_description.id)
        assert result["match_percentage"] == 0.0

    def test_extra_skills(self, db, owner, owned_resume, job_description):
        from app.models.parsed_resume import ParsedResume
        parsed = ParsedResume(
            resume_id=owned_resume.id,
            user_id=owner.id,
            raw_text="Python, FastAPI, React experience.",
        )
        db.add(parsed)
        db.commit()
        service = JobMatchingService(db)
        result = service.match_resume_to_job_description(owner, owned_resume.id, job_description.id)
        assert "Python" in result["matched_skills"]
        assert "FastAPI" in result["matched_skills"]
        assert "React" in result["extra_skills"]

    def test_duplicate_skills_do_not_inflate_match(self, db, owner, owned_resume, job_description):
        from app.models.parsed_resume import ParsedResume
        parsed = ParsedResume(
            resume_id=owned_resume.id,
            user_id=owner.id,
            raw_text="Python, Python, FastAPI, FastAPI, PostgreSQL.",
        )
        db.add(parsed)
        db.commit()
        service = JobMatchingService(db)
        result = service.match_resume_to_job_description(owner, owned_resume.id, job_description.id)
        assert len(set(result["matched_skills"])) == len(result["matched_skills"])

    def test_user_isolation_for_resume_or_job(self, db, owner, other_user, owned_resume, job_description):
        service = JobMatchingService(db)

        with pytest.raises(HTTPException) as exc:
            service.match_resume_to_job_description(other_user, owned_resume.id, job_description.id)
        assert exc.value.status_code in {403, 404}

    def test_invalid_resume_raises(self, db, owner, job_description):
        service = JobMatchingService(db)
        with pytest.raises(HTTPException) as exc:
            service.match_resume_to_job_description(owner, uuid.uuid4(), job_description.id)
        assert exc.value.status_code == 404

    def test_invalid_job_description_raises(self, db, owner, owned_resume):
        service = JobMatchingService(db)
        with pytest.raises(HTTPException) as exc:
            service.match_resume_to_job_description(owner, owned_resume.id, uuid.uuid4())
        assert exc.value.status_code == 404
