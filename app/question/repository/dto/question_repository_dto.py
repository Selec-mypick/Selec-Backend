from dataclasses import dataclass

from app.options.models.options import Options
from app.question.models.question import Question


@dataclass(frozen=True)
class QuestionOptionDetailRow:
    option: Options
    vote_count: int
    selected_option_seq: int | None


@dataclass(frozen=True)
class QuestionDetailDTO:
    question: Question
    option_rows: list[QuestionOptionDetailRow]
