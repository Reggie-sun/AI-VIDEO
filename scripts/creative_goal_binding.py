"""Read-only development intent joins; no media or Production state effects."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import importlib.util
import json
from pathlib import Path
from typing import Literal

from pydantic import Field

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.final_output_contracts import FinalOutputContract
from ai_video.production.paths import _read_regular_file_nofollow


class GoalBindingError(ValueError):
    """Stable diagnostics deliberately omit input text and parser payloads."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class FileReference(StrictModel):
    path: str = Field(min_length=1, strict=True)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$", strict=True)


class IntentBinding(StrictModel):
    intent_item_id: str = Field(min_length=1, strict=True)
    constraint_ids: tuple[str, ...]
    unit_ids: tuple[str, ...]
    requirement_ids: tuple[str, ...]


class GoalBinding(StrictModel):
    schema_version: Literal["creative-goal-binding/1"]
    authority: Literal["development_only"]
    creative_input: FileReference
    coverage: FileReference
    final_output_contract: FileReference
    bindings: tuple[IntentBinding, ...]


@dataclass(frozen=True)
class BoundFile:
    path: str
    data: bytes
    sha256: str


@dataclass(frozen=True)
class VerifiedGoalBinding:
    """Retained exact bytes allow packet snapshots without a second file read."""

    files: tuple[BoundFile, ...]
    binding: dict
    coverage: dict
    contract: FinalOutputContract
    diagnostics: tuple = ()

    @property
    def binding_sha256(self):
        return self.files[0].sha256

    def identity(self):
        return {"path": self.files[0].path, "sha256": self.binding_sha256,
            **{name: self.binding[name] for name in
                ("creative_input", "coverage", "final_output_contract")}}


def _read(root, relative):
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts or path == Path("."):
        raise GoalBindingError("invalid_reference")
    try:
        snapshot = _read_regular_file_nofollow(root / path, contained_by=root)
    except (ValueError, OSError):
        raise GoalBindingError("invalid_reference") from None
    return BoundFile(relative, snapshot.data, snapshot.file_sha256)


def _text(data):
    try:
        return data.decode("utf-8")
    except UnicodeError:
        raise GoalBindingError("invalid_encoding") from None


def _json(data, code):
    def unique_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result

    def reject_constant(value):
        raise ValueError("non-finite number")

    try:
        value = json.loads(_text(data), object_pairs_hook=unique_keys, parse_constant=reject_constant)
        if not isinstance(value, dict):
            raise ValueError("object required")
        return value
    except GoalBindingError:
        raise
    except ValueError:
        raise GoalBindingError(code) from None


def _director_validator():
    path = Path(__file__).resolve().parents[1] / ".agents/skills/open-video/scripts/validate_director_coverage.py"
    spec = importlib.util.spec_from_file_location("creative_goal_director_validator", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate_director_coverage


def _validate_join(envelope, coverage, contract):
    intents = {item["intent_item_id"]: item for item in coverage["intent_items"]}
    users = {name for name, item in intents.items() if item["origin"] == "explicit_user"}
    if not intents:
        raise GoalBindingError("unbound_user_intent")
    constraints = {item["constraint_id"]: item["scope"] for item in coverage["request"]["creative_constraints"]}
    units = {unit["unit_id"]: set(unit["constraint_ids"]) for unit in coverage["coverage_units"]}
    requirements = {rule.requirement_id for rule in contract.requirements}
    seen = set()
    for row in envelope.bindings:
        if row.intent_item_id in seen:
            raise GoalBindingError("duplicate_binding")
        seen.add(row.intent_item_id)
        if row.intent_item_id not in intents:
            raise GoalBindingError("unknown_intent")
        for ids, known, code in ((row.constraint_ids, constraints, "unknown_constraint"),
                (row.unit_ids, units, "unknown_unit"), (row.requirement_ids, requirements, "unknown_requirement")):
            if any(not isinstance(name, str) or not name.strip() for name in ids):
                raise GoalBindingError("invalid_binding")
            if len(ids) != len(set(ids)):
                raise GoalBindingError("duplicate_binding")
            if set(ids) - set(known):
                raise GoalBindingError(code)
        if not row.constraint_ids or any(constraints[name] not in {"global", "beat_specific"}
                for name in row.constraint_ids):
            raise GoalBindingError("unresolved_intent_scope")
        if not row.requirement_ids:
            raise GoalBindingError("unbound_user_intent")
        required_units = set()
        for name in row.constraint_ids:
            if constraints[name] == "beat_specific":
                referenced = {unit for unit, ids in units.items() if name in ids}
                if not referenced:
                    raise GoalBindingError("unresolved_intent_scope")
                required_units.update(referenced)
        if not required_units <= set(row.unit_ids):
            raise GoalBindingError("uncovered_intent_unit")
    if not users <= seen:
        raise GoalBindingError("unbound_user_intent")


def load_goal_binding(path: Path) -> VerifiedGoalBinding:
    path = Path(path).absolute()
    bound = _read(path.parent, path.name)
    payload = _json(bound.data, "invalid_binding")
    if payload.get("schema_version") != "creative-goal-binding/1":
        raise GoalBindingError("unsupported_binding_version")
    try:
        envelope = GoalBinding.model_validate(payload)
    except ValueError:
        raise GoalBindingError("invalid_binding") from None
    files = [bound]
    for name in ("creative_input", "coverage", "final_output_contract"):
        reference = getattr(envelope, name)
        snapshot = _read(path.parent, reference.path)
        if snapshot.sha256 != reference.sha256:
            raise GoalBindingError("source_identity_mismatch" if name == "creative_input" else "stale_binding")
        files.append(snapshot)
    if len({Path(item.path) for item in files}) != len(files):
        raise GoalBindingError("invalid_reference")
    source = _text(files[1].data)
    coverage = _json(files[2].data, "invalid_coverage")
    if coverage.get("schema_version") != "4":
        raise GoalBindingError("unsupported_coverage_version")
    if not isinstance(coverage.get("request"), dict) or coverage["request"].get("creative_input_evidence") != source:
        raise GoalBindingError("source_identity_mismatch")
    try:
        _director_validator()(coverage)
    except ValueError:
        raise GoalBindingError("invalid_coverage") from None
    contract_payload = _json(files[3].data, "invalid_contract")
    try:
        contract = FinalOutputContract.model_validate(contract_payload)
    except ValueError:
        raise GoalBindingError("invalid_contract") from None
    _validate_join(envelope, coverage, contract)
    return VerifiedGoalBinding(tuple(files), payload, coverage, contract)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binding", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        verified = load_goal_binding(args.binding)
    except GoalBindingError as exc:
        print(json.dumps({"authority": "development_only", "status": "invalid",
            "diagnostics": [{"code": exc.code}]}))
        return 2
    print(json.dumps({"authority": "development_only", "status": "verified",
        "identity": verified.identity(), "contract_hash": verified.contract.contract_hash,
        "diagnostics": []}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
