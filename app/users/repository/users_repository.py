from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models.users import Users


class UsersRepository:
    @staticmethod
    async def save(db: AsyncSession, users: Users) -> Users:
        db.add(users)
        await db.flush()
        await db.refresh(users)
        return users

    @staticmethod
    async def find_by_users_seq(db: AsyncSession, users_seq: str) -> Users | None:
        result = await db.execute(
            select(Users).where(
                Users.users_seq == users_seq,
                Users.active.is_(True)
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def find_by_nick_name(db: AsyncSession, nick_name: str) -> Users | None:
        result = await db.execute(
            select(Users).where(
                Users.nick_name == nick_name,
                Users.active.is_(True)
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def upsert_by_google(
            db: AsyncSession,
            google_id: str,
            email: str | None,
            name: str | None,
            profile_image: str | None,
    ) -> Users:
        result = await db.execute(
            select(Users).where(
                Users.google_id == google_id
            )
        )
        existing_users = result.scalar_one_or_none()

        if existing_users is not None:
            existing_users.update_google_profile(
                email=email,
                name=name,
                profile_image=profile_image,
            )
            await db.flush()
            await db.refresh(existing_users)
            return existing_users

        users = Users.create_from_google(
            google_id=google_id,
            email=email,
            name=name,
            profile_image=profile_image,
        )
        db.add(users)
        await db.flush()
        await db.refresh(users)
        return users
