from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.base.constants import BaseUtil
from app.base.response import BaseResponse
from app.base.response import VOTE_RESPONSES
from app.core.database import get_db
from app.users.dependency.users_seq import get_users_seq
from app.vote.schema.request.vote_request import CreateVoteRequest
from app.vote.schema.response.vote_response import GetVoteResultResponse
from app.vote.service.vote_service import create_vote, delete_vote, get_vote_result

router = APIRouter(prefix="/api/vote", tags=["VOTE"])


@router.post(
    "/{question_seq}",
    response_model=BaseResponse[dict],
    status_code=status.HTTP_201_CREATED,
    responses=VOTE_RESPONSES,
)
async def create_vote_endpoint(
        request: CreateVoteRequest,
        question_seq: int = Path(..., gt=0, description="질문 시퀀스"),
        users_seq: str = Depends(get_users_seq),
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
    await create_vote(question_seq, request, users_seq, db)
    return BaseResponse.of(status.HTTP_201_CREATED, BaseUtil.SUCCESS)


@router.get(
    "/{question_seq}/result",
    response_model=BaseResponse[GetVoteResultResponse],
    responses=VOTE_RESPONSES,
)
async def get_vote_result_endpoint(
        question_seq: int = Path(..., gt=0, description="질문 시퀀스"),
        users_seq: str = Depends(get_users_seq),
        db: AsyncSession = Depends(get_db),
):
    """
    투표 결과 조회

    익명 질문은 옵션별 투표 수만 조회하고, 비익명 질문은 권한이 있는 경우 투표자 목록까지 조회합니다.

    **Response**
    - `200`: 조회 성공
    - `401`: 인증 실패
    - `403`: 비익명 질문의 미투표 상태
    - `404`: 존재하지 않는 질문
    - `500`: 서버 오류
    """
    result = await get_vote_result(question_seq, users_seq, db)
    return BaseResponse.of(status.HTTP_200_OK, BaseUtil.SUCCESS, result)


@router.delete(
    "/{question_seq}",
    response_model=BaseResponse[dict],
    status_code=status.HTTP_200_OK,
    responses=VOTE_RESPONSES,
)
async def delete_vote_endpoint(
        question_seq: int = Path(..., gt=0, description="질문 시퀀스"),
        users_seq: str = Depends(get_users_seq),
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
    await delete_vote(question_seq, users_seq, db)
    return BaseResponse.of(status.HTTP_200_OK, BaseUtil.SUCCESS)
