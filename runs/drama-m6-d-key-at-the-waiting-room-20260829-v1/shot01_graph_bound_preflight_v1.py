"""Capture current canonical authoring-reopen blocker; never bypass or submit."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = Path(__file__).resolve().parent
OUTPUT = RUN / "evidence/drama-shot01-graph-bound-preflight-v1.blocked.json"
GRAPH_DRIVER_SHA = "51c281dae9f5e785a1c28f0d23039650fe1412efbfc3d512de8def8b6e432df0"
COMMITTED_SHA = "2021fa28f0df82fde878f4316c879aa2486a33797f49300702e7092f53730b1c"


def load(name, path, expected):
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise RuntimeError("sealed driver identity drift")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    if OUTPUT.exists():
        raise SystemExit("immutable blocker evidence already exists")
    graph = load("blocked_graph_parent", RUN / "shot01_graph_lineage_rebind_v1.py", GRAPH_DRIVER_SHA)
    d = load("blocked_first_parent", RUN / "shot01_first_submit_v1.py",
             "e708c4ac4dcfa840a448edd794fda9155dcbada982e18ab1800abd8442a200df")
    h = d.load_helper()
    h.SOURCE_COMMIT = graph.SOURCE_COMMIT
    inventory = h.committed_snapshot()
    source = h.load("blocked_source", "shot01_source_audio_policy_readiness_driver.py")
    timing = h.load("blocked_timing", "shot01_timing_request_readiness_driver.py")
    committed = h.sealed(RUN / "evidence/drama-shot01-graph-lineage-20260905-v1-committed.json", COMMITTED_SHA)
    before = source._tree_snapshot(source.PROJECT_ROOT)
    d.require(d.sha(h.canonical(before)) == committed["after_tree_sha256"], "committed Production tree drift")
    loaded = timing.load_production_project(source.PROJECT_ROOT / "project.yaml")
    d.require(loaded.manifest.active_dependency_graph.model_dump(mode="json") == committed["graph_pointer"], "selected graph drift")
    expected_reason = ("execution-intent source binding drift: {'active_pre_generation_graph_hash': "
        "{'overlay': '761c92a0a8507ae2b8f14de5338b337e0d567e78b654e36403d3428a0da47ff1', "
        "'current': 'a95a916f26b53f4a2437d90860a13910fa458e33735507963148360062e8742a'}}")
    try:
        graph.context()
    except RuntimeError as exc:
        d.require(str(exc) == expected_reason, "different reopen failure; no classified blocker evidence")
    else:
        raise RuntimeError("historical binding rejection no longer reproduced; reassess, do not submit")
    d.require(h.committed_snapshot() == inventory, "source drift during observation")
    d.require(source._tree_snapshot(source.PROJECT_ROOT) == before, "Production changed during observation")
    result = {
        "schema_version": "drama-shot01-graph-bound-preflight-blocker/1",
        "decision": "STOP_BEFORE_SUBMIT",
        "blocker": "EXECUTION_INTENT_SOURCE_BINDING_NOT_SUPERSEDED_FOR_ACTIVE_GRAPH",
        "driver_sha256": d.sha(Path(__file__).read_bytes()),
        "source_commit": graph.SOURCE_COMMIT,
        "graph_commit_evidence_sha256": COMMITTED_SHA,
        "source_inventory_sha256": d.sha(h.canonical(inventory)),
        "failed_seam": "authoring_to_request_driver._assert_source_binding",
        "expected_overlay_graph": "761c92a0a8507ae2b8f14de5338b337e0d567e78b654e36403d3428a0da47ff1",
        "current_graph_pointer": committed["graph_pointer"],
        "manifest_revision": loaded.manifest.manifest_revision,
        "new_graph_request_from_transition_evidence": committed["new_request_identity"],
        "fresh_full_request_reopen": "NOT_COMPLETED",
        "fresh_runtime_provider_preflight": "NOT_INVOKED",
        "production_tree_sha256_before": d.sha(h.canonical(before)),
        "production_tree_sha256_after": d.sha(h.canonical(before)),
        "production_writes": 0, "request_persistence": 0, "permit_mint": 0,
        "provider_submit": 0, "provider_http": 0, "runtime_lifecycle": 0,
        "media": 0, "video_analysis": 0, "retry_allowed": False,
        "m6_d": "NOT_EVALUATED", "next_shot_submit_allowed": False,
        "required_owner": "Execution-intent/authoring version selection and source-binding supersession",
        "bypass_allowed": False,
    }
    d.write_new(OUTPUT, result)
    print(json.dumps({"path": str(OUTPUT.relative_to(ROOT)), "sha256": d.sha(OUTPUT.read_bytes()),
                      "decision": result["decision"], "blocker": result["blocker"]}), flush=True)


if __name__ == "__main__":
    main()
