from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import StaleDataError

from app.core.exception import ServerException, BadRequestException, NotFoundException, ConflictException
from app.options.models.options import Options
from app.options.repository.options_repository import OptionsRepository
from app.question.models.question import Question
from app.question.repository.question_repository import QuestionRepository
from app.question.schema.request.question_request import CreateQuestionRequest, UpdateQuestionRequest
from app.question.schema.response.question_response import GetQuestionResponse
from app.users.repository.users_repository import UsersRepository
from app.vote.repository.vote_repository import VoteRepository


async def create_question(request: CreateQuestionRequest, db: AsyncSession) -> None:
    users = await UsersRepository.find_by_user_seq(db, request.user_seq)
    if users is None:
        raise BadRequestException("존재하지 않는 사용자입니다.")

    new_question = Question(
        user_seq=request.user_seq,
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


async def get_question(question_seq: int, db: AsyncSession) -> GetQuestionResponse:
    question = await QuestionRepository.find_by_question_seq(db, question_seq)
    if question is None:
        raise NotFoundException("존재하지 않는 질문입니다.")

    options = await OptionsRepository.find_all_by_question_seq(db, question_seq)

    return GetQuestionResponse.from_entity(question, options)


async def update_question(question_seq: int, request: UpdateQuestionRequest, db: AsyncSession) -> GetQuestionResponse:
    question = await QuestionRepository.find_by_question_seq(db, question_seq)
    if question is None:
        raise NotFoundException("존재하지 않는 질문입니다.")
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

    delete_votes = await VoteRepository.find_all_by_question_seq_and_options_seqs(
        db=db,
        question_seq=question_seq,
        options_seqs=delete_option_seqs,
    )

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

        for options_seq in delete_option_seqs:
            existing_options_by_seq[options_seq].deactivate()

        for vote in delete_votes:
            vote.deactivate()

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


async def delete_question(question_seq: int, db: AsyncSession) -> None:
    question = await QuestionRepository.find_by_question_seq(db, question_seq)
    if question is None:
        raise NotFoundException("존재하지 않는 질문입니다.")

    options = await OptionsRepository.find_all_by_question_seq(db, question_seq)
    votes = await VoteRepository.find_all_by_question_seq(db, question_seq)

    try:
        question.deactivate()

        for option in options:
            option.deactivate()

        for vote in votes:
            vote.deactivate()

        await db.commit()
    except Exception as e:
        await db.rollback()
        raise ServerException(f"질문 삭제 중 오류가 발생했습니다: {str(e)}")
