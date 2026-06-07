import aiohttp

from app.core.exceptions import BaseAPIException, ErrorCode
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
                        message = error.get("message") or ErrorCode.GEMINI_API_BAD_REQUEST.message
                        raise BaseAPIException(ErrorCode.GEMINI_API_BAD_REQUEST, message=message)
                    return data
        except BaseAPIException:
            raise
        except ValueError as e:
            raise BaseAPIException(ErrorCode.GEMINI_API_CALL_FAILED, message=str(e))
        except Exception as e:
            raise BaseAPIException(
                ErrorCode.GEMINI_API_CALL_FAILED,
                message=f"{ErrorCode.GEMINI_API_CALL_FAILED.message}: {str(e)}",
            )
