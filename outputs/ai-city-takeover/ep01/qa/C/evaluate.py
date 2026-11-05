"""Prepare or explicitly record C's exact raw analyzer feedback; no Provider I/O."""
from __future__ import annotations

import argparse
import asyncio
from functools import partial
import hashlib
import json
from pathlib import Path
import re
from types import SimpleNamespace

from ai_video.production.generation_evaluation import GenerationEvaluationSource, GenerationObservation
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import ToolIdentity
from ai_video.production.production_strategy_reader import selected_shot_generation_acceptance
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video_mcp.generation_feedback import ControlledPresentationVerifier, review_generation_attempt


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1] / "generation-c-draft/project"
ATTEMPT = "iris-ep01-c-source-003"
SHOT = "ep01-dns"
SHA = "974e83c050dd7cc079e6dabdf2ea3b168629d02fffc02cf8163c7881c4968f15"
SIZE = 12706989
QA_SHA = "b0dbc8e38b2fa0955a613cc33240dafbb7ff69221b6229b95d7ce08d5bb5cacd"
RUBRIC_SHA = "104bc2f01bf0963eceb0375f2e8a84c5c4dd95a166d7edbf88e638728bcdfe58"
REQUIRED = {"identity", "observer", "camera", "monitor-back"}
ACTOR = ToolIdentity(name="video-analysis", version="project-local")


def current_scope():
    loaded = load_production_project(PROJECT / "project.yaml")
    acceptance = selected_shot_generation_acceptance(loaded, SHOT)
    if (loaded.qa_policy.content_hash != QA_SHA or acceptance is None
            or acceptance.profile_content_hash != RUBRIC_SHA
            or set(acceptance.required_requirement_ids) != REQUIRED
            or not any(a.evaluator == ACTOR and a.proof == "analyzer"
                for a in loaded.qa_policy.generation_evaluation_authorities)):
        raise ValueError("Current C QA or its selected authority differs from this evaluator scope")
    attempt = next(a for a in loaded.manifest.attempts if a.attempt_id == ATTEMPT)
    fetch = attempt.video_generation_state.fetch_receipt
    if (attempt.status.value != "running" or attempt.video_generation_state.phase.value != "validate"
            or fetch is None or fetch.artifact_sha256 != SHA):
        raise ValueError("Expected C's exact running fetched qualification attempt")
    return loaded, attempt


def observer_evidence(expected_sha):
    if not isinstance(expected_sha, str) or re.fullmatch(r"[0-9a-f]{64}", expected_sha) is None:
        raise ValueError("Recording requires Parent's exact adopted observation SHA")
    directory = HERE / "observer-verification"
    raw = (directory / "observations.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ValueError("Observer report differs from Parent's adopted exact evidence")
    document = json.loads(raw)
    if (document["shot_id"] != SHOT or document["source_sha256"] != SHA or document["source_size_bytes"] != SIZE
            or document["qa_policy_hash"] != QA_SHA
            or document["acceptance_profile_hash"] != RUBRIC_SHA
            or set(document["required_requirement_ids"]) != REQUIRED):
        raise ValueError("Observer report identifies different C media or QA")
    index = json.loads((directory / "evidence-sha256.json").read_bytes())
    if index.get("observations.json") != expected_sha:
        raise ValueError("Evidence index does not identify the adopted observer report")
    for name, digest in index.items():
        path = (directory / name).resolve(strict=True)
        if not path.is_relative_to(directory.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError("Observer evidence bytes changed")
    for reference in document["references"]:
        if hashlib.sha256((HERE.parents[4] / reference["path"]).read_bytes()).hexdigest() != reference["sha256"]:
            raise ValueError("Observer reference bytes changed")
    # C's report separately lists the original MCP responses one directory up;
    # these are exact, whitelisted archived sources, not arbitrary path traversal.
    originals = document["original_project_mcp_evidence"]
    if {item["path"] for item in originals} != {"../mcp-analysis.json", "../mcp-review.json"}:
        raise ValueError("C report must retain its two original MCP responses")
    for item in originals:
        if hashlib.sha256((directory / item["path"]).read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("C's original MCP evidence changed")
        index[item["path"]] = item["sha256"]
    preceding = document["preceding_accepted_gate"]
    preceding_path = HERE.parents[4] / preceding["path"]
    if (hashlib.sha256(preceding_path.read_bytes()).hexdigest() != preceding["sha256"]
            or preceding["verdict"] != "PASS" or json.loads(preceding_path.read_bytes())["verdict"] != "PASS"):
        raise ValueError("C's preceding accepted raw Gate identity changed")
    playback = json.loads((directory / "normal-speed-playback.json").read_bytes())
    quality = playback["quality"]
    if (playback["source_sha256"] != SHA or playback["playbackRate"] != 1
            or not playback["ended"] or playback["error"] is not None
            or quality["totalVideoFrames"] <= 0
            or quality["totalVideoFrames"] != document["video_timing"]["decoded_frame_count"]
            or quality["droppedVideoFrames"] != 0 or quality["corruptedVideoFrames"] != 0):
        raise ValueError("C's exact normal-speed playback evidence is incomplete")
    findings = {item["requirement_id"]: item for item in document["findings"]}
    if set(findings) != REQUIRED or len(document["findings"]) != len(REQUIRED):
        raise ValueError("C needs its own four findings, including monitor-back")
    for finding in findings.values():
        if (finding["verdict"] not in {"PASS", "FAIL", "NOT_EVALUATED"}
                or not finding["reason"].strip() or not finding["evidence_refs"]
                or any(name not in index for name in finding["evidence_refs"])):
            raise ValueError("C finding lacks a real verdict or hashed observation evidence")
    return document, findings, index


class ArchivedActualMCP:
    async def call_tool(self, name, arguments):
        if (name != "video_analyze" or arguments.get("transcribe_audio") is not False
                or arguments.get("understand_audio", False)):
            raise ValueError("Only the archived exact visual MCP analysis is available")
        response = json.loads((HERE / "mcp-analysis.json").read_bytes())
        payload = response.get("structuredContent")
        if payload is None:
            payload = json.loads(next(c["text"] for c in response["content"] if c["type"] == "text"))
        if (payload["video_path"] != arguments["video_path"]
                or payload["probe"]["file"]["size_bytes"] != SIZE
                or hashlib.sha256(Path(arguments["video_path"]).read_bytes()).hexdigest() != SHA):
            raise ValueError("Archived MCP source differs from the exact C artifact")
        return SimpleNamespace(model_dump=lambda **_: response)


def judge(context, *, observer_sha):
    document, findings, _index = observer_evidence(observer_sha)
    items = context.evaluation_items
    if (context.request is not None or context.projection is not None or context.recipe is not None
            or {item.requirement_id for item in items} != REQUIRED
            or context.qa_policy.content_hash != document["qa_policy_hash"]):
        raise ValueError("Use C's actual controlled QA questions, not A01's findings")
    observations = []
    for item in items:
        if (item.artifact_sha256 != SHA or item.size_bytes != SIZE
                or item.rubric_hash != RUBRIC_SHA or item.proof != "analyzer"
                or item.observable != document["sealed_observables"][item.requirement_id]):
            raise ValueError("Presented criterion identifies different C evidence")
        finding = findings[item.requirement_id]
        detail = json.dumps(finding.get("subfindings", []), ensure_ascii=False, separators=(",", ":"))
        reason = (f"按[{item.requirement_id}] {finding['reason']} Evidence: "
            f"observer-verification/observations.json SHA256={observer_sha}; subfindings={detail}")
        observations.append(GenerationObservation(requirement_id=item.requirement_id,
            verdict=finding["verdict"], observation=reason, span_millis=tuple(finding["span_millis"]),
            evaluation_item_hash=item.evaluation_item_hash, question_text=item.question_text,
            presentation_ref=context.presentation_ref, answer_ref=context.answer_ref))
    first = items[0]
    return (GenerationEvaluationSource(schema_version="generation-evaluation/2",
        request_hash=first.request_hash, artifact_sha256=SHA, rubric_hash=first.rubric_hash,
        qa_policy_content_hash=context.qa_policy.content_hash, evaluator=ACTOR, proof="analyzer",
        observations=tuple(observations), analysis_evidence=context.analysis,
        size_bytes=SIZE, qa_policy_snapshot=context.qa_policy),)


def write_once(name, document):
    with (HERE / name).open("x", encoding="utf-8") as handle:
        json.dump(document, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


async def record(observer_sha):
    observer, findings, evidence = observer_evidence(observer_sha)
    loaded, attempt = current_scope()
    if loaded.project.revision != observer["project_revision"]:
        raise ValueError("Observer project revision is stale")
    for name in ("canonical-diagnosis.json", "post-media-gate.json", "evaluation-validation.json"):
        if (HERE / name).exists():
            raise ValueError("C feedback outputs exist; inspect exact replay instead of overwriting")
    paid_before = canonical_sha256(attempt.paid_provider_state.model_dump(mode="json"))
    fetch = attempt.video_generation_state.fetch_receipt
    committer = ProductionStateCommitter(PROJECT)
    adjudicate = partial(judge, observer_sha=observer_sha)
    verifier = ControlledPresentationVerifier(evaluator=ACTOR, proof="analyzer", adjudicate=adjudicate)
    diagnosis = await review_generation_attempt(committer=committer, attempt_id=ATTEMPT,
        session=ArchivedActualMCP(), adjudicate=adjudicate,
        presentation_verifier=verifier, understand_audio=False)
    verdict = "PASS" if diagnosis.all_required_observed_pass else "FAIL" if diagnosis.failed_requirements else "NOT_EVALUATED"
    write_once("canonical-diagnosis.json", diagnosis.model_dump(mode="json"))
    write_once("post-media-gate.json", {"shot_id": SHOT, "attempt_id": ATTEMPT,
        "artifact_path": str(PROJECT / fetch.artifact_path), "artifact_sha256": SHA,
        "verdict": verdict, "proof": "analyzer",
        "all_required_observed_pass": diagnosis.all_required_observed_pass,
        "required_findings": list(findings.values()), "observer_observations_sha256": observer_sha,
        "observer_evidence_sha256": evidence, "human_acceptance": "NOT_EVALUATED",
        "audio_semantics_or_listening": "NOT_EVALUATED", "production_activation": False,
        "provider_qualification_promotion": False, "next_shot_preparation_allowed": verdict == "PASS",
        "next_shot_submit_authorized": False, "new_provider_calls": 0})
    reopened = load_production_project(PROJECT / "project.yaml")
    after = next(a for a in reopened.manifest.attempts if a.attempt_id == ATTEMPT)
    if (after.video_generation_state.fetch_receipt != fetch
            or canonical_sha256(after.paid_provider_state.model_dump(mode="json")) != paid_before
            or reopened.project.content_hash != loaded.project.content_hash):
        raise ValueError("C feedback changed fetched source, paid history or authored project")
    class NoCalls:
        async def call_tool(self, *_args, **_kwargs):
            raise AssertionError("Exact C replay requested a new MCP call")
    replay = await review_generation_attempt(committer=committer, attempt_id=ATTEMPT,
        session=NoCalls(), adjudicate=None, understand_audio=False)
    final = load_production_project(PROJECT / "project.yaml")
    if replay != diagnosis or final.manifest.manifest_revision != reopened.manifest.manifest_revision:
        raise ValueError("C feedback replay changed diagnosis or Manifest")
    write_once("evaluation-validation.json", {"raw_analyzer_gate": verdict,
        "manifest_revision_before": loaded.manifest.manifest_revision,
        "manifest_revision_after": final.manifest.manifest_revision,
        "canonical_reader": "PASS", "controlled_marked_2_evaluation": "PASS",
        "observer_evidence_index": "PASS", "paid_and_source_history_unchanged": True,
        "exact_replay_no_new_mcp_calls": True, "exact_replay_manifest_unchanged": True,
        "human_acceptance": "NOT_EVALUATED", "production_activation": False, "new_provider_calls": 0})
    print(json.dumps({"raw_analyzer_gate": verdict,
        "all_required_observed_pass": diagnosis.all_required_observed_pass,
        "manifest_revision_before": loaded.manifest.manifest_revision,
        "manifest_revision_after": final.manifest.manifest_revision}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", action="store_true", help="Run only after Parent adopts actual observations and authorizes recording")
    parser.add_argument("--observer-sha256", help="Exact Parent-adopted observations.json SHA256")
    arguments = parser.parse_args()
    if arguments.record:
        asyncio.run(record(arguments.observer_sha256))
    else:
        loaded, attempt = current_scope()
        print(json.dumps({"mode": "read_only_inspection", "shot_id": SHOT, "attempt_id": ATTEMPT,
            "source_sha256": SHA, "required_requirement_ids": sorted(REQUIRED),
            "qa_policy_sha256": QA_SHA, "manifest_revision": loaded.manifest.manifest_revision,
            "canonical_writes": 0, "new_provider_calls": 0,
            "recording_requires": "Parent-adopted exact observer SHA and separate explicit record authorization"}, ensure_ascii=False))
