"""
Module 7 — Skill Extraction tests.

Covers the deterministic skill-extraction engine and the surrounding
repository/service layer. These tests use a real DB session (via
``SessionLocal``) following the pattern used elsewhere in the project, so a
running PostgreSQL database is required.
"""
import uuid

import pytest

from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models.parsed_resume import ParsedResume
from app.models.resume import Resume
from app.models.user import User
from app.repositories.extracted_skill_repository import ExtractedSkillRepository
from app.repositories.parsed_resume_repository import ParsedResumeRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.user_repository import UserRepository
from app.services.skill_extraction_service import SkillExtractionService
from app.utils.skill_extractor import extract_skills


SAMPLE_TEXT = (
    "John Doe\n"
    "john@example.com\n"
    "Python Developer with 5 years experience.\n"
    "Skills: Python, Django, React, PostgreSQL, Docker, Kubernetes, "
    "Machine Learning.\n"
    "Worked on Python backends with FastAPI and Node.js. "
    "Used PostgreSQL and React.\n"
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
        full_name="Skill Tester",
        email=f"skill_{uuid.uuid4().hex}@example.com",
        hashed_password=hash_password("Test@123"),
    )
    repo = UserRepository(db)
    saved = repo.create(user)
    yield saved
    # Cleanup
    db.query(User).filter(User.id == saved.id).delete()
    db.commit()


@pytest.fixture()
def owned_resume(db, owner):
    resume = Resume(
        user_id=owner.id,
        original_name="sample.pdf",
        stored_name="sample.pdf",
        file_path="uploads/sample.pdf",
        file_size=100,
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
    )
    repo = ParsedResumeRepository(db)
    saved = repo.create(record)
    yield saved
    db.query(ParsedResume).filter(ParsedResume.id == saved.id).delete()
    db.commit()


# --------------------------------------------------------------------------
# Extractor engine tests
# --------------------------------------------------------------------------
class TestExtractor:
    def test_exact_skill_extraction(self):
        result = extract_skills(SAMPLE_TEXT)
        names = {s.normalized_skill for s in result.skills}
        assert "python" in names
        assert "django" in names
        assert "react" in names
        assert "postgresql" in names
        assert "docker" in names

    def test_case_insensitive_matching(self):
        result = extract_skills("experience using PYTHON and React")
        names = {s.normalized_skill for s in result.skills}
        assert "python" in names

    def test_alias_maps_to_canonical(self):
        result = extract_skills("Built apps with React.js and Postgres")
        skills = {s.normalized_skill: s for s in result.skills}
        # React.js should map to canonical "react"
        assert "react" in skills
        # Postgres should map to canonical "postgresql"
        assert "postgresql" in skills

    def test_no_double_count_for_alias_overlap(self):
        # "Node.js" contains "node" — only count once.
        result = extract_skills("Worked with Node.js for backend services.")
        node = next(s for s in result.skills if s.normalized_skill == "node.js")
        assert node.count == 1

    def test_category_assignment(self):
        result = extract_skills("Python and PostgreSQL")
        by_name = {s.normalized_skill: s for s in result.skills}
        assert by_name["python"].category == "Programming Languages"
        assert by_name["postgresql"].category == "Databases"

    def test_duplicate_prevention(self):
        result = extract_skills("Python and Python and Python")
        pythons = [s for s in result.skills if s.normalized_skill == "python"]
        assert len(pythons) == 1
        assert pythons[0].count == 3

    def test_confidence_is_deterministic_and_bounded(self):
        result = extract_skills("Python, Python, Python, Python, Python")
        py = next(s for s in result.skills if s.normalized_skill == "python")
        assert 0.0 < py.confidence <= 1.0
        # Repeated extraction yields the same result.
        again = extract_skills("Python, Python, Python, Python, Python")
        py2 = next(s for s in again.skills if s.normalized_skill == "python")
        assert py.confidence == py2.confidence


# --------------------------------------------------------------------------
# Service / repository tests (require DB)
# --------------------------------------------------------------------------
class TestService:
    def test_extract_and_store_persists_records(self, db, owner, owned_resume, parsed):
        service = SkillExtractionService(db)
        records = service.extract_and_store(owner, owned_resume.id)
        assert len(records) > 0
        assert all(r.resume_id == owned_resume.id for r in records)
        assert all(r.normalized_skill for r in records)

    def test_extraction_is_idempotent(self, db, owner, owned_resume, parsed):
        service = SkillExtractionService(db)
        first = service.extract_and_store(owner, owned_resume.id)
        second = service.extract_and_store(owner, owned_resume.id)
        # No duplicate rows for the same (resume, skill).
        assert len(second) == len(first)
        by_name = {r.normalized_skill for r in second}
        assert len(by_name) == len(second)

    def test_get_skills(self, db, owner, owned_resume, parsed):
        service = SkillExtractionService(db)
        service.extract_and_store(owner, owned_resume.id)
        skills = service.get_skills(owner, owned_resume.id)
        assert len(skills) > 0

    def test_category_summary(self, db, owner, owned_resume, parsed):
        service = SkillExtractionService(db)
        service.extract_and_store(owner, owned_resume.id)
        grouped = service.get_category_summary(owner, owned_resume.id)
        assert "Programming Languages" in grouped
        assert any(s["skill"] == "Python" for s in grouped["Programming Languages"])

    def test_unauthorized_access_raises(self, db, owner, owned_resume, parsed):
        other_user = User(
            full_name="Other",
            email=f"other_{uuid.uuid4().hex}@example.com",
            hashed_password=hash_password("Test@123"),
        )
        other = UserRepository(db).create(other_user)
        try:
            service = SkillExtractionService(db)
            with pytest.raises(Exception) as exc:
                service.get_skills(other, owned_resume.id)
            assert exc.value.status_code == 404
        finally:
            db.query(User).filter(User.id == other.id).delete()
            db.commit()

    def test_unparsed_resume_raises(self, db, owner, owned_resume):
        # No ParsedResume record has been created for this resume.
        service = SkillExtractionService(db)
        with pytest.raises(Exception) as exc:
            service.extract_and_store(owner, owned_resume.id)
        assert exc.value.status_code == 404


# --------------------------------------------------------------------------
# Repository tests (require DB)
# --------------------------------------------------------------------------
class TestRepository:
    def test_replace_for_resume(self, db, owner, owned_resume, parsed):
        repo = ExtractedSkillRepository(db)
        service = SkillExtractionService(db)
        records = service.extract_and_store(owner, owned_resume.id)
        inserted = repo.get_by_resume(owned_resume.id)
        assert len(inserted) == len(records)
