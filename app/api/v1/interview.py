from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.interview_question import GenerateQuestionsRequest, GenerateQuestionsResponse, QuestionResponse
from app.services.interview_question_service import InterviewQuestionService

router = APIRouter(prefix="/interview", tags=["Interview Questions"])


@router.post(
    "/resume/{resume_id}/generate",
    response_model=GenerateQuestionsResponse,
    status_code=200,
)
def generate_interview_questions(
    resume_id: UUID,
    payload: GenerateQuestionsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.resume_id != resume_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="resume_id mismatch.")

    service = InterviewQuestionService(db)
    saved, generated = service.generate_questions(
        user=current_user,
        resume_id=resume_id,
        job_match_id=payload.job_match_id,
        max_questions=payload.max_questions,
    )

    category_counts: dict[str, int] = {}
    for q in generated:
        category_counts[q["category"]] = category_counts.get(q["category"], 0) + 1

    categories = [
        {"category": cat, "count": count}
        for cat, count in sorted(category_counts.items())
    ]

    return GenerateQuestionsResponse(
        message="Interview questions generated successfully.",
        resume_id=resume_id,
        job_match_id=payload.job_match_id,
        total_questions=len(saved),
        questions=[
            QuestionResponse(
                id=q.id,
                question=q.question,
                category=q.category,
                skill=q.skill,
                difficulty=q.difficulty,
                created_at=q.created_at,
            )
            for q in saved
        ],
        categories=categories,
    )


@router.get(
    "/resume/{resume_id}/questions",
    response_model=list[QuestionResponse],
)
def get_interview_questions(
    resume_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InterviewQuestionService(db)
    questions = service.get_questions(current_user, resume_id)
    return [
        QuestionResponse(
            id=q.id,
            question=q.question,
            category=q.category,
            skill=q.skill,
            difficulty=q.difficulty,
            created_at=q.created_at,
        )
        for q in questions
    ]


@router.delete(
    "/resume/{resume_id}/questions",
    status_code=204,
)
def delete_interview_questions(
    resume_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = InterviewQuestionService(db)
    service.delete_questions(current_user, resume_id)
    return None
