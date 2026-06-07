from fastapi import APIRouter, status

from app.base.constants import BaseUtil
from app.base.response import AUTHENTICATED_RESPONSES, BaseResponse
from app.batch.schema.request.batch_request import GeminiPromptRequest
from app.batch.schema.response.batch_response import GeminiPromptResponse
from app.batch.service.batch_service import generate_gemini_response

router = APIRouter(prefix="/api/batch", tags=["BATCH"])


@router.post(
    "/gemini",
    response_model=BaseResponse[GeminiPromptResponse],
    status_code=status.HTTP_200_OK,
    responses=AUTHENTICATED_RESPONSES,
)
async def generate_gemini_response_endpoint():
    """
    Gemini 투표 생성

    서버에 저장된 프롬프트 파일과 환경변수의 Gemini 모델을 사용해
    투표 생성 결과를 반환합니다.
    """
    result = await generate_gemini_response()
    return BaseResponse.of(status.HTTP_200_OK, BaseUtil.SUCCESS, result)
