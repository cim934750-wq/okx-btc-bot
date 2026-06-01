from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "btc_order_intent.schema.json"


def _load_schema() -> dict[str, Any]:
    with SCHEMA_PATH.open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    return schema


SCHEMA = _load_schema()


def _is_json_type(value: Any, expected_type: str) -> bool:
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "null":
        return value is None
    return False


def _type_matches(value: Any, expected: str | list[str]) -> bool:
    expected_types = expected if isinstance(expected, list) else [expected]
    return any(_is_json_type(value, expected_type) for expected_type in expected_types)


def _is_date_time(value: str) -> bool:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _validate_against_schema_subset(payload: dict[str, Any]) -> list[str]:
    """Validate the schema constraints used by the BTC intent schema without adding a runtime dependency."""

    errors: list[str] = []
    required = SCHEMA["required"]
    properties = SCHEMA["properties"]

    for field in required:
        if field not in payload:
            errors.append(f"{field}: required")

    if SCHEMA.get("additionalProperties") is False:
        for field in payload:
            if field not in properties:
                errors.append(f"{field}: additional property is not allowed")

    for field, value in payload.items():
        rules = properties.get(field)
        if rules is None:
            continue

        expected_type = rules.get("type")
        if expected_type is not None and not _type_matches(value, expected_type):
            errors.append(f"{field}: invalid type")
            continue

        if "const" in rules and value != rules["const"]:
            errors.append(f"{field}: expected {rules['const']!r}")

        if "enum" in rules and value not in rules["enum"]:
            errors.append(f"{field}: value is not allowed")

        if isinstance(value, str):
            if "minLength" in rules and len(value) < rules["minLength"]:
                errors.append(f"{field}: string is too short")
            if "maxLength" in rules and len(value) > rules["maxLength"]:
                errors.append(f"{field}: string is too long")
            if "pattern" in rules and re.fullmatch(rules["pattern"], value) is None:
                errors.append(f"{field}: pattern mismatch")
            if rules.get("format") == "date-time" and not _is_date_time(value):
                errors.append(f"{field}: invalid date-time")

        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if "minimum" in rules and value < rules["minimum"]:
                errors.append(f"{field}: below minimum")

        if isinstance(value, list):
            if rules.get("uniqueItems") is True and len(value) != len(set(json.dumps(item, sort_keys=True) for item in value)):
                errors.append(f"{field}: duplicate items")
            item_rules = rules.get("items", {})
            for index, item in enumerate(value):
                item_type = item_rules.get("type")
                if item_type is not None and not _type_matches(item, item_type):
                    errors.append(f"{field}[{index}]: invalid item type")
                    continue
                if isinstance(item, str):
                    if "minLength" in item_rules and len(item) < item_rules["minLength"]:
                        errors.append(f"{field}[{index}]: item string is too short")
                    if "maxLength" in item_rules and len(item) > item_rules["maxLength"]:
                        errors.append(f"{field}[{index}]: item string is too long")

    if payload.get("response_action") == "BLOCK" and payload.get("intended_action") != "NONE":
        errors.append("intended_action: BLOCK response requires 'NONE'")
    if payload.get("risk_level") == "BLOCK" and payload.get("intended_action") != "NONE":
        errors.append("intended_action: BLOCK risk level requires 'NONE'")
    if "stale_data" in payload.get("risk_flags", []) and payload.get("intended_action") != "NONE":
        errors.append("intended_action: stale_data requires 'NONE'")

    return errors


def _valid_wait_intent() -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "intent_id": "btc-intent-20260528T000000Z",
        "created_at_utc": "2026-05-28T00:00:00Z",
        "source": "btc_signal_response_mvp",
        "mode": "order_intent_only",
        "symbol": "BTCUSDT",
        "instrument_id": "BTC-USDT",
        "timeframe": "4h",
        "candle_timestamp": "2026-05-27T20:00:00Z",
        "signal_decision": "WAIT",
        "response_action": "WAIT",
        "risk_level": "LOW",
        "risk_flags": [],
        "long1_active": False,
        "confidence": "weak",
        "passed_conditions": ["weekly_bull"],
        "missing_conditions": ["daily_bull"],
        "intended_action": "WATCH_ONLY",
        "intended_side": "NONE",
        "intended_order_type": "NONE",
        "intended_quantity": 0,
        "intended_notional": 0,
        "max_notional_cap": 0,
        "stop_loss_reference": None,
        "invalidation_reason": None,
        "block_reason": None,
        "source_decision_log_path": "runtime/logs/btc_signal_decisions_20260528.jsonl",
        "source_snapshot_path": "runtime/daily_reviews/btc_daily_review_latest.json",
        "operator_review_required": True,
        "execution_allowed": False,
        "execution_blocked_reason": "schema_is_non_executing",
        "checksum_or_hash": "sha256:0123456789abcdef",
        "notes": "Schema validation fixture. No execution is allowed.",
    }


def _errors(payload: dict[str, Any]) -> list[str]:
    return _validate_against_schema_subset(payload)


def _assert_valid(payload: dict[str, Any]) -> None:
    errors = _errors(payload)
    assert errors == []


def _assert_invalid(payload: dict[str, Any]) -> list[str]:
    errors = _errors(payload)
    assert errors
    return errors


def test_valid_non_executing_wait_intent_passes() -> None:
    _assert_valid(_valid_wait_intent())


def test_valid_non_executing_block_intent_passes_with_none_action() -> None:
    payload = _valid_wait_intent()
    payload.update(
        {
            "signal_decision": "NO_SIGNAL",
            "response_action": "BLOCK",
            "risk_level": "BLOCK",
            "risk_flags": ["stale_data"],
            "intended_action": "NONE",
            "block_reason": "stale_data",
            "execution_blocked_reason": "stale_data blocks execution",
        }
    )

    _assert_valid(payload)


def test_execution_allowed_true_fails() -> None:
    payload = _valid_wait_intent()
    payload["execution_allowed"] = True

    errors = _assert_invalid(payload)

    assert "execution_allowed: expected False" in errors


def test_operator_review_required_false_fails() -> None:
    payload = _valid_wait_intent()
    payload["operator_review_required"] = False

    errors = _assert_invalid(payload)

    assert "operator_review_required: expected True" in errors


@pytest.mark.parametrize("mode", ["live", "testnet"])
def test_live_and_testnet_modes_fail_for_current_version(mode: str) -> None:
    payload = _valid_wait_intent()
    payload["mode"] = mode

    errors = _assert_invalid(payload)

    assert "mode: value is not allowed" in errors


@pytest.mark.parametrize(
    "field_name",
    [
        "api_key",
        "api_secret",
        "secret",
        "passphrase",
        "password",
        "token",
        "access_token",
        "refresh_token",
        "private_key",
        "exchange_api_key",
        "exchange_api_secret",
        "okx_api_key",
        "okx_secret_key",
        "okx_passphrase",
    ],
)
def test_credential_fields_fail(field_name: str) -> None:
    payload = _valid_wait_intent()
    payload[field_name] = "must-not-be-accepted"

    errors = _assert_invalid(payload)

    assert f"{field_name}: additional property is not allowed" in errors


def test_missing_execution_blocked_reason_fails() -> None:
    payload = _valid_wait_intent()
    del payload["execution_blocked_reason"]

    errors = _assert_invalid(payload)

    assert "execution_blocked_reason: required" in errors


def test_empty_execution_blocked_reason_fails() -> None:
    payload = _valid_wait_intent()
    payload["execution_blocked_reason"] = ""

    errors = _assert_invalid(payload)

    assert "execution_blocked_reason: string is too short" in errors


def test_stale_data_with_action_other_than_none_fails() -> None:
    payload = _valid_wait_intent()
    payload["risk_flags"] = ["stale_data"]
    payload["intended_action"] = "WATCH_ONLY"

    errors = _assert_invalid(payload)

    assert "intended_action: stale_data requires 'NONE'" in errors


def test_block_response_with_action_other_than_none_fails() -> None:
    payload = _valid_wait_intent()
    payload["response_action"] = "BLOCK"
    payload["intended_action"] = "WATCH_ONLY"

    errors = _assert_invalid(payload)

    assert "intended_action: BLOCK response requires 'NONE'" in errors


def test_block_risk_level_with_action_other_than_none_fails() -> None:
    payload = _valid_wait_intent()
    payload["risk_level"] = "BLOCK"
    payload["intended_action"] = "PAPER_LONG_INTENT"

    errors = _assert_invalid(payload)

    assert "intended_action: BLOCK risk level requires 'NONE'" in errors


def test_negative_intended_quantity_fails() -> None:
    payload = _valid_wait_intent()
    payload["intended_quantity"] = -1

    errors = _assert_invalid(payload)

    assert "intended_quantity: below minimum" in errors


def test_unknown_extra_field_fails() -> None:
    payload = _valid_wait_intent()
    payload["unexpected_field"] = "not allowed"

    errors = _assert_invalid(payload)

    assert "unexpected_field: additional property is not allowed" in errors


@pytest.mark.parametrize("timestamp_field", ["created_at_utc", "candle_timestamp"])
def test_malformed_timestamp_fails(timestamp_field: str) -> None:
    payload = deepcopy(_valid_wait_intent())
    payload[timestamp_field] = "not-a-timestamp"

    errors = _assert_invalid(payload)

    assert f"{timestamp_field}: invalid date-time" in errors
