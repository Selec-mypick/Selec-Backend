import json
import re
from pathlib import Path

from scheduler.client.gemini_client import GeminiClient
from scheduler.jobs.gemini_vote_create.config import BATCH_USERS_SEQ
from app.core.database.session import AsyncSessionLocal
from app.core.exceptions import ServerException
from app.question.schema.request.question_request import CreateQuestionRequest
from app.question.service.question_service import create_question
from config import settings

PROMPT_PATH = Path(__file__).resolve().parent / "prompt.txt"


async def create_question_from_gemini() -> None:
    model = settings.gemini_model

    if not model:
        raise ServerException("GEMINI_MODEL 환경변수가 설정되어 있지 않습니다.")

    if not PROMPT_PATH.exists():
        raise ServerException("Gemini 프롬프트 파일을 찾을 수 없습니다.")

    prompt = PROMPT_PATH.read_text(encoding="utf-8").strip()

    if not prompt:
        raise ServerException("Gemini 프롬프트 파일이 비어 있습니다.")

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

    # Gemini가 ```json ... ``` 코드블록으로 감싸는 경우 제거
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    text = text.strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        raise ServerException(f"Gemini 응답이 JSON 형식이 아닙니다. 응답값: {text}")

    title = parsed.get("title")
    description = parsed.get("description")
    is_anonymous = parsed.get("is_anonymous")
    options = parsed.get("options")

    if not isinstance(title, str) or not title.strip():
        raise ServerException("Gemini 응답의 title 값이 올바르지 않습니다.")

    if not isinstance(description, str) or not description.strip():
        raise ServerException("Gemini 응답의 description 값이 올바르지 않습니다.")

    if is_anonymous is not True:
        raise ServerException("Gemini 응답의 is_anonymous 값은 true여야 합니다.")

    if not isinstance(options, list):
        raise ServerException("Gemini 응답의 options 값이 배열이 아닙니다.")

    if len(options) < 3 or len(options) > 5:
        raise ServerException("Gemini 응답의 options 개수는 3개 이상 5개 이하이어야 합니다.")

    if any(not isinstance(option, str) or not option.strip() for option in options):
        raise ServerException("Gemini 응답의 options 항목이 올바르지 않습니다.")

    if len(set(options)) != len(options):
        raise ServerException("Gemini 응답의 options에 중복 값이 있습니다.")

    request = CreateQuestionRequest(
        title=title.strip(),
        description=description.strip(),
        is_anonymous=True,
        options=[option.strip() for option in options],
    )

    async with AsyncSessionLocal() as db:
        await create_question(request, BATCH_USERS_SEQ, db)
