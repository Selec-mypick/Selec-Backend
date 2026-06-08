from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils import now
from app.options.models.options import Options


class OptionsRepository:
    @staticmethod
    async def save_all(db: AsyncSession, options: list[Options]) -> list[Options]:
        db.add_all(options)
        await db.flush()

        for option in options:
            await db.refresh(option)

        return options

    @staticmethod
    async def find_all_by_question_seq(db: AsyncSession, question_seq: str) -> list[Options]:
        result = await db.execute(
            select(Options).where(
                Options.question_seq == question_seq,
                Options.active.is_(True),
            )
        )
        return result.scalars().all()

    @staticmethod
    async def deactivate_by_question_seq(db: AsyncSession, question_seq: str, updated_by: str) -> int:
        result = await db.execute(
            update(Options)
            .where(
                Options.question_seq == question_seq,
                Options.active.is_(True),
            )
            .values(
                active=False,
                updated_by=updated_by,
                updated_at=now(),
            )
        )
        return result.rowcount

    @staticmethod
    async def deactivate_by_options_seqs(
            db: AsyncSession,
            question_seq: str,
            options_seqs: set[int],
            updated_by: str,
    ) -> int:
        if not options_seqs:
            return 0

        result = await db.execute(
            update(Options)
            .where(
                Options.question_seq == question_seq,
                Options.options_seq.in_(options_seqs),
                Options.active.is_(True),
            )
            .values(
                active=False,
                updated_by=updated_by,
                updated_at=now(),
            )
        )
        return result.rowcount
