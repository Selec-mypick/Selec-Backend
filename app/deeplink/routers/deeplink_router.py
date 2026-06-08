from uuid import UUID

from fastapi import APIRouter, Path, Request
from fastapi.responses import HTMLResponse

from app.deeplink.service import render_question_install_page

router = APIRouter(tags=["DEEPLINK"])


@router.get("/deeplink/{question_seq}", response_class=HTMLResponse)
async def question_deeplink_fallback(
        request: Request,
        question_seq: UUID = Path(..., description="질문 UUID"),
):
    return render_question_install_page(question_seq, request.headers.get("user-agent", ""))
