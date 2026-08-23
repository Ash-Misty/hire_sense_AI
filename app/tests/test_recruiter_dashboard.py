import uuid

import pytest
from fastapi import HTTPException

from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models.application import Application
from app.models.job_description import JobDescription
from app.models.resume import Resume
from app.models.user import User
from app.repositories.application_repository import ApplicationRepository
from app.repositories.job_description_repository import JobDescriptionRepository
from app.repositories.resume_repository import ResumeRepository
from app.repositories.user_repository import UserRepository
from app.services.application_service import ApplicationService
from app.services.job_service import JobService
from app.services.recruiter_dashboard_service import RecruiterDashboardService


@pytest.fixture()
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def recruiter(db):
    user = User(
        full_name="Recruiter",
        email=f"recruiter_{uuid.uuid4().hex}@example.com",
        hashed_password=hash_password("Test@123"),
        role="recruiter",
    )
    saved = UserRepository(db).create(user)
    yield saved
    db.query(User).filter(User.id == saved.id).delete()
    db.commit()


@pytest.fixture()
def candidate(db):
    user = User(
        full_name="Candidate",
        email=f"candidate_{uuid.uuid4().hex}@example.com",
        hashed_password=hash_password("Test@123"),
        role="candidate",
    )
    saved = UserRepository(db).create(user)
    yield saved
    db.query(User).filter(User.id == saved.id).delete()
    db.commit()


@pytest.fixture()
def resume(db, candidate):
    resume = Resume(
        user_id=candidate.id,
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
def job(db, recruiter):
    job = JobDescription(
        user_id=recruiter.id,
        title="Python Developer",
        company="Tech Corp",
        description="Python, FastAPI, PostgreSQL",
    )
    saved = JobDescriptionRepository(db).create(job)
    yield saved
    db.query(JobDescription).filter(JobDescription.id == saved.id).delete()
    db.commit()


class TestRecruiterDashboardService:
    def test_get_dashboard_returns_stats(self, db, recruiter, job, resume):
        app_repo = ApplicationRepository(db)
        app_repo.create(Application(
            recruiter_id=recruiter.id,
            job_id=job.id,
            candidate_id=resume.user_id,
            resume_id=resume.id,
            status="shortlisted",
        ))

        service = RecruiterDashboardService(db)
        dashboard = service.get_dashboard(recruiter)

        assert dashboard["statistics"]["total_jobs"] == 1
        assert dashboard["statistics"]["shortlisted"] == 1
        assert len(dashboard["jobs"]) == 1
        assert len(dashboard["recent_candidates"]) == 1

    def test_candidate_cannot_access_dashboard(self, db, candidate):
        service = RecruiterDashboardService(db)
        with pytest.raises(HTTPException) as exc:
            service.get_dashboard(candidate)
        assert exc.value.status_code == 403


class TestJobService:
    def test_create_job(self, db, recruiter):
        service = JobService(db)
        job = service.create_job(
            recruiter=recruiter,
            title="Backend Engineer",
            company="Startup Inc",
            description="Python, FastAPI",
        )
        assert job.title == "Backend Engineer"
        assert job.user_id == recruiter.id

    def test_get_jobs(self, db, recruiter, job):
        service = JobService(db)
        jobs = service.get_jobs(recruiter)
        assert len(jobs) == 1

    def test_update_job(self, db, recruiter, job):
        service = JobService(db)
        updated = service.update_job(
            recruiter=recruiter,
            job_id=job.id,
            title="Senior Python Developer",
            company=None,
            description=None,
        )
        assert updated.title == "Senior Python Developer"

    def test_delete_job(self, db, recruiter, job):
        service = JobService(db)
        service.delete_job(recruiter, job.id)
        with pytest.raises(HTTPException) as exc:
            service.get_job(recruiter, job.id)
        assert exc.value.status_code == 404

    def test_candidate_cannot_create_job(self, db, candidate):
        service = JobService(db)
        with pytest.raises(HTTPException) as exc:
            service.create_job(
                recruiter=candidate,
                title="Dev",
                company="Corp",
                description="desc",
            )
        assert exc.value.status_code == 403


class TestApplicationService:
    def test_create_application(self, db, recruiter, candidate, job, resume):
        service = ApplicationService(db)
        app = service.create_application(
            recruiter=recruiter,
            job_id=job.id,
            candidate_id=candidate.id,
            resume_id=resume.id,
            application_status="shortlisted",
        )
        assert app.recruiter_id == recruiter.id
        assert app.candidate_id == candidate.id

    def test_update_application_status(self, db, recruiter, candidate, job, resume):
        service = ApplicationService(db)
        app = service.create_application(
            recruiter=recruiter,
            job_id=job.id,
            candidate_id=candidate.id,
            resume_id=resume.id,
        )
        from app.schemas.application import ApplicationUpdate
        updated = service.update_application_status(
            recruiter=recruiter,
            application_id=app.id,
            update_data=ApplicationUpdate(status="shortlisted"),
        )
        assert updated.status == "shortlisted"

    def test_get_candidates_for_job(self, db, recruiter, candidate, job, resume):
        service = ApplicationService(db)
        service.create_application(
            recruiter=recruiter,
            job_id=job.id,
            candidate_id=candidate.id,
            resume_id=resume.id,
        )
        apps, total = service.get_candidates_for_job(recruiter, job.id)
        assert total == 1
        assert len(apps) == 1

    def test_candidate_cannot_create_application(self, db, candidate, recruiter, job, resume):
        service = ApplicationService(db)
        with pytest.raises(HTTPException) as exc:
            service.create_application(
                recruiter=candidate,
                job_id=job.id,
                candidate_id=recruiter.id,
                resume_id=resume.id,
            )
        assert exc.value.status_code == 403
