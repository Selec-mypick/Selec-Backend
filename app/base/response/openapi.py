from typing import Any

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


def _resolve_schema(schema: dict | None, components: dict) -> dict:
    if not schema:
        return {}
    if "$ref" in schema:
        ref_name = schema["$ref"].split("/")[-1]
        return components.get(ref_name, {})
    return schema


def _build_schema_example(schema: dict | None, components: dict) -> Any:
    schema = _resolve_schema(schema, components)
    if not schema:
        return None

    if "example" in schema:
        return schema["example"]
    if "default" in schema:
        return schema["default"]
    if "enum" in schema:
        return schema["enum"][0]

    for composite_key in ("allOf", "anyOf", "oneOf"):
        variants = schema.get(composite_key)
        if variants:
            for variant in variants:
                if variant.get("type") == "null":
                    continue
                example = _build_schema_example(variant, components)
                if example is not None:
                    return example

    schema_type = schema.get("type")
    if schema_type == "object":
        properties = schema.get("properties")
        if not properties:
            return None
        return {
            name: _build_schema_example(property_schema, components)
            for name, property_schema in properties.items()
        }
    if schema_type == "array":
        item_example = _build_schema_example(schema.get("items"), components)
        return [] if item_example is None else [item_example]
    if schema_type == "integer":
        return 0
    if schema_type == "number":
        return 0
    if schema_type == "boolean":
        return False
    if schema_type == "string":
        if schema.get("format") == "date-time":
            return "2024-01-01T00:00:00"
        return "string"

    return None


def _build_success_example(http_key: str, json_content: dict, components: dict) -> dict:
    existing_example = json_content.get("example")
    if isinstance(existing_example, dict) and "data" in existing_example:
        return existing_example

    response_schema = _resolve_schema(json_content.get("schema"), components)
    data_schema = response_schema.get("properties", {}).get("data")
    data_example = None
    if data_schema and data_schema.get("type"):
        data_example = _build_schema_example(data_schema, components)
    elif data_schema and data_schema.get("$ref"):
        data_example = _build_schema_example(data_schema, components)

    return {
        "status": int(http_key),
        "code": BaseUtil.SUCCESS_CODE,
        "message": BaseUtil.SUCCESS,
        "data": data_example,
    }


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


def _transform_responses(responses: dict, components: dict) -> dict:
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
            example = _build_success_example(http_key, json_content, components)
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
    components = openapi_schema.get("components", {}).get("schemas", {})
    for path_item in openapi_schema.get("paths", {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            responses = operation.get("responses")
            if responses:
                operation["responses"] = _transform_responses(responses, components)
    return openapi_schema
