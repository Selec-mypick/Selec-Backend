from sqlalchemy import literal, select, true, update
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils import now
from app.question.models.question import Question
from app.question_invited.models.question_invited import QuestionInvited
from app.users.models.users import Users


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
    async def upsert_all_active_users_to_creator_questions(db: AsyncSession, creator_users_seq: str) -> int:
        requested_at = now()
        source = select(
            Question.question_seq,
            Users.users_seq,
            literal(True),
            literal(creator_users_seq),
            literal(creator_users_seq),
            literal(requested_at),
            literal(requested_at),
        ).select_from(
            Question
        ).join(
            Users,
            true(),
        ).where(
            Question.users_seq == creator_users_seq,
            Question.active.is_(True),
            Users.active.is_(True),
        )
        statement = insert(QuestionInvited).from_select(
            [
                "question_seq",
                "users_seq",
                "active",
                "created_by",
                "updated_by",
                "created_at",
                "updated_at",
            ],
            source,
        )
        result = await db.execute(
            statement.on_duplicate_key_update(
                active=True,
                updated_by=creator_users_seq,
                updated_at=requested_at,
            )
        )
        return result.rowcount

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
