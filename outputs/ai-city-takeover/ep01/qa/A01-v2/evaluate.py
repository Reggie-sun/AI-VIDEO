"""Record exact A01-v2 raw analyzer evidence through existing feedback owners."""
from __future__ import annotations

import asyncio
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from ai_video.production.generation_evaluation import (
    GenerationEvaluationSource, GenerationObservation,
)
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import ToolIdentity
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video_mcp.generation_feedback import (
    ControlledPresentationVerifier, review_generation_attempt,
)


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1] / "a01-first-frame-repair/project"
OLD_PROJECT = HERE.parents[1] / "generation/project"
ATTEMPT = "iris-ep01-a01-two-reference-repair-002"
SHA = "850b3807757e570dc59c2a6af96fcf930d8689322408e11f1be81db2c5adae1c"
OBSERVATION_SHA = "667fa77bf5d672434cf8e2da3b77e8c1a8f04e96b4fd01d10ee38cccbbbe7780"
REQUIRED = {"identity", "quiet-observer", "camera-space", "visual"}
ACTOR = ToolIdentity(name="video-analysis", version="project-local")


def write_once(name, document):
    with (HERE / name).open("x", encoding="utf-8") as handle:
        json.dump(document, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def observer_evidence():
    directory = HERE / "observer-verification"
    raw = (directory / "observations.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != OBSERVATION_SHA:
        raise ValueError("Observer observations differ from Parent's adopted exact evidence")
    document = json.loads(raw)
    if (document["source_sha256"] != SHA or document["source_size_bytes"] != 15395561
            or set(document["required_requirement_ids"]) != REQUIRED
            or document["video_timing"]["decoded_frames"] != 145):
        raise ValueError("Observer evidence identifies different source media or criteria")
    index = json.loads((directory / "evidence-sha256.json").read_bytes())
    for name, expected in index.items():
        path = (directory / name).resolve(strict=True)
        if not path.is_relative_to(directory.resolve()) or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("Observer evidence bytes changed")
    for reference in document["references"]:
        if hashlib.sha256((HERE.parents[4] / reference["path"]).read_bytes()).hexdigest() != reference["sha256"]:
            raise ValueError("Approved source reference changed")
    playback = json.loads((directory / "normal-speed-playback.json").read_bytes())
    if (playback["source_sha256"] != SHA or playback["playbackRate"] != 1
            or not playback["ended"] or playback["error"] is not None
            or playback["quality"] != {"totalVideoFrames": 145,
                "droppedVideoFrames": 0, "corruptedVideoFrames": 0}):
        raise ValueError("Exact normal-speed playback evidence is incomplete")
    correction = json.loads((directory / "scope-correction.json").read_bytes())
    if (correction["unchanged_media_sha256"] != SHA
            or correction["unchanged_qa_policy_hash"] != document["qa_policy_hash"]
            or not correction["no_media_edit"] or not correction["no_qa_policy_edit"]
            or index[correction["initial_report_archive"]] != correction["initial_archive_sha256"]):
        raise ValueError("Scope correction lost its exact original evidence or unchanged QA")
    findings = {item["requirement_id"]: item for item in document["findings"]}
    if set(findings) != REQUIRED or any(item["verdict"] != "PASS" for item in findings.values()):
        raise ValueError("Observer evidence is not the four Parent-adopted PASS findings")
    for item in findings.values():
        if any(name not in index for name in item["evidence_refs"]):
            raise ValueError("Finding cites unhashed observer evidence")
    return document, findings, index


class ArchivedActualMCP:
    async def call_tool(self, name, arguments):
        if (name != "video_analyze" or arguments.get("transcribe_audio") is not False
                or arguments.get("understand_audio", False)):
            raise ValueError("Only the exact archived visual MCP analysis is available")
        response = json.loads((HERE / "mcp-analysis.json").read_bytes())
        payload = response.get("structuredContent")
        if payload is None:
            payload = json.loads(next(c["text"] for c in response["content"] if c["type"] == "text"))
        if (payload["video_path"] != arguments["video_path"]
                or payload["probe"]["file"]["size_bytes"] != 15395561
                or hashlib.sha256(Path(arguments["video_path"]).read_bytes()).hexdigest() != SHA):
            raise ValueError("Archived MCP source differs from the fetched exact artifact")
        return SimpleNamespace(model_dump=lambda **_: response)


def judge(context):
    document, findings, index = observer_evidence()
    items = context.evaluation_items
    if (context.request is not None or context.projection is not None or context.recipe is not None
            or {item.requirement_id for item in items} != REQUIRED
            or context.qa_policy.content_hash != document["qa_policy_hash"]):
        raise ValueError("Use current controlled criterion presentation, not an old draft")
    observations = []
    for item in items:
        if (item.artifact_sha256 != SHA or item.size_bytes != 15395561 or item.proof != "analyzer"
                or item.rubric_hash != document["acceptance_profile_hash"]):
            raise ValueError("Presented QA item identifies different evidence or scope")
        finding = findings[item.requirement_id]
        detail = json.dumps({key: finding[key] for key in ("subfindings", "unclaimed_auxiliary_inference")
            if key in finding}, ensure_ascii=False, separators=(",", ":"))
        reason = (f"按[{item.requirement_id}] {finding['reason']} "
            f"Evidence: observer-verification/observations.json SHA256={OBSERVATION_SHA}; "
            f"scope-correction.json SHA256={index['scope-correction.json']}; details={detail}")
        observations.append(GenerationObservation(requirement_id=item.requirement_id,
            verdict=finding["verdict"], observation=reason, span_millis=tuple(finding["span_millis"]),
            evaluation_item_hash=item.evaluation_item_hash, question_text=item.question_text,
            presentation_ref=context.presentation_ref, answer_ref=context.answer_ref))
    first = items[0]
    return (GenerationEvaluationSource(schema_version="generation-evaluation/2",
        request_hash=first.request_hash, artifact_sha256=SHA, rubric_hash=first.rubric_hash,
        qa_policy_content_hash=context.qa_policy.content_hash, evaluator=ACTOR, proof="analyzer",
        observations=tuple(observations), analysis_evidence=context.analysis,
        size_bytes=first.size_bytes, qa_policy_snapshot=context.qa_policy),)


async def main():
    for name in ("canonical-diagnosis.json", "post-media-gate.json", "evaluation-validation.json"):
        if (HERE / name).exists():
            raise ValueError("Review outputs already exist; inspect exact replay instead of overwriting")
    observer, findings, evidence = observer_evidence()
    loaded = load_production_project(PROJECT / "project.yaml")
    if (loaded.project.revision != observer["project_revision"]
            or loaded.qa_policy.content_hash != observer["qa_policy_hash"]
            or not any(a.evaluator == ACTOR and a.proof == "analyzer"
                for a in loaded.qa_policy.generation_evaluation_authorities)):
        raise ValueError("Current project and selected evaluator differ from the observed scope")
    attempt = next(a for a in loaded.manifest.attempts if a.attempt_id == ATTEMPT)
    if attempt.status.value != "running" or attempt.video_generation_state.phase.value != "validate":
        raise ValueError("Expected the exact fetched qualification attempt")
    fetch = attempt.video_generation_state.fetch_receipt
    if fetch is None or fetch.artifact_sha256 != SHA:
        raise ValueError("Exact fetched A01-v2 is missing")
    paid_before = canonical_sha256(attempt.paid_provider_state.model_dump(mode="json"))
    old_before = canonical_sha256(load_production_project(OLD_PROJECT / "project.yaml").manifest)
    committer = ProductionStateCommitter(PROJECT)
    verifier = ControlledPresentationVerifier(evaluator=ACTOR, proof="analyzer", adjudicate=judge)
    diagnosis = await review_generation_attempt(committer=committer, attempt_id=ATTEMPT,
        session=ArchivedActualMCP(), adjudicate=judge, presentation_verifier=verifier,
        understand_audio=False)
    if not diagnosis.all_required_observed_pass or diagnosis.failure_classes or diagnosis.failed_requirements:
        raise ValueError("Canonical diagnosis did not confirm all four raw analyzer findings")
    write_once("canonical-diagnosis.json", diagnosis.model_dump(mode="json"))
    write_once("post-media-gate.json", {"shot_id": "ep01-intro", "attempt_id": ATTEMPT,
        "artifact_path": str(PROJECT / fetch.artifact_path), "artifact_sha256": SHA,
        "verdict": "PASS", "proof": "analyzer", "all_required_observed_pass": True,
        "required_findings": [{**finding, "proof": "analyzer",
            "evidence_ref": "observer-verification/observations.json"} for finding in findings.values()],
        "observer_observations_sha256": OBSERVATION_SHA,
        "scope_correction": {"path": "observer-verification/scope-correction.json",
            "sha256": evidence["scope-correction.json"], "criteria_unchanged": True},
        "human_acceptance": "NOT_EVALUATED", "audio_semantics_or_listening": "NOT_EVALUATED",
        "production_activation": False, "provider_qualification_promotion": False,
        "next_shot_preparation_allowed": True, "next_shot_submit_authorized": False,
        "next_shot_requires": "Its own exact preview, budget, intent and one-use permit.",
        "new_provider_calls": 0})
    reopened = load_production_project(PROJECT / "project.yaml")
    after = next(a for a in reopened.manifest.attempts if a.attempt_id == ATTEMPT)
    if (after.video_generation_state.fetch_receipt != fetch
            or canonical_sha256(after.paid_provider_state.model_dump(mode="json")) != paid_before
            or canonical_sha256(load_production_project(OLD_PROJECT / "project.yaml").manifest) != old_before):
        raise ValueError("Feedback changed source, paid state or the failed v1 history")
    class NoCalls:
        async def call_tool(self, *_args, **_kwargs):
            raise AssertionError("Exact feedback replay requested a new MCP call")
    replay = await review_generation_attempt(committer=committer, attempt_id=ATTEMPT,
        session=NoCalls(), adjudicate=None, understand_audio=False)
    final = load_production_project(PROJECT / "project.yaml")
    if replay != diagnosis or final.manifest.manifest_revision != reopened.manifest.manifest_revision:
        raise ValueError("Canonical feedback replay changed diagnosis or Manifest")
    write_once("evaluation-validation.json", {"raw_analyzer_gate": "PASS",
        "manifest_revision_before": loaded.manifest.manifest_revision,
        "manifest_revision_after": final.manifest.manifest_revision,
        "canonical_reader": "PASS", "controlled_marked_2_evaluation": "PASS",
        "observer_evidence_index": "PASS", "scope_correction_retained": True,
        "paid_and_source_history_unchanged": True, "failed_v1_history_unchanged": True,
        "exact_replay_no_new_mcp_calls": True, "exact_replay_manifest_unchanged": True,
        "human_acceptance": "NOT_EVALUATED", "production_activation": False,
        "new_provider_calls": 0})
    print(json.dumps({"raw_analyzer_gate": "PASS", "all_required_observed_pass": True,
        "manifest_revision_before": loaded.manifest.manifest_revision,
        "manifest_revision_after": final.manifest.manifest_revision,
        "next_shot_preparation_allowed": True, "next_shot_submit_authorized": False}, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
