#!/usr/bin/env python3
"""Materialize the offline M0 qualification stack without Provider effects."""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_execution_stack_materialization_source_path,
)
from ai_video.production.project import load_production_project
from ai_video.production.shot_continuity_m0_fast_validation import (
    M0FastQualificationProfile,
    load_m0_fast_qualification_execution_sources,
    validate_m0_fast_sources_against_stack,
)
from ai_video.production.shot_continuity_m0_policy import M0ValidationPolicyId
from ai_video.production.shot_continuity_m0_qualification import (
    M0QualificationProfile,
    load_m0_qualification_execution_sources,
    validate_m0_sources_against_stack,
)
from ai_video.production.shot_continuity_source_stack import (
    load_shot_continuity_source_execution_sources,
    reopen_materialized_shot_continuity_source_execution_sources,
    validate_shot_continuity_source_stack,
)
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.video_execution_stack import GenerationExecutionStackIdentity


QUALITY_PROFILE = Path(
    "workflows/qualification/minimax_h3_t8_c4_m0_candidate_v1_profile.json"
)
FAST_PROFILE = Path(
    "workflows/qualification/minimax_h3_t8_c4_m0_fast_v1_profile.json"
)


def _reopen_materialized_m0_seed_roots(
    project_root: Path,
    stack: GenerationExecutionStackIdentity,
    *,
    policy_id: M0ValidationPolicyId,
) -> tuple[str, str]:
    if stack.materialization_status != "materialized" or stack.profile_hash == "none":
        raise ValueError("M0 seed derivation roots require a materialized stack")
    source_path = project_root / canonical_execution_stack_materialization_source_path(
        "profile",
        stack.profile_hash,
    )
    try:
        snapshot = _read_regular_file_nofollow(
            source_path,
            contained_by=project_root,
        )
        if snapshot.file_sha256 != stack.profile_hash:
            raise ValueError("materialized M0 profile source hash does not match")
        envelope = json.loads(snapshot.data)
        if not isinstance(envelope, dict) or envelope.get("schema_version") != "1":
            raise ValueError("materialized M0 profile source envelope is invalid")
        profile_bytes = base64.b64decode(
            envelope["profile_bytes_base64"],
            validate=True,
        )
        profile_type = (
            M0FastQualificationProfile
            if policy_id is M0ValidationPolicyId.FAST_V1
            else M0QualificationProfile
        )
        profile = profile_type.model_validate_json(profile_bytes)
    except (OSError, KeyError, TypeError, ValueError, binascii.Error) as exc:
        raise ValueError("materialized M0 seed derivation roots could not be reopened") from exc
    return profile.initial_execution_stack_hash, profile.prepared_receipt_hash


def materialize(
    *,
    root: Path,
    artifact_root: Path,
    profile_path: Path | None,
    attempt_id: str,
    m0_policy_id: M0ValidationPolicyId,
) -> dict[str, object]:
    selected_policy = M0ValidationPolicyId(m0_policy_id)
    project_root = root.resolve(strict=True)
    source_root = artifact_root.resolve(strict=True)
    profile = profile_path or (
        FAST_PROFILE
        if selected_policy is M0ValidationPolicyId.FAST_V1
        else QUALITY_PROFILE
    )
    if not profile.is_absolute():
        profile = source_root / profile
    if selected_policy is M0ValidationPolicyId.FAST_V1:
        m0_sources = load_m0_fast_qualification_execution_sources(
            profile_path=profile,
            artifact_root=source_root,
        )
        validate_sources = validate_m0_fast_sources_against_stack
    else:
        m0_sources = load_m0_qualification_execution_sources(
            profile_path=profile,
            artifact_root=source_root,
        )
        validate_sources = validate_m0_sources_against_stack
    source_sources = load_shot_continuity_source_execution_sources(
        artifact_root=REPO_ROOT,
    )
    writer = ProductionStateCommitter(project_root)
    before_manifest = load_production_project(project_root / "project.yaml").manifest
    before = writer.reopen_p0_qualification_prepared()
    current_sources = writer.reopen_p0_qualification_source_stacks()
    if len(current_sources) > 1:
        raise ValueError("P0 qualification has more than one independent source stack")
    current_source = current_sources[0] if current_sources else None
    if current_source is not None:
        if current_source.materialization_status == "materialized":
            reopen_materialized_shot_continuity_source_execution_sources(
                project_root=project_root,
                stack=current_source,
            )
        else:
            validate_shot_continuity_source_stack(source_sources, current_source)
    current_m0 = before[1][0]
    if current_m0.materialization_status == "materialized" and (
        _reopen_materialized_m0_seed_roots(
            project_root,
            current_m0,
            policy_id=selected_policy,
        )
        != (
            m0_sources.profile.initial_execution_stack_hash,
            m0_sources.profile.prepared_receipt_hash,
        )
    ):
        raise ValueError("M0 materialized seed derivation roots cannot be replaced")
    validate_sources(
        m0_sources,
        current_m0,
        allow_materialized_source_reseal=(
            current_m0.materialization_status == "materialized"
        ),
    )
    profile = m0_sources.profile
    calibration = next(
        item for item in before[4] if item.input_kind == "calibration_fixture"
    ).payload
    if (
        calibration.get("m0_validation_policy_id", "quality-v1")
        != selected_policy.value
        or
        before[0].project.content_hash != profile.project_content_hash
        or before[0].registry.content_hash != profile.registry_content_hash
        or before[1][1].execution_stack_hash != profile.m1_execution_stack_hash
        or calibration.get("prompt_sha256") != profile.prompt_sha256
        or calibration.get("task_type") != profile.task_type
        or calibration.get("steps") != profile.steps
        or calibration.get("sampler") != profile.sampler
        or calibration.get("scheduler") != profile.scheduler
        or calibration.get("turbo_lora") is not profile.turbo_lora
        or before[1][0].materialization_status == "unmaterialized"
        and before[0].content_hash != profile.prepared_receipt_hash
    ):
        raise ValueError("M0 materialization target does not match the frozen P0 bundle")
    if before[1][1].materialization_status != "unmaterialized":
        raise ValueError("M1 must remain unmaterialized during M0 qualification")
    hybrid = next(
        item
        for item in before[1][1].components
        if item.component_id == "hybrid-artifact-candidate-v1"
    )
    if hybrid.presence != "absent" or hybrid.content_hash != "none":
        raise ValueError("M1 Hybrid artifact must remain explicit absent/none")

    materializations = (
        ((source_sources.materialization,) if current_source is not None else ())
        + (m0_sources.materialization,)
    )
    expected_hashes = (
        (
            (
                (current_source.execution_stack_hash,)
                if current_source is not None
                else ()
            )
            + (current_m0.execution_stack_hash,)
        )
        if current_m0.materialization_status == "materialized"
        and (
            current_source is None
            or current_source.materialization_status == "materialized"
        )
        else ()
    )
    committed = writer.materialize_p0_qualification(
        materializations=materializations,
        expected_materialized_stack_hashes=expected_hashes,
        expected_manifest_revision=before_manifest.manifest_revision,
        attempt_id=attempt_id,
    )
    receipt, stacks, policies, validation_set, inputs = (
        writer.reopen_p0_qualification_prepared(
            required_materialized_candidates=("m0",)
        )
    )
    validate_sources(m0_sources, stacks[0])
    materialized_sources = writer.reopen_p0_qualification_source_stacks(
        require_materialized=current_source is not None
    )
    if current_source is not None:
        validate_shot_continuity_source_stack(
            source_sources,
            materialized_sources[0],
        )
    if stacks[1] != before[1][1]:
        raise ValueError("M1 changed during M0-only materialization")
    return {
        "root": project_root.as_posix(),
        "manifest_schema_version": committed.schema_version,
        "manifest_revision": committed.manifest_revision,
        "p0_status": receipt.status,
        "p0_receipt_hash": receipt.content_hash,
        "validation_set_hash": validation_set.content_hash,
        "policy_hashes": [item.policy_hash for item in policies],
        "qualification_input_hashes": {
            item.input_kind: item.content_hash for item in inputs
        },
        "source_execution_stack_hash": (
            materialized_sources[0].execution_stack_hash
            if materialized_sources
            else None
        ),
        "source_materialization_status": (
            materialized_sources[0].materialization_status
            if materialized_sources
            else "legacy_alias"
        ),
        "m0_execution_stack_hash": stacks[0].execution_stack_hash,
        "m0_validation_policy_id": selected_policy.value,
        "m0_profile_hash": stacks[0].profile_hash,
        "m0_compiler_hash": stacks[0].compiler_hash,
        "m0_workflow_hash": stacks[0].workflow_hash,
        "m0_sealed_seed": profile.sealed_seed,
        "m1_execution_stack_hash": stacks[1].execution_stack_hash,
        "m1_materialization_status": stacks[1].materialization_status,
        "m1_hybrid_artifact": {
            "presence": hybrid.presence,
            "content_hash": hybrid.content_hash,
        },
        "claims": {
            "materialized_m0": True,
            "materialized_m1": False,
            "provider_effects": 0,
            "video_generated": False,
            "winner_selected": False,
            "active_capability_registered": False,
            "p6_pass": False,
            "final_acceptance": False,
        },
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--profile", type=Path)
    parser.add_argument(
        "--m0-policy",
        type=M0ValidationPolicyId,
        choices=tuple(M0ValidationPolicyId),
        required=True,
    )
    parser.add_argument(
        "--attempt-id",
        default="rainy-station-m0-execution-stack-materialization-v1",
    )
    return parser


def main() -> int:
    args = _parser().parse_args()
    print(
        json.dumps(
            materialize(
                root=args.root,
                artifact_root=args.artifact_root,
                profile_path=args.profile,
                attempt_id=args.attempt_id,
                m0_policy_id=args.m0_policy,
            ),
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
