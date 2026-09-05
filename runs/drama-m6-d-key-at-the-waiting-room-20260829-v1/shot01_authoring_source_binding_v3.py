"""Reopen the accepted Shot 01 source-binding view without any runtime effect.

Version 3 is deliberately a narrow metadata binding: it substitutes only the
committed active pre-generation graph in the original sealed source binding.
Planning, routing, compilation, resolution and lineage validation remain the
existing canonical seams.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType


REPO_ROOT = Path(__file__).resolve().parents[2]
RUN_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = RUN_ROOT / "production-project"
PROPOSAL_PATH = Path(
    "docs/superpowers/artifacts/drama/b-d0/execution-intent/"
    "key-at-the-waiting-room-shot-01-v3.proposed.json"
)
ACCEPTANCE_PATH = Path(
    "docs/superpowers/artifacts/drama/b-d0/execution-intent/"
    "key-at-the-waiting-room-shot-01-v3.accepted.json"
)
ACTIVE_GRAPH_HASH = "a95a916f26b53f4a2437d90860a13910fa458e33735507963148360062e8742a"
SOURCE_BINDING_VERSION = 3
LOADER_PATH = (RUN_ROOT.relative_to(REPO_ROOT) / Path(__file__).name).as_posix()
REQUEST_IDENTITY_KEYS = (
    "provider_bound_request_hash",
    "compiled_request_hash",
    "request_input_hash",
    "resolved_generation_hash",
    "preview_fingerprint",
)
REFERENCE_PATHS = {
    "semantic_overlay_acceptance": (
        "docs/superpowers/artifacts/drama/b-d0/execution-intent/"
        "key-at-the-waiting-room-shot-01-v1.accepted.json"
    ),
    "timing_repair_acceptance": (
        "docs/superpowers/artifacts/drama/b-d0/execution-intent/"
        "key-at-the-waiting-room-shot-01-v2.accepted.json"
    ),
    "source_audio_policy_acceptance": (
        "docs/superpowers/artifacts/drama/b-d0/source-audio-policy/"
        "key-at-the-waiting-room-shot-01-v3.accepted.json"
    ),
    "graph_transition_evidence": (
        "runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/evidence/"
        "drama-shot01-graph-lineage-20260905-v1-committed.json"
    ),
}
HELPER_PATHS = (
    LOADER_PATH,
    "runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/authoring_to_request_driver.py",
    "runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/shot01_timing_request_readiness_driver.py",
    "runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/provider_request_readiness_driver.py",
    "runs/drama-m6-d-key-at-the-waiting-room-20260829-v1/shot01_source_audio_policy_readiness_driver.py",
)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def _safe_path(path: str) -> Path:
    candidate = Path(path)
    _require(not candidate.is_absolute() and ".." not in candidate.parts, "unsafe binding path")
    resolved = (REPO_ROOT / candidate).resolve()
    _require(resolved.is_relative_to(REPO_ROOT.resolve()), "binding path escapes repository")
    current = REPO_ROOT
    for part in candidate.parts:
        current = current / part
        _require(not current.is_symlink(), "binding path uses symlink")
    return candidate


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


def _verify_reference(name: str, value: object) -> bytes:
    _require(isinstance(value, dict) and set(value) == {"path", "commit", "sha256"}, f"invalid {name} reference")
    path = value["path"]
    commit = value["commit"]
    digest = value["sha256"]
    _require(isinstance(path, str) and path == REFERENCE_PATHS[name], f"{name} path drift")
    _require(isinstance(commit, str) and len(commit) == 40, f"{name} commit drift")
    _require(isinstance(digest, str) and len(digest) == 64, f"{name} hash drift")
    relative = _safe_path(path)
    working = (REPO_ROOT / relative).read_bytes()
    committed = _git_blob(commit, path)
    _require(working == committed and _sha256(committed) == digest, f"{name} committed/working bytes drift")
    return committed


def _validate_binding_payload(payload: object, original_binding: dict[str, object]) -> dict[str, object]:
    _require(isinstance(payload, dict), "source-binding payload is not an object")
    expected_keys = {
        "schema_version", "record_kind", "overlay_id", "binding_version", "status",
        "domain_id", "lane_id", "references", "canonical_source_binding",
    }
    _require(set(payload) == expected_keys, "source-binding payload fields drifted")
    expected = {
        "schema_version": "drama-shot-source-binding/1",
        "record_kind": "drama_shot_source_binding",
        "overlay_id": "drama.execution-intent.key-at-the-waiting-room.shot-01",
        "binding_version": SOURCE_BINDING_VERSION,
        "status": "proposed",
        "domain_id": "drama",
        "lane_id": "M6-D",
    }
    _require(all(payload.get(key) == value for key, value in expected.items()), "source-binding payload identity drifted")
    references = payload["references"]
    _require(isinstance(references, dict) and set(references) == set(REFERENCE_PATHS), "source-binding references drifted")
    binding = payload["canonical_source_binding"]
    _require(isinstance(binding, dict), "source-binding view is not an object")
    expected_binding = {**original_binding, "active_pre_generation_graph_hash": ACTIVE_GRAPH_HASH}
    _require(binding == expected_binding, "source-binding changed semantic lineage outside active graph")
    return binding


def _load_accepted_binding(expected_acceptance_sha256: str) -> tuple[dict[str, object], dict[str, object]]:
    _require(isinstance(expected_acceptance_sha256, str) and len(expected_acceptance_sha256) == 64, "expected acceptance SHA-256 is required")
    acceptance_relative = _safe_path(ACCEPTANCE_PATH.as_posix())
    acceptance_bytes = (REPO_ROOT / acceptance_relative).read_bytes()
    _require(_sha256(acceptance_bytes) == expected_acceptance_sha256, "source-binding acceptance SHA-256 drift")
    acceptance = json.loads(acceptance_bytes)
    _require(isinstance(acceptance, dict), "source-binding acceptance is not an object")
    required = {
        "schema_version": "drama-shot-source-binding-acceptance/1",
        "record_kind": "drama_shot_source_binding_acceptance",
        "overlay_id": "drama.execution-intent.key-at-the-waiting-room.shot-01",
        "binding_version": SOURCE_BINDING_VERSION,
        "status": "accepted",
        "domain_id": "drama",
        "lane_id": "M6-D",
        "authority": "CURRENT_USER_METADATA_BINDING_AND_LOADER_AUTHORIZATION",
    }
    _require(all(acceptance.get(key) == value for key, value in required.items()), "source-binding acceptance identity drifted")
    boundary = {
        "accepted_scope": "Metadata-only graph source-binding supersession; original v1 semantics and v2 timing repair remain immutable",
        "execution_authority": False,
        "runtime_readiness": "NOT_EVALUATED",
        "provider_submit": False,
        "candidate_activation": False,
        "m6_d": "NOT_EVALUATED",
        "next_shot_submit_allowed": False,
    }
    _require(
        all(acceptance.get(key) == value for key, value in boundary.items()),
        "source-binding acceptance boundary drifted",
    )
    _require(
        set(acceptance) <= set(required) | set(boundary) | {"accepted_binding_payload", "review", "status_boundary"},
        "source-binding acceptance has unknown fields",
    )
    accepted = acceptance.get("accepted_binding_payload")
    _require(isinstance(accepted, dict) and set(accepted) == {"path", "commit", "git_blob_oid", "byte_size", "sha256"}, "accepted source-binding payload pointer drifted")
    path = accepted["path"]
    commit = accepted["commit"]
    oid = accepted["git_blob_oid"]
    size = accepted["byte_size"]
    digest = accepted["sha256"]
    _require(path == PROPOSAL_PATH.as_posix() and isinstance(commit, str) and len(commit) == 40, "accepted source-binding payload path/commit drifted")
    _require(isinstance(oid, str) and len(oid) == 40 and isinstance(size, int) and size >= 0 and isinstance(digest, str) and len(digest) == 64, "accepted source-binding payload identity drifted")
    relative = _safe_path(path)
    committed = _git_blob(commit, path)
    working = (REPO_ROOT / relative).read_bytes()
    _require(working == committed, "accepted source-binding working bytes drifted")
    _require(_git_blob_oid(commit, path) == oid and len(committed) == size and _sha256(committed) == digest, "accepted source-binding blob identity drifted")
    return json.loads(committed), {
        "authority_status": "ACCEPTED_AND_SEALED",
        "acceptance_path": ACCEPTANCE_PATH.as_posix(),
        "acceptance_sha256": expected_acceptance_sha256,
        "payload_path": path,
        "payload_commit": commit,
        "payload_git_blob_oid": oid,
        "payload_byte_size": size,
        "payload_sha256": digest,
    }


def _committed_source_inventory(source_commit: str) -> dict[str, str]:
    _require(isinstance(source_commit, str) and len(source_commit) == 40, "explicit source commit is required")
    paths = ("src", "workflows", *HELPER_PATHS)
    output = subprocess.run(
        ["git", "ls-tree", "-r", "-z", source_commit, "--", *paths],
        cwd=REPO_ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout
    inventory: dict[str, str] = {}
    for entry in output.split(b"\0"):
        if not entry:
            continue
        metadata, raw_path = entry.split(b"\t", 1)
        mode, kind, oid = metadata.split()
        _require(kind == b"blob" and mode in (b"100644", b"100755"), "unsupported pinned source entry")
        path = raw_path.decode("utf-8")
        relative = _safe_path(path)
        current = (REPO_ROOT / relative).read_bytes()
        committed = subprocess.run(
            ["git", "cat-file", "blob", oid.decode("ascii")],
            cwd=REPO_ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        ).stdout
        _require(current == committed, f"pinned source drift: {path}")
        inventory[path] = _sha256(current)
    _require(all(path in inventory for path in HELPER_PATHS), "pinned helper inventory incomplete")
    current_modules = {path.relative_to(REPO_ROOT).as_posix() for path in (REPO_ROOT / "src").rglob("*.py")}
    _require(current_modules <= inventory.keys(), "uncommitted Python module supplements pinned source")
    return inventory


def _load_pinned_module(inventory: dict[str, str], name: str, relative: str) -> ModuleType:
    _require(relative in inventory, f"unverified helper import: {relative}")
    path = REPO_ROOT / _safe_path(relative)
    _require(_sha256(path.read_bytes()) == inventory[relative], f"pinned helper drift before import: {relative}")
    spec = importlib.util.spec_from_file_location(name, path)
    _require(spec is not None and spec.loader is not None, f"could not import pinned helper: {relative}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validate_graph_evidence(value: object) -> dict[str, object]:
    _require(isinstance(value, dict), "graph transition evidence is not an object")
    pointer = value.get("graph_pointer")
    identities = value.get("new_request_identity")
    _require(isinstance(pointer, dict) and pointer.get("content_hash") == ACTIVE_GRAPH_HASH, "graph transition pointer drifted")
    _require(isinstance(identities, dict) and set(identities) == set(REQUEST_IDENTITY_KEYS), "graph request identity fields drifted")
    _require(all(isinstance(identities[key], str) and len(identities[key]) == 64 for key in REQUEST_IDENTITY_KEYS), "graph request identity values drifted")
    for key in ("planning_request_hash", "requirement_hash", "verified_projection_hash", "prompt_sha256"):
        _require(isinstance(value.get(key), str) and len(value[key]) == 64, f"graph {key} drifted")
    audio = value.get("source_audio_policy")
    _require(isinstance(audio, dict) and audio.get("selection") == "GENERATED + KEEP" and audio.get("native_audio") is True and audio.get("sound_facts_match") is True, "graph source-audio policy drifted")
    identity = audio.get("identity")
    _require(isinstance(identity, dict) and identity.get("authority_status") == "ACCEPTED_AND_SEALED", "graph source-audio acceptance drifted")
    return value


def _assert_audio_policy(policy: object, graph_audio: object, requirement: object, routed: object) -> dict[str, object]:
    _require(isinstance(policy, dict) and isinstance(policy.get("source_audio_policy"), dict), "source-audio policy is invalid")
    selection = policy["source_audio_policy"]
    _require(selection.get("source_type") == "GENERATED" and selection.get("policy") == "KEEP", "source-audio selection drifted")
    _require(selection.get("request_native_audio_required") is True, "source-audio native-audio requirement drifted")
    _require(isinstance(graph_audio, dict) and graph_audio.get("selection") == "GENERATED + KEEP" and graph_audio.get("native_audio") is True and graph_audio.get("sound_facts_match") is True, "graph source-audio facts drifted")
    intent = requirement.generation_intent
    _require(selection.get("required_dialogue") == intent.dialogue_intent.verbatim_text, "source-audio dialogue drifted")
    _require(selection.get("required_ambience") == intent.ambience_intent.environment_bed, "source-audio ambience drifted")
    _require(selection.get("music") == intent.music_intent.mode, "source-audio music drifted")
    _require(routed["request"].output_requirement.native_audio is True, "resolved request native-audio drifted")
    return {"identity": graph_audio["identity"], "selection": "GENERATED + KEEP", "native_audio": True, "sound_facts_match": True}


def _assert_imports_are_pinned(inventory: dict[str, str]) -> None:
    for module in tuple(sys.modules.values()):
        path = getattr(module, "__file__", None)
        if not path:
            continue
        resolved = Path(path).resolve()
        if resolved.is_relative_to(REPO_ROOT / "src"):
            relative = resolved.relative_to(REPO_ROOT).as_posix()
            _require(relative in inventory and _sha256(resolved.read_bytes()) == inventory[relative], "imported Product source escaped pinned inventory")


def reopen_exact_request(
    *,
    expected_acceptance_sha256: str,
    source_commit: str,
    binding_version: int = SOURCE_BINDING_VERSION,
) -> dict[str, object]:
    """Return the v3-bound in-memory request after strict canonical reopening."""
    _require(binding_version == SOURCE_BINDING_VERSION, "only source-binding version 3 is accepted")
    _require(isinstance(source_commit, str) and len(source_commit) == 40, "explicit source commit is required")
    binding_payload, binding_identity = _load_accepted_binding(expected_acceptance_sha256)
    inventory = _committed_source_inventory(source_commit)
    authoring = _load_pinned_module(inventory, "source_binding_authoring", HELPER_PATHS[1])
    timing = _load_pinned_module(inventory, "source_binding_timing", HELPER_PATHS[2])
    readiness = _load_pinned_module(inventory, "source_binding_readiness", HELPER_PATHS[3])
    source_audio = _load_pinned_module(inventory, "source_binding_audio", HELPER_PATHS[4])

    materialization_bytes = authoring.MATERIALIZATION_PATH.read_bytes()
    materialization = json.loads(materialization_bytes)
    original_overlay, original_identity = authoring._load_overlay()
    _require(original_identity.get("authority_status") == "ACCEPTED_AND_SEALED", "original semantic overlay is not accepted")
    binding = _validate_binding_payload(binding_payload, original_overlay["canonical_source_binding"])
    references = binding_payload["references"]
    reference_bytes = {name: _verify_reference(name, references[name]) for name in REFERENCE_PATHS}
    _require(_sha256(reference_bytes["semantic_overlay_acceptance"]) == original_identity.get("acceptance_sha256"), "semantic overlay reference drifted")
    composed_overlay = {**original_overlay, "canonical_source_binding": binding}
    authoring._assert_source_binding(composed_overlay, materialization_bytes, materialization)

    graph = _validate_graph_evidence(json.loads(reference_bytes["graph_transition_evidence"]))
    loaded = timing.load_production_project(PROJECT_ROOT / "project.yaml")
    _require(loaded.manifest.active_dependency_graph.content_hash == ACTIVE_GRAPH_HASH == binding["active_pre_generation_graph_hash"], "active graph does not match accepted source-binding")
    _require(loaded.manifest.active_dependency_graph.model_dump(mode="json") == graph["graph_pointer"], "active graph pointer differs from committed transition")

    repair, repair_identity = timing._load_repair()
    _require(repair_identity.get("authority_status") == "ACCEPTED_AND_SEALED", "timing repair is not accepted")
    _require(_sha256(reference_bytes["timing_repair_acceptance"]) == repair_identity.get("acceptance_sha256"), "timing repair reference drifted")
    original_request = timing.VideoPlanningRequest.model_validate(materialization["planner"]["request"])
    parent_intent = timing.GenerationIntent.model_validate(original_overlay["generation_intent"])
    parent_request, _ = authoring._new_request_and_projection(original_request, parent_intent)
    repaired_intent = timing._apply_generation_intent_repair(parent_intent, repair["timing_repair"])
    repaired_output = timing.OutputNeed.model_validate(repair["timing_repair"]["repaired_output_need"])
    request, projection = timing._new_request_and_projection(
        original_request=original_request,
        parent_projection=parent_request.generation_intent,
        generation_intent=repaired_intent,
        output_need=repaired_output,
    )
    requirement = timing.ProviderNeutralVideoRequirement.model_validate(projection.requirement.model_dump(mode="python"))
    prompt = timing.compile_h3_prompt(requirement)
    _require(isinstance(prompt, timing.H3PromptCompilation), "canonical H3 compilation is unsupported")
    routed = timing._route_compile_resolve_preview(readiness_driver=readiness, loaded=loaded, projection=projection)
    observed = {
        "planning_request_hash": request.request_content_hash,
        "requirement_hash": requirement.requirement_hash,
        "verified_projection_hash": projection.projection_hash,
        "prompt_sha256": prompt.prompt_sha256,
        "new_request_identity": {
            "provider_bound_request_hash": routed["provider_bound"].provider_bound_request_hash,
            "compiled_request_hash": routed["compiled"].compiled_request_hash,
            "request_input_hash": routed["request"].request_input_hash,
            "resolved_generation_hash": routed["resolved"].resolved_generation_hash,
            "preview_fingerprint": routed["preview"].preview_fingerprint,
        },
    }
    _require(all(observed[key] == graph[key] for key in ("planning_request_hash", "requirement_hash", "verified_projection_hash", "prompt_sha256", "new_request_identity")), "reopened request does not match committed graph lineage")
    policy, policy_identity = source_audio._load_policy()
    _require(policy_identity.get("authority_status") == "ACCEPTED_AND_SEALED", "source-audio policy is not accepted")
    _require(_sha256(reference_bytes["source_audio_policy_acceptance"]) == policy_identity.get("acceptance_sha256"), "source-audio acceptance reference drifted")
    _require(policy_identity == graph["source_audio_policy"]["identity"], "source-audio policy identity differs from committed graph")
    source_audio_identity = _assert_audio_policy(policy, graph["source_audio_policy"], requirement, routed)
    from ai_video.production.video_pre_generation import verify_current_video_generation_lineage

    verify_current_video_generation_lineage(loaded, routed["resolved"])
    _assert_imports_are_pinned(inventory)
    final_payload, final_binding_identity = _load_accepted_binding(expected_acceptance_sha256)
    _require(final_payload == binding_payload and final_binding_identity == binding_identity, "accepted source-binding changed during reopen")
    final_reference_bytes = {name: _verify_reference(name, references[name]) for name in REFERENCE_PATHS}
    _require(final_reference_bytes == reference_bytes, "source-binding references changed during reopen")
    final_materialization_bytes = authoring.MATERIALIZATION_PATH.read_bytes()
    final_materialization = json.loads(final_materialization_bytes)
    final_overlay, final_overlay_identity = authoring._load_overlay()
    _require(final_overlay == original_overlay and final_overlay_identity == original_identity, "original semantic overlay changed during reopen")
    authoring._assert_source_binding(
        {**final_overlay, "canonical_source_binding": binding},
        final_materialization_bytes,
        final_materialization,
    )
    final_loaded = timing.load_production_project(PROJECT_ROOT / "project.yaml")
    _require(final_loaded.manifest.active_dependency_graph.model_dump(mode="json") == graph["graph_pointer"], "active graph changed during reopen")
    verify_current_video_generation_lineage(final_loaded, routed["resolved"])
    _require(_committed_source_inventory(source_commit) == inventory, "pinned source inventory changed during reopen")
    _assert_imports_are_pinned(inventory)
    return {
        "request": request,
        "projection": projection,
        "requirement": requirement,
        "prompt": prompt,
        "routed": routed,
        "source_binding": {
            "identity": binding_identity,
            "canonical_source_binding": binding,
            "source_commit": source_commit,
            "inventory_sha256": _sha256((_canonical_json(inventory) + "\n").encode("utf-8")),
            "inventory_file_count": len(inventory),
        },
        "source_audio_policy": source_audio_identity,
        "source_identity": {"commit": source_commit, "inventory": inventory},
    }
