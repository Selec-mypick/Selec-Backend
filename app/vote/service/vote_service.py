from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import BadRequestException, NotFoundException, ServerException
from app.options.repository.options_repository import OptionsRepository
from app.question.repository.question_repository import QuestionRepository
from app.vote.repository.vote_repository import VoteRepository
from app.vote.schema.request.vote_request import CreateVoteRequest, DeleteVoteRequest


async def create_vote(request: CreateVoteRequest, users_seq: int, db: AsyncSession) -> None:
    question = await QuestionRepository.find_by_question_seq(db, request.question_seq)
    if question is None:
        raise NotFoundException("존재하지 않는 질문입니다.")
    if question.status != 'OPEN':
        raise BadRequestException("이미 종료된 투표입니다.")

    options = await OptionsRepository.find_all_by_question_seq(db, request.question_seq)
    option_seqs = {option.options_seq for option in options}
    if request.options_seq not in option_seqs:
        raise BadRequestException("질문에 속하지 않는 선택지입니다.")

    try:
        await VoteRepository.upsert(
            db=db,
            users_seq=users_seq,
            question_seq=request.question_seq,
            options_seq=request.options_seq,
        )
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise ServerException(f"투표 저장 중 오류가 발생했습니다: {str(e)}")


async def delete_vote(request: DeleteVoteRequest, users_seq: int, db: AsyncSession) -> None:
    vote = await VoteRepository.find_by_users_seq_and_question_seq(db, users_seq, request.question_seq)
    if vote is None:
        raise NotFoundException("투표 내역이 없습니다.")

    try:
        vote.deactivate()
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise ServerException(f"투표 취소 중 오류가 발생했습니다: {str(e)}")
