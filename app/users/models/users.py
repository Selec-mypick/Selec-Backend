from sqlalchemy import Column, Integer, Boolean

from app.base.base_time_entity import BaseTimeEntity


class Users(BaseTimeEntity):
    __tablename__ = 'users'

    users_seq = Column(Integer, primary_key=True, index=True)
    active = Column(Boolean, nullable=False, default=True)