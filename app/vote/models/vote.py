from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.base.entity import BaseAuditEntity
from app.core.utils import now


class Vote(BaseAuditEntity):
    __tablename__ = 'vote'
    __table_args__ = (
        UniqueConstraint('users_seq', 'question_seq', name='uq_vote_user_question'),
    )

    vote_seq = Column(Integer, primary_key=True, index=True)
    users_seq = Column(String(36), ForeignKey('users.users_seq'), nullable=False, index=True)
    question_seq = Column(String(36), ForeignKey('question.question_seq'), nullable=False, index=True)
    options_seq = Column(Integer, ForeignKey('options.options_seq'), nullable=False, index=True)
    active = Column(Boolean, nullable=False, default=True)

    user = relationship("Users")
    question = relationship("Question")
    option = relationship("Options")

    def deactivate(self, updated_by: str) -> None:
        self.active = False
        self.updated_by = updated_by
        self.updated_at = now()
