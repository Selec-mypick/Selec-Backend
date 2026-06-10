import json
import re
from pathlib import Path

import logging

from pydantic import ValidationError

from app.core.cache.redis_lock import RedisLock
from app.core.database.session import AsyncSessionLocal
from app.core.exceptions import BaseAPIException, ErrorCode
from app.question.schema.request.question_request import CreateQuestionRequest
from app.question.service.question_service import create_question
from config import settings
from scheduler.client.gemini_client import GeminiClient
from scheduler.jobs.gemini_vote_create.config import BATCH_USERS_SEQ

logger = logging.getLogger(__name__)
PROMPT_PATH = Path(__file__).resolve().parent / "prompt.txt"
SCHEDULER_LOCK_KEY = "scheduler:lock:gemini_vote_create"
SCHEDULER_LOCK_TTL_SECONDS = 600


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
        async with RedisLock.hold(SCHEDULER_LOCK_KEY, ttl_seconds=SCHEDULER_LOCK_TTL_SECONDS) as acquired:
            if not acquired:
                logger.info("Gemini vote create job skipped because another instance is running")
                return

            if not self.model:
                raise BaseAPIException(ErrorCode.GEMINI_MODEL_NOT_CONFIGURED)

            prompt = self.read_prompt()
            response = await GeminiClient.generate_content(prompt, self.model)
            request = self.to_create_question_request(response)

            async with AsyncSessionLocal() as db:
                await create_question(request, users_seq=self.users_seq, db=db)

    def read_prompt(self) -> str:
        if not self.prompt_path.exists():
            raise BaseAPIException(ErrorCode.GEMINI_PROMPT_NOT_FOUND)

        prompt = self.prompt_path.read_text(encoding="utf-8").strip()
        if not prompt:
            raise BaseAPIException(ErrorCode.GEMINI_PROMPT_EMPTY)

        return prompt

    def to_create_question_request(self, data: dict) -> CreateQuestionRequest:
        text = self.extract_response_text(data)
        text = self.strip_code_fence(text)
        return self.parse_question_json(text)

    def extract_response_text(self, data: dict) -> str:
        candidates = data.get("candidates") or []
        if not candidates:
            raise BaseAPIException(ErrorCode.GEMINI_RESPONSE_NO_CANDIDATES)

        parts = candidates[0].get("content", {}).get("parts") or []
        texts = [
            part.get("text")
            for part in parts
            if isinstance(part, dict) and part.get("text")
        ]

        if not texts:
            raise BaseAPIException(ErrorCode.GEMINI_RESPONSE_NO_TEXT)

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
            raise BaseAPIException(
                ErrorCode.GEMINI_RESPONSE_INVALID_JSON,
                message=f"{ErrorCode.GEMINI_RESPONSE_INVALID_JSON.message}. 응답값: {text}",
            )

        options = parsed.get("options")
        if not isinstance(options, list):
            raise BaseAPIException(ErrorCode.GEMINI_RESPONSE_INVALID_OPTIONS_TYPE)

        if len(options) < 3 or len(options) > 5:
            raise BaseAPIException(ErrorCode.GEMINI_RESPONSE_INVALID_OPTIONS_COUNT)

        if any(not isinstance(option, str) or not option.strip() for option in options):
            raise BaseAPIException(ErrorCode.GEMINI_RESPONSE_INVALID_OPTIONS_ITEM)

        if len(set(options)) != len(options):
            raise BaseAPIException(ErrorCode.GEMINI_RESPONSE_DUPLICATE_OPTIONS)

        try:
            return CreateQuestionRequest(
                title=parsed.get("title"),
                description=parsed.get("description"),
                options=[option.strip() for option in options],
            )
        except ValidationError as e:
            raise BaseAPIException(
                ErrorCode.GEMINI_RESPONSE_FIELD_VALIDATION_FAILED,
                message=f"{ErrorCode.GEMINI_RESPONSE_FIELD_VALIDATION_FAILED.message}: {e}",
            )
