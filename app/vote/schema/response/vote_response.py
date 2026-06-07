from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel

if TYPE_CHECKING:
    from app.options.models.options import Options
    from app.users.models.users import Users


class GetVoteResultResponse(BaseModel):
    is_anonymous: Optional[bool]
    options: list[dict]

    @classmethod
    def from_result_rows(
            cls,
            option_rows: list[tuple["Options", Optional["Users"]]],
            is_anonymous: bool,
    ) -> "GetVoteResultResponse":
        options_by_seq: dict[int, dict] = {}

        for option, voter in option_rows:
            if option.options_seq not in options_by_seq:
                options_by_seq[option.options_seq] = {
                    "options_seq": option.options_seq,
                    "content": option.content,
                    "vote_count": 0,
                }
                if not is_anonymous:
                    options_by_seq[option.options_seq]["voters"] = []

            if voter is not None:
                result_option = options_by_seq[option.options_seq]
                result_option["vote_count"] += 1
                if not is_anonymous:
                    result_option["voters"].append({
                        "google_id": voter.google_id,
                        "nick_name": voter.nick_name,
                        "email": voter.email,
                        "name": voter.name,
                        "profile_image": voter.profile_image,
                    })

        return cls(
            is_anonymous=is_anonymous,
            options=list(options_by_seq.values()),
        )
