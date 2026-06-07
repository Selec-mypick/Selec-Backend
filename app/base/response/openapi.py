from app.base.constants import BaseUtil
from app.base.response.api_response import BaseResponse
from app.core.exceptions.error_code import ErrorCode


def api_errors(*errors: ErrorCode) -> dict:
    responses: dict[int, dict] = {}

    for error in errors:
        if error.status_code not in responses:
            responses[error.status_code] = {
                "description": error.code,
                "model": BaseResponse,
                "content": {
                    "application/json": {
                        "examples": {},
                    }
                },
            }

        examples = responses[error.status_code]["content"]["application/json"]["examples"]
        examples[error.code] = {
            "summary": error.code,
            "value": {
                "status": error.status_code,
                "code": error.code,
                "message": error.message,
                "data": None,
            },
        }
        responses[error.status_code]["description"] = ", ".join(examples.keys())

    return responses


def _to_code_response(
        json_content: dict,
        example_obj: dict,
) -> dict:
    value = dict(example_obj.get("value", example_obj))
    value.setdefault("data", None)
    return {
        "description": "",
        "content": {
            "application/json": {
                "schema": json_content.get("schema"),
                "example": value,
            }
        },
    }


def _transform_responses(responses: dict) -> dict:
    transformed: dict[str, dict] = {}

    for http_key, response in responses.items():
        if not isinstance(response, dict):
            continue

        json_content = (response.get("content") or {}).get("application/json") or {}
        examples = json_content.get("examples")

        if examples:
            for code, example_obj in examples.items():
                transformed[code] = _to_code_response(json_content, example_obj)
            continue

        if http_key in ("200", "201"):
            example = json_content.get("example") or {
                "status": int(http_key),
                "code": BaseUtil.SUCCESS_CODE,
                "message": BaseUtil.SUCCESS,
                "data": None,
            }
            if "data" not in example:
                example = {**example, "data": None}
            transformed[BaseUtil.SUCCESS_CODE] = {
                "description": "",
                "content": {
                    "application/json": {
                        "schema": json_content.get("schema"),
                        "example": example,
                    }
                },
            }
            continue

        example = json_content.get("example")
        if isinstance(example, dict) and example.get("code"):
            code = str(example["code"])
            transformed[code] = _to_code_response(
                json_content,
                {"value": example},
            )
        else:
            transformed[http_key] = response

    ordered: dict[str, dict] = {}
    if BaseUtil.SUCCESS_CODE in transformed:
        ordered[BaseUtil.SUCCESS_CODE] = transformed.pop(BaseUtil.SUCCESS_CODE)
    for code in sorted(transformed.keys()):
        ordered[code] = transformed[code]
    return ordered


def apply_error_code_responses(openapi_schema: dict) -> dict:
    for path_item in openapi_schema.get("paths", {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            responses = operation.get("responses")
            if responses:
                operation["responses"] = _transform_responses(responses)
    return openapi_schema
