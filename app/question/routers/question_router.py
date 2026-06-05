from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.base.base_response import BaseResponse
from app.core.connection_config import get_db
from app.question.schema.request.question_request import CreateQuestionRequest, UpdateQuestionRequest
from app.question.schema.response.question_response import GetQuestionResponse
from app.question.service.question_service import create_question, get_question, update_question

router = APIRouter(prefix="/api/question", tags=["QUESTION"])


@router.post("", response_model=BaseResponse[dict])
async def create_question_endpoint(request: CreateQuestionRequest, db: AsyncSession = Depends(get_db)):
    """
    질문 생성

    사용자 시퀀스와 질문 정보를 입력받아 질문을 생성합니다.
    """
    await create_question(request, db)
    return BaseResponse.of_success(status.HTTP_201_CREATED, "SUCCESS")


@router.get("/{question_seq}", response_model=BaseResponse[GetQuestionResponse])
async def get_question_endpoint(question_seq: int = Path(..., gt=0, description="질문 시퀀스"), db: AsyncSession = Depends(get_db)):
    """
    질문 단건 조회
    """
    result = await get_question(question_seq, db)
    return BaseResponse.of(status.HTTP_200_OK, "SUCCESS", result)


@router.put("/{question_seq}", response_model=BaseResponse[GetQuestionResponse])
async def update_question_endpoint(request: UpdateQuestionRequest, question_seq: int = Path(..., gt=0, description="질문 시퀀스"), db: AsyncSession = Depends(get_db)):
    """
    질문 수정
    """
    result = await update_question(question_seq, request, db)
    return BaseResponse.of(status.HTTP_200_OK, "SUCCESS", result)
