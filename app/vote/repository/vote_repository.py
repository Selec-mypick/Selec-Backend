from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.vote.models.vote import Vote


class VoteRepository:
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
    async def find_all_by_question_seq(db: AsyncSession, question_seq: int) -> list[Vote]:
        result = await db.execute(
            select(Vote).where(
                Vote.question_seq == question_seq,
                Vote.active.is_(True),
            )
        )
        return result.scalars().all()

    @staticmethod
    async def find_all_by_question_seq_and_options_seqs(
            db: AsyncSession,
            question_seq: int,
            options_seqs: set[int],
    ) -> list[Vote]:
        if not options_seqs:
            return []

        result = await db.execute(
            select(Vote).where(
                Vote.question_seq == question_seq,
                Vote.options_seq.in_(options_seqs),
                Vote.active.is_(True),
            )
        )
        return result.scalars().all()
