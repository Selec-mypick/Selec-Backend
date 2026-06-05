from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import ServerException, BadRequestException, NotFoundException
from app.options.models.options import Options
from app.options.repository.options_repository import OptionsRepository
from app.options.schema.response.options_response import GetOptionResponse
from app.question.models.question import Question
from app.question.repository.question_repository import QuestionRepository
from app.question.schema.request.question_request import CreateQuestionRequest
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

    return GetQuestionResponse(
        question_seq=question.question_seq,
        user_seq=question.user_seq,
        title=question.title,
        description=question.description,
        is_multiple=question.is_multiple,
        is_anonymous=question.is_anonymous,
        status=question.status,
        active=question.active,
        created_at=question.created_at,
        updated_at=question.updated_at,
        options=[
            GetOptionResponse(
                options_seq=option.options_seq,
                question_seq=option.question_seq,
                content=option.content,
                active=option.active,
                created_at=option.created_at,
                updated_at=option.updated_at,
            )
            for option in options
        ],
    )
