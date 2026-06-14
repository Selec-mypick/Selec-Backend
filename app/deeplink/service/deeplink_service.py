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

    if "iphone" in normalized or "ipad" in normalized or "ipod" in normalized:
        web_url = build_install_fallback_url(settings.app_ios_install_url, question_seq)
        android_intent_url = ""
    elif "android" in normalized:
        web_url = build_install_fallback_url(settings.app_android_install_url, question_seq)
        android_fallback_url = quote(web_url, safe="")
        android_intent_url = (
            f"intent://deeplink/{encoded_question_seq}"
            f"#Intent;"
            f"scheme={settings.app_deeplink_scheme};"
            f"package={settings.app_android_package_name};"
            f"S.browser_fallback_url={android_fallback_url};"
            f"end"
        )
    else:
        raise ValueError("모바일 User-Agent가 아닙니다.")

    template = Template(TEMPLATE_PATH.read_text(encoding="utf-8"))
    return template.safe_substitute(
        android_intent_url=json.dumps(android_intent_url),
        web_url=json.dumps(web_url),
    )
