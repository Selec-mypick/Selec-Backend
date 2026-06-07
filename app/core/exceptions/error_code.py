from enum import Enum


class ErrorCode(Enum):
    def __init__(self, code: str, status_code: int, message: str):
        self.code = code
        self.status_code = status_code
        self.message = message

    # 401 Auth
    AUTH_HEADER_REQUIRED = ("AUTH_001", 401, "Authorization 헤더가 필요합니다.")
    AUTH_HEADER_INVALID_FORMAT = ("AUTH_002", 401, "Authorization 헤더 형식이 올바르지 않습니다. 'Bearer {token}' 형식이어야 합니다.")
    ACCESS_TOKEN_EXPIRED = ("AUTH_003", 401, "토큰이 만료되었습니다. 토큰을 재발급해주세요.")
    ACCESS_TOKEN_INVALID = ("AUTH_004", 401, "토큰 형식이 잘못되었거나 유효하지 않습니다.")
    ACCESS_TOKEN_MISSING_USER = ("AUTH_005", 401, "토큰에 사용자 정보가 없습니다(users_seq).")
    ACCESS_TOKEN_NOT_WHITELISTED = ("AUTH_006", 401, "토큰이 whitelist에 등록되어 있지 않습니다. 로그인이 필요합니다.")
    ACCESS_TOKEN_WHITELIST_MISMATCH = ("AUTH_007", 401, "토큰이 whitelist에 등록된 토큰과 일치하지 않습니다. 토큰이 재발급되었을 수 있습니다.")
    ACCESS_TOKEN_BLACKLISTED = ("AUTH_008", 401, "이미 무효화된 토큰입니다. 토큰이 재발급되어 이전 토큰은 사용할 수 없습니다.")
    AUTHENTICATED_USER_NOT_FOUND = ("AUTH_009", 401, "인증된 사용자 정보가 없습니다.")
    REFRESH_TOKEN_EXPIRED = ("AUTH_010", 401, "refresh token이 만료되었습니다.")
    REFRESH_TOKEN_INVALID = ("AUTH_011", 401, "유효하지 않은 refresh token입니다.")
    REFRESH_TOKEN_TYPE_INVALID = ("AUTH_012", 401, "refresh token이 아닙니다.")
    REFRESH_TOKEN_MISSING_USER = ("AUTH_013", 401, "refresh token에 사용자 정보가 없습니다.")
    REFRESH_TOKEN_BLACKLISTED = ("AUTH_014", 401, "이미 무효화된 refresh token입니다.")
    AUTH_USER_NOT_FOUND = ("AUTH_015", 401, "존재하지 않는 사용자입니다.")
    AUTH_USER_INACTIVE = ("AUTH_016", 401, "비활성화된 사용자입니다.")

    # 400 Bad Request
    GOOGLE_TOKEN_VERIFY_FAILED = ("BAD_001", 400, "Google id_token 검증 실패")
    GOOGLE_TOKEN_AUDIENCE_MISMATCH = ("BAD_002", 400, "Google id_token audience가 일치하지 않습니다.")
    GOOGLE_USER_NOT_FOUND = ("BAD_003", 400, "Google 사용자 정보를 확인할 수 없습니다.")
    VOTE_ALREADY_CLOSED = ("BAD_004", 400, "이미 종료된 투표입니다.")
    OPTION_NOT_IN_QUESTION = ("BAD_005", 400, "질문에 속하지 않는 선택지입니다.")
    DUPLICATE_OPTION_SEQ = ("BAD_006", 400, "중복된 선택지 시퀀스가 포함되어 있습니다.")
    OPTION_HAS_VOTES = ("BAD_007", 400, "이미 투표가 존재하는 선택지는 수정할 수 없습니다.")
    GEMINI_API_BAD_REQUEST = ("BAD_008", 400, "Gemini API 요청이 올바르지 않습니다.")
    VALIDATION_ERROR = ("VAL_000", 422, "요청 값이 올바르지 않습니다.")

    # 403 Forbidden
    QUESTION_UPDATE_FORBIDDEN = ("FORB_001", 403, "질문 수정 권한이 없습니다.")
    QUESTION_DELETE_FORBIDDEN = ("FORB_002", 403, "질문 삭제 권한이 없습니다.")
    VOTE_RESULT_FORBIDDEN = ("FORB_003", 403, "투표 후 결과를 조회할 수 있습니다.")

    # 404 Not Found
    USER_NOT_FOUND = ("NTF_001", 404, "존재하지 않는 사용자입니다.")
    QUESTION_NOT_FOUND = ("NTF_002", 404, "존재하지 않는 질문입니다.")
    VOTE_NOT_FOUND = ("NTF_003", 404, "투표 내역이 없습니다.")

    # 409 Conflict
    RESOURCE_CONFLICT = ("CNF_001", 409, "리소스 충돌이 발생했습니다.")
    GOOGLE_REGISTER_CONFLICT = ("CNF_002", 409, "Google 계정 등록 중 충돌이 발생했습니다. 다시 시도해주세요.")
    TEST_USER_CREATE_CONFLICT = ("CNF_003", 409, "테스트 유저 생성 중 충돌이 발생했습니다.")
    NICKNAME_ALREADY_USED = ("CNF_004", 409, "이미 사용 중인 닉네임입니다.")
    QUESTION_STALE = ("CNF_005", 409, "이미 수정된 질문입니다. 최신 질문 정보를 다시 조회해주세요.")

    # 500 Server
    INTERNAL_SERVER_ERROR = ("SRV_001", 500, "예상치 못한 오류가 발생했습니다.")
    TOKEN_STORE_FAILED = ("SRV_002", 500, "토큰 저장 중 오류가 발생했습니다.")
    TOKEN_REFRESH_FAILED = ("SRV_003", 500, "토큰 재발급 중 오류가 발생했습니다.")
    TRANSACTION_FAILED = ("SRV_004", 500, "요청 처리 중 오류가 발생했습니다.")
    REDIS_CONNECTION_FAILED = ("SRV_005", 500, "Redis 연결 실패")
    GEMINI_API_CALL_FAILED = ("SRV_006", 500, "Gemini API 호출 중 오류가 발생했습니다.")
    GEMINI_MODEL_NOT_CONFIGURED = ("SRV_007", 500, "GEMINI_MODEL 환경변수가 설정되어 있지 않습니다.")
    GEMINI_PROMPT_NOT_FOUND = ("SRV_008", 500, "Gemini 프롬프트 파일을 찾을 수 없습니다.")
    GEMINI_PROMPT_EMPTY = ("SRV_009", 500, "Gemini 프롬프트 파일이 비어 있습니다.")
    GEMINI_RESPONSE_NO_CANDIDATES = ("SRV_010", 500, "Gemini API 응답에 candidates가 없습니다.")
    GEMINI_RESPONSE_NO_TEXT = ("SRV_011", 500, "Gemini API 응답에서 text를 찾을 수 없습니다.")
    GEMINI_RESPONSE_INVALID_JSON = ("SRV_012", 500, "Gemini 응답이 JSON 형식이 아닙니다.")
    GEMINI_RESPONSE_INVALID_ANONYMOUS = ("SRV_013", 500, "Gemini 응답의 is_anonymous 값은 true여야 합니다.")
    GEMINI_RESPONSE_INVALID_OPTIONS_TYPE = ("SRV_014", 500, "Gemini 응답의 options 값이 배열이 아닙니다.")
    GEMINI_RESPONSE_INVALID_OPTIONS_COUNT = ("SRV_015", 500, "Gemini 응답의 options 개수는 3개 이상 5개 이하이어야 합니다.")
    GEMINI_RESPONSE_INVALID_OPTIONS_ITEM = ("SRV_016", 500, "Gemini 응답의 options 항목이 올바르지 않습니다.")
    GEMINI_RESPONSE_DUPLICATE_OPTIONS = ("SRV_017", 500, "Gemini 응답의 options에 중복 값이 있습니다.")
    GEMINI_RESPONSE_FIELD_VALIDATION_FAILED = ("SRV_018", 500, "Gemini 응답 필드 검증에 실패했습니다.")
