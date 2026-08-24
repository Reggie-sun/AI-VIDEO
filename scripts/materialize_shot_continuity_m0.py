#!/usr/bin/env python3
"""Materialize the offline M0 qualification stack without Provider effects."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from ai_video.production.project import load_production_project
from ai_video.production.shot_continuity_m0_qualification import (
    load_m0_qualification_execution_sources,
    validate_m0_sources_against_stack,
)
from ai_video.production.state_commit import ProductionStateCommitter


DEFAULT_PROFILE = Path(
    "workflows/qualification/minimax_h3_t8_c4_m0_candidate_v1_profile.json"
)


def materialize(
    *,
    root: Path,
    artifact_root: Path,
    profile_path: Path,
    attempt_id: str,
) -> dict[str, object]:
    project_root = root.resolve(strict=True)
    source_root = artifact_root.resolve(strict=True)
    profile = profile_path
    if not profile.is_absolute():
        profile = source_root / profile
    sources = load_m0_qualification_execution_sources(
        profile_path=profile,
        artifact_root=source_root,
    )
    writer = ProductionStateCommitter(project_root)
    before_manifest = load_production_project(project_root / "project.yaml").manifest
    before = writer.reopen_p0_qualification_prepared()
    current_m0 = before[1][0]
    validate_m0_sources_against_stack(
        sources,
        current_m0,
        allow_materialized_source_reseal=(
            current_m0.materialization_status == "materialized"
        ),
    )
    profile = sources.profile
    calibration = next(
        item for item in before[4] if item.input_kind == "calibration_fixture"
    ).payload
    if (
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

    committed = writer.materialize_p0_qualification(
        materializations=(sources.materialization,),
        expected_materialized_stack_hashes=(
            (current_m0.execution_stack_hash,)
            if current_m0.materialization_status == "materialized"
            else ()
        ),
        expected_manifest_revision=before_manifest.manifest_revision,
        attempt_id=attempt_id,
    )
    receipt, stacks, policies, validation_set, inputs = (
        writer.reopen_p0_qualification_prepared(
            required_materialized_candidates=("m0",)
        )
    )
    validate_m0_sources_against_stack(sources, stacks[0])
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
        "m0_execution_stack_hash": stacks[0].execution_stack_hash,
        "m0_profile_hash": stacks[0].profile_hash,
        "m0_compiler_hash": stacks[0].compiler_hash,
        "m0_workflow_hash": stacks[0].workflow_hash,
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
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
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
            ),
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
