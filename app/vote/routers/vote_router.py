from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.base.base_response import BaseResponse
from app.base.openapi_responses import VOTE_RESPONSES
from app.core.connection_config import get_db
from app.users.dependency.jwt_users import get_jwt_users
from app.users.schema.jwt_users import JwtUsers
from app.vote.schema.request.vote_request import CreateVoteRequest
from app.vote.service.vote_service import create_vote, delete_vote

router = APIRouter(prefix="/api/vote", tags=["VOTE"])


@router.post(
    "",
    response_model=BaseResponse[dict],
    status_code=status.HTTP_201_CREATED,
    responses=VOTE_RESPONSES,
)
async def create_vote_endpoint(
        request: CreateVoteRequest,
        jwt_users: JwtUsers = Depends(get_jwt_users),
        db: AsyncSession = Depends(get_db),
):
    """
    투표 생성

    JWT 토큰으로 인증된 사용자가 질문에 투표합니다. 동일 질문에 재투표 시 선택지가 변경됩니다.

    **Response**
    - `201`: 투표 성공
    - `400`: 종료된 투표, 유효하지 않은 선택지
    - `401`: 인증 실패
    - `404`: 존재하지 않는 질문
    - `500`: 서버 오류
    """
    await create_vote(request, jwt_users.users_seq, db)
    return BaseResponse.of_success(status.HTTP_201_CREATED, "SUCCESS")


@router.delete(
    "/{question_seq}",
    response_model=BaseResponse[dict],
    status_code=status.HTTP_200_OK,
    responses=VOTE_RESPONSES,
)
async def delete_vote_endpoint(
        question_seq: int = Path(..., gt=0, description="질문 시퀀스"),
        jwt_users: JwtUsers = Depends(get_jwt_users),
        db: AsyncSession = Depends(get_db),
):
    """
    투표 취소

    JWT 토큰으로 인증된 사용자의 해당 질문 투표를 소프트 삭제합니다.

    **Response**
    - `200`: 투표 취소 성공
    - `401`: 인증 실패
    - `404`: 투표 내역 없음
    - `500`: 서버 오류
    """
    await delete_vote(question_seq, jwt_users.users_seq, db)
    return BaseResponse.of_success(status.HTTP_200_OK, "SUCCESS")
