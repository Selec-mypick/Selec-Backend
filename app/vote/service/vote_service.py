from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.transaction import run_in_transaction
from app.core.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.options.repository.options_repository import OptionsRepository
from app.question.constants.question_status import QuestionStatus
from app.question.repository.question_repository import QuestionRepository
from app.vote.repository.vote_repository import VoteRepository
from app.vote.schema.request.vote_request import CreateVoteRequest
from app.vote.schema.response.vote_response import GetVoteResultResponse


async def create_vote(question_seq: int, request: CreateVoteRequest, users_seq: str, db: AsyncSession) -> None:
    question = await QuestionRepository.find_by_question_seq(db, question_seq)
    if question is None:
        raise NotFoundException("존재하지 않는 질문입니다.")
    if question.status != QuestionStatus.OPEN.value:
        raise BadRequestException("이미 종료된 투표입니다.")

    options = await OptionsRepository.find_all_by_question_seq(db, question_seq)
    option_seqs = {option.options_seq for option in options}
    if request.options_seq not in option_seqs:
        raise BadRequestException("질문에 속하지 않는 선택지입니다.")

    async def create_vote_action() -> None:
        await VoteRepository.upsert(
            db=db,
            users_seq=users_seq,
            question_seq=question_seq,
            options_seq=request.options_seq,
        )

    await run_in_transaction(db, create_vote_action, "투표 저장 중 오류가 발생했습니다")


async def get_vote_result(question_seq: int, users_seq: str, db: AsyncSession) -> GetVoteResultResponse:
    question = await QuestionRepository.find_by_question_seq(db, question_seq)
    if question is None:
        raise NotFoundException("존재하지 않는 질문입니다.")

    if not question.is_anonymous:
        is_creator = question.users_seq == users_seq
        if not is_creator and await VoteRepository.find_by_users_seq_and_question_seq(db, users_seq, question_seq) is None:
            raise ForbiddenException("투표 후 결과를 조회할 수 있습니다.")

    option_rows = await QuestionRepository.find_result_options_by_question_seq(db, question_seq)
    return GetVoteResultResponse.from_result_rows(option_rows, question.is_anonymous)


async def delete_vote(question_seq: int, users_seq: str, db: AsyncSession) -> None:
    vote = await VoteRepository.find_by_users_seq_and_question_seq(db, users_seq, question_seq)
    if vote is None:
        raise NotFoundException("투표 내역이 없습니다.")

    async def delete_vote_action() -> None:
        vote.deactivate(users_seq)

    await run_in_transaction(db, delete_vote_action, "투표 취소 중 오류가 발생했습니다")
