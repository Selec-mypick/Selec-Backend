from html import escape
from pathlib import Path as FilePath
from string import Template

from config import settings

TEMPLATE_PATH = FilePath(__file__).resolve().parents[1] / "templates" / "question_install.html"


def render_question_install_page(user_agent: str) -> str:
    normalized = user_agent.lower()
    if "iphone" in normalized or "ipad" in normalized or "ipod" in normalized:
        context = {
            "platform_message": "iPhone에서 Selec 앱으로 질문을 열 수 있습니다.",
            "primary_install_url": settings.app_ios_install_url,
            "primary_button_label": "App Store에서 설치",
        }
    elif "android" in normalized:
        context = {
            "platform_message": "Android에서 Selec 앱으로 질문을 열 수 있습니다.",
            "primary_install_url": settings.app_android_install_url,
            "primary_button_label": "Google Play에서 설치",
        }
    else:
        context = {
            "platform_message": "모바일 기기에서 Selec 앱을 설치하고 질문을 열어보세요.",
            "primary_install_url": settings.app_install_url,
            "primary_button_label": "앱 설치 페이지로 이동",
        }

    template = Template(TEMPLATE_PATH.read_text(encoding="utf-8"))
    return template.safe_substitute(
        platform_message=escape(context["platform_message"]),
        primary_install_url=escape(context["primary_install_url"], quote=True),
        primary_button_label=escape(context["primary_button_label"]),
    )
