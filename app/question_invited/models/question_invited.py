from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.base.entity import BaseAuditEntity
from app.core.utils import now


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

    @classmethod
    def create(cls, question_seq: str, users_seq: str, created_by: str) -> "QuestionInvited":
        return cls(
            question_seq=question_seq,
            users_seq=users_seq,
            active=True,
            created_by=created_by,
            updated_by=created_by,
        )

    def deac업tivate(self, updated_by: str) -> None:
        self.active = False
        self.updated_by = updated_by
        self.updated_at = now()
