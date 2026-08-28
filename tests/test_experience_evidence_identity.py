from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = (
    ROOT
    / ".agents"
    / "skills"
    / "distill-ai-video-learning"
    / "scripts"
    / "validate_evidence_identity.py"
)


def _load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_evidence_identity", VALIDATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _record(
    rows: list[str],
    *,
    eligibility: str = "eligible",
    version: str | None = "1",
) -> str:
    version_line = (
        f'evidence_index_version: "{version}"\n' if version is not None else ""
    )
    return (
        "---\n"
        "record_kind: media_experiment\n"
        "topic_id: h3-conditioning-attribution\n"
        f"learning_eligibility: {eligibility}\n"
        f"{version_line}"
        "---\n\n"
        "# Record\n\n"
        "## Evidence Index\n\n"
        "| evidence_id | independence_key | experiment_id | attempt_id | arm_id | "
        "artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | "
        "related_evidence_id | source |\n"
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
        + "\n".join(rows)
        + "\n"
    )


def _claim(
    supporting: list[str],
    counter: list[str] | None = None,
    *,
    admission_basis: str = "TWO_INDEPENDENT_ATTEMPTS",
    extra_frontmatter: str = "",
) -> str:
    def table(rows: list[str]) -> str:
        return (
            "| evidence_ref | independence_key | experiment_id | attempt_id | arm_id | "
            "artifact_sha256 | proof_layer | verdict | source |\n"
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |\n"
            + "\n".join(rows)
            + "\n"
        )

    return (
        "---\n"
        "document_kind: learning_claim\n"
        "claim_id: h3-conditioning-attribution\n"
        'evidence_index_version: "1"\n'
        f"admission_basis: {admission_basis}\n"
        f"{extra_frontmatter}"
        "---\n\n"
        "# Claim\n\n"
        "### Supporting Evidence\n\n"
        + table(supporting)
        + "\n### Counter Evidence\n\n"
        + table(counter or [])
    )


def _record_row(
    evidence_id: str,
    key: str,
    *,
    experiment: str = "exp-1",
    attempt: str = "attempt-1",
    arm: str = "N/A",
    sha: str = "a" * 64,
    proof: str = "TECHNICAL",
    verdict: str = "PASS",
    failure: str = "NONE",
    relation: str = "NEW_ATTEMPT",
    related: str = "NONE",
    source: str = "runs/exp-1/result.json",
) -> str:
    return (
        f"| {evidence_id} | {key} | {experiment} | {attempt} | {arm} | {sha} | "
        f"{proof} | {verdict} | {failure} | {relation} | {related} | {source} |"
    )


def _claim_row(
    evidence_ref: str,
    key: str,
    *,
    experiment: str = "exp-1",
    attempt: str = "attempt-1",
    arm: str = "N/A",
    sha: str = "a" * 64,
    proof: str = "TECHNICAL",
    verdict: str = "PASS",
    source: str = "runs/exp-1/result.json",
) -> str:
    return (
        f"| {evidence_ref} | {key} | {experiment} | {attempt} | {arm} | {sha} | "
        f"{proof} | {verdict} | {source} |"
    )


def test_same_attempt_across_records_and_proof_layers_counts_once(
    tmp_path: Path,
) -> None:
    validator = _load_validator()
    first = tmp_path / "first.md"
    second = tmp_path / "second.md"
    claim = tmp_path / "claim.md"
    shared_key = "local-h3:exp-1:attempt-1"
    first.write_text(
        _record([_record_row("technical", shared_key)]), encoding="utf-8"
    )
    second.write_text(
        _record(
            [
                _record_row(
                    "human",
                    shared_key,
                    proof="HUMAN",
                    verdict="FAIL",
                    failure="MOTION_QUALITY",
                    relation="SAME_EVIDENCE_NEW_PROOF_LAYER",
                    related="first.md#technical",
                    source="docs/record_for_agent/first.md",
                )
            ]
        ),
        encoding="utf-8",
    )
    claim.write_text(
        _claim(
            [
                _claim_row("first.md#technical", shared_key),
                _claim_row(
                    "second.md#human",
                    shared_key,
                    proof="HUMAN",
                    verdict="FAIL",
                    source="docs/record_for_agent/second.md",
                ),
            ]
        ),
        encoding="utf-8",
    )

    reports = validator.validate_paths([first, second, claim])
    claim_report = reports[-1]

    assert claim_report.support_keys == (shared_key,)
    assert claim_report.admitted is False
    assert "TWO_INDEPENDENT_ATTEMPTS requires at least two distinct supporting independence_key values" in claim_report.errors


def test_controlled_multi_arm_is_one_admission_basis(tmp_path: Path) -> None:
    validator = _load_validator()
    record = tmp_path / "record.md"
    claim = tmp_path / "claim.md"
    record.write_text(
        _record(
            [
                _record_row(
                    "arm-a",
                    "local-h3:exp-ab:attempt-a",
                    experiment="exp-ab",
                    attempt="attempt-a",
                    arm="A",
                ),
                _record_row(
                    "arm-b",
                    "local-h3:exp-ab:attempt-b",
                    experiment="exp-ab",
                    attempt="attempt-b",
                    arm="B",
                    sha="b" * 64,
                ),
            ]
        ),
        encoding="utf-8",
    )
    claim.write_text(
        _claim(
            [
                _claim_row(
                    "record.md#arm-a",
                    "local-h3:exp-ab:attempt-a",
                    experiment="exp-ab",
                    attempt="attempt-a",
                    arm="A",
                ),
                _claim_row(
                    "record.md#arm-b",
                    "local-h3:exp-ab:attempt-b",
                    experiment="exp-ab",
                    attempt="attempt-b",
                    arm="B",
                    sha="b" * 64,
                ),
            ],
            admission_basis="CONTROLLED_MULTI_ARM",
        ),
        encoding="utf-8",
    )

    report = validator.validate_paths([record, claim])[1]

    assert report.errors == ()
    assert report.admitted is True
    assert report.support_keys == (
        "local-h3:exp-ab:attempt-a",
        "local-h3:exp-ab:attempt-b",
    )


def test_material_existing_claim_update_requires_target_previous_evidence_and_delta(
    tmp_path: Path,
) -> None:
    validator = _load_validator()
    record = tmp_path / "record.md"
    claim = tmp_path / "claim.md"
    record.write_text(
        _record(
            [
                _record_row("old-human", "local-h3:exp-1:attempt-1"),
                _record_row(
                    "new-human",
                    "local-h3:exp-2:attempt-1",
                    experiment="exp-2",
                    sha="b" * 64,
                ),
            ]
        ),
        encoding="utf-8",
    )
    claim.write_text(
        _claim(
            [
                _claim_row(
                    "record.md#new-human",
                    "local-h3:exp-2:attempt-1",
                    experiment="exp-2",
                    sha="b" * 64,
                )
            ],
            admission_basis="MATERIAL_EXISTING_CLAIM_UPDATE",
        ),
        encoding="utf-8",
    )

    invalid = validator.validate_paths([record, claim])[1]
    assert invalid.admitted is False
    assert invalid.errors == (
        "MATERIAL_EXISTING_CLAIM_UPDATE requires material_update_target_claim",
        "MATERIAL_EXISTING_CLAIM_UPDATE requires material_update_previous_evidence",
        "MATERIAL_EXISTING_CLAIM_UPDATE requires material_update_delta",
    )

    claim.write_text(
        _claim(
            [
                _claim_row(
                    "record.md#new-human",
                    "local-h3:exp-2:attempt-1",
                    experiment="exp-2",
                    sha="b" * 64,
                )
            ],
            admission_basis="MATERIAL_EXISTING_CLAIM_UPDATE",
            extra_frontmatter=(
                "material_update_target_claim: h3-conditioning-attribution\n"
                "material_update_previous_evidence: record.md#old-human\n"
                "material_update_delta: narrows motion-quality scope after human FAIL\n"
            ),
        ),
        encoding="utf-8",
    )

    valid = validator.validate_paths([record, claim])[1]
    assert valid.errors == ()
    assert valid.admitted is True


def test_record_validation_fails_closed_for_identity_and_relation_errors(
    tmp_path: Path,
) -> None:
    validator = _load_validator()
    record = tmp_path / "record.md"
    record.write_text(
        _record(
            [
                _record_row("same", "", sha="not-a-sha"),
                _record_row(
                    "same",
                    "local-h3:exp-1:attempt-2",
                    attempt="attempt-2",
                    relation="SAME_EVIDENCE_NEW_PROOF_LAYER",
                    related="missing",
                ),
            ]
        ),
        encoding="utf-8",
    )

    report = validator.validate_paths([record])[0]

    assert report.admitted is False
    assert any("blank independence_key" in error for error in report.errors)
    assert any("malformed artifact_sha256" in error for error in report.errors)
    assert any("duplicate evidence_id 'same'" in error for error in report.errors)
    assert any("unresolved related_evidence_id 'missing'" in error for error in report.errors)


def test_same_sha_different_attempts_remain_distinct(tmp_path: Path) -> None:
    validator = _load_validator()
    shared_sha = "c" * 64
    record = tmp_path / "record.md"
    claim = tmp_path / "claim.md"
    record.write_text(
        _record(
            [
                _record_row(
                    "a",
                    "local-h3:exp-a:attempt-1",
                    experiment="exp-a",
                    sha=shared_sha,
                    source="runs/exp-a/result.json",
                ),
                _record_row(
                    "b",
                    "local-h3:exp-b:attempt-1",
                    experiment="exp-b",
                    sha=shared_sha,
                    source="runs/exp-b/result.json",
                ),
            ]
        ),
        encoding="utf-8",
    )
    claim.write_text(
        _claim(
            [
                _claim_row(
                    "record.md#a",
                    "local-h3:exp-a:attempt-1",
                    experiment="exp-a",
                    sha=shared_sha,
                    source="runs/exp-a/result.json",
                ),
                _claim_row(
                    "record.md#b",
                    "local-h3:exp-b:attempt-1",
                    experiment="exp-b",
                    sha=shared_sha,
                    source="runs/exp-b/result.json",
                ),
            ]
        ),
        encoding="utf-8",
    )

    report = validator.validate_paths([record, claim])[1]

    assert report.admitted is True
    assert len(report.support_keys) == 2


def test_q0_identity_hash_is_accepted(tmp_path: Path) -> None:
    validator = _load_validator()
    record = tmp_path / "record.md"
    claim = tmp_path / "claim.md"
    record.write_text(
        _record(
            [
                _record_row("a", f"q0:{'a' * 64}"),
                _record_row(
                    "b",
                    f"q0:{'b' * 64}",
                    experiment="exp-2",
                    sha="b" * 64,
                ),
            ]
        ),
        encoding="utf-8",
    )
    claim.write_text(
        _claim(
            [
                _claim_row("record.md#a", f"q0:{'a' * 64}"),
                _claim_row(
                    "record.md#b",
                    f"q0:{'b' * 64}",
                    experiment="exp-2",
                    sha="b" * 64,
                ),
            ]
        ),
        encoding="utf-8",
    )

    report = validator.validate_paths([record, claim])[1]
    assert report.errors == ()
    assert report.admitted is True


def test_claim_reference_must_match_explicit_source_evidence(tmp_path: Path) -> None:
    validator = _load_validator()
    record = tmp_path / "record.md"
    claim = tmp_path / "claim.md"
    record.write_text(
        _record(
            [
                _record_row("a", "local-h3:exp-1:attempt-1"),
                _record_row(
                    "b",
                    "local-h3:exp-2:attempt-1",
                    experiment="exp-2",
                    sha="b" * 64,
                ),
            ]
        ),
        encoding="utf-8",
    )
    claim.write_text(
        _claim(
            [
                _claim_row(
                    "record.md#a",
                    "local-h3:exp-1:wrong-attempt",
                ),
                _claim_row(
                    "record.md#missing",
                    "local-h3:exp-2:attempt-1",
                    experiment="exp-2",
                    sha="b" * 64,
                ),
            ]
        ),
        encoding="utf-8",
    )

    report = validator.validate_paths([record, claim])[1]

    assert report.admitted is False
    assert any("independence_key does not match" in error for error in report.errors)
    assert any("unresolved evidence_ref 'record.md#missing'" in error for error in report.errors)


def test_input_reuse_relation_cannot_support_a_claim(tmp_path: Path) -> None:
    validator = _load_validator()
    record = tmp_path / "record.md"
    claim = tmp_path / "claim.md"
    record.write_text(
        _record(
            [
                _record_row("original", "local-h3:exp-1:attempt-1"),
                _record_row(
                    "reuse",
                    "local-h3:exp-2:attempt-1",
                    experiment="exp-2",
                    relation="INPUT_REUSE_ONLY",
                    related="original",
                    sha="b" * 64,
                ),
            ]
        ),
        encoding="utf-8",
    )
    claim.write_text(
        _claim(
            [
                _claim_row("record.md#original", "local-h3:exp-1:attempt-1"),
                _claim_row(
                    "record.md#reuse",
                    "local-h3:exp-2:attempt-1",
                    experiment="exp-2",
                    sha="b" * 64,
                ),
            ]
        ),
        encoding="utf-8",
    )

    report = validator.validate_paths([record, claim])[1]

    assert report.admitted is False
    assert any(
        "INPUT_REUSE_ONLY is not supporting or counter evidence" in error
        for error in report.errors
    )


def test_needs_identity_is_readable_but_not_admitted(tmp_path: Path) -> None:
    validator = _load_validator()
    record = tmp_path / "record.md"
    record.write_text(
        "---\n"
        "record_kind: media_experiment\n"
        "topic_id: h3-conditioning-attribution\n"
        "learning_eligibility: needs_identity\n"
        "---\n\n# Record\n\nHistorical evidence awaiting identity.\n",
        encoding="utf-8",
    )

    report = validator.validate_paths([record])[0]

    assert report.errors == ()
    assert report.learning_eligibility == "needs_identity"
    assert report.admitted is False


def test_opted_in_record_requires_complete_classification(tmp_path: Path) -> None:
    validator = _load_validator()
    record = tmp_path / "record.md"
    record.write_text(
        "---\n"
        'evidence_index_version: "1"\n'
        "---\n\n# Record\n",
        encoding="utf-8",
    )

    report = validator.validate_paths([record])[0]

    assert report.errors == (
        "classified record requires record_kind",
        "classified record requires topic_id",
        'evidence_index_version "1" requires learning_eligibility',
    )


def test_declared_unknown_identity_version_fails_closed(tmp_path: Path) -> None:
    validator = _load_validator()
    record = tmp_path / "record.md"
    claim = tmp_path / "claim.md"
    record.write_text(
        "---\n"
        "record_kind: media_experiment\n"
        "topic_id: h3-conditioning-attribution\n"
        "learning_eligibility: ineligible\n"
        'evidence_index_version: "2"\n'
        "---\n\n# Record\n",
        encoding="utf-8",
    )
    claim.write_text(
        "---\n"
        "document_kind: learning_claim\n"
        "claim_id: claim\n"
        'evidence_index_version: "2"\n'
        "---\n\n# Claim\n",
        encoding="utf-8",
    )

    reports = validator.validate_paths([record, claim])

    assert all(
        report.errors == ("unsupported evidence_index_version '2'",)
        for report in reports
    )


def test_duplicate_owned_frontmatter_and_tables_fail_closed(tmp_path: Path) -> None:
    validator = _load_validator()
    record = tmp_path / "record.md"
    claim = tmp_path / "claim.md"
    base_record = _record(
        [
            _record_row("a", "local-h3:exp-1:attempt-1"),
            _record_row(
                "b",
                "local-h3:exp-2:attempt-1",
                experiment="exp-2",
                sha="b" * 64,
            ),
        ]
    )
    evidence_section = base_record.split("## Evidence Index", 1)[1]
    record.write_text(
        base_record + "\n## Evidence Index" + evidence_section,
        encoding="utf-8",
    )
    claim.write_text(
        _claim(
            [
                _claim_row("record.md#a", "local-h3:exp-1:attempt-1"),
                _claim_row(
                    "record.md#b",
                    "local-h3:exp-2:attempt-1",
                    experiment="exp-2",
                    sha="b" * 64,
                ),
            ],
            extra_frontmatter="admission_basis: CONTROLLED_MULTI_ARM\n",
        ),
        encoding="utf-8",
    )

    reports = validator.validate_paths([record, claim])

    assert any("duplicate heading ## Evidence Index" in error for error in reports[0].errors)
    assert any("duplicate frontmatter key 'admission_basis'" in error for error in reports[1].errors)


def test_duplicate_evidence_table_columns_fail_closed(tmp_path: Path) -> None:
    validator = _load_validator()
    record = tmp_path / "record.md"
    text = _record([_record_row("a", "local-h3:exp-1:attempt-1")])
    text = text.replace(
        "| evidence_id | independence_key |",
        "| evidence_id | evidence_id | independence_key |",
        1,
    ).replace(
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        1,
    )
    record.write_text(text, encoding="utf-8")

    report = validator.validate_paths([record])[0]

    assert any("duplicate columns: evidence_id" in error for error in report.errors)


def test_same_key_cannot_change_identity_across_records(tmp_path: Path) -> None:
    validator = _load_validator()
    first = tmp_path / "first.md"
    second = tmp_path / "second.md"
    shared_key = "local-h3:exp-1:attempt-1"
    first.write_text(
        _record([_record_row("a", shared_key)]), encoding="utf-8"
    )
    second.write_text(
        _record(
            [
                _record_row(
                    "b",
                    shared_key,
                    experiment="exp-2",
                    attempt="attempt-2",
                )
            ]
        ),
        encoding="utf-8",
    )

    reports = validator.validate_paths([first, second])

    assert all(
        "inconsistent identity across records" in " ".join(report.errors)
        for report in reports
    )


def test_same_attempt_tuple_cannot_mint_two_independence_keys(
    tmp_path: Path,
) -> None:
    validator = _load_validator()
    record = tmp_path / "record.md"
    claim = tmp_path / "claim.md"
    record.write_text(
        _record(
            [
                _record_row("a", "local-h3:first-key"),
                _record_row("b", "local-h3:second-key", sha="b" * 64),
            ]
        ),
        encoding="utf-8",
    )
    claim.write_text(
        _claim(
            [
                _claim_row("record.md#a", "local-h3:first-key"),
                _claim_row(
                    "record.md#b", "local-h3:second-key", sha="b" * 64
                ),
            ]
        ),
        encoding="utf-8",
    )

    reports = validator.validate_paths([record, claim])

    assert "maps to multiple independence_key values" in " ".join(
        reports[0].errors
    )
    assert reports[1].admitted is False
    assert any(
        "referenced evidence record is invalid" in error
        for error in reports[1].errors
    )


def test_same_artifact_source_anchor_cannot_mint_two_keys(tmp_path: Path) -> None:
    validator = _load_validator()
    first = tmp_path / "first.md"
    second = tmp_path / "second.md"
    first.write_text(
        _record([_record_row("a", "local-h3:first-key")]), encoding="utf-8"
    )
    second.write_text(
        _record(
            [
                _record_row(
                    "b",
                    "local-h3:second-key",
                    experiment="exp-2",
                    attempt="attempt-2",
                )
            ]
        ),
        encoding="utf-8",
    )

    reports = validator.validate_paths([first, second])

    assert all(
        "artifact/source anchor maps to multiple independence_key values"
        in " ".join(report.errors)
        for report in reports
    )


def test_legacy_and_ineligible_records_do_not_require_identity_index(
    tmp_path: Path,
) -> None:
    validator = _load_validator()
    legacy = tmp_path / "legacy.md"
    ineligible = tmp_path / "ineligible.md"
    legacy.write_text("# Historical record\n\nNarrative only.\n", encoding="utf-8")
    ineligible.write_text(
        _record([], eligibility="ineligible", version=None), encoding="utf-8"
    )

    reports = validator.validate_paths([legacy, ineligible])

    assert all(report.errors == () for report in reports)
    assert all(report.admitted is False for report in reports)


def test_eligible_record_without_evidence_index_fails(tmp_path: Path) -> None:
    validator = _load_validator()
    record = tmp_path / "record.md"
    record.write_text(
        "---\n"
        "record_kind: media_experiment\n"
        "topic_id: h3-conditioning-attribution\n"
        "learning_eligibility: eligible\n"
        'evidence_index_version: "1"\n'
        "---\n\n# Record\n",
        encoding="utf-8",
    )

    report = validator.validate_paths([record])[0]
    assert report.admitted is False
    assert report.errors == ("eligible record requires an Evidence Index table",)


def test_cli_returns_stable_json_and_nonzero_for_invalid_input(
    tmp_path: Path,
) -> None:
    record = tmp_path / "record.md"
    record.write_text(
        _record([_record_row("broken", "", sha="bad")]), encoding="utf-8"
    )

    result = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), "--json", str(record)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload[0]["path"] == str(record)
    assert payload[0]["admitted"] is False
    assert payload[0]["errors"]
