from app.core.database.session import AsyncSessionLocal
from app.core.database.transaction import run_in_transaction
from app.question_invited.repository.question_invited_repository import QuestionInvitedRepository
from config import settings


class QuestionInviteAllJob:
    def __init__(self, creator_users_seq: str | None = None) -> None:
        self.creator_users_seq = creator_users_seq or settings.scheduler_batch_users_seq

    async def execute(self) -> None:
        async with AsyncSessionLocal() as db:
            async def question_invite_all_action() -> int:
                return await QuestionInvitedRepository.upsert_all_active_users_to_creator_questions(
                    db,
                    creator_users_seq=self.creator_users_seq,
                )

            await run_in_transaction(
                db,
                question_invite_all_action,
                "전체 사용자 초대 job 실행 중 오류가 발생했습니다",
            )
