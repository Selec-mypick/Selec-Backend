from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.base.entity import BaseAuditEntity


class QuestionInvited(BaseAuditEntity):
    __tablename__ = 'question_invited'
    __table_args__ = (
        UniqueConstraint('question_seq', 'users_seq', name='uq_question_invited_question_user'),
    )

    question_invited_seq = Column(Integer, primary_key=True, index=True)
    question_seq = Column(String(36), ForeignKey('question.question_seq'), nullable=False, index=True)
    users_seq = Column(String(36), ForeignKey('users.users_seq'), nullable=False, index=True)
    active = Column(Boolean, nullable=False, default=True)

    question = relationship("Question")
    user = relationship("Users")
