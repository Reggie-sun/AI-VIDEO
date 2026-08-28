#!/usr/bin/env python3
"""Validate opted-in record and Learning Claim evidence identity.

The validator reads only the Markdown paths explicitly supplied by the caller.
It does not scan the corpus, refresh Agent Memory, or mutate repository state.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import re
from typing import Iterable, Sequence


_FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_SHA256 = re.compile(r"[0-9a-f]{64}")
_NO_ARTIFACT = re.compile(r"NO_ARTIFACT:[A-Z][A-Z0-9_]*")
_Q0_KEY = re.compile(r"q0:[0-9a-f]{64}")
_TYPED_TOKEN = re.compile(r"[A-Z][A-Z0-9_]*(?::[A-Z0-9_]+)*")

RECORD_KINDS = {
    "media_experiment",
    "provider_comparison",
    "architecture_implementation",
    "recovery_incident",
    "research_note",
    "session_summary",
}
LEARNING_ELIGIBILITY = {"eligible", "ineligible", "needs_identity"}
ADMISSION_BASES = {
    "TWO_INDEPENDENT_ATTEMPTS",
    "CONTROLLED_MULTI_ARM",
    "MATERIAL_EXISTING_CLAIM_UPDATE",
}
RELATION_KINDS = {
    "NEW_ATTEMPT",
    "SAME_EVIDENCE_NEW_PROOF_LAYER",
    "CONCLUSION_SUPERSEDED",
    "INPUT_REUSE_ONLY",
}
RECORD_COLUMNS = (
    "evidence_id",
    "independence_key",
    "experiment_id",
    "attempt_id",
    "arm_id",
    "artifact_sha256",
    "proof_layer",
    "verdict",
    "failure_class",
    "relation_kind",
    "related_evidence_id",
    "source",
)
CLAIM_COLUMNS = (
    "evidence_ref",
    "independence_key",
    "experiment_id",
    "attempt_id",
    "arm_id",
    "artifact_sha256",
    "proof_layer",
    "verdict",
    "source",
)


@dataclass(frozen=True)
class EvidenceRow:
    path: Path
    table: str
    number: int
    values: dict[str, str]

    @property
    def evidence_id(self) -> str:
        return self.values.get("evidence_id", "")

    @property
    def independence_key(self) -> str:
        return self.values.get("independence_key", "")


@dataclass(frozen=True)
class ValidationReport:
    path: str
    document_kind: str
    learning_eligibility: str
    admission_basis: str
    support_keys: tuple[str, ...]
    counter_keys: tuple[str, ...]
    admitted: bool
    errors: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass
class _Draft:
    path: Path
    frontmatter: dict[str, str]
    document_kind: str
    eligibility: str = ""
    admission_basis: str = ""
    record_rows: list[EvidenceRow] = field(default_factory=list)
    support_rows: list[EvidenceRow] = field(default_factory=list)
    counter_rows: list[EvidenceRow] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _unquote_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _parse_frontmatter(text: str) -> tuple[dict[str, str], list[str]]:
    match = _FRONTMATTER.match(text)
    if not match:
        return {}, []
    values: dict[str, str] = {}
    errors: list[str] = []
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        if key in values:
            errors.append(f"duplicate frontmatter key '{key}'")
            continue
        values[key] = _unquote_scalar(value)
    return values, errors


def _split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator(cells: Sequence[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def _table_after_heading(
    text: str,
    heading: str,
    required_columns: Sequence[str],
    path: Path,
    errors: list[str],
) -> list[EvidenceRow] | None:
    lines = text.splitlines()
    heading_indices = [
        index for index, line in enumerate(lines) if line.strip() == heading
    ]
    if not heading_indices:
        return None
    if len(heading_indices) > 1:
        errors.append(f"duplicate heading {heading}")
        return []
    heading_index = heading_indices[0]

    section_end = len(lines)
    for index in range(heading_index + 1, len(lines)):
        if lines[index].strip().startswith("#"):
            section_end = index
            break
    header_index: int | None = None
    for index in range(heading_index + 1, section_end):
        stripped = lines[index].strip()
        if stripped.startswith("|"):
            header_index = index
            break
    if header_index is None or header_index + 1 >= len(lines):
        return None

    table_starts = []
    for index in range(heading_index + 1, section_end - 1):
        if not lines[index].strip().startswith("|"):
            continue
        next_cells = _split_table_row(lines[index + 1])
        if _is_separator(next_cells):
            table_starts.append(index)
    if len(table_starts) > 1:
        errors.append(f"{heading} contains multiple Markdown tables")
        return []

    headers = _split_table_row(lines[header_index])
    separator = _split_table_row(lines[header_index + 1])
    if not _is_separator(separator) or len(separator) != len(headers):
        errors.append(f"{heading} has a malformed Markdown table separator")
        return []
    duplicate_headers = sorted(
        {header for header in headers if headers.count(header) > 1}
    )
    if duplicate_headers:
        errors.append(
            f"{heading} has duplicate columns: {', '.join(duplicate_headers)}"
        )
        return []
    missing = [column for column in required_columns if column not in headers]
    if missing:
        errors.append(f"{heading} missing columns: {', '.join(missing)}")
        return []

    rows: list[EvidenceRow] = []
    for index in range(header_index + 2, len(lines)):
        stripped = lines[index].strip()
        if not stripped.startswith("|"):
            break
        cells = _split_table_row(stripped)
        if len(cells) != len(headers):
            errors.append(
                f"{heading} row {len(rows) + 1} has {len(cells)} cells; "
                f"expected {len(headers)}"
            )
            continue
        rows.append(
            EvidenceRow(
                path=path,
                table=heading,
                number=len(rows) + 1,
                values=dict(zip(headers, cells)),
            )
        )
    return rows


def _validate_identity_row(
    row: EvidenceRow,
    required_columns: Sequence[str],
    errors: list[str],
) -> None:
    prefix = f"{row.table} row {row.number}"
    for column in required_columns:
        if not row.values.get(column, "").strip():
            errors.append(f"{prefix}: blank {column}")

    sha = row.values.get("artifact_sha256", "")
    if sha and not (_SHA256.fullmatch(sha) or _NO_ARTIFACT.fullmatch(sha)):
        errors.append(f"{prefix}: malformed artifact_sha256 '{sha}'")

    key = row.independence_key
    if key.startswith("q0:") and not _Q0_KEY.fullmatch(key):
        errors.append(f"{prefix}: malformed Q0 independence_key '{key}'")
    if key and (
        key.casefold().startswith(("chunk:", "path:")) or key.startswith("docs/")
    ):
        errors.append(f"{prefix}: independence_key must not derive from a chunk or path")

    proof = row.values.get("proof_layer", "")
    if proof and not _TYPED_TOKEN.fullmatch(proof):
        errors.append(f"{prefix}: malformed proof_layer '{proof}'")
    verdict = row.values.get("verdict", "")
    if verdict and not _TYPED_TOKEN.fullmatch(verdict):
        errors.append(f"{prefix}: malformed verdict '{verdict}'")
    failure_class = row.values.get("failure_class", "")
    if failure_class and not _TYPED_TOKEN.fullmatch(failure_class):
        errors.append(f"{prefix}: malformed failure_class '{failure_class}'")
    if verdict == "PASS" and failure_class and failure_class != "NONE":
        errors.append(f"{prefix}: PASS requires failure_class NONE")
    if verdict == "FAIL" and failure_class == "NONE":
        errors.append(f"{prefix}: FAIL requires a typed failure_class")


def _validate_identity_consistency(rows: Iterable[EvidenceRow], errors: list[str]) -> None:
    seen: dict[str, tuple[str, str, str]] = {}
    for row in rows:
        key = row.independence_key
        if not key:
            continue
        identity = tuple(
            row.values.get(column, "")
            for column in ("experiment_id", "attempt_id", "arm_id")
        )
        previous = seen.setdefault(key, identity)
        if previous != identity:
            errors.append(
                f"independence_key '{key}' has inconsistent experiment/attempt/arm identity"
            )


def _parse_draft(path: Path) -> _Draft:
    text = path.read_text(encoding="utf-8")
    frontmatter, frontmatter_errors = _parse_frontmatter(text)
    is_claim = frontmatter.get("document_kind") == "learning_claim"
    draft = _Draft(
        path=path,
        frontmatter=frontmatter,
        document_kind="learning_claim" if is_claim else "experience_record",
        eligibility=frontmatter.get("learning_eligibility", ""),
        admission_basis=frontmatter.get("admission_basis", ""),
        errors=frontmatter_errors,
    )

    evidence_index_version = frontmatter.get("evidence_index_version", "")
    opted_in = evidence_index_version == "1"
    if (
        "evidence_index_version" in frontmatter
        and evidence_index_version != "1"
    ):
        draft.errors.append(
            f"unsupported evidence_index_version '{evidence_index_version}'"
        )
    if not frontmatter and not is_claim:
        return draft

    if is_claim:
        if "evidence_index_version" not in frontmatter:
            return draft
        if not opted_in:
            return draft
        if draft.admission_basis not in ADMISSION_BASES:
            draft.errors.append(
                f"unsupported admission_basis '{draft.admission_basis}'"
            )
        support = _table_after_heading(
            text, "### Supporting Evidence", CLAIM_COLUMNS, path, draft.errors
        )
        counter = _table_after_heading(
            text, "### Counter Evidence", CLAIM_COLUMNS, path, draft.errors
        )
        if support is None:
            draft.errors.append("Learning Claim requires a Supporting Evidence table")
        else:
            draft.support_rows = support
        if counter is None:
            draft.errors.append("Learning Claim requires a Counter Evidence table")
        else:
            draft.counter_rows = counter
        for row in (*draft.support_rows, *draft.counter_rows):
            _validate_identity_row(row, CLAIM_COLUMNS, draft.errors)
        _validate_identity_consistency(
            (*draft.support_rows, *draft.counter_rows), draft.errors
        )
        return draft

    kind = frontmatter.get("record_kind", "")
    classified = any(
        key in frontmatter
        for key in (
            "record_kind",
            "topic_id",
            "learning_eligibility",
            "evidence_index_version",
        )
    )
    if kind and kind not in RECORD_KINDS:
        draft.errors.append(f"unsupported record_kind '{kind}'")
    if draft.eligibility and draft.eligibility not in LEARNING_ELIGIBILITY:
        draft.errors.append(
            f"unsupported learning_eligibility '{draft.eligibility}'"
        )
    if classified and not kind:
        draft.errors.append("classified record requires record_kind")
    if classified and not frontmatter.get("topic_id", ""):
        draft.errors.append("classified record requires topic_id")
    if opted_in and not draft.eligibility:
        draft.errors.append(
            'evidence_index_version "1" requires learning_eligibility'
        )
    if draft.eligibility != "eligible":
        return draft
    if not opted_in:
        draft.errors.append('eligible record requires evidence_index_version "1"')
        return draft
    rows = _table_after_heading(
        text, "## Evidence Index", RECORD_COLUMNS, path, draft.errors
    )
    if rows is None:
        draft.errors.append("eligible record requires an Evidence Index table")
        return draft
    draft.record_rows = rows
    if not rows:
        draft.errors.append("eligible record requires at least one evidence row")
    evidence_ids: set[str] = set()
    for row in rows:
        _validate_identity_row(row, RECORD_COLUMNS, draft.errors)
        evidence_id = row.evidence_id
        if evidence_id in evidence_ids:
            draft.errors.append(f"duplicate evidence_id '{evidence_id}'")
        elif evidence_id:
            evidence_ids.add(evidence_id)
        relation = row.values.get("relation_kind", "")
        if relation and relation not in RELATION_KINDS:
            draft.errors.append(
                f"{row.table} row {row.number}: unsupported relation_kind '{relation}'"
            )
        related = row.values.get("related_evidence_id", "")
        if relation == "NEW_ATTEMPT" and related not in {"", "NONE"}:
            draft.errors.append(
                f"{row.table} row {row.number}: NEW_ATTEMPT requires related_evidence_id NONE"
            )
        if relation != "NEW_ATTEMPT" and related == "NONE":
            draft.errors.append(
                f"{row.table} row {row.number}: {relation} requires related evidence"
            )
    _validate_identity_consistency(rows, draft.errors)
    return draft


def _record_reference_index(drafts: Sequence[_Draft]) -> dict[str, EvidenceRow]:
    references: dict[str, EvidenceRow] = {}
    ambiguous: set[str] = set()
    for draft in drafts:
        for row in draft.record_rows:
            path_references = {
                f"{draft.path}#{row.evidence_id}",
                f"{draft.path.as_posix()}#{row.evidence_id}",
                f"{draft.path.name}#{row.evidence_id}",
            }
            try:
                relative = draft.path.resolve().relative_to(Path.cwd().resolve())
            except ValueError:
                pass
            else:
                path_references.add(f"{relative.as_posix()}#{row.evidence_id}")
            for reference in path_references:
                if reference in references and references[reference] is not row:
                    ambiguous.add(reference)
                else:
                    references[reference] = row
    for reference in ambiguous:
        references.pop(reference, None)
    return references


def _validate_relations(drafts: Sequence[_Draft]) -> None:
    references = _record_reference_index(drafts)
    for draft in drafts:
        local = {row.evidence_id: row for row in draft.record_rows}
        for row in draft.record_rows:
            relation = row.values.get("relation_kind", "")
            related = row.values.get("related_evidence_id", "")
            if not related or related == "NONE" or relation == "NEW_ATTEMPT":
                continue
            target = local.get(related) or references.get(related)
            if target is None:
                draft.errors.append(
                    f"{row.table} row {row.number}: unresolved related_evidence_id '{related}'"
                )
                continue
            if target is row:
                draft.errors.append(
                    f"{row.table} row {row.number}: relation must not target itself"
                )
                continue
            if relation == "SAME_EVIDENCE_NEW_PROOF_LAYER":
                if target.independence_key != row.independence_key:
                    draft.errors.append(
                        f"{row.table} row {row.number}: SAME_EVIDENCE_NEW_PROOF_LAYER requires the same independence_key"
                    )
                if target.values.get("proof_layer") == row.values.get("proof_layer"):
                    draft.errors.append(
                        f"{row.table} row {row.number}: SAME_EVIDENCE_NEW_PROOF_LAYER requires a different proof_layer"
                    )
                if target.values.get("artifact_sha256") != row.values.get(
                    "artifact_sha256"
                ):
                    draft.errors.append(
                        f"{row.table} row {row.number}: SAME_EVIDENCE_NEW_PROOF_LAYER requires the same artifact_sha256"
                    )
            if (
                relation == "INPUT_REUSE_ONLY"
                and target.independence_key == row.independence_key
            ):
                draft.errors.append(
                    f"{row.table} row {row.number}: INPUT_REUSE_ONLY requires a distinct independence_key"
                )


def _validate_global_record_identity(drafts: Sequence[_Draft]) -> None:
    seen: dict[str, tuple[tuple[str, str, str], _Draft]] = {}
    keys_by_identity: dict[tuple[str, str, str], tuple[str, _Draft]] = {}
    keys_by_anchor: dict[tuple[str, str], tuple[str, _Draft]] = {}
    for draft in drafts:
        for row in draft.record_rows:
            key = row.independence_key
            if not key:
                continue
            identity = tuple(
                row.values.get(column, "")
                for column in ("experiment_id", "attempt_id", "arm_id")
            )
            previous = seen.setdefault(key, (identity, draft))
            if previous[0] != identity:
                message = (
                    f"independence_key '{key}' has inconsistent identity across records"
                )
                if message not in draft.errors:
                    draft.errors.append(message)
                if message not in previous[1].errors:
                    previous[1].errors.append(message)
            previous_key = keys_by_identity.setdefault(identity, (key, draft))
            if previous_key[0] != key:
                message = (
                    "experiment/attempt/arm identity maps to multiple "
                    f"independence_key values: '{previous_key[0]}' and '{key}'"
                )
                if message not in draft.errors:
                    draft.errors.append(message)
                if message not in previous_key[1].errors:
                    previous_key[1].errors.append(message)
            anchor = (
                row.values.get("artifact_sha256", ""),
                row.values.get("source", ""),
            )
            previous_anchor = keys_by_anchor.setdefault(anchor, (key, draft))
            if previous_anchor[0] != key:
                message = (
                    "artifact/source anchor maps to multiple independence_key "
                    f"values: '{previous_anchor[0]}' and '{key}'"
                )
                if message not in draft.errors:
                    draft.errors.append(message)
                if message not in previous_anchor[1].errors:
                    previous_anchor[1].errors.append(message)


def _validate_claim_references(drafts: Sequence[_Draft]) -> None:
    references = _record_reference_index(drafts)
    drafts_by_path = {draft.path: draft for draft in drafts}
    compared_columns = (
        "independence_key",
        "experiment_id",
        "attempt_id",
        "arm_id",
        "artifact_sha256",
        "proof_layer",
        "verdict",
        "source",
    )
    for draft in drafts:
        for row in (*draft.support_rows, *draft.counter_rows):
            reference = row.values.get("evidence_ref", "")
            target = references.get(reference)
            if target is None:
                draft.errors.append(
                    f"{row.table} row {row.number}: unresolved evidence_ref '{reference}'"
                )
                continue
            target_draft = drafts_by_path.get(target.path)
            if target_draft is not None and target_draft.errors:
                draft.errors.append(
                    f"{row.table} row {row.number}: referenced evidence record is invalid"
                )
            for column in compared_columns:
                if row.values.get(column, "") != target.values.get(column, ""):
                    draft.errors.append(
                        f"{row.table} row {row.number}: {column} does not match referenced evidence"
                    )
            if target.values.get("relation_kind") == "INPUT_REUSE_ONLY":
                draft.errors.append(
                    f"{row.table} row {row.number}: INPUT_REUSE_ONLY is not supporting or counter evidence"
                )
        if draft.admission_basis == "MATERIAL_EXISTING_CLAIM_UPDATE":
            previous = draft.frontmatter.get(
                "material_update_previous_evidence", ""
            )
            if previous:
                if previous not in references:
                    draft.errors.append(
                        "MATERIAL_EXISTING_CLAIM_UPDATE previous evidence is unresolved"
                    )
                current_refs = {
                    row.values.get("evidence_ref", "")
                    for row in (*draft.support_rows, *draft.counter_rows)
                }
                if previous in current_refs:
                    draft.errors.append(
                        "MATERIAL_EXISTING_CLAIM_UPDATE previous evidence must differ from new evidence"
                    )


def _unique_keys(rows: Iterable[EvidenceRow]) -> tuple[str, ...]:
    return tuple(sorted({row.independence_key for row in rows if row.independence_key}))


def _validate_admission(draft: _Draft) -> tuple[tuple[str, ...], tuple[str, ...]]:
    support_keys = _unique_keys(draft.support_rows)
    counter_keys = _unique_keys(draft.counter_rows)
    if draft.document_kind != "learning_claim" or not draft.admission_basis:
        return support_keys, counter_keys

    if draft.admission_basis == "TWO_INDEPENDENT_ATTEMPTS":
        if len(support_keys) < 2:
            draft.errors.append(
                "TWO_INDEPENDENT_ATTEMPTS requires at least two distinct supporting independence_key values"
            )
    elif draft.admission_basis == "CONTROLLED_MULTI_ARM":
        experiments = {
            row.values.get("experiment_id", "") for row in draft.support_rows
        }
        arms = {
            row.values.get("arm_id", "")
            for row in draft.support_rows
            if row.values.get("arm_id", "") != "N/A"
        }
        if len(experiments) != 1:
            draft.errors.append(
                "CONTROLLED_MULTI_ARM requires one shared experiment_id"
            )
        if len(arms) < 2 or len(support_keys) < 2:
            draft.errors.append(
                "CONTROLLED_MULTI_ARM requires at least two distinct arms and independence_key values"
            )
    elif draft.admission_basis == "MATERIAL_EXISTING_CLAIM_UPDATE":
        for field_name in (
            "material_update_target_claim",
            "material_update_previous_evidence",
            "material_update_delta",
        ):
            if not draft.frontmatter.get(field_name, ""):
                draft.errors.append(
                    f"MATERIAL_EXISTING_CLAIM_UPDATE requires {field_name}"
                )
        if not support_keys and not counter_keys:
            draft.errors.append(
                "MATERIAL_EXISTING_CLAIM_UPDATE requires new supporting or counter evidence"
            )
    return support_keys, counter_keys


def validate_paths(paths: Sequence[Path | str]) -> list[ValidationReport]:
    """Validate explicit Markdown paths and return stable per-document reports."""
    drafts: list[_Draft] = []
    for raw_path in paths:
        path = Path(raw_path)
        try:
            drafts.append(_parse_draft(path))
        except (OSError, UnicodeDecodeError) as exc:
            drafts.append(
                _Draft(
                    path=path,
                    frontmatter={},
                    document_kind="unreadable",
                    errors=[f"cannot read document: {exc}"],
                )
            )
    _validate_relations(drafts)
    _validate_global_record_identity(drafts)
    _validate_claim_references(drafts)

    reports: list[ValidationReport] = []
    for draft in drafts:
        support_keys, counter_keys = _validate_admission(draft)
        admitted = (
            draft.document_kind == "learning_claim"
            and bool(draft.admission_basis)
            and not draft.errors
        )
        reports.append(
            ValidationReport(
                path=str(draft.path),
                document_kind=draft.document_kind,
                learning_eligibility=draft.eligibility,
                admission_basis=draft.admission_basis,
                support_keys=support_keys,
                counter_keys=counter_keys,
                admitted=admitted,
                errors=tuple(draft.errors),
            )
        )
    return reports


def _format_text(reports: Sequence[ValidationReport]) -> str:
    lines: list[str] = []
    for report in reports:
        lines.append(f"{report.path}: {'PASS' if not report.errors else 'FAIL'}")
        lines.append(f"  admitted: {str(report.admitted).lower()}")
        if report.support_keys:
            lines.append(f"  support_keys: {', '.join(report.support_keys)}")
        if report.counter_keys:
            lines.append(f"  counter_keys: {', '.join(report.counter_keys)}")
        for error in report.errors:
            lines.append(f"  error: {error}")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate explicit AI-VIDEO evidence identity Markdown paths."
    )
    parser.add_argument("--json", action="store_true", help="emit JSON reports")
    parser.add_argument("paths", nargs="+", type=Path, help="Markdown paths to read")
    args = parser.parse_args(argv)

    reports = validate_paths(args.paths)
    if args.json:
        print(
            json.dumps(
                [report.to_dict() for report in reports],
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(_format_text(reports))
    return 1 if any(report.errors for report in reports) else 0


if __name__ == "__main__":
    raise SystemExit(main())
