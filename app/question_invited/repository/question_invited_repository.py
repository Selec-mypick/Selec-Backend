from sqlalchemy import update
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils import now
from app.question_invited.models.question_invited import QuestionInvited


class QuestionInvitedRepository:
    @staticmethod
    async def upsert(db: AsyncSession, question_seq: str, users_seq: str) -> None:
        statement = insert(QuestionInvited).values(
            question_seq=question_seq,
            users_seq=users_seq,
            active=True,
            created_by=users_seq,
            updated_by=users_seq,
            created_at=now(),
            updated_at=now(),
        )
        await db.execute(
            statement.on_duplicate_key_update(
                active=True,
                updated_by=users_seq,
                updated_at=now(),
            )
        )

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
