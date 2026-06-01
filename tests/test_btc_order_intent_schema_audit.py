from __future__ import annotations

import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

from btc_signal.order_intent_schema_audit import audit_schema, audit_to_dict, format_markdown_audit


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "btc_order_intent.schema.json"


def _schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _write_schema(tmp_path: Path, schema: dict[str, Any]) -> Path:
    path = tmp_path / "schema.json"
    path.write_text(json.dumps(schema, indent=2, sort_keys=True), encoding="utf-8")
    return path


def test_valid_current_schema_audits_as_pass() -> None:
    payload = audit_to_dict(audit_schema(SCHEMA_PATH))

    assert payload["safety_status"] == "PASS"
    assert payload["schema_found"] is True
    assert payload["json_valid"] is True
    assert payload["additional_properties_closed"] is True
    assert payload["execution_allowed_constraint"]["constrained"] is True
    assert payload["operator_review_required_constraint"]["constrained"] is True
    assert payload["credential_field_rejection_status"] is True


def test_missing_schema_path_returns_fail(tmp_path: Path) -> None:
    payload = audit_to_dict(audit_schema(tmp_path / "missing.schema.json"))

    assert payload["safety_status"] == "FAIL"
    assert payload["schema_found"] is False
    assert any("missing" in item for item in payload["failed_checks"])


def test_malformed_schema_json_returns_fail(tmp_path: Path) -> None:
    path = tmp_path / "bad.schema.json"
    path.write_text("{not-json", encoding="utf-8")

    payload = audit_to_dict(audit_schema(path))

    assert payload["safety_status"] == "FAIL"
    assert payload["json_valid"] is False
    assert any("could not be read" in item for item in payload["failed_checks"])


def test_schema_allowing_execution_allowed_true_returns_fail(tmp_path: Path) -> None:
    schema = _schema()
    schema["properties"]["execution_allowed"].pop("const")
    path = _write_schema(tmp_path, schema)

    payload = audit_to_dict(audit_schema(path))

    assert payload["safety_status"] == "FAIL"
    assert "execution_allowed is not constrained to false." in payload["failed_checks"]


def test_schema_allowing_live_mode_returns_fail(tmp_path: Path) -> None:
    schema = _schema()
    schema["properties"]["mode"]["enum"].append("live")
    path = _write_schema(tmp_path, schema)

    payload = audit_to_dict(audit_schema(path))

    assert payload["safety_status"] == "FAIL"
    assert "mode enum allows live." in payload["failed_checks"]


def test_schema_without_additional_properties_false_returns_fail(tmp_path: Path) -> None:
    schema = _schema()
    schema["additionalProperties"] = True
    path = _write_schema(tmp_path, schema)

    payload = audit_to_dict(audit_schema(path))

    assert payload["safety_status"] == "FAIL"
    assert any("additionalProperties" in item for item in payload["failed_checks"])


def test_schema_missing_stale_data_or_block_rules_returns_fail(tmp_path: Path) -> None:
    schema = _schema()
    schema["allOf"] = [schema["allOf"][0]]
    path = _write_schema(tmp_path, schema)

    payload = audit_to_dict(audit_schema(path))

    assert payload["safety_status"] == "FAIL"
    assert "BLOCK response rule requiring intended_action=NONE is absent." in payload["failed_checks"]
    assert "BLOCK risk-level rule requiring intended_action=NONE is absent." in payload["failed_checks"]
    assert "stale_data rule requiring intended_action=NONE is absent." in payload["failed_checks"]


def test_credential_like_field_acceptance_is_detected_as_fail(tmp_path: Path) -> None:
    schema = _schema()
    schema["additionalProperties"] = True
    schema["allOf"] = schema["allOf"][1:]
    path = _write_schema(tmp_path, schema)

    payload = audit_to_dict(audit_schema(path))

    assert payload["safety_status"] == "FAIL"
    assert payload["credential_field_rejection_status"] is False
    assert "api_key" in payload["credential_like_fields_not_explicitly_rejected"]


def test_schema_with_noncritical_missing_audit_field_returns_warn(tmp_path: Path) -> None:
    schema = _schema()
    schema["required"] = [field for field in schema["required"] if field != "checksum_or_hash"]
    path = _write_schema(tmp_path, schema)

    payload = audit_to_dict(audit_schema(path))

    assert payload["safety_status"] == "WARN"
    assert any("checksum_or_hash" in item for item in payload["warn_checks"])


def test_json_output_shape_is_stable() -> None:
    payload = audit_to_dict(audit_schema(SCHEMA_PATH))

    expected = {
        "mode",
        "schema_path",
        "schema_found",
        "json_valid",
        "schema_draft",
        "schema_version",
        "required_field_count",
        "required_fields",
        "additional_properties_closed",
        "execution_allowed_constraint",
        "operator_review_required_constraint",
        "allowed_modes",
        "credential_field_rejection_status",
        "safety_status",
        "failed_checks",
        "warn_checks",
        "safety_boundary",
    }
    assert expected.issubset(payload)


def test_markdown_rendering_includes_status() -> None:
    markdown = format_markdown_audit(audit_schema(SCHEMA_PATH))

    assert "# BTC Order-Intent Schema Audit" in markdown
    assert "Safety status: `PASS`" in markdown


def test_schema_audit_cli_outputs_json() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "audit_btc_order_intent_schema.py"),
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

    assert payload["mode"] == "btc_order_intent_schema_audit_read_only"
    assert payload["safety_status"] == "PASS"
    assert payload["safety_boundary"]["writes_order_intents"] is False


def test_audit_does_not_mutate_schema(tmp_path: Path) -> None:
    original = _schema()
    schema_copy = deepcopy(original)
    path = _write_schema(tmp_path, schema_copy)

    audit_schema(path)

    assert json.loads(path.read_text(encoding="utf-8")) == original
