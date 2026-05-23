#!/usr/bin/env python3
"""Validate Canon Boundary Guard SESSION_STATE and CANON_STATE_DELTA files.

This script performs mechanical checks only. It does not decide provenance.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas"
STATE_SCHEMA_PATH = SCHEMA_DIR / "SESSION_STATE.schema.json"
DELTA_SCHEMA_PATH = SCHEMA_DIR / "CANON_STATE_DELTA.schema.json"


def load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        raise ValueError(f"{path}: cannot read JSON: {exc}") from exc


def json_type(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int) and not isinstance(value, bool):
        return "integer"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return "number"
    return type(value).__name__


def schema_type_matches(value: object, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


def validate_with_jsonschema(value: object, schema: dict, label: str) -> list[str] | None:
    try:
        import jsonschema  # type: ignore
    except Exception:
        return None

    validator = jsonschema.Draft202012Validator(schema)
    errors = []
    for err in sorted(validator.iter_errors(value), key=lambda item: list(item.path)):
        path = ".".join(str(part) for part in err.path)
        location = f"{label}.{path}" if path else label
        errors.append(f"{location}: {err.message}")
    return errors


SUPPORTED_SCHEMA_KEYS = {
    "$schema",
    "title",
    "description",
    "type",
    "required",
    "properties",
    "additionalProperties",
    "const",
    "enum",
    "minimum",
    "items",
}


def validate_schema_strict(value: object, schema: dict, label: str) -> list[str]:
    errors: list[str] = []

    unsupported = set(schema) - SUPPORTED_SCHEMA_KEYS
    if unsupported:
        return [
            f"{label}: unsupported schema keyword(s): "
            + ", ".join(sorted(unsupported))
        ]

    if "type" in schema:
        expected = schema["type"]
        if not isinstance(expected, str):
            return [f"{label}: unsupported non-string schema type"]
        if not schema_type_matches(value, expected):
            return [f"{label}: expected {expected}, got {json_type(value)}"]

    if "const" in schema and value != schema["const"]:
        errors.append(f"{label}: expected constant {schema['const']!r}")

    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{label}: expected one of {schema['enum']!r}")

    if "minimum" in schema:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            errors.append(f"{label}: minimum applies to non-number")
        elif value < schema["minimum"]:
            errors.append(f"{label}: must be >= {schema['minimum']!r}")

    if schema.get("type") == "object":
        if not isinstance(value, dict):
            return errors

        required = schema.get("required", [])
        if not isinstance(required, list):
            return [f"{label}: unsupported non-list required"]
        for key in required:
            if key not in value:
                errors.append(f"{label}: missing required key: {key}")

        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            return [f"{label}: unsupported non-object properties"]

        if schema.get("additionalProperties") is False:
            extra = set(value) - set(properties)
            for key in sorted(extra):
                errors.append(f"{label}: unexpected key: {key}")
        elif "additionalProperties" in schema and schema.get("additionalProperties") is not True:
            return [f"{label}: unsupported additionalProperties schema"]

        for key, item in value.items():
            if key in properties:
                if not isinstance(properties[key], dict):
                    return [f"{label}.{key}: unsupported property schema"]
                errors.extend(validate_schema_strict(item, properties[key], f"{label}.{key}"))

    if schema.get("type") == "array":
        if not isinstance(value, list):
            return errors
        items = schema.get("items")
        if items is None:
            return [f"{label}: array schema missing items"]
        if not isinstance(items, dict):
            return [f"{label}: unsupported array items schema"]
        for index, item in enumerate(value):
            errors.extend(validate_schema_strict(item, items, f"{label}[{index}]"))

    return errors


def validate_against_schema(value: object, schema_path: Path, label: str) -> list[str]:
    try:
        schema = load_json(schema_path)
    except ValueError as exc:
        return [str(exc)]

    if not isinstance(schema, dict):
        return [f"{schema_path}: schema root must be object"]

    jsonschema_errors = validate_with_jsonschema(value, schema, label)
    if jsonschema_errors is not None:
        return jsonschema_errors

    return validate_schema_strict(value, schema, label)


def validate_state_obj(state: object, label: str = "SESSION_STATE") -> list[str]:
    return validate_against_schema(state, STATE_SCHEMA_PATH, label)


def validate_delta_obj(delta: object, label: str = "CANON_STATE_DELTA") -> list[str]:
    errors = validate_against_schema(delta, DELTA_SCHEMA_PATH, label)
    if isinstance(delta, dict):
        current_state = delta.get("current_state")
        if isinstance(current_state, dict) and isinstance(delta.get("seq"), int):
            if current_state.get("state_seq") != delta.get("seq"):
                errors.append(
                    f"{label}: current_state.state_seq should equal delta.seq "
                    f"({current_state.get('state_seq')} != {delta.get('seq')})"
                )
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=Path, help="Path to SESSION_STATE.json")
    parser.add_argument("--delta", type=Path, help="Path to CANON_STATE_DELTA.json")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    args = parser.parse_args()

    if not args.state and not args.delta:
        parser.error("provide --state and/or --delta")

    report = {"valid": True, "errors": []}

    try:
        if args.state:
            state = load_json(args.state)
            report["errors"].extend(validate_state_obj(state))
        if args.delta:
            delta = load_json(args.delta)
            report["errors"].extend(validate_delta_obj(delta))
    except ValueError as exc:
        report["errors"].append(str(exc))

    report["valid"] = not report["errors"]

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        if report["valid"]:
            print("valid")
        else:
            print("invalid")
            for err in report["errors"]:
                print(f"- {err}")

    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
