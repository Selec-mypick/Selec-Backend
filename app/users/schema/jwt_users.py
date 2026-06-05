from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from app.users.models.users import Users


class JwtUsers(BaseModel):
    users_seq: int
    active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, users: "Users") -> "JwtUsers":
        return cls(
            users_seq=users.users_seq,
            active=users.active,
            created_at=users.created_at,
            updated_at=users.updated_at,
        )
