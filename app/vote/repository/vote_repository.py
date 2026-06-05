from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.vote.models.vote import Vote


class VoteRepository:
    @staticmethod
    async def upsert(
            db: AsyncSession,
            users_seq: int,
            question_seq: int,
            options_seq: int,
    ) -> Vote:
        result = await db.execute(
            select(Vote).where(
                Vote.users_seq == users_seq,
                Vote.question_seq == question_seq,
            )
        )
        existing_vote = result.scalar_one_or_none()

        if existing_vote is not None:
            existing_vote.update_option(options_seq)
            await db.flush()
            await db.refresh(existing_vote)
            return existing_vote

        vote = Vote.create(users_seq, question_seq, options_seq)
        db.add(vote)
        await db.flush()
        await db.refresh(vote)
        return vote

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
