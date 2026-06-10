from uuid import uuid4

from sqlalchemy import Column, Boolean, String

from app.base.entity import BaseTimeEntity
from app.core.utils import now


class Users(BaseTimeEntity):
    __tablename__ = 'users'

    users_seq = Column(String(36), primary_key=True, default=lambda: str(uuid4()), index=True)
    google_id = Column(String(128), unique=True, nullable=False, index=True)
    nick_name = Column(String(128), unique=True, nullable=True, index=True)
    email = Column(String(256), nullable=True)
    name = Column(String(128), nullable=True)
    profile_image = Column(String(2048), nullable=True)
    active = Column(Boolean, nullable=False, default=True)

    @classmethod
    def create_from_google(
            cls,
            google_id: str,
            email: str | None,
            name: str | None,
            profile_image: str | None,
            nick_name: str | None = None,
    ) -> "Users":
        return cls(
            google_id=google_id,
            nick_name=nick_name,
            email=email,
            name=name,
            profile_image=profile_image,
            active=True,
        )

    def update_google_profile(
            self,
            email: str | None,
            name: str | None,
            profile_image: str | None,
    ) -> None:
        self.email = email
        self.name = name
        self.profile_image = profile_image
        self.active = True

    def update_nick_name(self, nick_name: str) -> None:
        self.nick_name = nick_name
        self.updated_at = now()
