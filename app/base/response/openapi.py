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
            "description": error.message,
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
        base: dict,
        json_content: dict,
        code: str,
        example_obj: dict,
        http_key: str,
) -> dict:
    value = example_obj.get("value", example_obj)
    description = example_obj.get("description") or example_obj.get("summary") or code
    response = {
        "description": description,
        "content": {
            "application/json": {
                "schema": json_content.get("schema"),
                "example": value,
            }
        },
    }
    if http_key.isdigit():
        response["x-http-status"] = int(http_key)
    if base.get("headers"):
        response["headers"] = base["headers"]
    return response


def _transform_responses(responses: dict) -> dict:
    transformed: dict[str, dict] = {}

    for http_key, response in responses.items():
        if not isinstance(response, dict):
            continue

        json_content = (response.get("content") or {}).get("application/json") or {}
        examples = json_content.get("examples")

        if examples:
            for code, example_obj in examples.items():
                transformed[code] = _to_code_response(response, json_content, code, example_obj, http_key)
            continue

        if http_key in ("200", "201"):
            example = json_content.get("example") or {
                "status": int(http_key),
                "code": BaseUtil.SUCCESS_CODE,
                "message": BaseUtil.SUCCESS,
                "data": None,
            }
            transformed[BaseUtil.SUCCESS_CODE] = {
                "description": BaseUtil.SUCCESS,
                "x-http-status": int(http_key),
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
                response,
                json_content,
                code,
                {"value": example},
                http_key,
            )
        else:
            transformed[http_key] = {
                **response,
                **({"x-http-status": int(http_key)} if http_key.isdigit() else {}),
            }

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
