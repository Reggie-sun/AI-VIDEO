#!/usr/bin/env python3
"""Validate ecommerce-ad-workflow input and package contracts offline."""

from __future__ import annotations

import argparse
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Literal

from pydantic import ValidationError


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from contract_gates import validate_input_contract, validate_package_contract
from contract_models import (
    EcommerceAdInput,
    EcommerceAdProductionPackage,
    StrictModel,
)


SKILL_ROOT = SCRIPT_DIR.parent
SCHEMA_PATHS = {
    "input": SKILL_ROOT / "schemas" / "ecommerce-ad-input.schema.json",
    "package": SKILL_ROOT
    / "schemas"
    / "ecommerce-ad-production-package.schema.json",
}
_MODELS = {
    "input": EcommerceAdInput,
    "package": EcommerceAdProductionPackage,
}
_GATE_VALIDATORS = {
    "input": validate_input_contract,
    "package": validate_package_contract,
}
_DIAGNOSTIC_CODE = re.compile(r"^[a-z][a-z0-9_]*$")
_AI_COMIC_FIELDS = frozenset(
    {
        "ai_comic_package",
        "character_bible",
        "cliffhanger",
        "episode",
        "episode_context",
        "episode_mode",
        "serial_arc",
        "serial_thread",
    }
)
_RUNTIME_EXECUTION_FIELDS = frozenset(
    {
        "activation",
        "active_output",
        "credential",
        "final_acceptance",
        "manifest_revision",
        "manifest_state",
        "p6_pass",
        "permit",
        "provider",
        "provider_name",
        "provider_profile",
        "provider_task_id",
        "render_path",
        "resolved_timeline",
        "task_id",
        "timeline_frames",
        "timeline_samples",
    }
)
_REQUIRED_VARIANT_CONSTANTS = frozenset(
    {
        "claim_ledger",
        "cta_destination",
        "delivery_intent",
        "objective",
        "platform_constraints",
        "product_identity",
        "product_truth",
        "rights",
        "unchanged_strategy_fields",
    }
)
_ROOT_DIAGNOSTIC_PATHS = {
    "ad_qc_blocked": "$.ad_qc_report",
    "audio_coverage_gap": "$.audio_plan",
    "blocked_capability_gap": "$.product_presentation",
    "claim_lineage": "$.claim_ledger",
    "commercial_copy_roles": "$.copy_graphics_plan",
    "cta_brand_closure": "$.cta",
    "dialogue_binding": "$.audio_plan.events",
    "hook_first_second": "$.hook_contract",
    "hook_contract": "$.hook_contract",
    "mechanical_pacing": "$.shot_intents",
    "mechanical_typography": "$.copy_graphics_plan",
    "medical_claim_forbidden": "$.product_truth.allowed_claims",
    "product_name_missing": "$.product_truth.product_name",
    "product_presentation_roles": "$.product_presentation",
    "rights_not_confirmed": "$.product_truth",
    "runtime_handoff": "$.runtime_handoff",
    "source_audio_policy": "$.audio_plan.source_audio_policies",
    "traceability": "$.ad_beats",
    "variant_isolation": "$.creative_variant_matrix",
}


@dataclass(frozen=True, order=True)
class Diagnostic:
    path: str
    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


class ContractFailure(ValueError):
    def __init__(self, diagnostics: Iterable[Diagnostic]) -> None:
        self.diagnostics = tuple(sorted(diagnostics))
        super().__init__("contract validation failed")


class SchemaParityFailure(RuntimeError):
    pass


def _canonical_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def schema_text(kind: Literal["input", "package"]) -> str:
    return (
        json.dumps(
            _MODELS[kind].model_json_schema(mode="validation"),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def validate_checked_in_schema(kind: Literal["input", "package"]) -> None:
    path = SCHEMA_PATHS[kind]
    try:
        checked_in = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SchemaParityFailure(f"checked-in {kind} schema is unavailable") from exc
    if checked_in != schema_text(kind):
        raise SchemaParityFailure(
            f"checked-in {kind} schema does not match the Pydantic contract"
        )


def _iter_mapping_items(
    value: object, path: str = "$"
) -> Iterable[tuple[str, object, str]]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            yield key_text, child, child_path
            yield from _iter_mapping_items(child, child_path)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            yield from _iter_mapping_items(child, f"{path}[{index}]")


def _preflight_document(
    kind: Literal["input", "package"], payload: Mapping[str, object]
) -> None:
    diagnostics: list[Diagnostic] = []
    for key, _value, path in _iter_mapping_items(payload):
        if key in _AI_COMIC_FIELDS:
            diagnostics.append(
                Diagnostic(
                    path=path,
                    code="forbidden_field",
                    message="field is forbidden by the ecommerce workflow boundary",
                )
            )
        if kind == "package" and key in _RUNTIME_EXECUTION_FIELDS:
            diagnostics.append(
                Diagnostic(
                    path=path,
                    code="forbidden_runtime_field",
                    message="Runtime execution and acceptance fields are forbidden",
                )
            )
    if kind == "package":
        handoff = payload.get("runtime_handoff")
        if isinstance(handoff, Mapping) and handoff.get("delivery_intent") != "video":
            diagnostics.append(
                Diagnostic(
                    path="$.runtime_handoff.delivery_intent",
                    code="delivery_intent",
                    message="package delivery intent must remain video",
                )
            )
        matrix = payload.get("creative_variant_matrix")
        variants = matrix.get("variants") if isinstance(matrix, Mapping) else None
        if isinstance(variants, Sequence) and not isinstance(
            variants, (str, bytes, bytearray)
        ):
            for index, item in enumerate(variants):
                if not isinstance(item, Mapping):
                    continue
                changed = item.get("changed_variable")
                held = item.get("held_constants")
                held_is_sequence = isinstance(held, Sequence) and not isinstance(
                    held, (str, bytes, bytearray)
                )
                if (
                    not isinstance(changed, str)
                    or not held_is_sequence
                    or set(held) != _REQUIRED_VARIANT_CONSTANTS
                ):
                    diagnostics.append(
                        Diagnostic(
                            path=f"$.creative_variant_matrix.variants[{index}]",
                            code="variant_isolation",
                            message="variant must change exactly one variable and hold complete truth constants",
                        )
                    )
        package_id = payload.get("package_id")
        identity_payload = dict(payload)
        identity_payload.pop("package_id", None)
        if package_id != _canonical_sha256(identity_payload):
            diagnostics.append(
                Diagnostic(
                    path="$.package_id",
                    code="package_identity",
                    message="package_id must bind canonical package bytes excluding package_id",
                )
            )
    if diagnostics:
        raise ContractFailure(diagnostics)


def _format_location(location: Sequence[object]) -> str:
    path = "$"
    for part in location:
        if isinstance(part, int):
            path += f"[{part}]"
        else:
            path += f".{part}"
    return path


def _split_coded_message(message: str) -> tuple[str, str]:
    if message.startswith("Value error, "):
        message = message.removeprefix("Value error, ")
    if ":" in message:
        candidate, detail = message.split(":", 1)
        if _DIAGNOSTIC_CODE.fullmatch(candidate):
            return candidate, detail.strip()
    return "contract_invalid", message


def _diagnostics_from_validation_error(error: ValidationError) -> tuple[Diagnostic, ...]:
    diagnostics: list[Diagnostic] = []
    for item in error.errors(include_input=False, include_url=False):
        code, message = _split_coded_message(
            str(item.get("msg", "contract validation failed"))
        )
        location = _format_location(item.get("loc", ()))
        if location == "$":
            location = _ROOT_DIAGNOSTIC_PATHS.get(code, location)
        diagnostics.append(Diagnostic(path=location, code=code, message=message))
    return tuple(sorted(diagnostics))


def _diagnostic_from_gate_error(error: ValueError) -> Diagnostic:
    code, message = _split_coded_message(str(error))
    return Diagnostic(
        path=_ROOT_DIAGNOSTIC_PATHS.get(code, "$"),
        code=code,
        message=message,
    )


def validate_file(
    kind: Literal["input", "package"], path: Path
) -> StrictModel:
    validate_checked_in_schema(kind)
    if not path.is_file() or path.is_symlink():
        raise ContractFailure(
            [
                Diagnostic(
                    path="$",
                    code="input_file_invalid",
                    message="file must be an existing regular non-symlink JSON file",
                )
            ]
        )
    try:
        raw_text = path.read_text(encoding="utf-8")
        payload = json.loads(raw_text)
    except (json.JSONDecodeError, UnicodeError):
        raise ContractFailure(
            [
                Diagnostic(
                    path="$",
                    code="malformed_json",
                    message="file is not valid JSON",
                )
            ]
        ) from None
    except OSError as exc:
        raise ContractFailure(
            [
                Diagnostic(
                    path="$",
                    code="input_file_invalid",
                    message="file could not be read",
                )
            ]
        ) from exc
    if not isinstance(payload, Mapping):
        raise ContractFailure(
            [
                Diagnostic(
                    path="$",
                    code="contract_invalid",
                    message="document root must be a JSON object",
                )
            ]
        )
    _preflight_document(kind, payload)
    try:
        document = _MODELS[kind].model_validate_json(raw_text)
    except ValidationError as exc:
        raise ContractFailure(_diagnostics_from_validation_error(exc)) from None
    try:
        _GATE_VALIDATORS[kind](document)
    except ValueError as exc:
        raise ContractFailure([_diagnostic_from_gate_error(exc)]) from None
    return document


def _emit(
    *,
    kind: str,
    status: Literal["valid", "invalid", "error"],
    diagnostics: Iterable[Diagnostic],
) -> None:
    document = {
        "diagnostics": [item.to_dict() for item in sorted(diagnostics)],
        "kind": kind,
        "status": status,
    }
    sys.stdout.write(
        json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        + "\n"
    )


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate ecommerce advertising authoring contracts."
    )
    parser.add_argument("--kind", choices=tuple(_MODELS), required=True)
    parser.add_argument("--file", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        validate_file(args.kind, args.file)
    except ContractFailure as exc:
        _emit(kind=args.kind, status="invalid", diagnostics=exc.diagnostics)
        return 2
    except Exception:
        _emit(
            kind=args.kind,
            status="error",
            diagnostics=(
                Diagnostic(
                    path="$",
                    code="validator_internal_failure",
                    message="validator could not complete",
                ),
            ),
        )
        return 3
    _emit(kind=args.kind, status="valid", diagnostics=())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
