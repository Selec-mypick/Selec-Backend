from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.base.base_response import BaseResponse
from app.core.connection_config import get_db
from app.users.dependency.jwt_users import get_jwt_users
from app.users.schema.jwt_users import JwtUsers
from app.question.schema.request.question_request import CreateQuestionRequest, UpdateQuestionRequest
from app.question.schema.response.question_response import GetQuestionResponse
from app.question.service.question_service import create_question, delete_question, get_question, update_question

router = APIRouter(prefix="/api/question", tags=["QUESTION"])


@router.post("", response_model=BaseResponse[dict])
async def create_question_endpoint(
        request: CreateQuestionRequest,
        jwt_users: JwtUsers = Depends(get_jwt_users),
        db: AsyncSession = Depends(get_db),
):
    """
    질문 생성
    """
    await create_question(request, jwt_users.users_seq, db)
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


@router.delete("/{question_seq}", response_model=BaseResponse[dict])
async def delete_question_endpoint(question_seq: int = Path(..., gt=0, description="질문 시퀀스"), db: AsyncSession = Depends(get_db)):
    """
    질문 삭제
    """
    await delete_question(question_seq, db)
    return BaseResponse.of_success(status.HTTP_200_OK, "SUCCESS")
