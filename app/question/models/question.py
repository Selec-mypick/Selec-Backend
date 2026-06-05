from sqlalchemy import Column, Integer, String, Boolean, ForeignKey

from app.base.base_time_entity import BaseTimeEntity


class Question(BaseTimeEntity):
    __tablename__ = 'question'

    question_seq = Column(Integer, primary_key=True, index=True)
    user_seq = Column(Integer, ForeignKey('users.users_seq'), nullable=False, index=True)

    title = Column(String(1024), unique=False, nullable=False)
    description = Column(String(2048), nullable=True)
    is_multiple = Column(Boolean, nullable=False, default=False)
    is_anonymous = Column(Boolean, nullable=False, default=False)
    status = Column(String(20), nullable=False, default='OPEN')
    active = Column(Boolean, nullable=False, default=True)