from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils import now
from app.question_invited.models.question_invited import QuestionInvited


class QuestionInvitedRepository:
    @staticmethod
    async def deactivate_by_question_seq(db: AsyncSession, question_seq: str, updated_by: str) -> int:
        result = await db.execute(
            update(QuestionInvited)
            .where(
                QuestionInvited.question_seq == question_seq,
                QuestionInvited.active.is_(True),
            )
            .values(
                active=False,
                updated_by=updated_by,
                updated_at=now(),
            )
        )
        return result.rowcount
