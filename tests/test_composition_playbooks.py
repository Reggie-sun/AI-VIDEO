from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from scripts.composition_playbooks import (
    CANONICAL_PLAYBOOK_ROOT,
    PlaybookValidationError,
    load_composition_playbook,
    load_composition_playbooks,
)


CANONICAL_IDS = {
    "hard_cut_continuation",
    "character_consistent_dialogue_scene",
    "narration_ai_comic",
}


def _canonical_payload(name: str = "hard_cut_continuation") -> dict[str, object]:
    path = CANONICAL_PLAYBOOK_ROOT / f"{name}.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _write_yaml(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def test_three_canonical_playbooks_validate_against_checked_in_schema() -> None:
    playbooks = load_composition_playbooks()

    assert {playbook.playbook_id for playbook in playbooks} == CANONICAL_IDS
    schema = json.loads(
        (CANONICAL_PLAYBOOK_ROOT / "schema.json").read_text(encoding="utf-8")
    )
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {
        "name",
        "version",
        "playbook_id",
        "description",
        "applicable_when",
        "required_inputs",
        "preferred_strategies",
        "forbidden_fallbacks",
        "evidence_required",
        "known_limitations",
        "expected_failure_modes",
        "review_requirements",
        "repair_playbook",
    }


def test_missing_required_field_fails(tmp_path: Path) -> None:
    payload = _canonical_payload()
    payload.pop("evidence_required")
    path = tmp_path / "missing.yaml"
    _write_yaml(path, payload)

    with pytest.raises(ValidationError, match="evidence_required"):
        load_composition_playbook(path)


def test_unknown_field_fails(tmp_path: Path) -> None:
    payload = _canonical_payload()
    payload["runtime_override"] = True
    path = tmp_path / "unknown.yaml"
    _write_yaml(path, payload)

    with pytest.raises(ValidationError, match="runtime_override"):
        load_composition_playbook(path)


def test_invalid_strategy_fails(tmp_path: Path) -> None:
    payload = _canonical_payload()
    payload["preferred_strategies"] = ["magic_video"]
    path = tmp_path / "invalid-strategy.yaml"
    _write_yaml(path, payload)

    with pytest.raises(ValidationError, match="preferred_strategies"):
        load_composition_playbook(path)


def test_duplicate_list_member_fails(tmp_path: Path) -> None:
    payload = _canonical_payload()
    payload["preferred_strategies"] = ["image_to_video", "image_to_video"]
    path = tmp_path / "duplicate.yaml"
    _write_yaml(path, payload)

    with pytest.raises(ValidationError, match="unique"):
        load_composition_playbook(path)


def test_empty_evidence_requirements_fail(tmp_path: Path) -> None:
    payload = _canonical_payload()
    payload["evidence_required"] = []
    path = tmp_path / "empty-evidence.yaml"
    _write_yaml(path, payload)

    with pytest.raises(ValidationError, match="at least 1"):
        load_composition_playbook(path)


@pytest.mark.parametrize(
    "forbidden_field",
    ["provider", "provider_task_id", "manifest_state", "active_output"],
)
def test_provider_and_runtime_state_fields_fail(
    tmp_path: Path, forbidden_field: str
) -> None:
    payload = _canonical_payload()
    payload[forbidden_field] = "must-not-exist"
    path = tmp_path / "forbidden.yaml"
    _write_yaml(path, payload)

    with pytest.raises(PlaybookValidationError, match="forbidden field"):
        load_composition_playbook(path)


@pytest.mark.parametrize("version", ["1", "v1", "1.0", "01.0.0", "1.0.0-dev"])
def test_invalid_version_fails(tmp_path: Path, version: str) -> None:
    payload = _canonical_payload()
    payload["version"] = version
    path = tmp_path / "invalid-version.yaml"
    _write_yaml(path, payload)

    with pytest.raises(ValidationError, match="version"):
        load_composition_playbook(path)


def test_duplicate_playbook_id_fails(tmp_path: Path) -> None:
    first = _canonical_payload("hard_cut_continuation")
    second = _canonical_payload("narration_ai_comic")
    second["playbook_id"] = first["playbook_id"]
    _write_yaml(tmp_path / "first.yaml", first)
    _write_yaml(tmp_path / "second.yaml", second)

    with pytest.raises(PlaybookValidationError, match="duplicate playbook_id"):
        load_composition_playbooks(tmp_path)


def test_yaml_parsing_is_deterministic_and_duplicate_keys_fail(tmp_path: Path) -> None:
    payload = _canonical_payload()
    ordered = tmp_path / "ordered.yaml"
    reversed_order = tmp_path / "reversed.yaml"
    _write_yaml(ordered, payload)
    _write_yaml(reversed_order, dict(reversed(tuple(payload.items()))))

    first = load_composition_playbook(ordered)
    second = load_composition_playbook(reversed_order)
    assert first.model_dump(mode="json") == second.model_dump(mode="json")

    duplicate_key = tmp_path / "duplicate-key.yaml"
    duplicate_key.write_text(
        ordered.read_text(encoding="utf-8") + "name: Duplicate\n",
        encoding="utf-8",
    )
    with pytest.raises(PlaybookValidationError, match="duplicate YAML key"):
        load_composition_playbook(duplicate_key)


@pytest.mark.parametrize(
    "absolute_value",
    [
        "/tmp/runtime-dependent-advice",
        "  /tmp/leading-whitespace",
        r"\\server\share\runtime-dependent-advice",
        r"  C:\runtime-dependent-advice",
    ],
)
def test_absolute_paths_are_rejected(
    tmp_path: Path, absolute_value: str
) -> None:
    payload = _canonical_payload()
    payload["known_limitations"] = [absolute_value]
    path = tmp_path / "absolute-path.yaml"
    _write_yaml(path, payload)

    with pytest.raises(PlaybookValidationError, match="absolute path"):
        load_composition_playbook(path)
