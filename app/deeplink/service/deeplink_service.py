import json
from html import escape
from pathlib import Path as FilePath
from string import Template
from urllib.parse import quote
from uuid import UUID

from config import settings

TEMPLATE_PATH = FilePath(__file__).resolve().parents[1] / "templates" / "question_install.html"
MOBILE_ONLY_TEMPLATE_PATH = FilePath(__file__).resolve().parents[1] / "templates" / "mobile_only.html"


def is_mobile_user_agent(user_agent: str) -> bool:
    normalized = user_agent.lower()
    return (
        "iphone" in normalized
        or "ipad" in normalized
        or "ipod" in normalized
        or "android" in normalized
    )


def render_mobile_only_page() -> str:
    return MOBILE_ONLY_TEMPLATE_PATH.read_text(encoding="utf-8")


def build_install_fallback_url(install_url: str, question_seq: UUID | str) -> str:
    return f"{install_url.rstrip('/')}/deeplink/question/{question_seq}"


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
            "store_link_section": "",
        }
    elif "android" in normalized:
        android_install_url = escape(settings.app_android_install_url, quote=True)
        context = {
            "platform_message": "Android에서 Selec 앱으로 질문을 열 수 있습니다.",
            "store_link_section": (
                f'<a class="store-link" href="{android_install_url}">Google Play에서 설치</a>'
            ),
        }
    else:
        raise ValueError("모바일 User-Agent가 아닙니다.")

    template = Template(TEMPLATE_PATH.read_text(encoding="utf-8"))
    return template.safe_substitute(
        platform_message=escape(context["platform_message"]),
        store_link_section=context["store_link_section"],
        app_scheme_url=json.dumps(app_scheme_url),
        android_intent_url=json.dumps(android_intent_url),
        android_install_url=json.dumps(settings.app_android_install_url),
        ios_fallback_url=json.dumps(build_install_fallback_url(settings.app_ios_install_url, question_seq)),
    )
