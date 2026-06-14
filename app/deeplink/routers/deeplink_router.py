from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Path as PathParam, Request
from fastapi.responses import HTMLResponse

from app.deeplink.service.deeplink_service import render_question_install_page

router = APIRouter(tags=["DEEPLINK"])

_MOBILE_ONLY_TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "mobile_only.html"


@router.get("/deeplink/{question_seq}", response_class=HTMLResponse, include_in_schema=False)
async def question_deeplink_fallback(
        request: Request,
        question_seq: UUID = PathParam(..., description="질문 UUID"),
):
    user_agent = request.headers.get("user-agent", "").lower()
    if not any(token in user_agent for token in ("iphone", "ipad", "ipod", "android")):
        return HTMLResponse(content=_MOBILE_ONLY_TEMPLATE.read_text(encoding="utf-8"))

    return HTMLResponse(content=render_question_install_page(question_seq, user_agent))
