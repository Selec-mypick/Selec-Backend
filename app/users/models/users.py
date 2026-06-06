from sqlalchemy import Column, Integer, Boolean, String

from app.base.base_time_entity import BaseTimeEntity
from app.core.timezone import now


class Users(BaseTimeEntity):
    __tablename__ = 'users'

    users_seq = Column(Integer, primary_key=True, autoincrement=True, index=True)
    google_id = Column(String(128), unique=True, nullable=False, index=True)
    nick_name = Column(String(20), unique=True, nullable=True, index=True)
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
    ) -> "Users":
        return cls(
            google_id=google_id,
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
