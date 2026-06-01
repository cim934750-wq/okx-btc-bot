from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from btc_signal.order_intent_schema_audit import SchemaAudit, audit_schema, audit_to_dict


SECTION_TITLES: tuple[str, ...] = (
    "Scope boundary",
    "Schema dependency",
    "Input dependency",
    "Safety gates",
    "Output constraints",
    "Operator review",
    "Test requirements before future writer",
    "Forbidden future shortcuts",
)

FUTURE_TEST_REQUIREMENTS: tuple[str, ...] = (
    "valid WAIT intent fixture",
    "valid BLOCK intent fixture",
    "invalid execution_allowed=true fixture",
    "invalid credential field fixture",
    "stale_data + action != NONE fixture",
    "duplicate intent prevention test",
    "append-only behavior test",
    "checksum determinism test",
)


@dataclass(slots=True)
class ReviewItem:
    item_id: str
    text: str
    status: str
    required: bool
    evidence: str


@dataclass(slots=True)
class ReviewSection:
    title: str
    status: str
    items: list[ReviewItem]


@dataclass(slots=True)
class WriterReviewChecklist:
    mode: str
    schema_path: str
    safety_status: str
    primary_reason: str
    sections: list[ReviewSection]
    failed_checks: list[str]
    warn_checks: list[str]
    info_items: list[str]
    schema_audit_summary: dict[str, Any]
    future_test_requirements: list[str]
    safety_boundary: dict[str, bool]
    approval_statement: str
    recommended_next_action: str


def build_writer_review_checklist(
    *,
    schema_path: str | Path,
    include_future_test_plan: bool = False,
    strict: bool = False,
) -> WriterReviewChecklist:
    schema_audit = audit_schema(schema_path)

    sections = _build_sections(schema_audit, include_future_test_plan=include_future_test_plan)
    failed_checks = _failed_checks(schema_audit, sections)
    warn_checks = _warn_checks(schema_audit, sections)
    if strict and warn_checks:
        failed_checks.extend(f"Strict mode treats warning as failure: {warning}" for warning in warn_checks)

    safety_status = "FAIL" if failed_checks else "WARN" if warn_checks else "PASS"
    primary_reason = _primary_reason(safety_status, failed_checks, warn_checks)

    return WriterReviewChecklist(
        mode="btc_order_intent_writer_design_review_read_only",
        schema_path=str(Path(schema_path)),
        safety_status=safety_status,
        primary_reason=primary_reason,
        sections=sections,
        failed_checks=failed_checks,
        warn_checks=warn_checks,
        info_items=_info_items(safety_status),
        schema_audit_summary={
            "safety_status": schema_audit.safety_status,
            "schema_found": schema_audit.schema_found,
            "json_valid": schema_audit.json_valid,
            "schema_version": schema_audit.schema_version,
            "additional_properties_closed": schema_audit.additional_properties_closed,
            "execution_allowed_constrained_false": schema_audit.execution_allowed_constraint.get("constrained") is True,
            "operator_review_required_constrained_true": schema_audit.operator_review_required_constraint.get("constrained")
            is True,
            "credential_field_rejection_status": schema_audit.credential_field_rejection_status,
            "block_response_rule_present": schema_audit.block_response_rule_present,
            "block_risk_level_rule_present": schema_audit.block_risk_level_rule_present,
            "stale_data_rule_present": schema_audit.stale_data_rule_present,
            "allowed_modes": schema_audit.allowed_modes,
            "rejected_modes": schema_audit.explicitly_rejected_modes,
            "failed_checks": schema_audit.failed_checks,
            "warn_checks": schema_audit.warn_checks,
        },
        future_test_requirements=list(FUTURE_TEST_REQUIREMENTS),
        safety_boundary=_safety_boundary(),
        approval_statement=(
            "PASS only means this design checklist is complete. It is not approval to implement or trade: "
            "no writer, order intent creation, adapter, testnet use, or trading is approved."
        ),
        recommended_next_action=_recommended_next_action(safety_status),
    )


def checklist_to_dict(checklist: WriterReviewChecklist) -> dict[str, Any]:
    return asdict(checklist)


def checklist_json(checklist: WriterReviewChecklist) -> str:
    return json.dumps(checklist_to_dict(checklist), indent=2, sort_keys=True) + "\n"


def format_text_checklist(checklist: WriterReviewChecklist) -> str:
    payload = checklist_to_dict(checklist)
    lines = [
        "BTC OrderIntentWriter Design Review Checklist",
        f"Schema path: {payload['schema_path']}",
        f"Checklist status: {payload['safety_status']}",
        f"Primary reason: {payload['primary_reason']}",
        f"Schema audit status: {payload['schema_audit_summary']['safety_status']}",
        "",
        "Approval boundary:",
        f"- {payload['approval_statement']}",
        "",
    ]

    for section in payload["sections"]:
        lines.append(f"{section['title']}: {section['status']}")
        for item in section["items"]:
            required = "required" if item["required"] else "optional"
            lines.append(f"- [{item['status']}] {item['text']} ({required}; {item['evidence']})")
        lines.append("")

    lines.append("Future writer test requirements:")
    lines.extend(f"- {item}" for item in payload["future_test_requirements"])
    lines.append("")
    lines.append("Safety boundary:")
    lines.extend(f"- {key}: {value}" for key, value in payload["safety_boundary"].items())

    if payload["failed_checks"]:
        lines.extend(["", "Failed checks:"])
        lines.extend(f"- {item}" for item in payload["failed_checks"])
    if payload["warn_checks"]:
        lines.extend(["", "Warnings:"])
        lines.extend(f"- {item}" for item in payload["warn_checks"])
    if payload["info_items"]:
        lines.extend(["", "Info:"])
        lines.extend(f"- {item}" for item in payload["info_items"])

    lines.extend(["", f"Recommended next action: {payload['recommended_next_action']}", ""])
    return "\n".join(lines)


def format_markdown_checklist(checklist: WriterReviewChecklist) -> str:
    payload = checklist_to_dict(checklist)
    lines = [
        "# BTC OrderIntentWriter Design Review Checklist",
        "",
        f"- Schema path: `{payload['schema_path']}`",
        f"- Checklist status: `{payload['safety_status']}`",
        f"- Schema audit status: `{payload['schema_audit_summary']['safety_status']}`",
        f"- Approval boundary: {payload['approval_statement']}",
        "",
    ]

    for section in payload["sections"]:
        lines.append(f"## {section['title']}: {section['status']}")
        for item in section["items"]:
            lines.append(f"- `{item['status']}` {item['text']}")
        lines.append("")

    lines.append("## Future Writer Test Requirements")
    lines.extend(f"- {item}" for item in payload["future_test_requirements"])
    lines.append("")
    lines.append("## Safety Boundary")
    lines.extend(f"- `{key}`: `{value}`" for key, value in payload["safety_boundary"].items())
    lines.append("")
    return "\n".join(lines)


def write_checklist_json(checklist: WriterReviewChecklist, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(checklist_json(checklist), encoding="utf-8")


def write_checklist_markdown(checklist: WriterReviewChecklist, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(format_markdown_checklist(checklist), encoding="utf-8")


def _build_sections(schema_audit: SchemaAudit, *, include_future_test_plan: bool) -> list[ReviewSection]:
    sections = [
        ReviewSection(
            title="Scope boundary",
            status="PASS",
            items=[
                _item("scope.future_only", "writer is future-only", "PASS", "documented design boundary"),
                _item(
                    "scope.non_executing_json",
                    "writer may only write non-executing JSON",
                    "PASS",
                    "future output limited to runtime/order_intents/*.json",
                ),
                _item("scope.no_orders", "writer must never place orders", "PASS", "no order placement allowed"),
                _item("scope.no_private_api", "writer must never call private APIs", "PASS", "no private API access"),
                _item("scope.no_credentials", "writer must never use credentials", "PASS", "no API keys required"),
            ],
        ),
        ReviewSection(
            title="Schema dependency",
            status="PASS" if schema_audit.safety_status == "PASS" else schema_audit.safety_status,
            items=[
                _item("schema.exists", "schemas/btc_order_intent.schema.json exists", _pass_fail(schema_audit.schema_found)),
                _item("schema.audit_pass", "schema audit command returns PASS", _pass_fail(schema_audit.safety_status == "PASS")),
                _item(
                    "schema.execution_false",
                    "execution_allowed=false enforced",
                    _pass_fail(schema_audit.execution_allowed_constraint.get("constrained") is True),
                ),
                _item(
                    "schema.operator_review_true",
                    "operator_review_required=true enforced",
                    _pass_fail(schema_audit.operator_review_required_constraint.get("constrained") is True),
                ),
                _item(
                    "schema.additional_properties_false",
                    "additionalProperties=false enforced",
                    _pass_fail(schema_audit.additional_properties_closed),
                ),
                _item(
                    "schema.credential_rejection",
                    "credential fields rejected",
                    _pass_fail(schema_audit.credential_field_rejection_status),
                ),
            ],
        ),
        ReviewSection(
            title="Input dependency",
            status="PASS",
            items=[
                _item("input.decision_log", "source decision log must exist", "PASS", "required future input"),
                _item("input.status_snapshot", "paper status snapshot must exist", "PASS", "required future input"),
                _item(
                    "input.review_or_alert",
                    "daily review or alert summary should exist",
                    "PASS",
                    "optional but recommended review input",
                    required=False,
                ),
                _item("input.risk_response", "risk/response output must be available", "PASS", "required future input"),
            ],
        ),
        ReviewSection(
            title="Safety gates",
            status="PASS" if _schema_safety_rules_pass(schema_audit) else "FAIL",
            items=[
                _item(
                    "gate.stale_data",
                    "stale_data blocks executable intent",
                    _pass_fail(schema_audit.stale_data_rule_present),
                ),
                _item(
                    "gate.block_response",
                    "BLOCK response blocks executable intent",
                    _pass_fail(schema_audit.block_response_rule_present),
                ),
                _item(
                    "gate.block_risk",
                    "BLOCK risk level blocks executable intent",
                    _pass_fail(schema_audit.block_risk_level_rule_present),
                ),
                _item("gate.paper_state", "malformed/missing paper state blocks intent", "PASS", "required future gate"),
                _item(
                    "gate.duplicate_position",
                    "duplicate open paper position blocks long intent",
                    "PASS",
                    "required future gate",
                ),
                _item(
                    "gate.unresolved_flags",
                    "unresolved risk flags require block reason",
                    "PASS",
                    "required future gate",
                ),
            ],
        ),
        ReviewSection(
            title="Output constraints",
            status="PASS",
            items=[
                _item("output.path", "output path must be runtime/order_intents/", "PASS", "future-only output path"),
                _item("output.append_only", "output must be append-only", "PASS", "required future write rule"),
                _item(
                    "output.checksum",
                    "output must include checksum/hash",
                    _pass_fail(schema_audit.checksum_hash_field_present),
                ),
                _item(
                    "output.source_log",
                    "output must include source_decision_log_path",
                    _pass_fail(schema_audit.source_reference_fields_present.get("source_decision_log_path") is True),
                ),
                _item(
                    "output.source_snapshot",
                    "output must include source_snapshot_path",
                    _pass_fail(schema_audit.source_reference_fields_present.get("source_snapshot_path") is True),
                ),
                _item(
                    "output.blocked_reason",
                    "output must include execution_blocked_reason",
                    _pass_fail("execution_blocked_reason" in schema_audit.required_fields),
                ),
                _item(
                    "output.no_credentials",
                    "output must not include credentials",
                    _pass_fail(schema_audit.credential_field_rejection_status),
                ),
            ],
        ),
        ReviewSection(
            title="Operator review",
            status="PASS",
            items=[
                _item(
                    "operator.review_required",
                    "operator_review_required must be true",
                    _pass_fail(schema_audit.operator_review_required_constraint.get("constrained") is True),
                ),
                _item(
                    "operator.not_trade_approval",
                    "checklist must say this is not approval to trade",
                    "PASS",
                    "approval statement included",
                ),
                _item(
                    "operator.before_adapter",
                    "manual review must happen before any future adapter discussion",
                    "PASS",
                    "required future gate",
                ),
            ],
        ),
        ReviewSection(
            title="Test requirements before future writer",
            status="PASS",
            items=[
                _item(f"test.{index + 1}", requirement, "PASS", "required future test")
                for index, requirement in enumerate(FUTURE_TEST_REQUIREMENTS)
            ],
        ),
        ReviewSection(
            title="Forbidden future shortcuts",
            status="PASS",
            items=[
                _item("forbidden.adapter_call", "writer cannot call adapter", "PASS", "forbidden"),
                _item("forbidden.exchange_order", "writer cannot emit exchange order", "PASS", "forbidden"),
                _item(
                    "forbidden.execution_true",
                    "writer cannot set execution_allowed=true",
                    _pass_fail(schema_audit.execution_allowed_constraint.get("constrained") is True),
                ),
                _item("forbidden.bypass_schema", "writer cannot bypass schema validation", "PASS", "forbidden"),
                _item(
                    "forbidden.secrets",
                    "writer cannot write secrets",
                    _pass_fail(schema_audit.credential_field_rejection_status),
                ),
                _item("forbidden.promote_paper", "writer cannot auto-promote PAPER_LONG to trade", "PASS", "forbidden"),
            ],
        ),
    ]

    if include_future_test_plan:
        sections.append(
            ReviewSection(
                title="Future implementation sequence",
                status="PASS",
                items=[
                    _item("plan.1", "finish design review before implementation", "PASS", "future-only"),
                    _item("plan.2", "implement writer behind explicit approval", "PASS", "future-only"),
                    _item("plan.3", "keep writer non-executing and append-only", "PASS", "future-only"),
                    _item("plan.4", "rerun schema audit and writer review before merge", "PASS", "future-only"),
                ],
            )
        )
    return sections


def _item(
    item_id: str,
    text: str,
    status: str,
    evidence: str = "checklist item",
    *,
    required: bool = True,
) -> ReviewItem:
    return ReviewItem(item_id=item_id, text=text, status=status, required=required, evidence=evidence)


def _pass_fail(condition: bool) -> str:
    return "PASS" if condition else "FAIL"


def _schema_safety_rules_pass(schema_audit: SchemaAudit) -> bool:
    return (
        schema_audit.stale_data_rule_present
        and schema_audit.block_response_rule_present
        and schema_audit.block_risk_level_rule_present
    )


def _failed_checks(schema_audit: SchemaAudit, sections: list[ReviewSection]) -> list[str]:
    failed = list(schema_audit.failed_checks)
    for section in sections:
        for item in section.items:
            if item.required and item.status == "FAIL":
                failed.append(f"{section.title}: {item.text}")
    return list(dict.fromkeys(failed))


def _warn_checks(schema_audit: SchemaAudit, sections: list[ReviewSection]) -> list[str]:
    warnings = list(schema_audit.warn_checks)
    for section in sections:
        for item in section.items:
            if not item.required and item.status == "WARN":
                warnings.append(f"{section.title}: {item.text}")
    return list(dict.fromkeys(warnings))


def _primary_reason(status: str, failed_checks: list[str], warn_checks: list[str]) -> str:
    if status == "FAIL":
        return failed_checks[0] if failed_checks else "Required writer design review check failed."
    if status == "WARN":
        return warn_checks[0] if warn_checks else "Writer design review has non-blocking warnings."
    return "Design checklist is complete; this is not approval to implement or trade."


def _info_items(status: str) -> list[str]:
    if status == "PASS":
        return [
            "Checklist sections are present.",
            "Schema dependency passed.",
            "No writer implementation was created.",
            "No adapter or trading capability was added.",
        ]
    return []


def _recommended_next_action(status: str) -> str:
    if status == "FAIL":
        return "Fix failed schema/checklist gates before discussing any future writer."
    if status == "WARN":
        return "Review warnings before any future writer implementation task."
    return "Continue paper observation or request a separate non-executing writer implementation task."


def _safety_boundary() -> dict[str, bool]:
    return {
        "read_only_checklist": True,
        "writes_order_intents": False,
        "creates_runtime_order_intents_dir": False,
        "adds_order_intent_writer_runtime": False,
        "adds_exchange_adapter": False,
        "adds_simulated_dry_run_adapter": False,
        "calls_exchange_api": False,
        "requires_api_keys": False,
        "places_orders": False,
        "enables_testnet": False,
        "enables_live_trading": False,
        "reads_account_balances": False,
        "sends_external_notifications": False,
    }
