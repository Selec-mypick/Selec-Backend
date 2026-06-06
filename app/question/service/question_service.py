from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError

from app.core.exception import ServerException, BadRequestException, NotFoundException, ConflictException, ForbiddenException
from app.options.models.options import Options
from app.options.repository.options_repository import OptionsRepository
from app.question.models.question import Question
from app.question.repository.question_repository import QuestionRepository
from app.question.schema.request.question_request import CreateQuestionRequest, UpdateQuestionRequest
from app.question.schema.response.question_response import GetQuestionResponse
from app.vote.repository.vote_repository import VoteRepository


async def create_question(request: CreateQuestionRequest, users_seq: int, db: AsyncSession) -> None:
    new_question = Question(
        users_seq=users_seq,
        title=request.title,
        description=request.description or None,
        is_anonymous=request.is_anonymous,
        status='OPEN',
        active=True
    )

    try:
        saved_question = await QuestionRepository.save(db, new_question)
        options = [
            Options.create(saved_question.question_seq, option)
            for option in request.options
        ]
        await OptionsRepository.save_all(db, options)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise ServerException(f"질문 생성 중 오류가 발생했습니다: {str(e)}")


async def get_question(question_seq: int, users_seq: int, db: AsyncSession) -> GetQuestionResponse:
    question_detail = await QuestionRepository.find_detail_by_question_seq(db, question_seq, users_seq)
    if question_detail is None:
        raise NotFoundException("존재하지 않는 질문입니다.")

    question, option_rows = question_detail
    return GetQuestionResponse.from_detail_rows(question, option_rows)


async def update_question(
        question_seq: int,
        request: UpdateQuestionRequest,
        users_seq: int,
        db: AsyncSession,
) -> GetQuestionResponse:
    question = await QuestionRepository.find_by_question_seq(db, question_seq)
    if question is None:
        raise NotFoundException("존재하지 않는 질문입니다.")
    if question.users_seq != users_seq:
        raise ForbiddenException("질문 수정 권한이 없습니다.")
    if question.version != request.version:
        raise ConflictException("이미 수정된 질문입니다. 최신 질문 정보를 다시 조회해주세요.")
    if question.status != 'OPEN':
        raise BadRequestException("이미 종료된 투표입니다.")

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
            insert_options.append(Options.create(question_seq, option.content))
            continue

        if option.options_seq in update_option_seqs:
            raise BadRequestException("중복된 선택지 시퀀스가 포함되어 있습니다.")

        update_option_seqs.add(option.options_seq)
        update_option_requests.append(option)

    if not update_option_seqs.issubset(existing_options_by_seq):
        raise BadRequestException("질문에 속하지 않는 선택지입니다.")

    delete_option_seqs = existing_options_by_seq.keys() - update_option_seqs
    change_option_seqs = {
        option.options_seq
        for option in update_option_requests
        if existing_options_by_seq[option.options_seq].content != option.content
    }
    if await VoteRepository.exists_active_by_question_seq_and_options_seqs(db, question_seq, change_option_seqs):
        raise BadRequestException("이미 투표가 존재하는 선택지는 수정할 수 없습니다.")

    response_options = []

    try:
        question.update(
            title=request.title,
            description=request.description,
            is_anonymous=request.is_anonymous,
        )

        for option_request in update_option_requests:
            option = existing_options_by_seq[option_request.options_seq]
            option.update_content(option_request.content)
            response_options.append(option)

        await OptionsRepository.deactivate_by_options_seqs(db, question_seq, delete_option_seqs)
        await VoteRepository.deactivate_by_question_seq_and_options_seqs(db, question_seq, delete_option_seqs)

        if insert_options:
            await OptionsRepository.save_all(db, insert_options)
            response_options.extend(insert_options)

        await db.commit()
    except StaleDataError:
        await db.rollback()
        raise ConflictException("이미 수정된 질문입니다. 최신 질문 정보를 다시 조회해주세요.")
    except Exception as e:
        await db.rollback()
        raise ServerException(f"질문 수정 중 오류가 발생했습니다: {str(e)}")

    return GetQuestionResponse.from_entity(question, response_options)


async def delete_question(question_seq: int, users_seq: int, db: AsyncSession) -> None:
    question = await QuestionRepository.find_by_question_seq(db, question_seq)
    if question is None:
        raise NotFoundException("존재하지 않는 질문입니다.")
    if question.users_seq != users_seq:
        raise ForbiddenException("질문 삭제 권한이 없습니다.")

    try:
        question.deactivate()
        await OptionsRepository.deactivate_by_question_seq(db, question_seq)
        await VoteRepository.deactivate_by_question_seq(db, question_seq)

        await db.commit()
    except StaleDataError:
        await db.rollback()
        raise ConflictException("이미 수정된 질문입니다. 최신 질문 정보를 다시 조회해주세요.")
    except Exception as e:
        await db.rollback()
        raise ServerException(f"질문 삭제 중 오류가 발생했습니다: {str(e)}")
