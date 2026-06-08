import json
from html import escape
from pathlib import Path as FilePath
from string import Template
from urllib.parse import quote
from uuid import UUID

from config import settings

TEMPLATE_PATH = FilePath(__file__).resolve().parents[1] / "templates" / "question_install.html"


def render_question_install_page(question_seq: UUID, user_agent: str) -> str:
    normalized = user_agent.lower()
    encoded_question_seq = escape(str(question_seq), quote=True)
    app_scheme_url = f"{settings.app_deeplink_scheme}://deeplink/{encoded_question_seq}"
    android_fallback_url = quote(settings.app_android_install_url, safe="")
    android_intent_url = (
        f"intent://deeplink/{encoded_question_seq}"
        f"#Intent;"
        f"scheme={settings.app_deeplink_scheme};"
        f"package={settings.app_android_package_name};"
        f"S.browser_fallback_url={android_fallback_url};"
        f"end"
    )

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
        app_scheme_url=json.dumps(app_scheme_url),
        android_intent_url=json.dumps(android_intent_url),
        android_install_url=json.dumps(settings.app_android_install_url),
        ios_install_url=json.dumps(settings.app_ios_install_url),
    )
