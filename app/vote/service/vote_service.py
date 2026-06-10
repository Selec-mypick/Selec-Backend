from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.transaction import run_in_transaction
from app.core.exceptions import BaseAPIException, ErrorCode
from app.options.repository.options_repository import OptionsRepository
from app.question.repository.question_repository import QuestionRepository
from app.question.schema.response.question_response import GetQuestionResponse
from app.vote.repository.vote_repository import VoteRepository
from app.vote.schema.request.vote_request import CreateVoteRequest


async def create_vote(question_seq: str, request: CreateVoteRequest, users_seq: str, db: AsyncSession) -> GetQuestionResponse:
    question = await QuestionRepository.find_by_question_seq(db, question_seq)
    if question is None:
        raise BaseAPIException(ErrorCode.QUESTION_NOT_FOUND)

    options = await OptionsRepository.find_all_by_question_seq(db, question_seq)
    option_seqs = {option.options_seq for option in options}
    if request.options_seq not in option_seqs:
        raise BaseAPIException(ErrorCode.OPTION_NOT_IN_QUESTION)

    async def create_vote_action() -> GetQuestionResponse:
        await VoteRepository.upsert(
            db=db,
            users_seq=users_seq,
            question_seq=question_seq,
            options_seq=request.options_seq,
        )

        question_detail_rows = await QuestionRepository.find_detail_rows_by_question_seq(db, question_seq, users_seq)
        if not question_detail_rows:
            raise BaseAPIException(ErrorCode.QUESTION_NOT_FOUND)

        return GetQuestionResponse.from_detail_rows(question_detail_rows, users_seq)

    return await run_in_transaction(db, create_vote_action, "투표 저장 중 오류가 발생했습니다")


async def delete_vote(question_seq: str, users_seq: str, db: AsyncSession) -> None:
    vote = await VoteRepository.find_by_users_seq_and_question_seq(db, users_seq, question_seq)
    if vote is None:
        raise BaseAPIException(ErrorCode.VOTE_NOT_FOUND)

    async def delete_vote_action() -> None:
        vote.deactivate(users_seq)

    await run_in_transaction(db, delete_vote_action, "투표 취소 중 오류가 발생했습니다")
