from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.base.base_response import BaseResponse
from app.core.connection_config import get_db
from app.vote.schema.request.vote_request import CreateVoteRequest
from app.vote.service.vote_service import create_vote


router = APIRouter(prefix="/api/vote", tags=["VOTE"])


@router.post("", response_model=BaseResponse[dict])
async def create_vote_endpoint(request: CreateVoteRequest, db: AsyncSession = Depends(get_db)):
    """
    투표 생성
    """
    await create_vote(request, db)
    return BaseResponse.of_success(status.HTTP_201_CREATED, "SUCCESS")
