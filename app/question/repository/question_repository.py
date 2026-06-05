from sqlalchemy.ext.asyncio import AsyncSession

from app.question.models.question import Question


class QuestionRepository:
    @staticmethod
    async def save(db: AsyncSession, question: Question) -> Question:
        db.add(question)
        await db.flush()
        await db.refresh(question)
        return question
