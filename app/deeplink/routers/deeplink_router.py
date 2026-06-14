from uuid import UUID

from fastapi import APIRouter, Path, Request
from fastapi.responses import HTMLResponse

from app.deeplink.service.deeplink_service import (
    is_mobile_user_agent,
    render_mobile_only_page,
    render_question_install_page,
)

router = APIRouter(tags=["DEEPLINK"])


@router.get("/deeplink/{question_seq}", response_class=HTMLResponse, include_in_schema=False)
async def question_deeplink_fallback(
        request: Request,
        question_seq: UUID = Path(..., description="질문 UUID"),
):
    user_agent = request.headers.get("user-agent", "")
    if not is_mobile_user_agent(user_agent):
        return HTMLResponse(content=render_mobile_only_page())

    return HTMLResponse(content=render_question_install_page(question_seq, user_agent))
