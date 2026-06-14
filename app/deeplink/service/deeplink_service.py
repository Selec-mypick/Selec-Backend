import json
from html import escape
from pathlib import Path as FilePath
from string import Template
from urllib.parse import quote
from uuid import UUID

from config import settings

_TEMPLATE = FilePath(__file__).resolve().parents[1] / "templates" / "question_install.html"


def render_question_install_page(question_seq: UUID, user_agent: str) -> str:
    normalized = user_agent.lower()
    encoded_question_seq = escape(str(question_seq), quote=True)

    if "iphone" in normalized or "ipad" in normalized or "ipod" in normalized:
        web_url = f"{settings.app_ios_install_url.rstrip('/')}/deeplink/question/{question_seq}"
        android_intent_url = ""
    elif "android" in normalized:
        web_url = f"{settings.app_android_install_url.rstrip('/')}/deeplink/question/{question_seq}"
        android_intent_url = (
            f"intent://deeplink/{encoded_question_seq}"
            f"#Intent;"
            f"scheme={settings.app_deeplink_scheme};"
            f"package={settings.app_android_package_name};"
            f"S.browser_fallback_url={quote(web_url, safe='')};"
            f"end"
        )
    else:
        raise ValueError("모바일 User-Agent가 아닙니다.")

    return Template(_TEMPLATE.read_text(encoding="utf-8")).safe_substitute(
        android_intent_url=json.dumps(android_intent_url),
        web_url=json.dumps(web_url),
    )
