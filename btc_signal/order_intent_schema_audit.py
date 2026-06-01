from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


EXPECTED_REQUIRED_FIELDS: tuple[str, ...] = (
    "schema_version",
    "intent_id",
    "created_at_utc",
    "source",
    "mode",
    "symbol",
    "instrument_id",
    "timeframe",
    "candle_timestamp",
    "signal_decision",
    "response_action",
    "risk_level",
    "risk_flags",
    "long1_active",
    "confidence",
    "passed_conditions",
    "missing_conditions",
    "intended_action",
    "intended_side",
    "intended_order_type",
    "intended_quantity",
    "intended_notional",
    "max_notional_cap",
    "stop_loss_reference",
    "invalidation_reason",
    "block_reason",
    "source_decision_log_path",
    "source_snapshot_path",
    "operator_review_required",
    "execution_allowed",
    "execution_blocked_reason",
    "checksum_or_hash",
    "notes",
)

CREDENTIAL_FIELDS: tuple[str, ...] = (
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
)

EXPECTED_REJECTED_MODES: tuple[str, ...] = ("testnet", "live")
NUMERIC_NON_NEGATIVE_FIELDS: tuple[str, ...] = ("intended_quantity", "intended_notional", "max_notional_cap")
TIMESTAMP_FIELDS: tuple[str, ...] = ("created_at_utc", "candle_timestamp")
SOURCE_REFERENCE_FIELDS: tuple[str, ...] = ("source_decision_log_path", "source_snapshot_path")


@dataclass(slots=True)
class SchemaAudit:
    mode: str
    schema_path: str
    schema_found: bool
    json_valid: bool
    schema_draft: str | None
    schema_version: str | None
    required_field_count: int
    required_fields: list[str]
    missing_required_fields: list[str]
    additional_properties: Any
    additional_properties_closed: bool
    execution_allowed_constraint: dict[str, Any]
    operator_review_required_constraint: dict[str, Any]
    allowed_modes: list[str]
    explicitly_rejected_modes: list[str]
    allowed_signal_decisions: list[str]
    allowed_response_actions: list[str]
    allowed_risk_levels: list[str]
    allowed_intended_actions: list[str]
    allowed_intended_sides: list[str]
    allowed_intended_order_types: list[str]
    block_response_rule_present: bool
    block_risk_level_rule_present: bool
    stale_data_rule_present: bool
    credential_field_rejection_status: bool
    credential_like_fields_checked: list[str]
    credential_like_fields_not_explicitly_rejected: list[str]
    numeric_non_negative_constraints: dict[str, bool]
    timestamp_format_constraints: dict[str, bool]
    source_reference_fields_present: dict[str, bool]
    checksum_hash_field_present: bool
    safety_status: str
    failed_checks: list[str]
    warn_checks: list[str]
    info_items: list[str]
    safety_boundary: dict[str, bool]


def load_schema(schema_path: str | Path) -> tuple[dict[str, Any] | None, str | None]:
    path = Path(schema_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, f"Schema file is missing: {path}"
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"Schema JSON could not be read: {path}: {exc}"
    if not isinstance(payload, dict):
        return None, f"Schema JSON was not an object: {path}"
    return payload, None


def audit_schema(schema_path: str | Path) -> SchemaAudit:
    path = Path(schema_path)
    schema, error = load_schema(path)
    if error is not None or schema is None:
        return _failed_load_audit(path, error or "Schema could not be loaded.")

    properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    required_fields = _str_list(schema.get("required"))
    missing_required_fields = [field for field in EXPECTED_REQUIRED_FIELDS if field not in required_fields]

    additional_properties = schema.get("additionalProperties")
    additional_properties_closed = additional_properties is False

    execution_constraint = _const_constraint(properties.get("execution_allowed"), expected=False)
    review_constraint = _const_constraint(properties.get("operator_review_required"), expected=True)

    allowed_modes = _enum_values(properties.get("mode"))
    rejected_modes = [mode for mode in EXPECTED_REJECTED_MODES if mode not in allowed_modes]

    block_response_rule = _has_conditional_none_rule(schema, trigger_field="response_action", trigger_value="BLOCK")
    block_risk_rule = _has_conditional_none_rule(schema, trigger_field="risk_level", trigger_value="BLOCK")
    stale_data_rule = _has_stale_data_none_rule(schema)

    explicit_credential_rejections = _explicitly_rejected_fields(schema)
    missing_credential_rejections = [field for field in CREDENTIAL_FIELDS if field not in explicit_credential_rejections]
    credential_field_rejection_status = additional_properties_closed and not missing_credential_rejections

    numeric_constraints = {
        field: _has_non_negative_number_constraint(properties.get(field)) for field in NUMERIC_NON_NEGATIVE_FIELDS
    }
    timestamp_constraints = {field: _has_date_time_constraint(properties.get(field)) for field in TIMESTAMP_FIELDS}
    source_reference_fields = {field: field in properties and field in required_fields for field in SOURCE_REFERENCE_FIELDS}
    checksum_hash_field_present = "checksum_or_hash" in properties and "checksum_or_hash" in required_fields

    failed_checks: list[str] = []
    warn_checks: list[str] = []
    info_items: list[str] = []

    if missing_required_fields:
        warn_checks.append(f"Missing expected required fields: {', '.join(missing_required_fields)}")
    if not additional_properties_closed:
        failed_checks.append("additionalProperties is not false; unknown credential-like fields may be accepted.")
    if not execution_constraint["constrained"]:
        failed_checks.append("execution_allowed is not constrained to false.")
    if not review_constraint["constrained"]:
        failed_checks.append("operator_review_required is not constrained to true.")
    if "live" in allowed_modes:
        failed_checks.append("mode enum allows live.")
    if "testnet" in allowed_modes:
        failed_checks.append("mode enum allows testnet.")
    if not credential_field_rejection_status:
        failed_checks.append("Credential-like field rejection is incomplete.")
    if not block_response_rule:
        failed_checks.append("BLOCK response rule requiring intended_action=NONE is absent.")
    if not block_risk_rule:
        failed_checks.append("BLOCK risk-level rule requiring intended_action=NONE is absent.")
    if not stale_data_rule:
        failed_checks.append("stale_data rule requiring intended_action=NONE is absent.")

    for field, passed in numeric_constraints.items():
        if not passed:
            warn_checks.append(f"{field} is missing a non-negative numeric constraint.")
    for field, passed in timestamp_constraints.items():
        if not passed:
            warn_checks.append(f"{field} is missing date-time format validation.")
    for field, present in source_reference_fields.items():
        if not present:
            warn_checks.append(f"{field} is not present as a required source reference field.")
    if not checksum_hash_field_present:
        warn_checks.append("checksum_or_hash is not present as a required audit field.")

    if not failed_checks:
        info_items.extend(
            [
                "Schema JSON parsed successfully.",
                "execution_allowed is constrained to false.",
                "operator_review_required is constrained to true.",
                "live/testnet modes are not allowed.",
                "Credential-like fields are rejected.",
                "BLOCK and stale_data safety rules are represented.",
            ]
        )

    safety_status = "FAIL" if failed_checks else "WARN" if warn_checks else "PASS"

    return SchemaAudit(
        mode="btc_order_intent_schema_audit_read_only",
        schema_path=str(path),
        schema_found=True,
        json_valid=True,
        schema_draft=str(schema.get("$schema")) if schema.get("$schema") is not None else None,
        schema_version=_schema_version(properties),
        required_field_count=len(required_fields),
        required_fields=required_fields,
        missing_required_fields=missing_required_fields,
        additional_properties=additional_properties,
        additional_properties_closed=additional_properties_closed,
        execution_allowed_constraint=execution_constraint,
        operator_review_required_constraint=review_constraint,
        allowed_modes=allowed_modes,
        explicitly_rejected_modes=rejected_modes,
        allowed_signal_decisions=_enum_values(properties.get("signal_decision")),
        allowed_response_actions=_enum_values(properties.get("response_action")),
        allowed_risk_levels=_enum_values(properties.get("risk_level")),
        allowed_intended_actions=_enum_values(properties.get("intended_action")),
        allowed_intended_sides=_enum_values(properties.get("intended_side")),
        allowed_intended_order_types=_enum_values(properties.get("intended_order_type")),
        block_response_rule_present=block_response_rule,
        block_risk_level_rule_present=block_risk_rule,
        stale_data_rule_present=stale_data_rule,
        credential_field_rejection_status=credential_field_rejection_status,
        credential_like_fields_checked=list(CREDENTIAL_FIELDS),
        credential_like_fields_not_explicitly_rejected=missing_credential_rejections,
        numeric_non_negative_constraints=numeric_constraints,
        timestamp_format_constraints=timestamp_constraints,
        source_reference_fields_present=source_reference_fields,
        checksum_hash_field_present=checksum_hash_field_present,
        safety_status=safety_status,
        failed_checks=failed_checks,
        warn_checks=warn_checks,
        info_items=info_items,
        safety_boundary=_safety_boundary(),
    )


def audit_to_dict(audit: SchemaAudit) -> dict[str, Any]:
    return asdict(audit)


def audit_json(audit: SchemaAudit) -> str:
    return json.dumps(audit_to_dict(audit), indent=2, sort_keys=True) + "\n"


def format_text_audit(audit: SchemaAudit) -> str:
    data = audit_to_dict(audit)
    lines = [
        "BTC Order-Intent Schema Audit",
        f"Schema path: {data['schema_path']}",
        f"Safety status: {data['safety_status']}",
        f"Schema found: {data['schema_found']}",
        f"JSON valid: {data['json_valid']}",
        f"Schema draft: {data['schema_draft']}",
        f"Schema version: {data['schema_version']}",
        f"Required fields: {data['required_field_count']}",
        f"additionalProperties closed: {data['additional_properties_closed']}",
        f"execution_allowed=false: {data['execution_allowed_constraint']['constrained']}",
        f"operator_review_required=true: {data['operator_review_required_constraint']['constrained']}",
        f"Allowed modes: {', '.join(data['allowed_modes']) or 'none'}",
        f"Rejected modes: {', '.join(data['explicitly_rejected_modes']) or 'none'}",
        f"Allowed signal decisions: {', '.join(data['allowed_signal_decisions']) or 'none'}",
        f"Allowed response actions: {', '.join(data['allowed_response_actions']) or 'none'}",
        f"Allowed risk levels: {', '.join(data['allowed_risk_levels']) or 'none'}",
        f"Allowed intended actions: {', '.join(data['allowed_intended_actions']) or 'none'}",
        f"Allowed intended sides: {', '.join(data['allowed_intended_sides']) or 'none'}",
        f"Allowed intended order types: {', '.join(data['allowed_intended_order_types']) or 'none'}",
        f"BLOCK response rule present: {data['block_response_rule_present']}",
        f"BLOCK risk-level rule present: {data['block_risk_level_rule_present']}",
        f"stale_data rule present: {data['stale_data_rule_present']}",
        f"Credential fields rejected: {data['credential_field_rejection_status']}",
        f"Credential fields checked: {', '.join(data['credential_like_fields_checked'])}",
        f"Numeric non-negative constraints: {_bool_map_text(data['numeric_non_negative_constraints'])}",
        f"Timestamp format constraints: {_bool_map_text(data['timestamp_format_constraints'])}",
        f"Source reference fields: {_bool_map_text(data['source_reference_fields_present'])}",
        f"checksum_or_hash present: {data['checksum_hash_field_present']}",
        "",
        "Safety boundary:",
    ]
    for key, value in data["safety_boundary"].items():
        lines.append(f"- {key}: {value}")

    if data["failed_checks"]:
        lines.extend(["", "Failed checks:"])
        lines.extend(f"- {item}" for item in data["failed_checks"])
    if data["warn_checks"]:
        lines.extend(["", "Warnings:"])
        lines.extend(f"- {item}" for item in data["warn_checks"])
    if data["info_items"]:
        lines.extend(["", "Info:"])
        lines.extend(f"- {item}" for item in data["info_items"])

    lines.append("")
    return "\n".join(lines)


def format_markdown_audit(audit: SchemaAudit) -> str:
    data = audit_to_dict(audit)
    lines = [
        "# BTC Order-Intent Schema Audit",
        "",
        f"- Schema path: `{data['schema_path']}`",
        f"- Safety status: `{data['safety_status']}`",
        f"- Required field count: `{data['required_field_count']}`",
        f"- additionalProperties closed: `{data['additional_properties_closed']}`",
        f"- execution_allowed=false: `{data['execution_allowed_constraint']['constrained']}`",
        f"- operator_review_required=true: `{data['operator_review_required_constraint']['constrained']}`",
        f"- Allowed modes: `{', '.join(data['allowed_modes']) or 'none'}`",
        f"- Rejected modes: `{', '.join(data['explicitly_rejected_modes']) or 'none'}`",
        f"- Credential fields rejected: `{data['credential_field_rejection_status']}`",
        f"- BLOCK response rule present: `{data['block_response_rule_present']}`",
        f"- BLOCK risk-level rule present: `{data['block_risk_level_rule_present']}`",
        f"- stale_data rule present: `{data['stale_data_rule_present']}`",
        "",
        "## Failed Checks",
    ]
    lines.extend(f"- {item}" for item in data["failed_checks"] or ["none"])
    lines.append("")
    lines.append("## Warnings")
    lines.extend(f"- {item}" for item in data["warn_checks"] or ["none"])
    lines.append("")
    lines.append("## Boundary")
    lines.extend(f"- `{key}`: `{value}`" for key, value in data["safety_boundary"].items())
    lines.append("")
    return "\n".join(lines)


def write_audit_json(audit: SchemaAudit, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(audit_json(audit), encoding="utf-8")


def write_audit_markdown(audit: SchemaAudit, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(format_markdown_audit(audit), encoding="utf-8")


def _failed_load_audit(path: Path, message: str) -> SchemaAudit:
    return SchemaAudit(
        mode="btc_order_intent_schema_audit_read_only",
        schema_path=str(path),
        schema_found=path.exists(),
        json_valid=False,
        schema_draft=None,
        schema_version=None,
        required_field_count=0,
        required_fields=[],
        missing_required_fields=list(EXPECTED_REQUIRED_FIELDS),
        additional_properties=None,
        additional_properties_closed=False,
        execution_allowed_constraint={"constrained": False, "expected": False, "actual": None},
        operator_review_required_constraint={"constrained": False, "expected": True, "actual": None},
        allowed_modes=[],
        explicitly_rejected_modes=[],
        allowed_signal_decisions=[],
        allowed_response_actions=[],
        allowed_risk_levels=[],
        allowed_intended_actions=[],
        allowed_intended_sides=[],
        allowed_intended_order_types=[],
        block_response_rule_present=False,
        block_risk_level_rule_present=False,
        stale_data_rule_present=False,
        credential_field_rejection_status=False,
        credential_like_fields_checked=list(CREDENTIAL_FIELDS),
        credential_like_fields_not_explicitly_rejected=list(CREDENTIAL_FIELDS),
        numeric_non_negative_constraints={field: False for field in NUMERIC_NON_NEGATIVE_FIELDS},
        timestamp_format_constraints={field: False for field in TIMESTAMP_FIELDS},
        source_reference_fields_present={field: False for field in SOURCE_REFERENCE_FIELDS},
        checksum_hash_field_present=False,
        safety_status="FAIL",
        failed_checks=[message],
        warn_checks=[],
        info_items=[],
        safety_boundary=_safety_boundary(),
    )


def _schema_version(properties: dict[str, Any]) -> str | None:
    schema_version = properties.get("schema_version")
    if isinstance(schema_version, dict) and isinstance(schema_version.get("const"), str):
        return schema_version["const"]
    return None


def _str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _enum_values(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return []
    return _str_list(value.get("enum"))


def _const_constraint(value: Any, *, expected: bool) -> dict[str, Any]:
    actual = value.get("const") if isinstance(value, dict) else None
    return {"constrained": actual is expected, "expected": expected, "actual": actual}


def _has_non_negative_number_constraint(value: Any) -> bool:
    return isinstance(value, dict) and value.get("type") == "number" and value.get("minimum") == 0


def _has_date_time_constraint(value: Any) -> bool:
    return isinstance(value, dict) and value.get("type") == "string" and value.get("format") == "date-time"


def _has_conditional_none_rule(schema: dict[str, Any], *, trigger_field: str, trigger_value: str) -> bool:
    for rule in _all_of_rules(schema):
        rule_if = rule.get("if")
        rule_then = rule.get("then")
        if not isinstance(rule_if, dict) or not isinstance(rule_then, dict):
            continue
        if _property_const(rule_if, trigger_field) != trigger_value:
            continue
        if _property_const(rule_then, "intended_action") == "NONE":
            return True
    return False


def _has_stale_data_none_rule(schema: dict[str, Any]) -> bool:
    for rule in _all_of_rules(schema):
        rule_if = rule.get("if")
        rule_then = rule.get("then")
        if not isinstance(rule_if, dict) or not isinstance(rule_then, dict):
            continue
        risk_flags = rule_if.get("properties", {}).get("risk_flags")
        if not isinstance(risk_flags, dict):
            continue
        contains = risk_flags.get("contains")
        if isinstance(contains, dict) and contains.get("const") == "stale_data":
            if _property_const(rule_then, "intended_action") == "NONE":
                return True
    return False


def _all_of_rules(schema: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in schema.get("allOf", []) if isinstance(item, dict)]


def _property_const(rule: dict[str, Any], field: str) -> Any:
    properties = rule.get("properties")
    if not isinstance(properties, dict):
        return None
    field_rule = properties.get(field)
    if not isinstance(field_rule, dict):
        return None
    return field_rule.get("const")


def _explicitly_rejected_fields(schema: dict[str, Any]) -> set[str]:
    rejected: set[str] = set()
    for rule in _all_of_rules(schema):
        not_rule = rule.get("not")
        if not isinstance(not_rule, dict):
            continue
        for item in not_rule.get("anyOf", []):
            if not isinstance(item, dict):
                continue
            required = item.get("required")
            if isinstance(required, list):
                rejected.update(str(field) for field in required)
    return rejected


def _safety_boundary() -> dict[str, bool]:
    return {
        "read_only": True,
        "writes_order_intents": False,
        "adds_exchange_adapter": False,
        "calls_exchange_api": False,
        "requires_api_keys": False,
        "places_orders": False,
        "enables_testnet": False,
        "enables_live_trading": False,
        "reads_account_balances": False,
        "sends_external_notifications": False,
    }


def _bool_map_text(mapping: dict[str, bool]) -> str:
    return ", ".join(f"{key}={value}" for key, value in mapping.items())
