from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.question.models.question import Question


class QuestionRepository:
    @staticmethod
    async def save(db: AsyncSession, question: Question) -> Question:
        db.add(question)
        await db.flush()
        await db.refresh(question)
        return question

    @staticmethod
    async def find_by_question_seq(db: AsyncSession, question_seq: int) -> Question | None:
        result = await db.execute(
            select(Question).where(
                Question.question_seq == question_seq,
                Question.active.is_(True),
            )
        )
        return result.scalar_one_or_none()
