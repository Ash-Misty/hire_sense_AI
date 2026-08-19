from uuid import UUID

from sqlalchemy.orm import Session

from app.models.interview_question import InterviewQuestion


class InterviewQuestionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, question: InterviewQuestion) -> InterviewQuestion:
        self.db.add(question)
        self.db.commit()
        self.db.refresh(question)
        return question

    def create_many(self, questions: list[InterviewQuestion]) -> list[InterviewQuestion]:
        self.db.add_all(questions)
        self.db.commit()
        for q in questions:
            self.db.refresh(q)
        return questions

    def get_by_id(self, question_id: UUID, user_id: UUID | None = None) -> InterviewQuestion | None:
        query = self.db.query(InterviewQuestion).filter(InterviewQuestion.id == question_id)
        if user_id is not None:
            query = query.filter(InterviewQuestion.user_id == user_id)
        return query.first()

    def get_by_resume(self, resume_id: UUID, user_id: UUID) -> list[InterviewQuestion]:
        return (
            self.db.query(InterviewQuestion)
            .filter(InterviewQuestion.resume_id == resume_id, InterviewQuestion.user_id == user_id)
            .order_by(InterviewQuestion.created_at.desc())
            .all()
        )

    def get_by_user(self, user_id: UUID) -> list[InterviewQuestion]:
        return (
            self.db.query(InterviewQuestion)
            .filter(InterviewQuestion.user_id == user_id)
            .order_by(InterviewQuestion.created_at.desc())
            .all()
        )

    def delete(self, question: InterviewQuestion) -> None:
        self.db.delete(question)
        self.db.commit()

    def delete_by_resume(self, resume_id: UUID, user_id: UUID) -> int:
        count = (
            self.db.query(InterviewQuestion)
            .filter(InterviewQuestion.resume_id == resume_id, InterviewQuestion.user_id == user_id)
            .delete(synchronize_session=False)
        )
        self.db.commit()
        return count
