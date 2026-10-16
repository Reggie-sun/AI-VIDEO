"""Authored input mappings inside the existing requirement inventory.

These declarations constrain compiler input, not Provider quality or QA verdicts.
There is no selection, timeline, media lookup, authorization or state here.
"""

from collections import defaultdict
from typing import Literal

from pydantic import Field, field_validator, model_validator

from ai_video.production.artifact_contracts import StrictModel


class ReferenceDuty(StrictModel):
    asset_id: str = Field(pattern=r"^[A-Za-z0-9._:/-]{1,256}$")
    asset_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    role: str
    purpose: Literal["identity", "appearance", "layout", "motion", "camera",
                     "whitebox", "audio", "opening", "closing"]
    scope_text: str | None = None
    canonical_owner_id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9._:/-]{1,256}$")
    independent_identity: bool = False

    @field_validator("role")
    @classmethod
    def _semantic_role(cls, value):
        # Resolve at validation time to keep the existing model import graph
        # acyclic; the canonical role vocabulary still has one owner.
        from ai_video.production.video_requirement import SemanticReferenceRole

        return SemanticReferenceRole(value).value

    @field_validator("scope_text")
    @classmethod
    def _nonblank_scope(cls, value):
        if value is not None and not value.strip():
            raise ValueError("reference scope must be nonblank")
        return value

    @model_validator(mode="after")
    def _independent_identity(self):
        if self.independent_identity and (self.purpose != "identity" or self.canonical_owner_id is None):
            raise ValueError("independent identity input requires an explicit identity owner")
        return self


class GenerationInputControl(StrictModel):
    contract_version: Literal["generation-input-control/1"] = "generation-input-control/1"
    mechanism: Literal["prompt_guidance", "reference_guidance", "first_frame", "last_frame", "native_output"]
    references: tuple[ReferenceDuty, ...] = ()

    @model_validator(mode="after")
    def _shape(self):
        if self.mechanism in {"prompt_guidance", "native_output"} and self.references:
            raise ValueError("text/output input controls cannot claim reference duties")
        if self.mechanism == "reference_guidance" and (
            not self.references or any(duty.scope_text is None for duty in self.references)
        ):
            raise ValueError("reference guidance requires exact references and explicit scope text")
        if self.mechanism in {"first_frame", "last_frame"}:
            purpose = "opening" if self.mechanism == "first_frame" else "closing"
            if len(self.references) != 1 or self.references[0].purpose != purpose:
                raise ValueError("endpoint input requires one corresponding opening/closing reference")
        return self


def reference_intent_path(path):
    """Paths whose native expression is the exact reference binder, not prose."""
    return any(path == root or path.startswith(root + ".")
               for root in ("asset_evidence", "semantic_reference_roles"))


def input_control_issues(expressions, requirement, prompt):
    """The compiler's lexical/identity check, also projected by read-only previews.

    A modern inventory must map every raw non-diagnostic objective. Historical
    inventories remain readable with no fabricated per-objective coverage.
    Distinct exact bytes are necessary, not sufficient, for independent identity
    references. A declared whitebox duty does not certify its media quality.
    """
    if not any(item.input_control is not None for item in expressions):
        return {}
    from ai_video.production._video_requirement_routing import native_binding_role
    from ai_video.production.video_requirement import SemanticReferenceRole

    issues, independent = defaultdict(set), defaultdict(list)
    evidence = {(e.role.value, e.asset_id, e.asset_sha256): e for e in requirement.asset_evidence}
    for item in expressions:
        if item.stage != "raw_generation" or item.level == "diagnostic":
            continue
        control, rid = item.input_control, item.requirement_id
        if control is None:
            issues[rid].add("UNMAPPED_CONTROL")
            continue
        if any(not text or text not in prompt for text in item.native_text):
            issues[rid].add("MISSING_NATIVE_FRAGMENT")
        for duty in control.references:
            asset = evidence.get((duty.role, duty.asset_id, duty.asset_sha256))
            if asset is None or (duty.canonical_owner_id is not None
                                and duty.canonical_owner_id != asset.canonical_owner_id):
                issues[rid].add("REFERENCE_IDENTITY_MISMATCH")
                continue
            if duty.scope_text is not None and duty.scope_text not in prompt:
                issues[rid].add("REFERENCE_SCOPE_NOT_EXPRESSED")
            native_role = native_binding_role(SemanticReferenceRole(duty.role))
            if control.mechanism in {"first_frame", "last_frame"} and native_role != control.mechanism:
                issues[rid].add("ENDPOINT_ROLE_MISMATCH")
            if duty.purpose == "whitebox" and not (
                native_role == "reference_video" and asset.mime_type.startswith("video/")
                or native_role in {"reference", "first_frame", "last_frame"}
                and asset.mime_type.startswith("image/")
            ):
                issues[rid].add("WHITEBOX_MEDIA_REQUIRED")
            if duty.purpose == "audio" and native_role != "reference_audio":
                issues[rid].add("AUDIO_REFERENCE_REQUIRED")
            if duty.independent_identity:
                if duty.role != "identity" or not asset.mime_type.startswith("image/"):
                    issues[rid].add("INDEPENDENT_IDENTITY_REFERENCE_REQUIRED")
                independent[asset.asset_sha256].append(
                    (rid, duty.asset_id, duty.role, duty.canonical_owner_id))
    for group in independent.values():
        if len({row[1:] for row in group}) > 1:
            for rid, *_ in group:
                issues[rid].add("INDEPENDENT_REFERENCE_BYTES_REUSED")
    return {rid: tuple(sorted(codes)) for rid, codes in sorted(issues.items())}
