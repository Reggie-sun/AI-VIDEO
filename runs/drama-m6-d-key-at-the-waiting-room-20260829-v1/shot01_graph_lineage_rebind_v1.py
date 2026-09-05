"""Rehearse and seal one canonical graph-only transition; never submit media."""
from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = Path(__file__).resolve().parent
SOURCE_COMMIT = "36305dec492b07d3d1d7e037c3f96521f19b414d"
ATTEMPT = "drama-shot01-graph-lineage-20260905-v1"
EVIDENCE = RUN / "evidence/drama-shot01-graph-lineage-rehearsal-v7.json"
APPROVAL = ROOT / "docs/superpowers/artifacts/drama/b-d0/pre-generation-rebind/key-at-the-waiting-room-shot-01-v1.accepted.json"


def context():
    path = RUN / "shot01_first_submit_v1.py"
    import hashlib
    if hashlib.sha256(path.read_bytes()).hexdigest() != "e708c4ac4dcfa840a448edd794fda9155dcbada982e18ab1800abd8442a200df":
        raise RuntimeError("historical driver drift")
    spec = importlib.util.spec_from_file_location("graph_rebind_parent", path)
    d = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(d)
    h = d.load_helper()
    h.SOURCE_COMMIT = SOURCE_COMMIT
    inventory = h.committed_snapshot()
    lineage = d.creative_lineage(h)
    source = h.load("graph_rebind_source", "shot01_source_audio_policy_readiness_driver.py")
    timing = h.load("graph_rebind_timing", "shot01_timing_request_readiness_driver.py")
    readiness = h.load("graph_rebind_runtime", "provider_request_readiness_driver.py")
    policy, policy_identity = source._load_policy()
    # Graph reconciliation consumes canonical planning/compilation, not a live server.
    exact = reopen_planning(source, timing, readiness)
    previous_bytes = (RUN / "evidence/drama-shot01-first-submit-preflight-v3.json").read_bytes()
    d.require(d.sha(previous_bytes) == "28b320b076297cbf553345eba585d20801088b94d91d02e6184eb3655639a624", "sealed parent preflight drift")
    previous = json.loads(previous_bytes)
    d.require(exact["request"].request_content_hash == previous["readiness"]["canonical_identity"]["request_hash"], "planning request drift")
    d.require(exact["projection"].projection_hash == previous["readiness"]["canonical_identity"]["verified_projection_hash"], "projection drift")
    d.require(exact["requirement"].requirement_hash == previous["readiness"]["canonical_identity"]["requirement_hash"], "requirement drift")
    d.require(exact["prompt"].prompt_sha256 == previous["readiness"]["canonical_identity"]["prompt_sha256"], "prompt drift")
    d.require(policy_identity == previous["readiness"]["source_audio_policy"]["identity"], "audio policy identity drift")
    audio = policy["source_audio_policy"]
    intent = exact["requirement"].generation_intent
    d.require(audio["source_type"] == "GENERATED" and audio["policy"] == "KEEP", "audio selection drift")
    d.require(audio["request_native_audio_required"] is True and exact["routed"]["request"].output_requirement.native_audio is True, "native audio drift")
    d.require(audio["required_dialogue"] == intent.dialogue_intent.verbatim_text == source.EXACT_DIALOGUE, "dialogue drift")
    d.require(audio["required_ambience"] == intent.ambience_intent.environment_bed and audio["music"] == intent.music_intent.mode, "sound facts drift")
    exact["source_audio_policy"] = {"identity": policy_identity, "selection": "GENERATED + KEEP", "native_audio": True, "sound_facts_match": True}
    return d, h, source, timing, readiness, exact, inventory, lineage


def reopen_planning(source, timing, readiness):
    authoring = timing._load_module(timing.AUTHORING_DRIVER_PATH, "graph_rebind_authoring")
    repair, repair_identity = timing._load_repair()
    if repair_identity["authority_status"] != "ACCEPTED_AND_SEALED":
        raise RuntimeError("timing repair is not sealed")
    materialization_bytes = authoring.MATERIALIZATION_PATH.read_bytes()
    materialization = json.loads(materialization_bytes)
    overlay, overlay_identity = authoring._load_overlay()
    authoring._assert_source_binding(overlay, materialization_bytes, materialization)
    if overlay_identity["acceptance_sha256"] != timing.PARENT_ACCEPTANCE_SHA256:
        raise RuntimeError("parent overlay drift")
    original = timing.VideoPlanningRequest.model_validate(materialization["planner"]["request"])
    parent_intent = timing.GenerationIntent.model_validate(overlay["generation_intent"])
    parent_request, _ = authoring._new_request_and_projection(original, parent_intent)
    intent = timing._apply_generation_intent_repair(parent_intent, repair["timing_repair"])
    request, projection = timing._new_request_and_projection(original_request=original,
        parent_projection=parent_request.generation_intent, generation_intent=intent,
        output_need=timing.OutputNeed.model_validate(repair["timing_repair"]["repaired_output_need"]))
    requirement = timing.ProviderNeutralVideoRequirement.model_validate(projection.requirement.model_dump(mode="python"))
    prompt = timing.compile_h3_prompt(requirement)
    if not isinstance(prompt, timing.H3PromptCompilation):
        raise RuntimeError("accepted native prompt is unsupported")
    loaded = timing.load_production_project(source.PROJECT_ROOT / "project.yaml")
    routed = timing._route_compile_resolve_preview(readiness_driver=readiness, loaded=loaded, projection=projection)
    return {"request": request, "projection": projection, "requirement": requirement, "prompt": prompt, "routed": routed}


def prepare(root, exact):
    from ai_video.production.project import load_production_project
    from ai_video.production.dependency import desired_fingerprints, resolve_dependency_state
    from ai_video.production.state_commit import ProductionStateCommitter, StateCommitRequest, prepare_dependency_graph_transition
    from ai_video.production.video_pre_generation import VideoPreGenerationDependencyInputs, build_video_pre_generation_dependency_graph, build_video_pre_generation_applied_evidence, generation_target_node_id
    loaded = load_production_project(root / "project.yaml")
    m = loaded.manifest
    inputs = VideoPreGenerationDependencyInputs(project=loaded, target_shot_id="drama.shot.waiting-room.001", target_asset_role="final_visual",
        requirement_hash=exact["requirement"].requirement_hash, planning_request_hash=exact["request"].request_content_hash,
        verified_projection_hash=exact["projection"].projection_hash)
    graph = build_video_pre_generation_dependency_graph(inputs)
    resolution = resolve_dependency_state(graph, build_video_pre_generation_applied_evidence(inputs))
    if resolution.ready_node_ids != (generation_target_node_id(inputs.target_shot_id, inputs.target_asset_role),):
        raise RuntimeError("target is not unique ready frontier")
    transition = prepare_dependency_graph_transition(expected_manifest_revision=m.manifest_revision,
        base_dependency_graph=m.active_dependency_graph, candidate_graph=graph, candidate_dependency_states=resolution.states,
        expected_desired_fingerprints=desired_fingerprints(graph))
    c = ProductionStateCommitter(root)
    graph_bytes = (json.dumps(graph.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
    artifacts = tuple(c.prepare_artifact(ATTEMPT, path, data) for path, data in (
        (m.active_project.path, (root / m.active_project.path).read_bytes()),
        (m.active_registry.path, (root / m.active_registry.path).read_bytes()),
        (transition.candidate_dependency_graph.path, graph_bytes)))
    request = StateCommitRequest(attempt_id=ATTEMPT, operation="commit_project_registry", expected_manifest_revision=m.manifest_revision,
        artifacts=artifacts, next_project=m.active_project, next_registry=m.active_registry, dependency_graph_transition=transition)
    return loaded, graph, request, c


def request_identity(routed):
    return {"provider_bound_request_hash": routed["provider_bound"].provider_bound_request_hash,
        "compiled_request_hash": routed["compiled"].compiled_request_hash,
        "request_input_hash": routed["request"].request_input_hash,
        "resolved_generation_hash": routed["resolved"].resolved_generation_hash,
        "preview_fingerprint": routed["preview"].preview_fingerprint}


def transition_and_verify(root, ctx, *, rehearsal, expected=None):
    d, h, source, timing, readiness, exact, inventory, lineage = ctx
    from ai_video.production.video_pre_generation import verify_current_video_generation_lineage
    before_tree = source._tree_snapshot(root)
    before, graph, request, committer = prepare(root, exact)
    d.require(before.manifest.active_dependency_graph.content_hash == "761c92a0a8507ae2b8f14de5338b337e0d567e78b654e36403d3428a0da47ff1", "unexpected base graph")
    try:
        verify_current_video_generation_lineage(before, exact["routed"]["resolved"])
    except ValueError as exc:
        d.require(str(exc) == "video request does not match the active generation target", "unexpected old request rejection")
    else:
        raise RuntimeError("expected historical lineage mismatch absent")
    d.require(h.committed_snapshot() == inventory and d.creative_lineage(h) == lineage, "source/creative drift before transition")
    d.require(source._load_policy()[1] == exact["source_audio_policy"]["identity"], "audio identity drift before transition")
    if not rehearsal:
        d.require(expected is not None, "live transition requires exact candidate seal")
        candidate_identity = {"graph_pointer": request.dependency_graph_transition.candidate_dependency_graph.model_dump(mode="json"),
            "source_commit": SOURCE_COMMIT, "driver_sha256": d.sha(Path(__file__).read_bytes()),
            "creative_lineage": lineage, "source_audio_policy": exact["source_audio_policy"],
            "prompt_sha256": exact["prompt"].prompt_sha256, "requirement_hash": exact["requirement"].requirement_hash,
            "planning_request_hash": exact["request"].request_content_hash, "verified_projection_hash": exact["projection"].projection_hash,
            "before_manifest_revision": before.manifest.manifest_revision,
            "before_tree_sha256": d.sha(h.canonical(before_tree))}
        d.require(all(value == expected[key] for key, value in candidate_identity.items()), "candidate identity drift before commit")
        d.require(source._tree_snapshot(root) == before_tree, "Production changed during live preparation")
    committed = committer.commit(request)
    reopened = timing.load_production_project(root / "project.yaml")
    d.require(reopened.manifest == committed and reopened.dependency_graph == graph, "graph reopen mismatch")
    d.require(committed.schema_version == before.manifest.schema_version == "2.7", "schema changed")
    d.require(committed.active_project == before.manifest.active_project and committed.active_registry == before.manifest.active_registry, "Project/Registry changed")
    d.require(committed.manifest_revision == before.manifest.manifest_revision + 2, "unexpected Manifest revision")
    after_tree = source._tree_snapshot(root)
    changed = sorted(path for path in set(before_tree) | set(after_tree) if before_tree.get(path) != after_tree.get(path))
    d.require(changed == sorted(["state/manifest.json", str(committed.active_dependency_graph.path)]), "unexpected durable bytes changed")
    routed = timing._route_compile_resolve_preview(readiness_driver=readiness, loaded=reopened, projection=exact["projection"])
    verify_current_video_generation_lineage(reopened, routed["resolved"])
    old_rejected = False
    try:
        verify_current_video_generation_lineage(reopened, exact["routed"]["resolved"])
    except ValueError:
        old_rejected = True
    d.require(old_rejected, "old graph-bound request unexpectedly accepted")
    result = {"schema_version": "drama-shot01-graph-lineage-rebind/1", "attempt_id": ATTEMPT,
        "source_commit": SOURCE_COMMIT, "driver_sha256": d.sha(Path(__file__).read_bytes()), "creative_lineage": lineage,
        "before_manifest_revision": before.manifest.manifest_revision, "after_manifest_revision": committed.manifest_revision,
        "schema_preserved": committed.schema_version, "project_registry_preserved": True,
        "before_tree_sha256": d.sha(h.canonical(before_tree)), "after_tree_sha256": d.sha(h.canonical(after_tree)),
        "changed_paths": changed, "graph_pointer": committed.active_dependency_graph.model_dump(mode="json"),
        "canonical_lineage_validator": "PASS", "old_graph_bound_request_rejected": old_rejected,
        "new_request_identity": request_identity(routed), "prompt_sha256": exact["prompt"].prompt_sha256,
        "source_audio_policy": exact["source_audio_policy"],
        "planning_request_hash": exact["request"].request_content_hash, "requirement_hash": exact["requirement"].requirement_hash,
        "verified_projection_hash": exact["projection"].projection_hash, "provider_submit": 0, "media": 0,
        "candidate_activation": False, "m6_d": "NOT_EVALUATED", "next_shot_submit_allowed": False}
    if rehearsal:
        committer.commit(request)
        d.require(source._tree_snapshot(root) == after_tree, "graph replay wrote bytes")
        committer.begin_video_generation(attempt_id="isolated-readiness-proof-only", request=routed["resolved"])
        result["isolated_canonical_start"] = "PASS_REQUEST_PERSISTENCE_ONLY_NO_SUBMIT"
        result["exact_transition_replay"] = "ZERO_BYTE_CHANGE"
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply-approved-sha256")
    args = parser.parse_args()
    marker = RUN / f"evidence/{ATTEMPT}-invoked.json"
    if args.apply_approved_sha256 and marker.exists():
        print(json.dumps({"decision": "REPLAY_DENIED", "attempt_id": ATTEMPT}), flush=True)
        raise SystemExit(1)
    ctx = context()
    d, h, source, *_ = ctx
    before = source._tree_snapshot(source.PROJECT_ROOT)
    if args.apply_approved_sha256:
        data = APPROVAL.read_bytes()
        d.require(d.sha(data) == args.apply_approved_sha256, "approval bytes drift")
        approval = json.loads(data)
        d.require(approval["decision"] == "ACCEPT_CANONICAL_GRAPH_ONLY_TRANSITION", "wrong approval")
        d.require(approval["driver_sha256"] == d.sha(Path(__file__).read_bytes()), "driver drift")
        evidence_bytes = EVIDENCE.read_bytes()
        d.require(approval["rehearsal_sha256"] == d.sha(evidence_bytes), "rehearsal drift")
        expected = json.loads(evidence_bytes)
        d.require(expected["before_tree_sha256"] == d.sha(h.canonical(before)), "Production drift")
        d.require(ctx[5]["source_audio_policy"] == expected["source_audio_policy"], "rehearsal audio identity drift")
        # Recompute through the real loader/committer in an isolated copy. No
        # fabricated LoadedProductionProject or patched VideoGenerationRequest.
        with tempfile.TemporaryDirectory(prefix="drama-graph-prewrite-") as temporary:
            target = Path(temporary) / "project"
            shutil.copytree(source.PROJECT_ROOT, target)
            prewrite = transition_and_verify(target, ctx, rehearsal=True)
        identity_keys = ("attempt_id", "source_commit", "driver_sha256", "creative_lineage", "source_audio_policy",
            "before_manifest_revision", "after_manifest_revision", "schema_preserved", "before_tree_sha256",
            "graph_pointer", "new_request_identity", "prompt_sha256", "planning_request_hash", "requirement_hash",
            "verified_projection_hash", "changed_paths", "canonical_lineage_validator", "old_graph_bound_request_rejected")
        d.require(all(prewrite[key] == expected[key] for key in identity_keys), "prewrite/rehearsal identity drift")
        d.require(source._tree_snapshot(source.PROJECT_ROOT) == before, "Production drift during prewrite proof")
        d.write_new(marker, {"approval_sha256": args.apply_approved_sha256})
        try:
            result = transition_and_verify(source.PROJECT_ROOT, ctx, rehearsal=False, expected=expected)
            for key in ("graph_pointer", "new_request_identity", "prompt_sha256", "changed_paths", "source_audio_policy"):
                d.require(result[key] == expected[key], f"live/rehearsal mismatch: {key}")
            d.write_new(RUN / f"evidence/{ATTEMPT}-committed.json", result)
        except BaseException as exc:
            # Observation only: never recover, retry or write Production state here.
            outcome = "OUTCOME_UNKNOWN_EXPLICIT_RECOVERY_REQUIRED"
            observed = {}
            try:
                after = source._tree_snapshot(source.PROJECT_ROOT)
                reopened = ctx[3].load_production_project(source.PROJECT_ROOT / "project.yaml")
                observed = {"tree_sha256": d.sha(h.canonical(after)), "manifest_revision": reopened.manifest.manifest_revision,
                    "active_graph": reopened.manifest.active_dependency_graph.model_dump(mode="json")}
                code = str(getattr(exc, "code", ""))
                if "OUTCOME_UNKNOWN" not in code:
                    if after == before:
                        outcome = "KNOWN_NO_PRODUCTION_BYTE_CHANGE"
                    elif observed["active_graph"] == expected["graph_pointer"]:
                        outcome = "GRAPH_SELECTED_POSTCHECK_INCOMPLETE_EXPLICIT_REVIEW_REQUIRED"
            except Exception:
                pass
            d.write_new(RUN / f"evidence/{ATTEMPT}-stopped.json", {"attempt_id": ATTEMPT,
                "error_type": type(exc).__name__, "reason": getattr(exc, "user_message", "Graph transition stopped; inspect exact checkpoint."),
                "outcome": outcome, "observation": observed, "retry_allowed": False, "provider_submit": 0})
            raise SystemExit(1) from None
        print(json.dumps(result), flush=True)
    else:
        d.require(not EVIDENCE.exists(), "immutable rehearsal exists")
        with tempfile.TemporaryDirectory(prefix="drama-graph-rehearsal-") as temporary:
            target = Path(temporary) / "project"
            shutil.copytree(source.PROJECT_ROOT, target)
            result = transition_and_verify(target, ctx, rehearsal=True)
        d.require(source._tree_snapshot(source.PROJECT_ROOT) == before, "canonical Production changed during rehearsal")
        result["canonical_production_unchanged"] = True
        d.write_new(EVIDENCE, result)
        print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
