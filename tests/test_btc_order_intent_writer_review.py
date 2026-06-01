from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from btc_signal.order_intent_writer_review import (
    SECTION_TITLES,
    build_writer_review_checklist,
    checklist_to_dict,
    format_text_checklist,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "btc_order_intent.schema.json"


def _payload(schema_path: Path = SCHEMA_PATH) -> dict:
    return checklist_to_dict(build_writer_review_checklist(schema_path=schema_path))


def test_checklist_generation_returns_deterministic_sections() -> None:
    payload = _payload()

    assert [section["title"] for section in payload["sections"]] == list(SECTION_TITLES)
    assert payload["safety_status"] == "PASS"


def test_checklist_includes_no_trading_boundary() -> None:
    payload = _payload()
    text = format_text_checklist(build_writer_review_checklist(schema_path=SCHEMA_PATH))

    assert payload["safety_boundary"]["places_orders"] is False
    assert payload["safety_boundary"]["enables_live_trading"] is False
    assert "writer must never place orders" in text
    assert "writer must never call private APIs" in text


def test_checklist_includes_schema_dependency() -> None:
    payload = _payload()
    schema_section = next(section for section in payload["sections"] if section["title"] == "Schema dependency")

    item_text = [item["text"] for item in schema_section["items"]]
    assert "schemas/btc_order_intent.schema.json exists" in item_text
    assert "schema audit command returns PASS" in item_text
    assert "execution_allowed=false enforced" in item_text
    assert schema_section["status"] == "PASS"


def test_checklist_includes_credential_rejection() -> None:
    payload = _payload()

    assert payload["schema_audit_summary"]["credential_field_rejection_status"] is True
    assert any(
        item["text"] == "credential fields rejected"
        for section in payload["sections"]
        for item in section["items"]
    )


def test_checklist_includes_block_and_stale_data_constraints() -> None:
    payload = _payload()
    safety_section = next(section for section in payload["sections"] if section["title"] == "Safety gates")
    item_text = [item["text"] for item in safety_section["items"]]

    assert "stale_data blocks executable intent" in item_text
    assert "BLOCK response blocks executable intent" in item_text
    assert "BLOCK risk level blocks executable intent" in item_text


def test_checklist_includes_future_test_requirements() -> None:
    payload = _payload()

    assert "valid WAIT intent fixture" in payload["future_test_requirements"]
    assert "valid BLOCK intent fixture" in payload["future_test_requirements"]
    assert "invalid execution_allowed=true fixture" in payload["future_test_requirements"]
    assert "invalid credential field fixture" in payload["future_test_requirements"]
    assert "stale_data + action != NONE fixture" in payload["future_test_requirements"]
    assert "duplicate intent prevention test" in payload["future_test_requirements"]
    assert "append-only behavior test" in payload["future_test_requirements"]
    assert "checksum determinism test" in payload["future_test_requirements"]


def test_json_output_shape_is_stable() -> None:
    payload = _payload()

    expected = {
        "mode",
        "schema_path",
        "safety_status",
        "primary_reason",
        "sections",
        "failed_checks",
        "warn_checks",
        "info_items",
        "schema_audit_summary",
        "future_test_requirements",
        "safety_boundary",
        "approval_statement",
        "recommended_next_action",
    }
    assert expected.issubset(payload)


def test_cli_text_output_works() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "review_btc_order_intent_writer_design.py"),
            "--schema-path",
            str(SCHEMA_PATH),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "BTC OrderIntentWriter Design Review Checklist" in result.stdout
    assert "Checklist status: PASS" in result.stdout


def test_cli_json_output_works() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "review_btc_order_intent_writer_design.py"),
            "--schema-path",
            str(SCHEMA_PATH),
            "--format",
            "json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["mode"] == "btc_order_intent_writer_design_review_read_only"
    assert payload["safety_status"] == "PASS"


def test_missing_schema_path_produces_fail(tmp_path: Path) -> None:
    payload = _payload(tmp_path / "missing.schema.json")

    assert payload["safety_status"] == "FAIL"
    assert any("Schema file is missing" in item for item in payload["failed_checks"])


def test_pass_does_not_imply_writer_approval() -> None:
    payload = _payload()

    assert payload["safety_status"] == "PASS"
    assert "not approval to implement or trade" in payload["approval_statement"]
    assert payload["safety_boundary"]["writes_order_intents"] is False
    assert payload["safety_boundary"]["adds_order_intent_writer_runtime"] is False


def test_include_future_test_plan_adds_extra_section() -> None:
    payload = checklist_to_dict(
        build_writer_review_checklist(schema_path=SCHEMA_PATH, include_future_test_plan=True)
    )

    assert [section["title"] for section in payload["sections"]][-1] == "Future implementation sequence"
