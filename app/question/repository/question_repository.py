from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.options.models.options import Options
from app.question.models.question import Question
from app.question.repository.dto.question_repository_dto import (
    QuestionDetailDTO,
    QuestionOptionDetailRow,
    VoteResultOptionRow,
)
from app.users.models.users import Users
from app.vote.models.vote import Vote


class QuestionRepository:
    @staticmethod
    async def save(db: AsyncSession, question: Question) -> Question:
        db.add(question)
        await db.flush()
        await db.refresh(question)
        return question

    @staticmethod
    async def find_by_question_seq(db: AsyncSession, question_seq: int) -> Question | None:
        result = await db.execute(
            select(Question).where(
                Question.question_seq == question_seq,
                Question.active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def find_detail_by_question_seq(
            db: AsyncSession,
            question_seq: int,
            users_seq: str,
    ) -> QuestionDetailDTO | None:
        vote_count_subquery = (
            select(
                Vote.options_seq.label("options_seq"),
                func.count(Vote.vote_seq).label("vote_count"),
            )
            .where(
                Vote.question_seq == question_seq,
                Vote.active.is_(True),
            )
            .group_by(Vote.options_seq)
            .subquery()
        )

        user_vote_subquery = (
            select(Vote.options_seq.label("options_seq"))
            .where(
                Vote.question_seq == question_seq,
                Vote.users_seq == users_seq,
                Vote.active.is_(True),
            )
            .subquery()
        )

        result = await db.execute(
            select(
                Question,
                Options,
                func.coalesce(vote_count_subquery.c.vote_count, 0),
                user_vote_subquery.c.options_seq,
            )
            .outerjoin(
                Options,
                and_(
                    Options.question_seq == Question.question_seq,
                    Options.active.is_(True),
                ),
            )
            .outerjoin(
                vote_count_subquery,
                vote_count_subquery.c.options_seq == Options.options_seq,
            )
            .outerjoin(
                user_vote_subquery,
                user_vote_subquery.c.options_seq == Options.options_seq,
            )
            .where(
                Question.question_seq == question_seq,
                Question.active.is_(True),
            )
            .order_by(Options.options_seq.asc())
        )

        rows = result.all()
        if not rows:
            return None

        question = rows[0][0]
        option_rows = [
            QuestionOptionDetailRow(
                option=option,
                vote_count=vote_count,
                selected_option_seq=selected_option_seq,
            )
            for _, option, vote_count, selected_option_seq in rows
            if option is not None
        ]
        return QuestionDetailDTO(question=question, option_rows=option_rows)

    @staticmethod
    async def find_result_options_by_question_seq(
            db: AsyncSession,
            question_seq: int,
    ) -> list[VoteResultOptionRow]:
        result = await db.execute(
            select(Options, Users)
            .outerjoin(
                Vote,
                and_(
                    Vote.question_seq == question_seq,
                    Vote.options_seq == Options.options_seq,
                    Vote.active.is_(True),
                ),
            )
            .outerjoin(
                Users,
                and_(
                    Users.users_seq == Vote.users_seq,
                    Users.active.is_(True),
                ),
            )
            .where(
                Options.question_seq == question_seq,
                Options.active.is_(True),
            )
            .order_by(Options.options_seq.asc(), Vote.vote_seq.asc())
        )
        return [
            VoteResultOptionRow(option=option, voter=voter)
            for option, voter in result.all()
        ]
