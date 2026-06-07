from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.transaction import run_in_transaction
from app.core.exceptions import BaseAPIException, ErrorCode
from app.options.models.options import Options
from app.options.repository.options_repository import OptionsRepository
from app.question.constants.question_status import QuestionStatus
from app.question.models.question import Question
from app.question.repository.question_repository import QuestionRepository
from app.question.schema.request.question_request import CreateQuestionRequest, UpdateQuestionRequest
from app.question.schema.response.question_response import (
    CreateQuestionResponse,
    GetQuestionResponse,
    UpdateQuestionResponse,
)
from app.vote.repository.vote_repository import VoteRepository


async def create_question(request: CreateQuestionRequest, users_seq: str, db: AsyncSession) -> CreateQuestionResponse:
    async def create_question_action() -> CreateQuestionResponse:
        new_question = Question(
            users_seq=users_seq,
            title=request.title,
            description=request.description or None,
            is_anonymous=request.is_anonymous,
            status=QuestionStatus.OPEN.value,
            active=True,
            created_by=users_seq,
            updated_by=users_seq,
        )
        saved_question = await QuestionRepository.save(db, new_question)
        options = [
            Options.create(saved_question.question_seq, option, users_seq)
            for option in request.options
        ]
        await OptionsRepository.save_all(db, options)
        return CreateQuestionResponse(question_seq=saved_question.question_seq)

    return await run_in_transaction(db, create_question_action, "질문 생성 중 오류가 발생했습니다")


async def get_question(question_seq: int, users_seq: str, db: AsyncSession) -> GetQuestionResponse:
    question_detail = await QuestionRepository.find_detail_by_question_seq(db, question_seq, users_seq)
    if question_detail is None:
        raise BaseAPIException(ErrorCode.QUESTION_NOT_FOUND)

    return GetQuestionResponse.from_detail_dto(question_detail, users_seq)


async def update_question(
        question_seq: int,
        request: UpdateQuestionRequest,
        users_seq: str,
        db: AsyncSession,
) -> UpdateQuestionResponse:
    stale_exception = BaseAPIException(ErrorCode.QUESTION_STALE)

    async def update_question_action() -> UpdateQuestionResponse:
        question = await QuestionRepository.find_by_question_seq_for_update(db, question_seq)
        if question is None:
            raise BaseAPIException(ErrorCode.QUESTION_NOT_FOUND)
        if question.users_seq != users_seq:
            raise BaseAPIException(ErrorCode.QUESTION_UPDATE_FORBIDDEN)
        if question.version != request.version:
            raise BaseAPIException(ErrorCode.QUESTION_STALE)
        if question.status != QuestionStatus.OPEN.value:
            raise BaseAPIException(ErrorCode.VOTE_ALREADY_CLOSED)

        existing_options = await OptionsRepository.find_all_by_question_seq(db, question_seq)
        existing_options_by_seq = {
            option.options_seq: option
            for option in existing_options
        }

        update_option_requests = []
        insert_options = []
        update_option_seqs = set()

        for option in request.options:
            if option.options_seq is None:
                insert_options.append(Options.create(question_seq, option.content, users_seq))
                continue

            if option.options_seq in update_option_seqs:
                raise BaseAPIException(ErrorCode.DUPLICATE_OPTION_SEQ)

            update_option_seqs.add(option.options_seq)
            update_option_requests.append(option)

        if not update_option_seqs.issubset(existing_options_by_seq):
            raise BaseAPIException(ErrorCode.OPTION_NOT_IN_QUESTION)

        delete_option_seqs = existing_options_by_seq.keys() - update_option_seqs
        change_option_seqs = {
            option.options_seq
            for option in update_option_requests
            if existing_options_by_seq[option.options_seq].content != option.content
        }
        if await VoteRepository.exists_active_by_question_seq_and_options_seqs(db, question_seq, change_option_seqs):
            raise BaseAPIException(ErrorCode.OPTION_HAS_VOTES)

        question.update(
            title=request.title,
            description=request.description,
            is_anonymous=request.is_anonymous,
            updated_by=users_seq,
        )

        for option_request in update_option_requests:
            option = existing_options_by_seq[option_request.options_seq]
            option.update_content(option_request.content, users_seq)

        await OptionsRepository.deactivate_by_options_seqs(db, question_seq, delete_option_seqs, users_seq)
        await VoteRepository.deactivate_by_question_seq_and_options_seqs(db, question_seq, delete_option_seqs, users_seq)

        if insert_options:
            await OptionsRepository.save_all(db, insert_options)

        await db.flush()
        await db.refresh(question)
        return UpdateQuestionResponse(version=question.version)

    return await run_in_transaction(
        db,
        update_question_action,
        "질문 수정 중 오류가 발생했습니다",
        stale_exception=stale_exception,
    )


async def delete_question(question_seq: int, users_seq: str, db: AsyncSession) -> None:
    stale_exception = BaseAPIException(ErrorCode.QUESTION_STALE)

    async def delete_question_action() -> None:
        question = await QuestionRepository.find_by_question_seq_for_update(db, question_seq)
        if question is None:
            raise BaseAPIException(ErrorCode.QUESTION_NOT_FOUND)
        if question.users_seq != users_seq:
            raise BaseAPIException(ErrorCode.QUESTION_DELETE_FORBIDDEN)

        question.deactivate(users_seq)
        await OptionsRepository.deactivate_by_question_seq(db, question_seq, users_seq)
        await VoteRepository.deactivate_by_question_seq(db, question_seq, users_seq)

    await run_in_transaction(
        db,
        delete_question_action,
        "질문 삭제 중 오류가 발생했습니다",
        stale_exception=stale_exception,
    )
