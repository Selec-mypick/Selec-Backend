from pydantic import BaseModel, Field


class VoteResultVoterResponse(BaseModel):
    google_id: str
    nick_name: str | None = None
    email: str | None = None
    name: str | None = None
    profile_image: str | None = None


class VoteResultOptionResponse(BaseModel):
    options_seq: int
    content: str
    vote_count: int = 0
    voters: list[VoteResultVoterResponse] | None = None


class GetVoteResultResponse(BaseModel):
    is_anonymous: bool | None
    options: list[VoteResultOptionResponse]

    @classmethod
    def from_result_rows(
            cls,
            option_rows,
            is_anonymous: bool,
    ) -> "GetVoteResultResponse":
        options_by_seq: dict[int, VoteResultOptionResponse] = {}

        for row in option_rows:
            if row.option.options_seq not in options_by_seq:
                options_by_seq[row.option.options_seq] = VoteResultOptionResponse(
                    options_seq=row.option.options_seq,
                    content=row.option.content,
                    vote_count=0,
                    voters=[] if not is_anonymous else None,
                )

            if row.voter is not None:
                result_option = options_by_seq[row.option.options_seq]
                result_option.vote_count += 1
                if not is_anonymous and result_option.voters is not None:
                    result_option.voters.append(
                        VoteResultVoterResponse(
                            google_id=row.voter.google_id,
                            nick_name=row.voter.nick_name,
                            email=row.voter.email,
                            name=row.voter.name,
                            profile_image=row.voter.profile_image,
                        )
                    )

        return cls(
            is_anonymous=is_anonymous,
            options=list(options_by_seq.values()),
        )
