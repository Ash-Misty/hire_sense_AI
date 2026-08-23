from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.roles import is_recruiter
from app.models.application import Application
from app.models.job_match import JobMatch
from app.models.user import User
from app.repositories.application_repository import ApplicationRepository
from app.repositories.job_description_repository import JobDescriptionRepository
from app.repositories.job_match_repository import JobMatchRepository
from app.repositories.resume_repository import ResumeRepository


class RecruiterDashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.job_repo = JobDescriptionRepository(db)
        self.application_repo = ApplicationRepository(db)
        self.match_repo = JobMatchRepository(db)
        self.resume_repo = ResumeRepository(db)

    def get_dashboard(self, recruiter: User) -> dict:
        if not is_recruiter(recruiter):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Recruiter access required.",
            )

        jobs = self.job_repo.get_all_by_user(recruiter.id)
        applications, _ = self.application_repo.get_by_recruiter(recruiter.id, skip=0, limit=1000)

        job_ids = [job.id for job in jobs]
        matches = []
        if job_ids:
            all_matches = []
            for job_id in job_ids:
                job_matches = self.match_repo.db.query(JobMatch).filter(
                    JobMatch.job_description_id == job_id,
                    JobMatch.user_id == recruiter.id,
                ).all()
                all_matches.extend(job_matches)
            matches = all_matches

        stats = self.application_repo.get_statistics(recruiter.id)

        job_summaries = []
        for job in jobs:
            job_apps = [a for a in applications if a.job_id == job.id]
            job_matches = [m for m in matches if m.job_description_id == job.id]
            avg_score = None
            if job_matches:
                avg_score = sum(m.match_percentage for m in job_matches) / len(job_matches)

            job_summaries.append({
                "id": str(job.id),
                "title": job.title,
                "company": job.company,
                "candidate_count": len(job_apps),
                "avg_match_score": round(avg_score, 2) if avg_score is not None else None,
                "shortlisted_count": len([a for a in job_apps if a.status == "shortlisted"]),
                "interview_count": len([a for a in job_apps if a.status == "interview"]),
                "selected_count": len([a for a in job_apps if a.status == "selected"]),
                "created_at": job.created_at,
            })

        candidate_map = {}
        for app in applications:
            if app.candidate_id not in candidate_map:
                candidate_map[app.candidate_id] = {
                    "id": app.candidate_id,
                    "applied_at": app.created_at,
                    "status": app.status,
                    "job_id": app.job_id,
                }

        recent_candidates = []
        for candidate_id, info in sorted(candidate_map.items(), key=lambda x: x[1]["applied_at"], reverse=True)[:10]:
            resume = self.resume_repo.get_by_user(candidate_id)
            resume_info = None
            if resume:
                resume_info = resume[0] if isinstance(resume, list) else resume

            user = self.db.query(User).filter(User.id == candidate_id).first()
            match = None
            if resume_info:
                match = self.match_repo.db.query(JobMatch).filter(
                    JobMatch.resume_id == resume_info.id,
                    JobMatch.user_id == recruiter.id,
                ).first()

            recent_candidates.append({
                "id": str(candidate_id),
                "full_name": user.full_name if user else "Unknown",
                "email": user.email if user else "",
                "resume_id": str(resume_info.id) if resume_info else "",
                "match_percentage": match.match_percentage if match else None,
                "status": info["status"],
                "applied_at": info["applied_at"],
            })

        top_candidates = []
        for candidate_id, info in candidate_map.items():
            resume = self.resume_repo.get_by_user(candidate_id)
            resume_info = None
            if resume:
                resume_info = resume[0] if isinstance(resume, list) else resume

            match = None
            if resume_info:
                match = self.match_repo.db.query(JobMatch).filter(
                    JobMatch.resume_id == resume_info.id,
                    JobMatch.user_id == recruiter.id,
                ).first()

            if match and match.match_percentage is not None:
                user = self.db.query(User).filter(User.id == candidate_id).first()
                top_candidates.append({
                    "id": str(candidate_id),
                    "full_name": user.full_name if user else "Unknown",
                    "email": user.email if user else "",
                    "resume_id": str(resume_info.id) if resume_info else "",
                    "match_percentage": match.match_percentage,
                    "matched_skills": match.matched_skills,
                    "missing_skills": match.missing_skills,
                    "status": info["status"],
                })

        top_candidates.sort(key=lambda x: x["match_percentage"] or 0, reverse=True)
        top_candidates = top_candidates[:10]

        return {
            "statistics": {
                "total_jobs": len(jobs),
                "active_jobs": len(jobs),
                "total_candidates": len(candidate_map),
                "candidates_under_review": stats["reviewing"],
                "shortlisted": stats["shortlisted"],
                "interviews": stats["interview"],
                "selected": stats["selected"],
            },
            "jobs": job_summaries,
            "recent_candidates": recent_candidates,
            "top_candidates": top_candidates,
        }
