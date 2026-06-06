from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.base.entity import BaseAuditEntity
from app.core.utils import now


class Options(BaseAuditEntity):
    __tablename__ = 'options'

    options_seq = Column(Integer, primary_key=True, index=True)
    question_seq = Column(Integer, ForeignKey('question.question_seq'), nullable=False, index=True)

    content = Column(String(1024), nullable=False)
    active = Column(Boolean, nullable=False, default=True)

    question = relationship("Question")

    @classmethod
    def create(cls, question_seq: int, content: str, users_seq: int) -> "Options":
        return cls(
            question_seq=question_seq,
            content=content,
            active=True,
            created_by=users_seq,
            updated_by=users_seq,
        )

    def update_content(self, content: str, updated_by: int) -> None:
        self.content = content
        self.active = True
        self.updated_by = updated_by
        self.updated_at = now()

    def deactivate(self, updated_by: int) -> None:
        self.active = False
        self.updated_by = updated_by
        self.updated_at = now()
