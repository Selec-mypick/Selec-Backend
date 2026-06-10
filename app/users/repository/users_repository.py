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
    async def find_by_google_id(db: AsyncSession, google_id: str) -> Users | None:
        result = await db.execute(
            select(Users).where(
                Users.google_id == google_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def exists_by_nick_name(db: AsyncSession, nick_name: str) -> bool:
        result = await db.execute(
            select(Users.users_seq).where(
                Users.nick_name == nick_name,
            )
        )
        return result.first() is not None

    @staticmethod
    async def upsert_by_google(
            db: AsyncSession,
            google_id: str,
            email: str | None,
            name: str | None,
            profile_image: str | None,
            nick_name: str,
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
            if existing_users.nick_name is None:
                existing_users.nick_name = nick_name
            await db.flush()
            await db.refresh(existing_users)
            return existing_users

        users = Users.create_from_google(
            google_id=google_id,
            email=email,
            name=name,
            profile_image=profile_image,
            nick_name=nick_name,
        )
        db.add(users)
        await db.flush()
        await db.refresh(users)
        return users
