from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.base.base_response import BaseResponse
from app.core.connection_config import get_db
from app.question.schema.request.question_request import CreateQuestionRequest
from app.question.service.question_service import create_question

router = APIRouter(prefix="/api/question", tags=["QUESTION"])


@router.post("", response_model=BaseResponse[dict])
async def create_question_endpoint(request: CreateQuestionRequest, db: AsyncSession = Depends(get_db)):
    """
    질문 생성

    사용자 시퀀스와 질문 정보를 입력받아 질문을 생성합니다.
    """
    await create_question(request, db)
    return BaseResponse.of_success(status.HTTP_201_CREATED, "SUCCESS")
