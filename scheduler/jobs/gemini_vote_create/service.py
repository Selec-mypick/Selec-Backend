import json
import re
from pathlib import Path

from pydantic import ValidationError

from app.core.database.session import AsyncSessionLocal
from app.core.exceptions import ServerException
from app.question.schema.request.question_request import CreateQuestionRequest
from app.question.service.question_service import create_question
from config import settings
from scheduler.client.gemini_client import GeminiClient
from scheduler.jobs.gemini_vote_create.config import BATCH_USERS_SEQ

PROMPT_PATH = Path(__file__).resolve().parent / "prompt.txt"


class GeminiVoteCreateJob:
    """Gemini API로 투표 질문 JSON을 만들고 question 테이블에 저장한다."""

    def __init__(
            self,
            users_seq: str = BATCH_USERS_SEQ,
            prompt_path: Path = PROMPT_PATH,
            model: str | None = None,
    ) -> None:
        self.users_seq = users_seq
        self.prompt_path = prompt_path
        self.model = model or settings.gemini_model

    async def execute(self) -> None:
        if not self.model:
            raise ServerException("GEMINI_MODEL 환경변수가 설정되어 있지 않습니다.")

        prompt = self.read_prompt()
        response = await GeminiClient.generate_content(prompt, self.model)
        request = self.to_create_question_request(response)

        async with AsyncSessionLocal() as db:
            await create_question(request, users_seq=self.users_seq, db=db)

    def read_prompt(self) -> str:
        if not self.prompt_path.exists():
            raise ServerException("Gemini 프롬프트 파일을 찾을 수 없습니다.")

        prompt = self.prompt_path.read_text(encoding="utf-8").strip()
        if not prompt:
            raise ServerException("Gemini 프롬프트 파일이 비어 있습니다.")

        return prompt

    def to_create_question_request(self, data: dict) -> CreateQuestionRequest:
        text = self.extract_response_text(data)
        text = self.strip_code_fence(text)
        return self.parse_question_json(text)

    def extract_response_text(self, data: dict) -> str:
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

        return "".join(texts).strip()

    def strip_code_fence(self, text: str) -> str:
        text = re.sub(r"^```json\s*", "", text)
        text = re.sub(r"^```\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return text.strip()

    def parse_question_json(self, text: str) -> CreateQuestionRequest:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            raise ServerException(f"Gemini 응답이 JSON 형식이 아닙니다. 응답값: {text}")

        if parsed.get("is_anonymous") is not True:
            raise ServerException("Gemini 응답의 is_anonymous 값은 true여야 합니다.")

        options = parsed.get("options")
        if not isinstance(options, list):
            raise ServerException("Gemini 응답의 options 값이 배열이 아닙니다.")

        if len(options) < 3 or len(options) > 5:
            raise ServerException("Gemini 응답의 options 개수는 3개 이상 5개 이하이어야 합니다.")

        if any(not isinstance(option, str) or not option.strip() for option in options):
            raise ServerException("Gemini 응답의 options 항목이 올바르지 않습니다.")

        if len(set(options)) != len(options):
            raise ServerException("Gemini 응답의 options에 중복 값이 있습니다.")

        try:
            return CreateQuestionRequest(
                title=parsed.get("title"),
                description=parsed.get("description"),
                is_anonymous=True,
                options=[option.strip() for option in options],
            )
        except ValidationError as e:
            raise ServerException(f"Gemini 응답 필드 검증에 실패했습니다: {e}")
