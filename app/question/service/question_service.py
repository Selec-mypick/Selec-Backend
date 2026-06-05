from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import ServerException, BadRequestException, NotFoundException
from app.options.models.options import Options
from app.options.repository.options_repository import OptionsRepository
from app.question.models.question import Question
from app.question.repository.question_repository import QuestionRepository
from app.question.schema.request.question_request import CreateQuestionRequest, UpdateQuestionRequest
from app.question.schema.response.question_response import GetQuestionResponse
from app.users.repository.users_repository import UsersRepository


async def create_question(request: CreateQuestionRequest, db: AsyncSession) -> None:
    users = await UsersRepository.find_by_user_seq(db, request.user_seq)
    if users is None:
        raise BadRequestException("존재하지 않는 사용자입니다.")

    new_question = Question(
        user_seq=request.user_seq,
        title=request.title,
        description=request.description or None,
        is_multiple=request.is_multiple,
        is_anonymous=request.is_anonymous,
        status='OPEN',
        active=True
    )

    try:
        saved_question = await QuestionRepository.save(db, new_question)
        options = [
            Options(
                question_seq=saved_question.question_seq,
                content=option,
                active=True,
            )
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

    existing_options = await OptionsRepository.find_all_by_question_seq(db, question_seq)
    existing_options_by_seq = {
        option.options_seq: option
        for option in existing_options
    }

    requested_option_seqs = set()
    new_options = []

    question.update(
        title=request.title,
        description=request.description,
        is_multiple=request.is_multiple,
        is_anonymous=request.is_anonymous,
    )

    try:
        for option_request in request.options:
            if option_request.options_seq is None:
                new_options.append(
                    Options(
                        question_seq=question_seq,
                        content=option_request.content,
                        active=True,
                    )
                )
                continue

            if option_request.options_seq in requested_option_seqs:
                raise BadRequestException("중복된 선택지 시퀀스가 포함되어 있습니다.")

            option = existing_options_by_seq.get(option_request.options_seq)
            if option is None:
                raise BadRequestException("질문에 속하지 않는 선택지입니다.")

            requested_option_seqs.add(option_request.options_seq)
            option.update_content(option_request.content)

        for option in existing_options:
            if option.options_seq not in requested_option_seqs:
                option.deactivate()

        if new_options:
            await OptionsRepository.save_all(db, new_options)

        await db.commit()
    except BadRequestException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise ServerException(f"질문 수정 중 오류가 발생했습니다: {str(e)}")

    return await get_question(question_seq, db)
