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
async def generate_gemini_response_endpoint(request: GeminiPromptRequest | None = None):
    """
    Gemini 프롬프트 실행

    전달받은 프롬프트를 Gemini API로 전송하고 생성된 텍스트를 반환합니다.
    """
    if request is None:
        request = GeminiPromptRequest()

    result = await generate_gemini_response(request)
    return BaseResponse.of(status.HTTP_200_OK, BaseUtil.SUCCESS, result)