"""Record Parent findings over the exact archived MCP response; no generation."""
from __future__ import annotations

import asyncio
import argparse
from functools import partial
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from ai_video.errors import ErrorCode
from ai_video.production.generation_evaluation import (
    GenerationEvaluationSource, GenerationObservation,
)
from ai_video.production.models import ActorIdentity, ToolIdentity
from ai_video.production.hashing import canonical_sha256
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video_mcp.generation_feedback import (
    ControlledPresentationVerifier, review_generation_attempt,
)


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1] / "generation/project"
ATTEMPT = "iris-ep01-a01-qualification-001"
SHA = "65f17d6860cbde39df398f42138149a7b4fc7a0bda7fdd96952b88134a0601d5"
ACTOR = ToolIdentity(name="video-analysis", version="project-local")
REJECTION_ACTOR = ActorIdentity(actor_id="codex-a01-quality-review", actor_kind="codex")
FINDINGS = {
    "identity": ("NOT_EVALUATED", "本次未完成脸部、左耳装置及左领灯线在所有时间片的逐项完整审查，不从参考图或工具成功推断身份通过。"),
    "quiet-observer": ("NOT_EVALUATED", "本次未完成正常速度的自然呼吸、轻微眨眼和闭口观察全项审看；不把静态联系图当作完整表演通过。"),
    "camera-space": ("FAIL", "按[camera-space]核对已认可 A01-v1.png 与本 exact MP4 的首段样本/contact-sheet.jpg：认可图是较正面的头胸中近景，实际样本明显更远、人物更侧身并露出肩背；起始景别和姿态未保持认可构图。仍为同一阳台且 MCP 报告单一场景不能抵消该偏差。"),
    "visual": ("FAIL", "按[visual]旧封存要求『不新增文字、屏幕或人物』核对：exact MP4 的已审样本左上可见平台『AI生成』标识。用户后续认可保留 AI 标识仅用于未来修订，不追改本次旧封存要求或本次失败历史。"),
}


def write_once(name, document):
    with (HERE / name).open("x", encoding="utf-8") as handle:
        json.dump(document, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def repaired_findings():
    """Reopen the independent same-bytes observations, not a new QA policy."""
    directory = HERE / "observer-verification"
    payload = (directory / "observations.json").read_bytes()
    observation = json.loads(payload)
    if (observation["source_sha256"] != SHA or observation["source_size_bytes"] != 10354579
            or observation["decoded_video_frame_count"] != 145):
        raise ValueError("Observer evidence identifies different media")
    playback = json.loads((directory / "normal-speed-playback.json").read_bytes())
    # Preserve the actual verifier file as evidence; its summary is separately
    # checked here without turning playback into human viewing or hearing.
    summary = observation["normal_speed_playback"]
    if (summary["playback_rate"] != 1 or summary["total_video_frames"] != 145
            or summary["dropped_frames"] != 0 or summary["corrupted_frames"] != 0
            or playback["source_sha256"] != SHA or playback["playbackRate"] != 1
            or not playback["ended"] or playback["error"] is not None
            or playback["quality"]["totalVideoFrames"] != 145
            or playback["quality"]["droppedVideoFrames"] != 0
            or playback["quality"]["corruptedVideoFrames"] != 0):
        raise ValueError("Normal-speed playback evidence is incomplete")
    actual = {item["requirement_id"]: item for item in observation["findings"]}
    if {key: item["verdict"] for key, item in actual.items()} != {
            "identity": "PASS", "quiet-observer": "FAIL"}:
        raise ValueError("Observer findings differ from Parent's adopted evidence repair")
    for reference in observation["references"]:
        path = HERE.parents[4] / reference["path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != reference["sha256"]:
            raise ValueError("Observer reference bytes changed")
    evidence = {"observations.json": hashlib.sha256(payload).hexdigest()}
    findings = dict(FINDINGS)
    for key, item in actual.items():
        for name in item["evidence_refs"]:
            path = (directory / name).resolve(strict=True)
            if not path.is_relative_to(directory.resolve()):
                raise ValueError("Observer evidence path escapes its directory")
            evidence[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        details = json.dumps(item.get("subfindings", []), ensure_ascii=False, separators=(",", ":"))
        reason = (f"按[{key}] {item['observation']} Evidence: observer-verification/observations.json "
                  f"SHA256={evidence['observations.json']}; subfindings={details}")
        findings[key] = (item["verdict"], reason)
    return findings, evidence


class ArchivedActualMCP:
    async def call_tool(self, name, arguments):
        if name != "video_analyze" or arguments.get("understand_audio", False):
            raise ValueError("Only the exact archived visual analysis is available")
        if arguments.get("transcribe_audio") is not False:
            raise ValueError("This review does not claim audio semantics")
        document = json.loads((HERE / "mcp-analysis.json").read_bytes())
        payload = document.get("structuredContent")
        if payload is None:
            payload = json.loads(next(c["text"] for c in document["content"] if c["type"] == "text"))
        if payload["video_path"] != arguments["video_path"]:
            raise ValueError("Archived MCP identifies different media")
        if hashlib.sha256(Path(arguments["video_path"]).read_bytes()).hexdigest() != SHA:
            raise ValueError("Exact fetched bytes changed")
        return SimpleNamespace(model_dump=lambda **_: document)


def judge(context, *, repaired=False):
    findings = repaired_findings()[0] if repaired else FINDINGS
    items = context.evaluation_items
    if {item.requirement_id for item in items} != set(findings):
        raise ValueError("Selected QA differs from this Parent adjudication")
    if context.request is not None or context.projection is not None or context.recipe is not None:
        raise ValueError("Use the controlled criterion presentation")
    observations = []
    for item in items:
        if item.artifact_sha256 != SHA or item.proof != "analyzer":
            raise ValueError("Presented criterion identifies different evidence")
        verdict, reason = findings[item.requirement_id]
        observations.append(GenerationObservation(requirement_id=item.requirement_id,
            verdict=verdict, observation=reason,
            evaluation_item_hash=item.evaluation_item_hash, question_text=item.question_text,
            presentation_ref=context.presentation_ref, answer_ref=context.answer_ref))
    first = items[0]
    return (GenerationEvaluationSource(schema_version="generation-evaluation/2",
        request_hash=first.request_hash, artifact_sha256=SHA,
        rubric_hash=first.rubric_hash, qa_policy_content_hash=context.qa_policy.content_hash,
        evaluator=ACTOR, proof="analyzer", observations=tuple(observations),
        analysis_evidence=context.analysis, size_bytes=first.size_bytes,
        qa_policy_snapshot=context.qa_policy),)


async def main(*, repair_evidence=False, close_known_quality_failure=False):
    loaded = load_production_project(PROJECT / "project.yaml")
    attempt = next(a for a in loaded.manifest.attempts if a.attempt_id == ATTEMPT)
    state = attempt.video_generation_state
    pointer = state.fetch_receipt
    if pointer is None:
        raise ValueError("A01 must already be fetched")
    artifact = PROJECT / pointer.artifact_path
    if hashlib.sha256(artifact.read_bytes()).hexdigest() != SHA:
        raise ValueError("Fetched A01 bytes changed")
    findings, observer_evidence = repaired_findings() if repair_evidence else (FINDINGS, None)
    if close_known_quality_failure and not repair_evidence:
        raise ValueError("Closing requires the explicit same-bytes evidence-repair operation")
    names = ("canonical-diagnosis.json", "post-media-gate.json", "evaluation-validation.json")
    if repair_evidence:
        for name in names:
            if not (HERE / name).is_file() or (HERE / name.replace(".json", "-v1.json")).exists():
                raise ValueError("Original review must exist and its history archive must be unused")
        for name in names:
            (HERE / name).rename(HERE / name.replace(".json", "-v1.json"))
    elif any((HERE / name).exists() for name in names):
        raise ValueError("Review outputs exist; inspect canonical replay instead of overwriting")
    adjudicate = partial(judge, repaired=repair_evidence)
    verifier = ControlledPresentationVerifier(evaluator=ACTOR, proof="analyzer", adjudicate=adjudicate)
    committer = ProductionStateCommitter(PROJECT)
    diagnosis = await review_generation_attempt(committer=committer,
        attempt_id=ATTEMPT, session=ArchivedActualMCP(), adjudicate=adjudicate,
        presentation_verifier=verifier, understand_audio=False, repair_evidence=repair_evidence)
    write_once("canonical-diagnosis.json", diagnosis.model_dump(mode="json"))
    write_once("post-media-gate.json", {
        "shot_id": "ep01-intro", "attempt_id": ATTEMPT,
        "artifact_path": str(artifact), "artifact_sha256": SHA,
        "verdict": "FAIL", "current_attempt_decision": "STOP", "proof": "analyzer",
        "required_findings": [{"requirement_id": key, "verdict": verdict, "reason": reason,
            "evidence_refs": ["mcp-analysis.json", "mcp-review.json", "contact-sheet.jpg"] +
                (["observer-verification/observations.json"] if key in {"identity", "quiet-observer"} and repair_evidence else [])}
            for key, (verdict, reason) in findings.items()],
        "human_acceptance": "NOT_EVALUATED", "audio_semantics": "NOT_EVALUATED",
        "production_activation": False, "next_shot_submit_allowed": False,
        "user_ai_label_exception": "Future authoring only; old sealed findings remain unchanged.",
        "new_provider_calls": 0,
        "evidence_repair": repair_evidence,
        "observer_evidence_sha256": observer_evidence,
    })
    reopened = load_production_project(PROJECT / "project.yaml")
    if close_known_quality_failure:
        if diagnosis.failure_classes != ("QUALITY_FAILURE",):
            raise ValueError("Known-quality close requires a pure canonical QUALITY_FAILURE diagnosis")
        prior = next(a for a in reopened.manifest.attempts if a.attempt_id == ATTEMPT)
        paid_before = canonical_sha256(prior.paid_provider_state.model_dump(mode="json"))
        fetch_before = prior.video_generation_state.fetch_receipt
        arguments = {"attempt_id": ATTEMPT,
            "expected_manifest_revision": reopened.manifest.manifest_revision,
            "experience_content_hash": prior.video_generation_state.generation_experiences[-1].content_hash,
            "actor": REJECTION_ACTOR}
        closed = committer.reject_video_generation(**arguments)
        strict = load_production_project(PROJECT / "project.yaml")
        rejected = next(a for a in strict.manifest.attempts if a.attempt_id == ATTEMPT)
        if (rejected.status.value != "failed" or rejected.error_code != ErrorCode.VIDEO_QUALITY_REJECTED.value
                or rejected.video_generation_state.quality_rejection is None
                or rejected.video_generation_state.fetch_receipt != fetch_before
                or canonical_sha256(rejected.paid_provider_state.model_dump(mode="json")) != paid_before):
            raise ValueError("Quality close did not preserve the exact fetched and paid history")
        replay = committer.reject_video_generation(**arguments)
        if replay.manifest_revision != closed.manifest_revision:
            raise ValueError("Quality rejection replay changed Manifest")
        readback = await review_generation_attempt(committer=committer, attempt_id=ATTEMPT,
            session=None, adjudicate=None, understand_audio=False)
        if readback != diagnosis:
            raise ValueError("Closed canonical diagnosis differs from recorded quality failure")
        write_once("quality-close-result.json", {
            "attempt_id": ATTEMPT, "actor": REJECTION_ACTOR.model_dump(mode="json"),
            "status": rejected.status.value, "error_code": rejected.error_code,
            "manifest_revision_before_close": reopened.manifest.manifest_revision,
            "manifest_revision_after_close": strict.manifest.manifest_revision,
            "quality_rejection": rejected.video_generation_state.quality_rejection.model_dump(mode="json"),
            "diagnosis": readback.model_dump(mode="json"),
            "paid_history_unchanged": True, "fetched_source_unchanged": True,
            "exact_replay_manifest_unchanged": True, "canonical_readback": "PASS",
            "new_provider_calls": 0, "abandonment": False,
        })
        reopened = strict
    print(json.dumps({"gate": "FAIL", "next_shot_submit_allowed": False,
        "manifest_revision_before": loaded.manifest.manifest_revision,
        "manifest_revision_after": reopened.manifest.manifest_revision,
        "diagnosis": diagnosis.model_dump(mode="json")}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair-evidence", action="store_true")
    parser.add_argument("--close-known-quality-failure", action="store_true")
    arguments = parser.parse_args()
    asyncio.run(main(repair_evidence=arguments.repair_evidence,
        close_known_quality_failure=arguments.close_known_quality_failure))
