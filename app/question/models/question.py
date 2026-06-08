from uuid import uuid4

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey

from app.base.entity import BaseAuditEntity
from app.core.utils import now
from app.question.constants.question_status import QuestionStatus


class Question(BaseAuditEntity):
    __tablename__ = 'question'

    question_seq = Column(Integer, primary_key=True, index=True)
    users_seq = Column(String(36), ForeignKey('users.users_seq'), nullable=False, index=True)
    share_token = Column(String(36), unique=True, nullable=False, index=True)

    title = Column(String(1024), unique=False, nullable=False)
    description = Column(String(2048), nullable=True)
    is_anonymous = Column(Boolean, nullable=False, default=True)
    status = Column(String(20), nullable=False, default=QuestionStatus.OPEN.value)
    active = Column(Boolean, nullable=False, default=True)

    version = Column(Integer, nullable=False, default=0)
    __mapper_args__ = {"version_id_col": version}

    @staticmethod
    def generate_share_token() -> str:
        return str(uuid4())

    def update(self, title: str, description: str | None, is_anonymous: bool, updated_by: str) -> None:
        self.title = title
        self.description = description or None
        self.is_anonymous = is_anonymous
        self.updated_by = updated_by
        self.updated_at = now()

    def deactivate(self, updated_by: str) -> None:
        self.active = False
        self.updated_by = updated_by
        self.updated_at = now()
