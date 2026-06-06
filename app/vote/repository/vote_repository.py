from sqlalchemy import exists, func, select, update
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.timezone import now
from app.vote.models.vote import Vote


class VoteRepository:
    @staticmethod
    async def upsert(
            db: AsyncSession,
            users_seq: int,
            question_seq: int,
            options_seq: int,
    ) -> Vote:
        statement = insert(Vote).values(
            users_seq=users_seq,
            question_seq=question_seq,
            options_seq=options_seq,
            active=True,
            created_at=now(),
            updated_at=now(),
        )
        await db.execute(
            statement.on_duplicate_key_update(
                options_seq=options_seq,
                active=True,
                updated_at=now(),
            )
        )
        await db.flush()

        result = await db.execute(
            select(Vote).where(
                Vote.users_seq == users_seq,
                Vote.question_seq == question_seq,
            )
        )
        return result.scalar_one()

    @staticmethod
    async def exists_active_by_question_seq_and_options_seqs(
            db: AsyncSession,
            question_seq: int,
            options_seqs: set[int],
    ) -> bool:
        if not options_seqs:
            return False

        result = await db.execute(
            select(
                exists().where(
                    Vote.question_seq == question_seq,
                    Vote.options_seq.in_(options_seqs),
                    Vote.active.is_(True),
                )
            )
        )
        return result.scalar()

    @staticmethod
    async def count_by_question_seq_group_by_options_seq(db: AsyncSession, question_seq: int) -> dict[int, int]:
        result = await db.execute(
            select(
                Vote.options_seq,
                func.count(Vote.vote_seq),
            )
            .where(
                Vote.question_seq == question_seq,
                Vote.active.is_(True),
            )
            .group_by(Vote.options_seq)
        )
        return {
            options_seq: count
            for options_seq, count in result.all()
        }

    @staticmethod
    async def find_by_users_seq_and_question_seq(
            db: AsyncSession,
            users_seq: int,
            question_seq: int,
    ) -> Vote | None:
        result = await db.execute(
            select(Vote).where(
                Vote.users_seq == users_seq,
                Vote.question_seq == question_seq,
                Vote.active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def deactivate_by_question_seq(db: AsyncSession, question_seq: int) -> int:
        result = await db.execute(
            update(Vote)
            .where(
                Vote.question_seq == question_seq,
                Vote.active.is_(True),
            )
            .values(
                active=False,
                updated_at=now(),
            )
        )
        return result.rowcount

    @staticmethod
    async def deactivate_by_question_seq_and_options_seqs(
            db: AsyncSession,
            question_seq: int,
            options_seqs: set[int],
    ) -> int:
        if not options_seqs:
            return 0

        result = await db.execute(
            update(Vote)
            .where(
                Vote.question_seq == question_seq,
                Vote.options_seq.in_(options_seqs),
                Vote.active.is_(True),
            )
            .values(
                active=False,
                updated_at=now(),
            )
        )
        return result.rowcount
