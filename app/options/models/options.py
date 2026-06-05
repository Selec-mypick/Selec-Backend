from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.core.timezone import now
from app.base.base_time_entity import BaseTimeEntity


class Options(BaseTimeEntity):
    __tablename__ = 'options'

    options_seq = Column(Integer, primary_key=True, index=True)
    question_seq = Column(Integer, ForeignKey('question.question_seq'), nullable=False, index=True)

    content = Column(String(1024), nullable=False)
    active = Column(Boolean, nullable=False, default=True)

    question = relationship("Question")

    @classmethod
    def create(cls, question_seq: int, content: str) -> "Options":
        return cls(
            question_seq=question_seq,
            content=content,
            active=True,
        )

    def update_content(self, content: str) -> None:
        self.content = content
        self.active = True
        self.updated_at = now()

    def deactivate(self) -> None:
        self.active = False
        self.updated_at = now()
