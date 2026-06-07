from pathlib import Path

from app.batch.client.gemini_client import GeminiClient
from app.batch.schema.request.batch_request import GeminiPromptRequest
from app.batch.schema.response.batch_response import GeminiPromptResponse
from app.core.exceptions import ServerException
from config import settings


async def generate_gemini_response(request: GeminiPromptRequest) -> GeminiPromptResponse:
    model = request.model or settings.gemini_model

    prompt_path = Path("app/batch/prompt/prompt.txt")

    if not prompt_path.exists():
        raise ServerException("Gemini 프롬프트 파일을 찾을 수 없습니다.")

    prompt = prompt_path.read_text(encoding="utf-8").strip()

    data = await GeminiClient.generate_content(prompt, model)

    candidates = data.get("candidates") or []
    if not candidates:
        raise ServerException("Gemini API 응답에 candidates가 없습니다.")

    parts = candidates[0].get("content", {}).get("parts") or []
    texts = [
        part.get("text")
        for part in parts
        if isinstance(part, dict) and part.get("text")
    ]

    if not texts:
        raise ServerException("Gemini API 응답에서 text를 찾을 수 없습니다.")

    text = "".join(texts).strip()

    return GeminiPromptResponse(
        model=model,
        text=text,
    )
