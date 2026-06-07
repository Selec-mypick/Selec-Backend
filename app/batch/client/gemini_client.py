import aiohttp

from app.core.exceptions import BadRequestException, ServerException
from config import settings


class GeminiClient:
    @staticmethod
    async def generate_content(prompt: str, model: str | None = None) -> dict:
        model_name = model or settings.gemini_model
        url = f"{settings.gemini_api_base_url}/models/{model_name}:generateContent"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                    ],
                },
            ],
        }
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": settings.gemini_api_key,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=30) as response:
                    data = await response.json(content_type=None)
                    if response.status >= 400:
                        error = data.get("error", {}) if isinstance(data, dict) else {}
                        message = error.get("message") or "Gemini API 호출에 실패했습니다."
                        raise BadRequestException(message)
                    return data
        except BadRequestException:
            raise
        except ValueError as e:
            raise ServerException(str(e))
        except Exception as e:
            raise ServerException(f"Gemini API 호출 중 오류가 발생했습니다: {str(e)}")
