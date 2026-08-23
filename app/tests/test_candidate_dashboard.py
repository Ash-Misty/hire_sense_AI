import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.database.session import SessionLocal
from app.main import app
from app.models.ats_score import AtsScore
from app.models.extracted_skill import ExtractedSkill
from app.models.interview_question import InterviewQuestion
from app.models.job_description import JobDescription
from app.models.job_match import JobMatch
from app.models.parsed_resume import ParsedResume
from app.models.resume import Resume
from app.models.user import User
from app.repositories.ats_score_repository import AtsScoreRepository
from app.repositories.extracted_skill_repository import ExtractedSkillRepository
from app.repositories.interview_question_repository import InterviewQuestionRepository
from app.repositories.job_description_repository import JobDescriptionRepository
from app.repositories.job_match_repository import JobMatchRepository
from app.repositories.parsed_resume_repository import ParsedResumeRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.user_repository import UserRepository
from app.services.candidate_dashboard_service import CandidateDashboardService

client = TestClient(app)


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def candidate(db):
    user = User(
        full_name="Dashboard Candidate",
        email=f"candidate_{uuid.uuid4().hex}@example.com",
        hashed_password=hash_password("Test@123"),
        role="candidate",
    )
    saved = UserRepository(db).create(user)
    yield saved
    db.query(User).filter(User.id == saved.id).delete()
    db.commit()


@pytest.fixture()
def other_candidate(db):
    user = User(
        full_name="Other Candidate",
        email=f"other_candidate_{uuid.uuid4().hex}@example.com",
        hashed_password=hash_password("Test@123"),
        role="candidate",
    )
    saved = UserRepository(db).create(user)
    yield saved
    db.query(User).filter(User.id == saved.id).delete()
    db.commit()


@pytest.fixture()
def token(candidate):
    return create_access_token(data={"sub": str(candidate.id)})


@pytest.fixture()
def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


class TestCandidateDashboardApi:
    def test_dashboard_without_token_returns_401(self):
        response = client.get("/api/v1/candidate/dashboard")
        assert response.status_code == 401

    def test_dashboard_with_valid_token_returns_200(self, auth_header):
        response = client.get("/api/v1/candidate/dashboard", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert "profile" in data
        assert "resume_summary" in data
        assert "skills" in data
        assert "job_matches" in data
        assert "interview" in data

    def test_dashboard_returns_profile(self, auth_header, candidate):
        response = client.get("/api/v1/candidate/dashboard", headers=auth_header)
        assert response.status_code == 200
        data = response.json()
        assert data["profile"]["id"] == str(candidate.id)
        assert data["profile"]["full_name"] == candidate.full_name
        assert data["profile"]["email"] == candidate.email

    def test_dashboard_isolates_users(self, db, candidate, other_candidate):
        resume = Resume(
            user_id=candidate.id,
            original_name="cv.pdf",
            stored_name="cv.pdf",
            file_path="uploads/cv.pdf",
            file_size=100,
        )
        ResumeRepository(db).create(resume)

        other_token = create_access_token(data={"sub": str(other_candidate.id)})
        other_header = {"Authorization": f"Bearer {other_token}"}

        response = client.get("/api/v1/candidate/dashboard", headers=other_header)
        assert response.status_code == 200
        data = response.json()
        assert data["resume_summary"]["total_resumes"] == 0

        response = client.get("/api/v1/candidate/dashboard", headers={"Authorization": f"Bearer {create_access_token(data={'sub': str(candidate.id)})}"})
        assert response.status_code == 200
        data = response.json()
        assert data["resume_summary"]["total_resumes"] == 1


class TestCandidateDashboardService:
    def test_empty_dashboard(self, db, candidate):
        service = CandidateDashboardService(db)
        dashboard = service.get_dashboard(candidate)

        assert dashboard["profile"]["id"] == candidate.id
        assert dashboard["resume_summary"]["total_resumes"] == 0
        assert dashboard["resume_summary"]["parsed_resumes"] == 0
        assert dashboard["skills"]["total_skills"] == 0
        assert dashboard["skills"]["top_skills"] == []
        assert dashboard["ats_summary"] is None
        assert dashboard["job_matches"]["total_matches"] == 0
        assert dashboard["interview"]["total_questions"] == 0

    def test_dashboard_with_resumes(self, db, candidate):
        resume = Resume(
            user_id=candidate.id,
            original_name="resume.pdf",
            stored_name="resume.pdf",
            file_path="uploads/resume.pdf",
            file_size=100,
        )
        ResumeRepository(db).create(resume)

        parsed = ParsedResume(
            resume_id=resume.id,
            user_id=candidate.id,
            raw_text="Python developer",
        )
        ParsedResumeRepository(db).create(parsed)

        service = CandidateDashboardService(db)
        dashboard = service.get_dashboard(candidate)

        assert dashboard["resume_summary"]["total_resumes"] == 1
        assert dashboard["resume_summary"]["parsed_resumes"] == 1
        assert dashboard["resume_summary"]["latest_resume_name"] == "resume.pdf"

    def test_dashboard_with_skills(self, db, candidate):
        resume = Resume(
            user_id=candidate.id,
            original_name="resume.pdf",
            stored_name="resume.pdf",
            file_path="uploads/resume.pdf",
            file_size=100,
        )
        saved_resume = ResumeRepository(db).create(resume)

        skill = ExtractedSkill(
            resume_id=saved_resume.id,
            skill="Python",
            normalized_skill="python",
            category="technical",
            count=5,
            confidence=0.9,
        )
        ExtractedSkillRepository(db).create(skill)

        service = CandidateDashboardService(db)
        dashboard = service.get_dashboard(candidate)

        assert dashboard["skills"]["total_skills"] == 1
        assert "Python" in dashboard["skills"]["top_skills"]
        assert "technical" in dashboard["skills"]["skills_by_category"]

    def test_dashboard_with_ats_scores(self, db, candidate):
        resume = Resume(
            user_id=candidate.id,
            original_name="resume.pdf",
            stored_name="resume.pdf",
            file_path="uploads/resume.pdf",
            file_size=100,
        )
        saved_resume = ResumeRepository(db).create(resume)

        ats = AtsScore(
            resume_id=saved_resume.id,
            user_id=candidate.id,
            score=85.0,
            category_scores=[],
            feedback=[],
            score_breakdown={},
        )
        AtsScoreRepository(db).create(ats)

        service = CandidateDashboardService(db)
        dashboard = service.get_dashboard(candidate)

        assert dashboard["ats_summary"] is not None
        assert dashboard["ats_summary"]["latest_score"] == 85.0
        assert dashboard["ats_summary"]["highest_score"] == 85.0
        assert dashboard["ats_summary"]["average_score"] == 85.0
        assert dashboard["ats_summary"]["total_analyzed"] == 1

    def test_dashboard_with_job_matches(self, db, candidate):
        resume = Resume(
            user_id=candidate.id,
            original_name="resume.pdf",
            stored_name="resume.pdf",
            file_path="uploads/resume.pdf",
            file_size=100,
        )
        saved_resume = ResumeRepository(db).create(resume)

        job = JobDescription(
            user_id=candidate.id,
            title="Python Developer",
            company="Tech Corp",
            description="Python, FastAPI, PostgreSQL",
        )
        saved_job = JobDescriptionRepository(db).create(job)

        match = JobMatch(
            user_id=candidate.id,
            resume_id=saved_resume.id,
            job_description_id=saved_job.id,
            match_percentage=75.0,
            matched_skills=["Python"],
            missing_skills=["Docker"],
            extra_skills=[],
            category_scores={},
        )
        JobMatchRepository(db).create(match)

        service = CandidateDashboardService(db)
        dashboard = service.get_dashboard(candidate)

        assert dashboard["job_matches"]["total_matches"] == 1
        assert dashboard["job_matches"]["highest_match_percentage"] == 75.0
        assert dashboard["job_matches"]["average_match_percentage"] == 75.0

    def test_dashboard_with_interview_questions(self, db, candidate):
        resume = Resume(
            user_id=candidate.id,
            original_name="resume.pdf",
            stored_name="resume.pdf",
            file_path="uploads/resume.pdf",
            file_size=100,
        )
        saved_resume = ResumeRepository(db).create(resume)

        question = InterviewQuestion(
            user_id=candidate.id,
            resume_id=saved_resume.id,
            job_match_id=None,
            question="What is Python?",
            category="technical",
            skill="Python",
            difficulty="easy",
        )
        InterviewQuestionRepository(db).create(question)

        service = CandidateDashboardService(db)
        dashboard = service.get_dashboard(candidate)

        assert dashboard["interview"]["total_questions"] == 1
        assert len(dashboard["interview"]["recent_questions"]) == 1
        assert dashboard["interview"]["recent_questions"][0]["question"] == "What is Python?"

    def test_dashboard_recent_activity(self, db, candidate):
        resume = Resume(
            user_id=candidate.id,
            original_name="resume.pdf",
            stored_name="resume.pdf",
            file_path="uploads/resume.pdf",
            file_size=100,
        )
        saved_resume = ResumeRepository(db).create(resume)

        parsed = ParsedResume(
            resume_id=saved_resume.id,
            user_id=candidate.id,
            raw_text="Python developer",
        )
        ParsedResumeRepository(db).create(parsed)

        service = CandidateDashboardService(db)
        dashboard = service.get_dashboard(candidate)

        assert len(dashboard["recent_activity"]) > 0
        activity_types = [a["activity_type"] for a in dashboard["recent_activity"]]
        assert "resume_upload" in activity_types
        assert "resume_parsed" in activity_types
