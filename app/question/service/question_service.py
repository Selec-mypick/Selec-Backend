from sqlalchemy.ext.asyncio import AsyncSession

from app.base.response import PageResponse
from app.core.database.transaction import run_in_transaction
from app.core.exceptions import BaseAPIException, ErrorCode
from app.options.models.options import Options
from app.options.repository.options_repository import OptionsRepository
from app.question.models.question import Question
from app.question.repository.question_repository import QuestionRepository
from app.question.schema.request.question_request import CreateQuestionRequest, UpdateQuestionRequest
from app.question.schema.response.question_response import (
    CreateQuestionResponse,
    GetQuestionResponse,
    UpdateQuestionResponse,
)
from app.question_invited.repository.question_invited_repository import QuestionInvitedRepository
from app.vote.repository.vote_repository import VoteRepository
from config import settings


async def create_question(request: CreateQuestionRequest, users_seq: str, db: AsyncSession) -> CreateQuestionResponse:
    async def create_question_action() -> CreateQuestionResponse:
        question_seq = Question.generate_question_seq()
        share_url = f"{settings.service_base_url}/deeplink/{question_seq}"
        new_question = Question(
            question_seq=question_seq,
            users_seq=users_seq,
            share_url=share_url,
            title=request.title,
            description=request.description or None,
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
        await QuestionInvitedRepository.upsert(db, saved_question.question_seq, users_seq)
        return CreateQuestionResponse(
            question_seq=saved_question.question_seq,
            share_url=saved_question.share_url,
        )

    return await run_in_transaction(db, create_question_action, "질문 생성 중 오류가 발생했습니다")


async def get_question(question_seq: str, users_seq: str, db: AsyncSession) -> GetQuestionResponse:
    async def get_question_action() -> GetQuestionResponse:
        question_detail_rows = await QuestionRepository.find_details_by_question_seqs(db, [question_seq], users_seq)
        if not question_detail_rows:
            raise BaseAPIException(ErrorCode.QUESTION_NOT_FOUND)

        await QuestionInvitedRepository.upsert(db, question_seq, users_seq)

        return GetQuestionResponse.from_detail_rows(question_detail_rows, users_seq)

    return await run_in_transaction(db, get_question_action, "질문 조회 중 오류가 발생했습니다")


async def get_invited_questions(users_seq: str, page: int, size: int, db: AsyncSession) -> PageResponse[GetQuestionResponse]:
    total_elements = await QuestionRepository.count_invited_by_users_seq(db, users_seq)
    question_seqs = await QuestionRepository.find_invited_question_seqs_by_users_seq(db, users_seq, page, size)
    question_detail_rows = await QuestionRepository.find_details_by_question_seqs(db, question_seqs, users_seq)

    question_detail_rows_by_seq = {}
    for question, option, vote_count, selected_option_seq in question_detail_rows:
        question_seq = question.question_seq
        if question_seq not in question_detail_rows_by_seq:
            question_detail_rows_by_seq[question_seq] = []
        question_detail_rows_by_seq[question_seq].append((question, option, vote_count, selected_option_seq))

    question_detail_rows_list = [
        question_detail_rows_by_seq[question_seq]
        for question_seq in question_seqs
        if question_seq in question_detail_rows_by_seq
    ]
    content = [
        GetQuestionResponse.from_detail_rows(rows, users_seq)
        for rows in question_detail_rows_list
    ]
    return PageResponse.of(content, page, size, total_elements)


async def update_question(
        question_seq: str,
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


async def delete_question(question_seq: str, users_seq: str, db: AsyncSession) -> None:
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
        await QuestionInvitedRepository.deactivate_by_question_seq(db, question_seq, users_seq)

    await run_in_transaction(
        db,
        delete_question_action,
        "질문 삭제 중 오류가 발생했습니다",
        stale_exception=stale_exception,
    )
