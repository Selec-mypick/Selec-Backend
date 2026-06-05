from sqlalchemy import Boolean, Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.timezone import now
from app.base.base_time_entity import BaseTimeEntity


class Vote(BaseTimeEntity):
    __tablename__ = 'vote'
    __table_args__ = (
        UniqueConstraint('users_seq', 'question_seq', 'options_seq', name='uq_vote_user_question_option'),
    )

    vote_seq = Column(Integer, primary_key=True, index=True)
    users_seq = Column(Integer, ForeignKey('users.users_seq'), nullable=False, index=True)
    question_seq = Column(Integer, ForeignKey('question.question_seq'), nullable=False, index=True)
    options_seq = Column(Integer, ForeignKey('options.options_seq'), nullable=False, index=True)
    active = Column(Boolean, nullable=False, default=True)

    user = relationship("Users")
    question = relationship("Question")
    option = relationship("Options")

    def deactivate(self) -> None:
        self.active = False
        self.updated_at = now()
