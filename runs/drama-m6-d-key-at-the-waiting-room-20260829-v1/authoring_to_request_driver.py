from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from ai_video.planning import (
    VideoPlanner,
    VideoPlanningRequest,
    require_current_video_plan,
)
from ai_video.production._h3_prompt import H3PromptCompilation, compile_h3_prompt
from ai_video.production.project import load_production_project
from ai_video.production.video_requirement import (
    GenerationIntent,
    ProviderNeutralGenerationIntentProjection,
    ProviderNeutralVideoRequirement,
    VerifiedGenerationRequirementProjection,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = RUN_ROOT / "production-project"
MATERIALIZATION_PATH = RUN_ROOT / "evidence/drama-canonical-materialization.json"
GRAPH_EVIDENCE_PATH = RUN_ROOT / "evidence/drama-pre-generation-graph.json"
OVERLAY_PATH = Path(
    "docs/superpowers/artifacts/drama/b-d0/execution-intent/"
    "key-at-the-waiting-room-shot-01-v1.proposed.json"
)
ACCEPTANCE_PATH = Path(
    "docs/superpowers/artifacts/drama/b-d0/execution-intent/"
    "key-at-the-waiting-room-shot-01-v1.accepted.json"
)
PACKAGE_ACCEPTANCE_PATH = Path(
    "docs/superpowers/artifacts/drama/b-d0/authoring-package/"
    "key-at-the-waiting-room-v3.accepted.json"
)
EVIDENCE_PATH = RUN_ROOT / "evidence/drama-shot-01-authoring-to-request.json"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _json_bytes(value: object) -> bytes:
    return (_canonical_json(value) + "\n").encode("utf-8")


def _git_blob(commit: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=REPO_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout


def _git_blob_oid(commit: str, path: str) -> str:
    return subprocess.run(
        ["git", "rev-parse", f"{commit}:{path}"],
        cwd=REPO_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ).stdout.strip()


def _tree_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): _sha256(path.read_bytes())
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _load_overlay() -> tuple[dict[str, object], dict[str, object]]:
    if not (REPO_ROOT / ACCEPTANCE_PATH).exists():
        payload_bytes = (REPO_ROOT / OVERLAY_PATH).read_bytes()
        payload = json.loads(payload_bytes)
        return payload, {
            "authority_status": "PROPOSED_PENDING_DELEGATED_ACCEPTANCE",
            "payload_path": OVERLAY_PATH.as_posix(),
            "payload_sha256": _sha256(payload_bytes),
            "acceptance_path": None,
            "acceptance_sha256": None,
        }

    acceptance_bytes = (REPO_ROOT / ACCEPTANCE_PATH).read_bytes()
    acceptance = json.loads(acceptance_bytes)
    expected = {
        "schema_version": "drama-shot-execution-intent-overlay-acceptance/1",
        "record_kind": "drama_shot_execution_intent_overlay_acceptance",
        "overlay_id": "drama.execution-intent.key-at-the-waiting-room.shot-01",
        "overlay_version": 1,
        "status": "accepted",
        "domain_id": "drama",
        "lane_id": "M6-D",
    }
    if any(acceptance.get(key) != value for key, value in expected.items()):
        raise RuntimeError("execution-intent acceptance envelope identity is not canonical")
    accepted = acceptance["accepted_overlay_payload"]
    payload_bytes = _git_blob(accepted["commit"], accepted["path"])
    if (
        len(payload_bytes) != accepted["byte_size"]
        or _sha256(payload_bytes) != accepted["accepted_record_sha256"]
        or _git_blob_oid(accepted["commit"], accepted["path"])
        != accepted["git_blob_oid"]
    ):
        raise RuntimeError("accepted execution-intent overlay bytes do not match")
    payload = json.loads(payload_bytes)
    return payload, {
        "authority_status": "ACCEPTED_AND_SEALED",
        "payload_path": accepted["path"],
        "payload_commit": accepted["commit"],
        "payload_git_blob_oid": accepted["git_blob_oid"],
        "payload_byte_size": accepted["byte_size"],
        "payload_sha256": accepted["accepted_record_sha256"],
        "acceptance_path": ACCEPTANCE_PATH.as_posix(),
        "acceptance_sha256": _sha256(acceptance_bytes),
    }


def _assert_source_binding(
    overlay: dict[str, object], materialization_bytes: bytes, materialization: dict[str, object]
) -> None:
    binding = overlay["canonical_source_binding"]
    if not isinstance(binding, dict):
        raise RuntimeError("overlay canonical source binding is not an object")
    package_acceptance_bytes = (REPO_ROOT / PACKAGE_ACCEPTANCE_PATH).read_bytes()
    manifest = json.loads((PROJECT_ROOT / "state/manifest.json").read_bytes())
    expected = {
        "accepted_package_acceptance_sha256": _sha256(package_acceptance_bytes),
        "canonical_materialization_sha256": _sha256(materialization_bytes),
        "project_content_hash": materialization["project"]["content_hash"],
        "registry_content_hash": materialization["registry"]["content_hash"],
        "active_pre_generation_graph_hash": manifest["active_dependency_graph"][
            "content_hash"
        ],
        "historical_request_hash": materialization["planner"]["request"][
            "request_content_hash"
        ],
        "historical_requirement_hash": materialization["planner"]["plan"][
            "generation_requirement"
        ]["requirement_hash"],
    }
    mismatches = {
        key: {"overlay": binding.get(key), "current": value}
        for key, value in expected.items()
        if binding.get(key) != value
    }
    if mismatches:
        raise RuntimeError(f"execution-intent source binding drift: {mismatches}")


def _new_request_and_projection(
    original_request: VideoPlanningRequest,
    generation_intent: GenerationIntent,
) -> tuple[
    VideoPlanningRequest,
    VerifiedGenerationRequirementProjection,
]:
    original_projection = original_request.generation_intent
    if original_projection is None:
        raise RuntimeError("canonical request has no generation-intent projection")
    projection_values = {
        field: getattr(original_projection, field)
        for field in type(original_projection).model_fields
        if field not in {"projection_hash", "generation_intent"}
    }
    projection_values["generation_intent"] = generation_intent
    new_generation_projection = ProviderNeutralGenerationIntentProjection.create(
        **projection_values
    )
    request_values = original_request.model_dump(
        mode="python",
        exclude={"request_content_hash", "generation_intent"},
    )
    request_values.update(
        request_id="drama-m6-d-shot-001-execution-intent-v1",
        generation_intent=new_generation_projection,
    )
    request = VideoPlanningRequest.create(**request_values)
    plan = VideoPlanner().plan(request)
    projection = require_current_video_plan(current_request=request, plan=plan)
    return request, VerifiedGenerationRequirementProjection.model_validate(
        projection.model_dump(mode="python")
    )


def _prompt_audit(prompt: str, exact_dialogue: str) -> dict[str, object]:
    forbidden_fragments = (
        "unspecified",
        "{",
        "}",
        "dramatic_function",
        "next_shot_obligation",
        "dialogue_intent",
        "Shot 2",
        "Shot 3",
        "drama.story",
        "drama.scene",
        "drama.character",
        "M6-D",
        "林峻想证明自己会留下",
        "林岚要在不被逼迫的情况下判断是否重新信任他",
    )
    found = tuple(fragment for fragment in forbidden_fragments if fragment in prompt)
    lines = prompt.splitlines()
    if (
        len(lines) != 3
        or not lines[0].startswith("integrated_multimodal_description: ")
        or not lines[1].startswith("overall_soundscape: ")
        or not lines[2].startswith("non_diegetic_music: ")
        or prompt.count(exact_dialogue) != 1
        or found
    ):
        raise RuntimeError(
            f"compiled H3 prompt audit failed: lines={len(lines)} "
            f"dialogue_count={prompt.count(exact_dialogue)} forbidden={found}"
        )
    return {
        "exactly_three_lines": True,
        "line_prefixes": tuple(line.split(":", 1)[0] for line in lines),
        "exact_dialogue_occurrences": 1,
        "raw_json_absent": True,
        "story_scene_future_bookkeeping_absent": True,
        "opaque_canonical_identity_ids_absent": True,
        "abstract_objective_absent": True,
        "unspecified_absent": True,
        "supported_dialogue_tag_present": "<d>[Chinese]" in prompt,
        "no_music_explicit": lines[2] == "non_diegetic_music: none",
    }


def main() -> None:
    before = _tree_snapshot(PROJECT_ROOT)
    materialization_bytes = MATERIALIZATION_PATH.read_bytes()
    materialization = json.loads(materialization_bytes)
    overlay, overlay_identity = _load_overlay()
    _assert_source_binding(overlay, materialization_bytes, materialization)

    loaded = load_production_project(PROJECT_ROOT / "project.yaml")
    original_request = VideoPlanningRequest.model_validate(
        materialization["planner"]["request"]
    )
    original_requirement = ProviderNeutralVideoRequirement.model_validate(
        materialization["planner"]["plan"]["generation_requirement"]
    )
    if (
        original_request.target_shot != loaded.shots[0]
        or original_request.scene_context != loaded.scenes[0]
        or original_requirement.requirement_hash
        != "d07dba76f19e2a1d998d9bf087df8583a1a99653cc7c1d9760935f72534c9b81"
    ):
        raise RuntimeError("canonical request/requirement no longer binds selected Shot 01")

    generation_intent = GenerationIntent.model_validate(overlay["generation_intent"])
    if "unspecified" in _canonical_json(generation_intent.model_dump(mode="json")):
        raise RuntimeError("overlay-owned generation intent still contains unspecified")
    request, projection = _new_request_and_projection(
        original_request,
        generation_intent,
    )
    requirement = ProviderNeutralVideoRequirement.model_validate(
        projection.requirement.model_dump(mode="python")
    )
    compilation = compile_h3_prompt(requirement)
    if not isinstance(compilation, H3PromptCompilation):
        raise RuntimeError(
            "complete execution-intent overlay did not compile: "
            f"{compilation.model_dump(mode='json')}"
        )
    exact_dialogue = generation_intent.dialogue_intent.verbatim_text
    if exact_dialogue is None:
        raise RuntimeError("overlay dialogue is not explicit")
    prompt_audit = _prompt_audit(compilation.prompt_text, exact_dialogue)

    after = _tree_snapshot(PROJECT_ROOT)
    if before != after:
        raise RuntimeError("authoring-to-request driver mutated canonical production state")
    evidence = {
        "schema_version": "drama-m6-d-shot-authoring-to-request/1",
        "status": (
            "CANONICAL_SHOT_01_EXECUTION_INTENT_READY"
            if overlay_identity["authority_status"] == "ACCEPTED_AND_SEALED"
            else "CANDIDATE_EXECUTION_INTENT_COMPILES_PENDING_ACCEPTANCE"
        ),
        "domain_id": "drama",
        "lane_id": "M6-D",
        "target_shot": overlay["target_shot"],
        "overlay_identity": overlay_identity,
        "canonical_lineage": {
            "accepted_package_acceptance_sha256": overlay[
                "canonical_source_binding"
            ]["accepted_package_acceptance_sha256"],
            "project_content_hash": loaded.project.content_hash,
            "registry_content_hash": loaded.registry.content_hash,
            "active_pre_generation_graph_hash": overlay[
                "canonical_source_binding"
            ]["active_pre_generation_graph_hash"],
            "materialization_path": MATERIALIZATION_PATH.relative_to(
                REPO_ROOT
            ).as_posix(),
            "materialization_sha256": _sha256(materialization_bytes),
            "pre_generation_graph_path": GRAPH_EVIDENCE_PATH.relative_to(
                REPO_ROOT
            ).as_posix(),
            "pre_generation_graph_sha256": _sha256(
                GRAPH_EVIDENCE_PATH.read_bytes()
            ),
        },
        "historical_identity_preserved": {
            "request_hash": original_request.request_content_hash,
            "requirement_hash": original_requirement.requirement_hash,
            "overwritten": False,
        },
        "new_canonical_projection": {
            "request_id": request.request_id,
            "request_hash": request.request_content_hash,
            "generation_intent_hash": request.generation_intent.projection_hash,
            "plan_hash": projection.plan_hash,
            "verified_projection_hash": projection.projection_hash,
            "requirement_id": requirement.requirement_id,
            "requirement_hash": requirement.requirement_hash,
            "strict_request_reopen": True,
            "strict_requirement_reopen": True,
            "strict_verified_projection_reopen": True,
        },
        "h3_compilation": {
            "compiler": "ai_video.production._h3_prompt.compile_h3_prompt",
            "compiler_contract": "legacy-t2va-current",
            "prompt_text": compilation.prompt_text,
            "prompt_sha256": compilation.prompt_sha256,
            "prompt_audit": prompt_audit,
        },
        "effects": {
            "production_state_files_before": len(before),
            "production_state_files_after": len(after),
            "production_state_writes": 0,
            "video_generation_request_persisted": False,
            "provider_selected": False,
            "provider_submit_count": 0,
            "generated_media_count": 0,
            "video_analysis_call_count": 0,
            "manifest_or_registry_writes": 0,
            "candidate_activation_count": 0,
        },
        "m6_d_status": "NOT_EVALUATED",
        "next_shot_submit_allowed": False,
        "remaining_gate": "PROVIDER_PROFILE_RUNTIME_IDENTITY_AND_EXACT_REQUEST_NOT_SELECTED",
    }
    EVIDENCE_PATH.write_bytes(_json_bytes(evidence))
    print(EVIDENCE_PATH.relative_to(REPO_ROOT).as_posix())
    print(_sha256(EVIDENCE_PATH.read_bytes()))


if __name__ == "__main__":
    main()
