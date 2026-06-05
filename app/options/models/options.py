from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.base.base_time_entity import BaseTimeEntity


class Options(BaseTimeEntity):
    __tablename__ = 'options'

    options_seq = Column(Integer, primary_key=True, index=True)
    question_seq = Column(Integer, ForeignKey('question.question_seq'), nullable=False, index=True)

    content = Column(String(1024), nullable=False)
    active = Column(Boolean, nullable=False, default=True)

    vote = relationship("Question")
