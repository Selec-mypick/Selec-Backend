from html import escape
from pathlib import Path as FilePath
from string import Template
from uuid import UUID

from fastapi import APIRouter, Path, Request
from fastapi.responses import HTMLResponse

from config import settings

router = APIRouter(tags=["DEEPLINK"])
TEMPLATE_PATH = FilePath(__file__).resolve().parents[1] / "templates" / "question_install.html"


def _detect_platform(user_agent: str) -> str:
    normalized = user_agent.lower()
    if "iphone" in normalized or "ipad" in normalized or "ipod" in normalized:
        return "ios"
    if "android" in normalized:
        return "android"
    return "web"


def _install_context(platform: str) -> dict[str, str]:
    if platform == "ios":
        return {
            "platform_message": "iPhone에서 Selec 앱으로 질문을 열 수 있습니다.",
            "primary_install_url": settings.app_ios_install_url,
            "primary_button_label": "App Store에서 설치",
        }

    if platform == "android":
        return {
            "platform_message": "Android에서 Selec 앱으로 질문을 열 수 있습니다.",
            "primary_install_url": settings.app_android_install_url,
            "primary_button_label": "Google Play에서 설치",
        }

    return {
        "platform_message": "모바일 기기에서 Selec 앱을 설치하고 질문을 열어보세요.",
        "primary_install_url": settings.app_install_url,
        "primary_button_label": "앱 설치 페이지로 이동",
    }


@router.get("/deeplink/{question_seq}", response_class=HTMLResponse)
async def question_deeplink_fallback(
        request: Request,
        question_seq: UUID = Path(..., description="질문 UUID"),
):
    platform = _detect_platform(request.headers.get("user-agent", ""))
    context = _install_context(platform)
    template = Template(TEMPLATE_PATH.read_text(encoding="utf-8"))

    return template.safe_substitute(
        question_id=escape(str(question_seq)),
        platform_message=escape(context["platform_message"]),
        primary_install_url=escape(context["primary_install_url"], quote=True),
        primary_button_label=escape(context["primary_button_label"]),
    )
