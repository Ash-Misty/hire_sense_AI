import uuid

import pytest
from fastapi import HTTPException

from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models.interview_question import InterviewQuestion
from app.models.job_match import JobMatch
from app.models.resume import Resume
from app.models.user import User
from app.repositories.interview_question_repository import InterviewQuestionRepository
from app.repositories.job_match_repository import JobMatchRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.user_repository import UserRepository
from app.services.interview_question_service import InterviewQuestionService


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
def parsed_resume(db, owner, owned_resume):
    from app.models.parsed_resume import ParsedResume
    parsed = ParsedResume(
        resume_id=owned_resume.id,
        user_id=owner.id,
        raw_text="Python developer with FastAPI, PostgreSQL, Docker, AWS and Kubernetes experience.",
    )
    saved = db.query(ParsedResume).filter(ParsedResume.resume_id == owned_resume.id).first()
    if saved:
        db.delete(saved)
        db.commit()
    parsed = ParsedResume(
        resume_id=owned_resume.id,
        user_id=owner.id,
        raw_text="Python developer with FastAPI, PostgreSQL, Docker, AWS and Kubernetes experience.",
    )
    db.add(parsed)
    db.commit()
    yield parsed
    db.query(ParsedResume).filter(ParsedResume.resume_id == owned_resume.id).delete()
    db.commit()


class TestInterviewQuestionService:
    def test_generate_questions_returns_questions(self, db, owner, owned_resume, parsed_resume):
        service = InterviewQuestionService(db)
        saved, generated = service.generate_questions(
            user=owner,
            resume_id=owned_resume.id,
            max_questions=10,
        )
        assert len(saved) > 0
        assert len(generated) > 0
        for q in saved:
            assert q.user_id == owner.id
            assert q.resume_id == owned_resume.id

    def test_generate_questions_with_job_match(self, db, owner, owned_resume, parsed_resume):
        from app.models.job_description import JobDescription
        from app.repositories.job_description_repository import JobDescriptionRepository
        jd = JobDescription(
            user_id=owner.id,
            title="Python Developer",
            company="Tech Corp",
            description="Python, FastAPI, PostgreSQL, Docker, AWS, Kubernetes",
        )
        JobDescriptionRepository(db).create(jd)
        job_match = JobMatch(
            user_id=owner.id,
            resume_id=owned_resume.id,
            job_description_id=jd.id,
            match_percentage=80.0,
            matched_skills=["Python", "FastAPI", "PostgreSQL"],
            missing_skills=["AWS", "Kubernetes"],
            extra_skills=[],
            category_scores={},
        )
        JobMatchRepository(db).create(job_match)

        service = InterviewQuestionService(db)
        saved, generated = service.generate_questions(
            user=owner,
            resume_id=owned_resume.id,
            job_match_id=job_match.id,
            max_questions=10,
        )
        assert len(saved) > 0
        categories = {q["category"] for q in generated}
        assert "job_specific" in categories

    def test_generate_questions_for_other_users_resume_raises(self, db, owner, other_user, owned_resume):
        service = InterviewQuestionService(db)
        with pytest.raises(HTTPException) as exc:
            service.generate_questions(user=other_user, resume_id=owned_resume.id)
        assert exc.value.status_code in {403, 404}

    def test_get_questions_returns_user_questions(self, db, owner, owned_resume, parsed_resume):
        service = InterviewQuestionService(db)
        service.generate_questions(user=owner, resume_id=owned_resume.id, max_questions=5)
        questions = service.get_questions(owner, owned_resume.id)
        assert len(questions) > 0
        for q in questions:
            assert q.user_id == owner.id

    def test_get_questions_other_user_returns_empty(self, db, owner, other_user, owned_resume, parsed_resume):
        service = InterviewQuestionService(db)
        service.generate_questions(user=owner, resume_id=owned_resume.id, max_questions=5)
        with pytest.raises(HTTPException) as exc:
            service.get_questions(other_user, owned_resume.id)
        assert exc.value.status_code in {403, 404}

    def test_delete_questions_removes_questions(self, db, owner, owned_resume, parsed_resume):
        service = InterviewQuestionService(db)
        service.generate_questions(user=owner, resume_id=owned_resume.id, max_questions=5)
        service.delete_questions(owner, owned_resume.id)
        questions = service.get_questions(owner, owned_resume.id)
        assert len(questions) == 0

    def test_generate_questions_unparsed_resume_raises(self, db, owner, owned_resume):
        service = InterviewQuestionService(db)
        with pytest.raises(HTTPException) as exc:
            service.generate_questions(user=owner, resume_id=owned_resume.id)
        assert exc.value.status_code == 404

    def test_generate_questions_invalid_job_match_raises(self, db, owner, owned_resume, parsed_resume):
        service = InterviewQuestionService(db)
        with pytest.raises(HTTPException) as exc:
            service.generate_questions(
                user=owner,
                resume_id=owned_resume.id,
                job_match_id=uuid.uuid4(),
            )
        assert exc.value.status_code == 404

    def test_generate_questions_regenerates_on_duplicate(self, db, owner, owned_resume, parsed_resume):
        service = InterviewQuestionService(db)
        saved1, _ = service.generate_questions(user=owner, resume_id=owned_resume.id, max_questions=5)
        saved2, _ = service.generate_questions(user=owner, resume_id=owned_resume.id, max_questions=5)
        questions = service.get_questions(owner, owned_resume.id)
        assert len(questions) == len(saved2)
        assert len(questions) < len(saved1) + len(saved2)

    def test_generate_questions_respects_max(self, db, owner, owned_resume, parsed_resume):
        service = InterviewQuestionService(db)
        saved, _ = service.generate_questions(user=owner, resume_id=owned_resume.id, max_questions=3)
        assert len(saved) <= 3
