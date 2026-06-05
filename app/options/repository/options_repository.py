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
