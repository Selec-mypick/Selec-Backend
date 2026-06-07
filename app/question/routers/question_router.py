from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.base.constants import BaseUtil
from app.base.response import BaseResponse
from app.base.response import AUTHENTICATED_RESPONSES, QUESTION_READ_RESPONSES, QUESTION_WRITE_RESPONSES
from app.core.database import get_db
from app.users.dependency.jwt_users import get_jwt_users
from app.users.schema.dto.jwt_users import JwtUsers
from app.question.schema.request.question_request import CreateQuestionRequest, UpdateQuestionRequest
from app.question.schema.response.question_response import (
    CreateQuestionResponse,
    GetQuestionResponse,
    GetQuestionVoteResultResponse,
)
from app.question.service.question_service import (
    create_question,
    delete_question,
    get_question,
    get_question_result,
    update_question,
)

router = APIRouter(prefix="/api/question", tags=["QUESTION"])


@router.post(
    "",
    response_model=BaseResponse[CreateQuestionResponse],
    status_code=status.HTTP_201_CREATED,
    responses=AUTHENTICATED_RESPONSES,
)
async def create_question_endpoint(
        request: CreateQuestionRequest,
        jwt_users: JwtUsers = Depends(get_jwt_users),
        db: AsyncSession = Depends(get_db),
):
    """
    질문 생성

    JWT 토큰으로 인증된 사용자가 질문과 선택지를 생성합니다.

    **Response**
    - `201`: 질문 생성 성공
    - `400`: 잘못된 요청
    - `401`: 인증 실패
    - `500`: 서버 오류
    """
    result = await create_question(request, jwt_users.users_seq, db)
    return BaseResponse.of(status.HTTP_201_CREATED, BaseUtil.SUCCESS, result)


@router.get(
    "/{question_seq}",
    response_model=BaseResponse[GetQuestionResponse],
    responses=QUESTION_READ_RESPONSES,
)
async def get_question_endpoint(
        question_seq: int = Path(..., gt=0, description="질문 시퀀스"),
        jwt_users: JwtUsers = Depends(get_jwt_users),
        db: AsyncSession = Depends(get_db),
):
    """
    질문 단건 조회

    질문 작성자이거나 본인이 해당 질문에 투표한 경우 각 선택지의 `vote_count`가 함께 반환됩니다.

    **Response**
    - `200`: 조회 성공
    - `401`: 인증 실패
    - `404`: 존재하지 않는 질문
    - `500`: 서버 오류
    """
    result = await get_question(question_seq, jwt_users.users_seq, db)
    return BaseResponse.of(status.HTTP_200_OK, BaseUtil.SUCCESS, result)


@router.get(
    "/{question_seq}/result",
    response_model=BaseResponse[GetQuestionVoteResultResponse],
    responses=QUESTION_READ_RESPONSES,
)
async def get_question_result_endpoint(
        question_seq: int = Path(..., gt=0, description="질문 시퀀스"),
        jwt_users: JwtUsers = Depends(get_jwt_users),
        db: AsyncSession = Depends(get_db),
):
    """
    질문 투표 결과 조회

    비익명 질문에 본인이 투표를 완료한 경우 옵션별 투표자 목록을 조회합니다.

    **Response**
    - `200`: 조회 성공
    - `401`: 인증 실패
    - `403`: 익명 질문, 미투표 상태
    - `404`: 존재하지 않는 질문
    - `500`: 서버 오류
    """
    result = await get_question_result(question_seq, jwt_users.users_seq, db)
    return BaseResponse.of(status.HTTP_200_OK, BaseUtil.SUCCESS, result)


@router.put(
    "/{question_seq}",
    response_model=BaseResponse[GetQuestionResponse],
    responses=QUESTION_WRITE_RESPONSES,
)
async def update_question_endpoint(
        request: UpdateQuestionRequest,
        question_seq: int = Path(..., gt=0, description="질문 시퀀스"),
        jwt_users: JwtUsers = Depends(get_jwt_users),
        db: AsyncSession = Depends(get_db),
):
    """
    질문 수정

    **Response**
    - `200`: 수정 성공
    - `400`: 종료된 투표, 유효하지 않은 선택지, 이미 투표된 선택지 수정 시도
    - `401`: 인증 실패
    - `404`: 존재하지 않는 질문
    - `409`: 버전 충돌 (낙관적 락)
    - `500`: 서버 오류
    """
    result = await update_question(question_seq, request, jwt_users.users_seq, db)
    return BaseResponse.of(status.HTTP_200_OK, BaseUtil.SUCCESS, result)


@router.delete(
    "/{question_seq}",
    response_model=BaseResponse[dict],
    responses=QUESTION_READ_RESPONSES,
)
async def delete_question_endpoint(
        question_seq: int = Path(..., gt=0, description="질문 시퀀스"),
        jwt_users: JwtUsers = Depends(get_jwt_users),
        db: AsyncSession = Depends(get_db),
):
    """
    질문 삭제

    **Response**
    - `200`: 삭제 성공
    - `404`: 존재하지 않는 질문
    - `500`: 서버 오류
    """
    await delete_question(question_seq, jwt_users.users_seq, db)
    return BaseResponse.of(status.HTTP_200_OK, BaseUtil.SUCCESS)
