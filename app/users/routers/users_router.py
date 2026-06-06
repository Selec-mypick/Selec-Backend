from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.base.constants import BaseUtil
from app.base.response import BaseResponse
from app.base.response import AUTHENTICATED_RESPONSES
from app.core.database import get_db
from app.users.dependency.jwt_users import get_jwt_users
from app.users.schema.dto.jwt_users import JwtUsers
from app.users.schema.request.users_request import UpdateMyInfoRequest
from app.users.schema.response.users_response import GetMyInfoResponse
from app.users.services.user_service import get_my_info, update_my_info

router = APIRouter(prefix="/api/users", tags=["USERS"])


@router.get(
    "/me",
    response_model=BaseResponse[GetMyInfoResponse],
    status_code=status.HTTP_200_OK,
    responses=AUTHENTICATED_RESPONSES,
)
async def get_my_info_endpoint(
        jwt_users: JwtUsers = Depends(get_jwt_users),
        db: AsyncSession = Depends(get_db),
):
    """
    내 정보 조회

    JWT 토큰으로 인증된 사용자의 기본 정보를 조회합니다.
    """
    result = await get_my_info(jwt_users.users_seq, db)
    return BaseResponse.of(status.HTTP_200_OK, BaseUtil.SUCCESS, result)


@router.put(
    "",
    response_model=BaseResponse[GetMyInfoResponse],
    status_code=status.HTTP_200_OK,
    responses=AUTHENTICATED_RESPONSES,
)
async def update_my_info_endpoint(
        request: UpdateMyInfoRequest,
        jwt_users: JwtUsers = Depends(get_jwt_users),
        db: AsyncSession = Depends(get_db),
):
    """
    회원 정보 수정

    JWT 토큰으로 인증된 사용자의 닉네임을 수정합니다.
    """
    result = await update_my_info(jwt_users.users_seq, request, db)
    return BaseResponse.of(status.HTTP_200_OK, BaseUtil.SUCCESS, result)
