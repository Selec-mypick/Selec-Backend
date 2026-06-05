from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exception import ServerException, BadRequestException
from app.options.models.options import Options
from app.options.repository.options_repository import OptionsRepository
from app.question.models.question import Question
from app.question.repository.question_repository import QuestionRepository
from app.users.repository.users_repository import UsersRepository
from app.question.schema.request.question_request import CreateQuestionRequest


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
