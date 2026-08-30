"""Bind one explicit Shot 01 SourceAudioPolicy before any runtime effect.

The driver reopens the accepted timing repair and reconstructs the exact
Planner -> Router -> adapter compiler -> resolver -> preview chain.  It binds
the separately authored SourceAudioPolicy to that in-memory request identity;
it does not add a Product request field, persist a request, invoke Provider
preflight, submit, generate media, or write canonical Production state.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path
from types import ModuleType


REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = RUN_ROOT / "production-project"
TIMING_DRIVER_PATH = RUN_ROOT / "shot01_timing_request_readiness_driver.py"
POLICY_PATH = Path(
    "docs/superpowers/artifacts/drama/b-d0/source-audio-policy/"
    "key-at-the-waiting-room-shot-01-v3.proposed.json"
)
ACCEPTANCE_PATH = Path(
    "docs/superpowers/artifacts/drama/b-d0/source-audio-policy/"
    "key-at-the-waiting-room-shot-01-v3.accepted.json"
)
CANDIDATE_EVIDENCE_PATH = RUN_ROOT / (
    "evidence/drama-shot-01-source-audio-policy-readiness-candidate-v3.json"
)
ACCEPTED_EVIDENCE_PATH = RUN_ROOT / (
    "evidence/drama-shot-01-source-audio-policy-readiness-accepted-v3.json"
)

TIMING_PROPOSAL_SHA256 = (
    "9e37a8a6c6e14f4c82c356294fbf781332324bacee693fcc768496d14582f56e"
)
TIMING_ACCEPTANCE_SHA256 = (
    "b508cb375b6c326cbaaa5342d6aec051d20276f2d652e094f9cbca3a48efee10"
)
TIMING_DRIVER_SHA256 = (
    "668712bedae6419dac88669a8c1215d72c1b6d13b5c5a64990b196579671ee88"
)
TIMING_EVIDENCE_SHA256 = (
    "e3463ca9acc9ac381d0c2cc350f9b449214c588bcbade6f74fa7438c86b6f113"
)
BLOCKED_V2_SHA256 = (
    "5fde388ce6b46225ed68031d79edca79d83b988ef7a4b391e28c6be4eea82f5e"
)
REQUEST_HASH = "6dd31121a17d0178f4372bb4fa764f350216133b18f91d476675137af1480047"
PROJECTION_HASH = "e201aebeb90a324549138163c0d0f4f93405ad7755f3645b1a9bd99c5413ea21"
REQUIREMENT_HASH = "735c670eeee9bef29f9e9980ae8e476bde7bfff8786a78edf54af644d9eed924"
PROMPT_SHA256 = "e6cc74114e4dd41db284a29a83db228cbd9a034370fb5577a0e534d560139b47"
PROVIDER_BOUND_HASH = "69b470cd4a188fc31a73b04d69c59bba9b0efe8ab1f1eb9bde994f7999e951aa"
COMPILED_REQUEST_HASH = "56a6a21750a93ea392139a1e98a0558d9e7d5ae0576e1210f7b744e3118b7656"
REQUEST_INPUT_HASH = "de4b222eef59e867eaa30c591a10f98808558a19fa9b5d8973c7aece366b27d2"
RESOLVED_HASH = "5a9ee2722103a6cee533b36cd5ca2d6254f3ca2bf4c7e0e22da752bd48fecc95"
PREVIEW_HASH = "4ba6861de793286c47215d480d94237ab7202c966f9c4836716144008d7ecb76"
RUNTIME_BLOCKER = "SELECTED_PROFILE_RUNTIME_IDENTITY_MISMATCH"
EXACT_DIALOGUE = "钥匙还在。回去，一起开门。"
EXACT_AMBIENCE = (
    "steady soft rain heard outside the waiting-room windows with quiet "
    "enclosed room reflections, continuous for the full take"
)
EXACT_MUSIC = "none"
TARGET_CONTENT_HASH = "4cf53970d6642d4bfe73c23e5c12f9714c069843b0a7b47069dfb2519c47253b"
NORMALIZED_SELECTION = (
    "source_type=GENERATED;policy=KEEP;"
    "shot_id=drama.shot.waiting-room.001;revision=1"
)
EXPECTED_PROVIDER = "comfy-local-h3-t8"
EXPECTED_MODEL = "minimax-h3-t8-t2va-quality"
EXPECTED_CAPABILITY = "minimax-h3-t8-t2va-quality-v1"
EXACT_RAW_AUDIO_FINDINGS = (
    "decoded audio stream is usable and audible",
    "Lin-Jun says the exact verbatim dialogue 钥匙还在。回去，一起开门。 "
    "exactly once with no extra speech",
    "speaker and visible lip-sync binding are credible",
    "rain ambience is present without unintended music or duplicate speech",
    "audio timing remains synchronized with the exact Shot action",
)
EXPECTED_FORBIDDEN_EFFECTS = (
    "Provider or ComfyUI preflight under mismatched runtime",
    "ComfyUI checkout or lifecycle change",
    "VideoGenerationRequest persistence, durable submit intent or permit minting",
    "Provider submit, media generation, retry, repair or video-analysis",
    "Manifest, Registry, candidate activation, M6-D PASS, P6 or Final Acceptance",
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _write_immutable(path: Path, payload: bytes) -> None:
    if path.exists():
        if path.read_bytes() != payload:
            raise RuntimeError(f"immutable evidence path has other bytes: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(payload)


def _tree_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): _sha256(path.read_bytes())
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"module could not be loaded: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def _assert_path_hash(path: str, expected: str) -> None:
    actual = _sha256((REPO_ROOT / path).read_bytes())
    if actual != expected:
        raise RuntimeError(f"immutable parent path drifted: {path}")


def _validate_policy(payload: dict[str, object]) -> None:
    expected_keys = {
        "schema_version",
        "record_kind",
        "policy_id",
        "policy_version",
        "status",
        "domain_id",
        "lane_id",
        "target_shot",
        "parent_lineage",
        "explicit_user_selection",
        "source_audio_policy",
        "binding_contract",
        "replacement_reason",
        "forbidden_effects",
        "status_boundary",
    }
    if set(payload) != expected_keys:
        raise RuntimeError("SourceAudioPolicy payload fields drifted")
    target = payload.get("target_shot")
    lineage = payload.get("parent_lineage")
    selection = payload.get("explicit_user_selection")
    policy = payload.get("source_audio_policy")
    binding = payload.get("binding_contract")
    if (
        payload.get("schema_version") != "drama-shot-source-audio-policy/3"
        or payload.get("record_kind") != "drama_shot_source_audio_policy"
        or payload.get("policy_id")
        != "drama.source-audio.key-at-the-waiting-room.shot-01"
        or payload.get("policy_version") != 3
        or payload.get("status") != "proposed"
        or payload.get("domain_id") != "drama"
        or payload.get("lane_id") != "M6-D"
        or not isinstance(target, dict)
        or target.get("shot_id") != "drama.shot.waiting-room.001"
        or target.get("revision") != 1
        or target.get("content_hash") != TARGET_CONTENT_HASH
        or not isinstance(lineage, dict)
        or lineage.get("accepted_timing_repair_envelope_sha256")
        != TIMING_ACCEPTANCE_SHA256
        or lineage.get("accepted_timing_readiness_evidence_sha256")
        != TIMING_EVIDENCE_SHA256
        or lineage.get("blocked_readiness_envelope_sha256") != BLOCKED_V2_SHA256
        or lineage.get("rejected_policy_candidate_v1_commit")
        != "c3dd44940a251966790ea105d26e3c941879c3ac"
        or lineage.get("rejected_policy_candidate_v1_sha256")
        != "141cc81edd0557ed94bc867676817b1f482e9c9c4a28efc3b34d2f8138755b11"
        or lineage.get("rejected_policy_evidence_v1_sha256")
        != "0ca93cee2c882c996513c33572e95e8c1fc35b9cf1fd94ace90679b7d693920c"
        or lineage.get("rejected_policy_candidate_v2_commit")
        != "f230896ba7504e79f383c177bc8a3c3198b015ee"
        or lineage.get("rejected_policy_candidate_v2_sha256")
        != "5968e99d3a6f7bacc1bf812b607fdec55a3bdf69265a5d6b5ccae75057577cb3"
        or lineage.get("rejected_policy_evidence_v2_sha256")
        != "c3ab3b9ba2a6d2ab60048021831cf88129a91b866610231b8dc582bcaa0df13e"
        or lineage.get("request_hash") != REQUEST_HASH
        or lineage.get("verified_projection_hash") != PROJECTION_HASH
        or lineage.get("requirement_hash") != REQUIREMENT_HASH
        or lineage.get("prompt_sha256") != PROMPT_SHA256
        or lineage.get("provider_bound_request_hash") != PROVIDER_BOUND_HASH
        or lineage.get("compiled_request_hash") != COMPILED_REQUEST_HASH
        or lineage.get("request_input_hash") != REQUEST_INPUT_HASH
        or lineage.get("resolved_generation_hash") != RESOLVED_HASH
        or lineage.get("preview_fingerprint") != PREVIEW_HASH
        or not isinstance(selection, dict)
        or selection.get("source_id")
        != "current-session:user-selected-source-audio-policy-20260830"
        or selection.get("selection_channel") != "request_user_input"
        or selection.get("normalized_selection") != NORMALIZED_SELECTION
        or selection.get("selection_is_default_or_inference") is not False
        or not isinstance(policy, dict)
        or policy.get("source_type") != "GENERATED"
        or policy.get("policy") != "KEEP"
        or policy.get("trim_start_seconds") is not None
        or policy.get("request_native_audio_required") is not True
        or policy.get("required_dialogue") != EXACT_DIALOGUE
        or policy.get("required_ambience") != EXACT_AMBIENCE
        or policy.get("music") != EXACT_MUSIC
        or tuple(policy.get("required_raw_shot_audio_findings", ()))
        != EXACT_RAW_AUDIO_FINDINGS
        or not isinstance(binding, dict)
        or binding.get("selected_provider") != EXPECTED_PROVIDER
        or binding.get("selected_model") != EXPECTED_MODEL
        or binding.get("selected_capability") != EXPECTED_CAPABILITY
        or binding.get("exact_request_native_audio") is not True
        or binding.get("policy_matches_exact_request") is not True
        or binding.get("raw_shot_audio_pass_does_not_imply_final_composition_audio_pass")
        is not True
        or binding.get("canonical_p4_composition_required_before_final_delivery_claim")
        is not True
        or tuple(payload.get("forbidden_effects", ())) != EXPECTED_FORBIDDEN_EFFECTS
        or not isinstance(payload.get("status_boundary"), dict)
        or payload["status_boundary"].get("m6_d") != "NOT_EVALUATED"
        or payload["status_boundary"].get("execution") != "STOP_BEFORE_SUBMIT"
        or payload["status_boundary"].get("next_shot_submit_allowed") is not False
        or payload["status_boundary"].get(
            "candidate_acceptance_required_before_audio_blocker_can_clear"
        )
        is not True
        or payload["status_boundary"].get("remaining_runtime_blocker")
        != RUNTIME_BLOCKER
    ):
        raise RuntimeError("SourceAudioPolicy contract is invalid")


def _load_policy() -> tuple[dict[str, object], dict[str, object]]:
    policy_path = REPO_ROOT / POLICY_PATH
    if not ACCEPTANCE_PATH.is_absolute() and (REPO_ROOT / ACCEPTANCE_PATH).exists():
        acceptance_path = REPO_ROOT / ACCEPTANCE_PATH
        acceptance_bytes = acceptance_path.read_bytes()
        acceptance = json.loads(acceptance_bytes)
        accepted = acceptance.get("accepted_policy_payload")
        if (
            acceptance.get("schema_version")
            != "drama-shot-source-audio-policy-acceptance/3"
            or acceptance.get("status") != "accepted"
            or not isinstance(accepted, dict)
            or accepted.get("path") != POLICY_PATH.as_posix()
        ):
            raise RuntimeError("SourceAudioPolicy acceptance envelope is invalid")
        commit = accepted.get("commit")
        expected_sha = accepted.get("accepted_record_sha256")
        if not isinstance(commit, str) or not isinstance(expected_sha, str):
            raise RuntimeError("SourceAudioPolicy accepted identity is incomplete")
        payload_bytes = _git_blob(commit, POLICY_PATH.as_posix())
        if (
            _sha256(payload_bytes) != expected_sha
            or _git_blob_oid(commit, POLICY_PATH.as_posix())
            != accepted.get("git_blob_oid")
            or len(payload_bytes) != accepted.get("byte_size")
            or policy_path.read_bytes() != payload_bytes
        ):
            raise RuntimeError("SourceAudioPolicy accepted bytes drifted")
        payload = json.loads(payload_bytes)
        _validate_policy(payload)
        return payload, {
            "authority_status": "ACCEPTED_AND_SEALED",
            "payload_sha256": expected_sha,
            "payload_commit": commit,
            "acceptance_sha256": _sha256(acceptance_bytes),
        }
    payload_bytes = policy_path.read_bytes()
    payload = json.loads(payload_bytes)
    _validate_policy(payload)
    return payload, {
        "authority_status": "PROPOSED_PENDING_ACCEPTANCE",
        "payload_sha256": _sha256(payload_bytes),
        "payload_commit": None,
        "acceptance_sha256": None,
    }


def _reopen_exact_request(timing: ModuleType) -> dict[str, object]:
    authoring = timing._load_module(
        timing.AUTHORING_DRIVER_PATH,
        "drama_authoring_for_source_audio_policy",
    )
    readiness = timing._load_module(
        timing.READINESS_DRIVER_PATH,
        "drama_readiness_for_source_audio_policy",
    )
    repair, repair_identity = timing._load_repair()
    if repair_identity.get("authority_status") != "ACCEPTED_AND_SEALED":
        raise RuntimeError("accepted timing repair could not be reopened")
    materialization_bytes = authoring.MATERIALIZATION_PATH.read_bytes()
    materialization = json.loads(materialization_bytes)
    parent_overlay, parent_identity = authoring._load_overlay()
    authoring._assert_source_binding(
        parent_overlay,
        materialization_bytes,
        materialization,
    )
    if parent_identity.get("acceptance_sha256") != timing.PARENT_ACCEPTANCE_SHA256:
        raise RuntimeError("parent authoring identity drifted")
    loaded = timing.load_production_project(PROJECT_ROOT / "project.yaml")
    original_request = timing.VideoPlanningRequest.model_validate(
        materialization["planner"]["request"]
    )
    parent_intent = timing.GenerationIntent.model_validate(
        parent_overlay["generation_intent"]
    )
    parent_request, _ = authoring._new_request_and_projection(
        original_request,
        parent_intent,
    )
    repair_values = repair["timing_repair"]
    repaired_intent = timing._apply_generation_intent_repair(
        parent_intent,
        repair_values,
    )
    repaired_output = timing.OutputNeed.model_validate(
        repair_values["repaired_output_need"]
    )
    request, projection = timing._new_request_and_projection(
        original_request=original_request,
        parent_projection=parent_request.generation_intent,
        generation_intent=repaired_intent,
        output_need=repaired_output,
    )
    requirement = timing.ProviderNeutralVideoRequirement.model_validate(
        projection.requirement.model_dump(mode="python")
    )
    prompt = timing.compile_h3_prompt(requirement)
    if not isinstance(prompt, timing.H3PromptCompilation):
        raise RuntimeError("accepted timing requirement no longer compiles")
    routed = timing._route_compile_resolve_preview(
        readiness_driver=readiness,
        loaded=loaded,
        projection=projection,
    )
    supervisor_before = readiness._supervisor_status()
    runtime = readiness._runtime_identity(routed["profile"], supervisor_before)
    runtime.pop("canonical_provider_preflight", None)
    supervisor_after = readiness._supervisor_status()
    if supervisor_before != supervisor_after:
        raise RuntimeError("ComfyUI supervisor changed during read-only inspection")
    return {
        "request": request,
        "projection": projection,
        "requirement": requirement,
        "prompt": prompt,
        "routed": routed,
        "runtime": {
            **runtime,
            "supervisor_before": supervisor_before,
            "supervisor_after": supervisor_after,
            "comfyui_lifecycle_changed": False,
            "canonical_provider_preflight": (
                "NOT_INVOKED_SOURCE_AUDIO_POLICY_ONLY_SLICE"
            ),
        },
    }


def main() -> None:
    before = _tree_snapshot(PROJECT_ROOT)
    for path, expected in (
        (
            "docs/superpowers/artifacts/drama/b-d0/execution-intent/"
            "key-at-the-waiting-room-shot-01-v2.proposed.json",
            TIMING_PROPOSAL_SHA256,
        ),
        (
            "docs/superpowers/artifacts/drama/b-d0/execution-intent/"
            "key-at-the-waiting-room-shot-01-v2.accepted.json",
            TIMING_ACCEPTANCE_SHA256,
        ),
        (
            "runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/"
            "shot01_timing_request_readiness_driver.py",
            TIMING_DRIVER_SHA256,
        ),
        (
            "runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/"
            "drama-shot-01-timing-request-readiness-accepted-v1.json",
            TIMING_EVIDENCE_SHA256,
        ),
        (
            "docs/superpowers/artifacts/drama/b-d0/pre-submit-readiness/"
            "key-at-the-waiting-room-shot-01-v2.blocked.json",
            BLOCKED_V2_SHA256,
        ),
        (
            "docs/superpowers/artifacts/drama/b-d0/source-audio-policy/"
            "key-at-the-waiting-room-shot-01-v1.proposed.json",
            "141cc81edd0557ed94bc867676817b1f482e9c9c4a28efc3b34d2f8138755b11",
        ),
        (
            "runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/"
            "drama-shot-01-source-audio-policy-readiness-candidate-v1.json",
            "0ca93cee2c882c996513c33572e95e8c1fc35b9cf1fd94ace90679b7d693920c",
        ),
        (
            "docs/superpowers/artifacts/drama/b-d0/source-audio-policy/"
            "key-at-the-waiting-room-shot-01-v2.proposed.json",
            "5968e99d3a6f7bacc1bf812b607fdec55a3bdf69265a5d6b5ccae75057577cb3",
        ),
        (
            "runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/"
            "drama-shot-01-source-audio-policy-readiness-candidate-v2.json",
            "c3ab3b9ba2a6d2ab60048021831cf88129a91b866610231b8dc582bcaa0df13e",
        ),
    ):
        _assert_path_hash(path, expected)
    policy, policy_identity = _load_policy()
    timing = _load_module(
        TIMING_DRIVER_PATH,
        "drama_timing_for_source_audio_policy",
    )
    exact = _reopen_exact_request(timing)
    request = exact["request"]
    projection = exact["projection"]
    requirement = exact["requirement"]
    prompt = exact["prompt"]
    routed = exact["routed"]
    request_preview = routed["request"]
    resolved = routed["resolved"]
    preview = routed["preview"]
    expected_identities = (
        request.request_content_hash,
        projection.projection_hash,
        requirement.requirement_hash,
        prompt.prompt_sha256,
        routed["provider_bound"].provider_bound_request_hash,
        routed["compiled"].compiled_request_hash,
        request_preview.request_input_hash,
        resolved.resolved_generation_hash,
        preview.preview_fingerprint,
    )
    if expected_identities != (
        REQUEST_HASH,
        PROJECTION_HASH,
        REQUIREMENT_HASH,
        PROMPT_SHA256,
        PROVIDER_BOUND_HASH,
        COMPILED_REQUEST_HASH,
        REQUEST_INPUT_HASH,
        RESOLVED_HASH,
        PREVIEW_HASH,
    ):
        raise RuntimeError("canonical exact request lineage drifted")
    audio_policy = policy["source_audio_policy"]
    exact_sound_facts_match = (
        audio_policy["required_dialogue"]
        == requirement.generation_intent.dialogue_intent.verbatim_text
        and audio_policy["required_ambience"]
        == requirement.generation_intent.ambience_intent.environment_bed
        and audio_policy["music"] == requirement.generation_intent.music_intent.mode
        and prompt.prompt_text.count(f"<d>[Chinese]{EXACT_DIALOGUE}</d>") == 1
    )
    exact_request_binding_matches = (
        requirement.audio_need.value == "required"
        and request_preview.output_requirement.native_audio is True
        and tuple(routed["selected"].output_capability.native_audio_options)
        == (True,)
        and audio_policy["source_type"] == "GENERATED"
        and audio_policy["policy"] == "KEEP"
        and audio_policy["request_native_audio_required"] is True
        and routed["family"].capabilities().provider_name == EXPECTED_PROVIDER
        and routed["selected"].model_id == EXPECTED_MODEL
        and routed["selected"].capability_id == EXPECTED_CAPABILITY
        and exact_sound_facts_match
    )
    if not exact_request_binding_matches:
        raise RuntimeError("SourceAudioPolicy does not match exact request capability")
    gate_boundaries_validated = (
        policy["binding_contract"][
            "raw_shot_audio_pass_does_not_imply_final_composition_audio_pass"
        ]
        is True
        and policy["binding_contract"][
            "canonical_p4_composition_required_before_final_delivery_claim"
        ]
        is True
    )
    stop_boundary_validated = (
        policy["status_boundary"]["m6_d"] == "NOT_EVALUATED"
        and policy["status_boundary"]["execution"] == "STOP_BEFORE_SUBMIT"
        and policy["status_boundary"]["next_shot_submit_allowed"] is False
    )
    if not gate_boundaries_validated or not stop_boundary_validated:
        raise RuntimeError("SourceAudioPolicy Gate or stop boundary drifted")
    policy_binding = {
        "policy_payload_sha256": policy_identity["payload_sha256"],
        "shot_id": policy["target_shot"]["shot_id"],
        "shot_revision": policy["target_shot"]["revision"],
        "shot_content_hash": policy["target_shot"]["content_hash"],
        "source_type": "GENERATED",
        "policy": "KEEP",
        "request_hash": REQUEST_HASH,
        "request_input_hash": REQUEST_INPUT_HASH,
        "resolved_generation_hash": RESOLVED_HASH,
        "preview_fingerprint": PREVIEW_HASH,
        "native_audio": True,
        "prompt_sha256": PROMPT_SHA256,
    }
    policy_binding_hash = timing.canonical_sha256(policy_binding)
    accepted = policy_identity["authority_status"] == "ACCEPTED_AND_SEALED"
    blockers = [] if accepted else ["SOURCE_AUDIO_POLICY_ACCEPTANCE_PENDING"]
    if exact["runtime"]["result"] != "MATCH":
        blockers.append(RUNTIME_BLOCKER)
    after = _tree_snapshot(PROJECT_ROOT)
    if before != after:
        raise RuntimeError("SourceAudioPolicy driver mutated Production state")
    evidence = {
        "schema_version": "drama-m6-d-shot01-source-audio-readiness/3",
        "status": (
            "SOURCE_AUDIO_POLICY_ACCEPTED_RUNTIME_BLOCKED"
            if accepted
            else "SOURCE_AUDIO_POLICY_CANDIDATE_PENDING_ACCEPTANCE"
        ),
        "domain_id": "drama",
        "lane_id": "M6-D",
        "target_shot": policy["target_shot"],
        "policy_identity": policy_identity,
        "explicit_user_selection": policy["explicit_user_selection"],
        "canonical_lineage": {
            "request_hash": REQUEST_HASH,
            "verified_projection_hash": PROJECTION_HASH,
            "requirement_hash": REQUIREMENT_HASH,
            "prompt_sha256": PROMPT_SHA256,
            "provider_bound_request_hash": PROVIDER_BOUND_HASH,
            "compiled_request_hash": COMPILED_REQUEST_HASH,
            "request_input_hash": REQUEST_INPUT_HASH,
            "resolved_generation_hash": RESOLVED_HASH,
            "preview_fingerprint": PREVIEW_HASH,
            "strict_request_reopen": True,
            "strict_requirement_reopen": True,
            "strict_preview_reopen": True,
        },
        "source_audio_resolution": {
            "source_type": audio_policy["source_type"],
            "policy": audio_policy["policy"],
            "trim_start_seconds": audio_policy["trim_start_seconds"],
            "request_native_audio": request_preview.output_requirement.native_audio,
            "selected_capability_native_audio_options": list(
                routed["selected"].output_capability.native_audio_options
            ),
            "requirement_audio_need": requirement.audio_need.value,
            "required_dialogue": audio_policy["required_dialogue"],
            "required_ambience": audio_policy["required_ambience"],
            "music": audio_policy["music"],
            "policy_binding": policy_binding,
            "policy_binding_hash": policy_binding_hash,
            "default_or_inference_used": False,
            "exact_sound_facts_match": exact_sound_facts_match,
            "exact_request_binding_matches": exact_request_binding_matches,
            "raw_shot_gate_requirements": audio_policy[
                "required_raw_shot_audio_findings"
            ],
            "raw_and_final_gate_boundaries_validated": gate_boundaries_validated,
            "final_composition_audio_gate_still_required": policy[
                "binding_contract"
            ]["canonical_p4_composition_required_before_final_delivery_claim"],
        },
        "runtime_identity": exact["runtime"],
        "submit_readiness": {
            "budget": "NOT_APPLICABLE_LOCAL_UNMETERED",
            "cloud_egress": "DENIED_AND_NOT_USED",
            "durable_submit_intent": "NOT_CREATED",
            "one_use_permit": "NOT_MINTED",
            "provider_preflight": "NOT_INVOKED_SOURCE_AUDIO_POLICY_ONLY_SLICE",
            "provider_submit": "NOT_INVOKED",
            "ready": False,
            "blockers": blockers,
        },
        "historical_evidence_preserved": {
            "timing_readiness_accepted_v1": {
                "path": policy["parent_lineage"][
                    "accepted_timing_readiness_evidence_path"
                ],
                "sha256": TIMING_EVIDENCE_SHA256,
                "overwritten": False,
            },
            "blocked_readiness_v2": {
                "path": policy["parent_lineage"]["blocked_readiness_envelope_path"],
                "sha256": BLOCKED_V2_SHA256,
                "overwritten": False,
            },
            "rejected_policy_candidate_v1": {
                "path": policy["parent_lineage"]["rejected_policy_candidate_v1_path"],
                "commit": policy["parent_lineage"]["rejected_policy_candidate_v1_commit"],
                "sha256": policy["parent_lineage"]["rejected_policy_candidate_v1_sha256"],
                "overwritten": False,
            },
            "rejected_policy_evidence_v1": {
                "path": policy["parent_lineage"]["rejected_policy_evidence_v1_path"],
                "sha256": policy["parent_lineage"]["rejected_policy_evidence_v1_sha256"],
                "overwritten": False,
            },
            "rejected_policy_candidate_v2": {
                "path": policy["parent_lineage"]["rejected_policy_candidate_v2_path"],
                "commit": policy["parent_lineage"]["rejected_policy_candidate_v2_commit"],
                "sha256": policy["parent_lineage"]["rejected_policy_candidate_v2_sha256"],
                "overwritten": False,
            },
            "rejected_policy_evidence_v2": {
                "path": policy["parent_lineage"]["rejected_policy_evidence_v2_path"],
                "sha256": policy["parent_lineage"]["rejected_policy_evidence_v2_sha256"],
                "overwritten": False,
            },
        },
        "source_identity": {
            "actor_identity": "codex_primary_agent",
            "generator_id": "drama-shot01-source-audio-policy-readiness-driver@3",
            "driver_path": Path(__file__).relative_to(REPO_ROOT).as_posix(),
            "driver_sha256": _sha256(Path(__file__).read_bytes()),
            "policy_path": POLICY_PATH.as_posix(),
            "policy_sha256": policy_identity["payload_sha256"],
            "files": {
                path: _sha256((REPO_ROOT / path).read_bytes())
                for path in (
                    "runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/"
                    "shot01_timing_request_readiness_driver.py",
                    "runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/"
                    "authoring_to_request_driver.py",
                    "runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/"
                    "provider_request_readiness_driver.py",
                    "docs/superpowers/artifacts/drama/b-d0/execution-intent/"
                    "key-at-the-waiting-room-shot-01-v2.accepted.json",
                    "runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/"
                    "drama-shot-01-timing-request-readiness-accepted-v1.json",
                    "docs/superpowers/artifacts/drama/b-d0/pre-submit-readiness/"
                    "key-at-the-waiting-room-shot-01-v2.blocked.json",
                    *timing.SOURCE_PATHS,
                )
            },
        },
        "effects": {
            "production_state_files_before": len(before),
            "production_state_files_after": len(after),
            "driver_production_state_writes": 0,
            "driver_video_generation_request_persisted": False,
            "driver_provider_preflight_count": 0,
            "driver_provider_submit_count": 0,
            "driver_permit_mint_count": 0,
            "driver_generated_media_count": 0,
            "driver_video_analysis_call_count": 0,
            "driver_manifest_or_registry_writes": 0,
            "driver_candidate_activation_count": 0,
        },
        "stop_boundary_validated": stop_boundary_validated,
        "m6_d_status": policy["status_boundary"]["m6_d"],
        "execution_status": policy["status_boundary"]["execution"],
        "next_shot_submit_allowed": policy["status_boundary"][
            "next_shot_submit_allowed"
        ],
        "remaining_blockers": blockers,
    }
    output_path = ACCEPTED_EVIDENCE_PATH if accepted else CANDIDATE_EVIDENCE_PATH
    evidence_bytes = _canonical_json_bytes(evidence)
    _write_immutable(output_path, evidence_bytes)
    print(output_path.relative_to(REPO_ROOT).as_posix())
    print(_sha256(evidence_bytes))


if __name__ == "__main__":
    main()
