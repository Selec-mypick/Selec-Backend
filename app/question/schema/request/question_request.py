from pydantic import BaseModel, Field

from app.options.schema.request.options_request import UpdateOptionRequest


class CreateQuestionRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=1024, description="질문 제목", example="점심 뭐 먹을까요?")
    description: str | None = Field(None, max_length=2048, description="질문 설명", example="오늘 점심 메뉴를 투표로 정합니다.")
    is_anonymous: bool = Field(True, description="익명 투표 여부", example=True)
    options: list[str] = Field(..., description="질문 선택지 목록", example=["김치찌개", "제육볶음", "비빔밥"])


class UpdateQuestionRequest(BaseModel):
    version: int = Field(..., ge=0, description="질문 버전", example=1)
    title: str = Field(..., min_length=1, max_length=1024, description="질문 제목", example="점심 뭐 먹을까요?")
    description: str | None = Field(None, max_length=2048, description="질문 설명", example="오늘 점심 메뉴를 투표로 정합니다.")
    is_anonymous: bool = Field(True, description="익명 투표 여부", example=True)
    options: list[UpdateOptionRequest] = Field(..., description="수정할 질문 선택지 목록",example=[{"options_seq": 1, "content": "김치찌개"}, {"options_seq": 2, "content": "제육볶음"}, {"content": "비빔밥"}])
