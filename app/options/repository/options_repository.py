from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
    async def find_all_by_question_seq(db: AsyncSession, question_seq: int) -> list[Options]:
        result = await db.execute(
            select(Options).where(
                Options.question_seq == question_seq,
                Options.active.is_(True),
            )
        )
        return result.scalars().all()
