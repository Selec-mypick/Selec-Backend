from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models.users import Users


class UsersRepository:

    @staticmethod
    async def find_by_user_seq(db: AsyncSession, user_seq: int) -> Users | None:
        result = await db.execute(
            select(Users).where(Users.users_seq == user_seq)
        )
        return result.scalar_one_or_none()
