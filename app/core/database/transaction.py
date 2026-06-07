from collections.abc import Awaitable, Callable
from typing import TypeVar

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError

from app.core.exceptions import BaseAPIException, ConflictException, ServerException

T = TypeVar("T")


async def run_in_transaction(
        db: AsyncSession,
        action: Callable[[], Awaitable[T]],
        error_message: str,
        *,
        stale_exception: BaseAPIException | None = None,
        integrity_exception: BaseAPIException | None = None,
) -> T:
    try:
        result = await action()
        await db.commit()
        return result
    except StaleDataError:
        await db.rollback()
        if stale_exception is not None:
            raise stale_exception
        raise
    except IntegrityError:
        await db.rollback()
        if integrity_exception is not None:
            raise integrity_exception
        raise ConflictException("리소스 충돌이 발생했습니다.")
    except BaseAPIException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise ServerException(f"{error_message}: {str(e)}")
