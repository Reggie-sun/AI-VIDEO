"""Typed development-only review binding for cuts in one resolved timeline."""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Literal

from pydantic import ConfigDict, Field, field_validator

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.composition import timeline_fingerprint
from ai_video.production.hashing import canonical_sha256, verify_artifact_hash
from ai_video.production.models import EvidenceStrength, ResolvedTimeline


_SHA256 = r"^[0-9a-f]{64}$"


class JunctionVisualSpan(StrictModel):
    layer_id: str
    shot_id: str
    asset_id: str
    asset_sha256: str = Field(pattern=_SHA256)
    start_frame: int = Field(ge=0)
    duration_frames: int = Field(gt=0)
    trim_start_frame: int = Field(ge=0)
    trim_duration_frames: int | None = Field(default=None, gt=0)
    opacity_milli: int = Field(ge=0, le=1000)
    z_index: int


class JunctionAudioSpan(StrictModel):
    track_id: str
    audio_kind: str
    asset_id: str
    asset_sha256: str = Field(pattern=_SHA256)
    start_sample: int = Field(ge=0)
    duration_samples: int = Field(gt=0)
    source_start_sample: int = Field(ge=0)
    source_duration_samples: int = Field(gt=0)
    gain_millidb: int
    fade_in_samples: int = Field(ge=0)
    fade_out_samples: int = Field(ge=0)


class JunctionInventory(StrictModel):
    junction_id: str = Field(pattern=_SHA256)
    from_shot_id: str
    to_shot_id: str
    transition_kind: str
    transition_duration_frames: int = Field(ge=0)
    frame: int = Field(ge=0)
    time_ms: int = Field(ge=0)
    sample: int = Field(ge=0)
    visual_spans: tuple[JunctionVisualSpan, ...]
    audio_window_start_sample: int = Field(ge=0)
    audio_window_end_sample: int = Field(ge=0)
    audio_spans: tuple[JunctionAudioSpan, ...]


class JunctionActionObservation(StrictModel):
    verdict: Literal["pass", "fail", "not_evaluated"]
    observation: str = Field(min_length=1)

    @field_validator("observation")
    @classmethod
    def _nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("action observation must not be blank")
        return value


class JunctionActionReview(StrictModel):
    repetition: JunctionActionObservation
    state_continuity: JunctionActionObservation
    pacing: JunctionActionObservation


class ShotEditingIntent(StrictModel):
    """Director advice for one cut; never a timeline or an execution permit."""

    narrative_type: Literal["drama", "advertisement", "opening", "other"]
    technique: Literal["hard_cut", "cut_on_action", "match_cut", "reaction", "reveal", "scene_reset"]
    reason: str = Field(min_length=1)
    expected_effect: str = Field(min_length=1)
    outgoing_phase: str = Field(min_length=1)
    incoming_phase: str = Field(min_length=1)
    axis_eyeline_space: str = Field(min_length=1)
    scale_reaction: str = Field(min_length=1)
    rhythm_reveal: str = Field(min_length=1)
    continuity_risks: tuple[str, ...] = Field(min_length=1)
    audio_treatment: Literal["sync", "j_cut", "l_cut", "sound_bridge", "silence"]
    audio_reason: str = Field(min_length=1)
    audio_track_ids: tuple[str, ...] = ()
    pickup_requirement: str | None = Field(default=None, min_length=1)

    @field_validator("reason", "expected_effect", "outgoing_phase", "incoming_phase",
                     "axis_eyeline_space", "scale_reaction", "rhythm_reveal", "audio_reason",
                     "pickup_requirement")
    @classmethod
    def _nonblank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("editing intent text must not be blank")
        return value

    @field_validator("continuity_risks", "audio_track_ids")
    @classmethod
    def _named_items(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if any(not value.strip() for value in values) or len(set(values)) != len(values):
            raise ValueError("editing items must be nonblank and unique")
        return values


class JunctionSourceSelection(StrictModel):
    outgoing: JunctionVisualSpan
    incoming: JunctionVisualSpan
    source_out_frame_exclusive: int = Field(strict=True, gt=0)
    source_in_frame: int = Field(strict=True, ge=0)


class JunctionEditingReview(StrictModel):
    action_match: JunctionActionObservation
    axis_eyeline_space: JunctionActionObservation
    scale_reaction: JunctionActionObservation
    rhythm_reveal: JunctionActionObservation
    sound_bridge: JunctionActionObservation


def junction_source_selection(cut: JunctionInventory) -> JunctionSourceSelection | None:
    """Expose exact resolved windows; never guess among composited visual layers."""
    outgoing = [s for s in cut.visual_spans if s.shot_id == cut.from_shot_id]
    incoming = [s for s in cut.visual_spans if s.shot_id == cut.to_shot_id]
    if len(outgoing) != 1 or len(incoming) != 1:
        return None
    before, after = outgoing[0], incoming[0]
    return JunctionSourceSelection(outgoing=before, incoming=after,
        source_out_frame_exclusive=before.trim_start_frame + (before.trim_duration_frames or before.duration_frames),
        source_in_frame=after.trim_start_frame)


def _editing_gaps(cut: JunctionInventory, finding: JunctionFinding) -> tuple[list[str], bool]:
    gaps, failed = [], False
    intent, selection, review = finding.editing_intent, finding.source_selection, finding.editing_review
    if intent is None:
        gaps.append("missing_editing_intent")
    else:
        if intent.pickup_requirement is not None:
            gaps.append("pickup_required_return_to_director")
            failed = True
        if intent.audio_treatment in {"j_cut", "l_cut", "sound_bridge"}:
            crossing = {s.track_id for s in cut.audio_spans
                if s.start_sample < cut.sample < s.start_sample + s.duration_samples}
            if not intent.audio_track_ids or not set(intent.audio_track_ids) <= crossing:
                gaps.append("audio_bridge_not_resolved_across_cut")
                failed = True
        if intent.audio_treatment == "silence" and cut.audio_spans:
            gaps.append("editing_silence_has_resolved_audio")
            failed = True
    if selection is None:
        gaps.append("missing_source_selection")
    else:
        before, after = selection.outgoing, selection.incoming
        outgoing = [s for s in cut.visual_spans if s.shot_id == cut.from_shot_id]
        incoming = [s for s in cut.visual_spans if s.shot_id == cut.to_shot_id]
        if (before not in outgoing or after not in incoming
                or before.start_frame + before.duration_frames != max(
                    (s.start_frame + s.duration_frames for s in outgoing), default=-1)
                or after.start_frame != cut.frame
                or selection.source_out_frame_exclusive != before.trim_start_frame
                    + (before.trim_duration_frames or before.duration_frames)
                or selection.source_in_frame != after.trim_start_frame):
            gaps.append("editing_source_selection_mismatch")
            failed = True
    if review is None:
        gaps.append("missing_editing_review")
    else:
        for name in JunctionEditingReview.model_fields:
            observation = getattr(review, name)
            if observation.verdict == "fail":
                gaps.append(f"editing_{name}_failed")
                failed = True
            elif observation.verdict != "pass":
                gaps.append(f"editing_{name}_not_evaluated")
    return gaps, failed


class JunctionFinding(StrictModel):
    """One evaluator's explicit decision and separate audio/visual observations."""

    junction_id: str = Field(pattern=_SHA256)
    inventory_sha256: str = Field(pattern=_SHA256)
    edit_decision: Literal["trim", "retain_with_reason"] | None = None
    edit_reason: str = Field(min_length=1)
    visual_verdict: Literal["pass", "fail", "not_evaluated"]
    visual_observation: str = Field(min_length=1)
    audio_verdict: Literal["pass", "fail", "not_evaluated"]
    audio_observation: str = Field(min_length=1)
    audio_basis: Literal["actual_listening", "deliberately_silent", "not_listened"]
    audio_reason: str | None = None
    viewing_mode: Literal["sampled_frames", "full_playback"] | None = None
    viewing_speed_milli: int | None = Field(default=None, strict=True, gt=0)
    action_review: JunctionActionReview | None = None
    editing_intent: ShotEditingIntent | None = None
    source_selection: JunctionSourceSelection | None = None
    editing_review: JunctionEditingReview | None = None

    @field_validator("edit_reason", "visual_observation", "audio_observation")
    @classmethod
    def _nonblank_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("junction review text must not be blank")
        return value


class JunctionCutResult(StrictModel):
    junction_id: str = Field(pattern=_SHA256)
    from_shot_id: str
    to_shot_id: str
    frame: int = Field(ge=0)
    verdict: Literal["pass", "fail", "not_evaluated"]
    edit_decision: Literal["trim", "retain_with_reason"] | None
    edit_reason: str
    visual_verdict: Literal["pass", "fail", "not_evaluated"]
    visual_observation: str
    audio_verdict: Literal["pass", "fail", "not_evaluated"]
    audio_observation: str
    audio_basis: Literal["actual_listening", "deliberately_silent", "not_listened"] | None
    audio_reason: str | None
    viewing_mode: Literal["sampled_frames", "full_playback"] | None
    viewing_speed_milli: int | None = Field(default=None, strict=True, gt=0)
    evidence_gaps: tuple[str, ...] = ()
    editing_intent: ShotEditingIntent | None = None
    source_selection: JunctionSourceSelection | None = None
    editing_review: JunctionEditingReview | None = None


class JunctionReviewResult(StrictModel):
    verdict: Literal["pass", "fail", "not_evaluated"]
    evidence_gaps: tuple[str, ...] = ()
    cuts: tuple[JunctionCutResult, ...] = ()


class RenderMeasurement(StrictModel):
    model_config = ConfigDict(extra="allow", frozen=True)

    width: int = Field(strict=True, gt=0)
    height: int = Field(strict=True, gt=0)
    fps_num: int = Field(strict=True, gt=0)
    fps_den: int = Field(strict=True, gt=0)
    duration_frames: int = Field(strict=True, gt=0)
    codec_name: str = Field(min_length=1)


class HyperFramesCheck(StrictModel):
    model_config = ConfigDict(extra="allow", frozen=True)

    command: Literal["lint", "check"]
    tool_version: str = Field(min_length=1)
    exit_code: int = Field(strict=True)
    error_count: int = Field(strict=True, ge=0)
    warning_count: int = Field(strict=True, ge=0)


class HyperFramesRenderReport(StrictModel):
    """The existing local HyperFrames output report, with unrelated report fields retained."""

    model_config = ConfigDict(extra="allow", frozen=True)

    output: str = Field(min_length=1)
    sha256: str = Field(pattern=_SHA256)
    size_bytes: int = Field(strict=True, gt=0)
    measured: RenderMeasurement
    timeline_fingerprint: str = Field(pattern=_SHA256)
    timeline_frames: int | None = Field(default=None, strict=True, gt=0)
    checks: tuple[HyperFramesCheck, ...] = Field(min_length=2)


def _timeline_visual_span(span) -> JunctionVisualSpan:
    return JunctionVisualSpan(
        layer_id=span.layer_id,
        shot_id=span.shot_id,
        asset_id=span.asset_id,
        asset_sha256=span.asset_sha256,
        start_frame=span.start_frame,
        duration_frames=span.duration_frames,
        trim_start_frame=span.trim_start_frame,
        trim_duration_frames=span.trim_duration_frames,
        opacity_milli=span.opacity_milli,
        z_index=span.z_index,
    )


def _timeline_audio_span(span) -> JunctionAudioSpan:
    return JunctionAudioSpan(
        track_id=span.track_id,
        audio_kind=span.audio_kind.value,
        asset_id=span.asset_id,
        asset_sha256=span.asset_sha256,
        start_sample=span.start_sample,
        duration_samples=span.duration_samples,
        source_start_sample=span.source_start_sample,
        source_duration_samples=span.source_duration_samples,
        gain_millidb=span.gain_millidb,
        fade_in_samples=span.fade_in_samples,
        fade_out_samples=span.fade_out_samples,
    )


def derive_junction_inventory(timeline: ResolvedTimeline) -> tuple[JunctionInventory, ...]:
    """Project every resolved Shot boundary, including implicit hard cuts."""

    transitions = {}
    first_by_shot = {}
    for span in timeline.visual_spans:
        first = first_by_shot.get(span.shot_id)
        if first is None or span.start_frame < first.start_frame:
            first_by_shot[span.shot_id] = span
        transition = span.incoming_transition
        if transition is not None:
            key = (transition.from_shot_id, transition.to_shot_id)
            current = transitions.get(key)
            if current is not None and current != (transition.kind.value, transition.duration_frames):
                raise ValueError("ResolvedTimeline has conflicting incoming transitions for one cut")
            transitions[key] = (transition.kind.value, transition.duration_frames)

    ordered = sorted(first_by_shot, key=lambda shot: first_by_shot[shot].start_frame)
    if len({first_by_shot[shot].start_frame for shot in ordered}) != len(ordered):
        raise ValueError("Resolved Shot boundaries are ambiguous")
    adjacent = set(zip(ordered, ordered[1:]))
    if not set(transitions) <= adjacent:
        raise ValueError("Resolved transition does not join adjacent Shot spans")
    # Composition permits omitted transition labels. The visual span starts
    # still seal a real cut; absence of a label cannot waive its review.
    for pair in adjacent:
        transitions.setdefault(pair, ("cut", 0))

    fps = timeline.delivery_profile.fps
    sample_rate = timeline.sample_rate
    window_samples = sample_rate
    result = []
    for (from_shot_id, to_shot_id), (kind, duration_frames) in sorted(
        transitions.items(), key=lambda item: first_by_shot[item[0][1]].start_frame
    ):
        first = first_by_shot[to_shot_id]
        frame = first.start_frame
        cut_sample = first.start_sample
        window_start = max(0, cut_sample - window_samples)
        window_end = min(timeline.total_samples, cut_sample + window_samples)
        nearby_visual = [
            span for span in timeline.visual_spans
            if span.shot_id in {from_shot_id, to_shot_id}
            and span.start_frame < frame + fps
            and span.start_frame + span.duration_frames > max(0, frame - fps)
        ]
        visual_spans = tuple(
            _timeline_visual_span(span)
            for span in sorted(nearby_visual, key=lambda item: (item.start_frame, item.z_index, item.layer_id))
        )
        nearby_audio = [
            span for span in timeline.audio_spans
            if span.start_sample < window_end
            and span.start_sample + span.duration_samples > window_start
        ]
        audio_spans = tuple(
            _timeline_audio_span(span)
            for span in sorted(nearby_audio, key=lambda item: (item.start_sample, item.track_id, item.asset_id))
        )
        identity = {
            "timeline_content_hash": timeline.content_hash,
            "timeline_composition_fingerprint": timeline.composition_fingerprint,
            "from_shot_id": from_shot_id,
            "to_shot_id": to_shot_id,
            "transition_kind": kind,
            "transition_duration_frames": duration_frames,
            "frame": frame,
        }
        result.append(JunctionInventory(
            junction_id=canonical_sha256(identity),
            from_shot_id=from_shot_id,
            to_shot_id=to_shot_id,
            transition_kind=kind,
            transition_duration_frames=duration_frames,
            frame=frame,
            time_ms=frame * 1000 // fps,
            sample=cut_sample,
            visual_spans=visual_spans,
            audio_window_start_sample=window_start,
            audio_window_end_sample=window_end,
            audio_spans=audio_spans,
        ))
    return tuple(result)


def junction_inventory_sha256(inventory: tuple[JunctionInventory, ...]) -> str:
    return canonical_sha256({"junctions": [item.model_dump(mode="json") for item in inventory]})


def validate_timeline_and_report(
    timeline_bytes: bytes,
    report_bytes: bytes,
    *,
    video_path: Path,
    video_sha256: str,
    video_size_bytes: int,
) -> tuple[ResolvedTimeline, HyperFramesRenderReport]:
    """Validate exact timeline/report snapshots against one immutable output."""

    try:
        timeline = ResolvedTimeline.model_validate_json(timeline_bytes)
        report = HyperFramesRenderReport.model_validate_json(report_bytes)
    except ValueError as exc:
        raise ValueError("ResolvedTimeline or HyperFrames render report is malformed") from exc
    if not verify_artifact_hash(timeline):
        raise ValueError("ResolvedTimeline content hash is invalid")
    if timeline_fingerprint(timeline) != timeline.composition_fingerprint:
        raise ValueError("ResolvedTimeline composition fingerprint is invalid")
    if timeline.renderer.kind.value != "hyperframes":
        raise ValueError("Full-contract review requires a HyperFrames render report")
    checks = {check.command: check for check in report.checks}
    if (
        set(checks) != {"lint", "check"}
        or len(checks) != len(report.checks)
        or any(
            check.tool_version != timeline.renderer.version
            or check.exit_code != 0
            or check.error_count != 0
            or check.warning_count != 0
            for check in report.checks
        )
    ):
        raise ValueError("HyperFrames report must retain clean lint and check receipts for its renderer version")
    measured = report.measured
    rate = Fraction(measured.fps_num, measured.fps_den)
    if (
        Path(report.output).resolve(strict=False) != video_path.resolve(strict=True)
        or report.sha256 != video_sha256
        or report.size_bytes != video_size_bytes
        or report.timeline_fingerprint != timeline.composition_fingerprint
        or report.timeline_frames is not None and report.timeline_frames != timeline.total_frames
        or measured.width != timeline.delivery_profile.width
        or measured.height != timeline.delivery_profile.height
        or rate != Fraction(timeline.delivery_profile.fps, 1)
        or measured.duration_frames != timeline.total_frames
    ):
        raise ValueError("HyperFrames render report does not match the exact video and ResolvedTimeline")
    return timeline, report


def validate_probe_matches_report(probe: dict, timeline: ResolvedTimeline, report: HyperFramesRenderReport) -> None:
    streams = probe.get("streams")
    videos = [stream for stream in streams or () if stream.get("codec_type") == "video"]
    if len(videos) != 1:
        raise ValueError("Rendered MP4 must contain exactly one video stream")
    video = videos[0]
    measured = report.measured
    try:
        actual_rate = Fraction(video["avg_frame_rate"])
        actual_frames = int(video["nb_frames"])
        actual_duration = Decimal(video.get("duration") or probe["format"]["duration"])
    except (KeyError, ValueError, ZeroDivisionError) as exc:
        raise ValueError("Rendered MP4 lacks exact frame, rate, or duration metadata") from exc
    expected_rate = Fraction(measured.fps_num, measured.fps_den)
    expected_duration = Decimal(timeline.total_frames * expected_rate.denominator) / Decimal(expected_rate.numerator)
    one_frame = Decimal(expected_rate.denominator) / Decimal(expected_rate.numerator)
    if (
        int(video.get("width", 0)) != measured.width
        or int(video.get("height", 0)) != measured.height
        or video.get("codec_name") != measured.codec_name
        or actual_rate != expected_rate
        or actual_frames != measured.duration_frames
        or abs(actual_duration - expected_duration) > one_frame / Decimal(2)
    ):
        raise ValueError("Rendered MP4 frame count, rate, or duration differs from its HyperFrames report")


def evaluate_junction_review(
    inventory: tuple[JunctionInventory, ...],
    findings: tuple[JunctionFinding, ...],
    *,
    inventory_sha256: str,
    strength: EvidenceStrength,
    require_action_review: bool = False,
    require_editing_review: bool = False,
) -> JunctionReviewResult:
    """Adjudicate only explicit per-cut answers; technical bindings never imply a pass."""

    ids = [finding.junction_id for finding in findings]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate junction findings")
    known = {item.junction_id for item in inventory}
    if not set(ids) <= known:
        raise ValueError("Unknown junction finding")
    by_id = {finding.junction_id: finding for finding in findings}
    cuts = []
    global_gaps = []
    for item in inventory:
        finding = by_id.get(item.junction_id)
        gaps = []
        visual = "not_evaluated"
        audio = "not_evaluated"
        decision = None
        reason = "尚未评审；需记录剪辑决定和依据。"
        visual_observation = "尚未以正常速度检查该接点。"
        audio_observation = "尚未实际聆听该接点。"
        audio_basis = None
        audio_reason = None
        viewing_mode = None
        viewing_speed_milli = None
        cut_viewing_ok = False
        if finding is None:
            gaps.append("missing_junction_finding")
        else:
            decision = finding.edit_decision
            reason = finding.edit_reason
            visual_observation = finding.visual_observation
            audio_observation = finding.audio_observation
            audio_basis = finding.audio_basis
            audio_reason = finding.audio_reason
            viewing_mode = finding.viewing_mode
            viewing_speed_milli = finding.viewing_speed_milli
            if finding.inventory_sha256 != inventory_sha256:
                gaps.append("junction_inventory_mismatch")
            cut_viewing_ok = (
                strength is EvidenceStrength.HUMAN
                and finding.viewing_mode == "full_playback"
                and finding.viewing_speed_milli == 1000
            )
            if not cut_viewing_ok:
                gaps.append("normal_speed_human_playback_unverified")
            if decision is None:
                gaps.append("missing_edit_decision")
            elif decision == "trim":
                gaps.append("trim_recommended")
            elif not reason.strip():
                gaps.append("missing_edit_reason")
            if finding.visual_verdict == "fail":
                visual = "fail"
            elif finding.visual_verdict == "pass" and cut_viewing_ok and finding.inventory_sha256 == inventory_sha256:
                visual = "pass"
            else:
                gaps.append(
                    "visual_not_evaluated" if finding.visual_verdict == "not_evaluated"
                    else "visual_pass_unverified"
                )
            if finding.audio_verdict == "fail":
                audio = "fail"
            elif finding.audio_basis == "actual_listening":
                if cut_viewing_ok and finding.inventory_sha256 == inventory_sha256:
                    audio = finding.audio_verdict
                else:
                    gaps.append("actual_listening_unverified")
            elif finding.audio_basis == "deliberately_silent":
                if not (finding.audio_reason or "").strip():
                    gaps.append("missing_silence_reason")
                elif item.audio_spans:
                    gaps.append("timeline_audio_overlaps_declared_silence")
                elif cut_viewing_ok and finding.inventory_sha256 == inventory_sha256:
                    audio = finding.audio_verdict
                else:
                    gaps.append("silent_join_unverified")
            else:
                gaps.append("audio_not_listened")
            if audio == "not_evaluated":
                gaps.append(
                    "audio_not_evaluated" if finding.audio_verdict == "not_evaluated"
                    else "audio_pass_unverified"
                )
            if require_action_review:
                if finding.action_review is None:
                    gaps.append("missing_action_review")
                else:
                    for name in ("repetition", "state_continuity", "pacing"):
                        observation = getattr(finding.action_review, name)
                        if observation.verdict == "fail":
                            visual = "fail"
                            gaps.append(f"action_{name}_failed")
                        elif observation.verdict != "pass":
                            gaps.append(f"action_{name}_not_evaluated")
            if require_editing_review or any((finding.editing_intent, finding.source_selection, finding.editing_review)):
                editing_gaps, editing_failed = _editing_gaps(item, finding)
                gaps.extend(editing_gaps)
                if editing_failed:
                    audio_failures = {"audio_bridge_not_resolved_across_cut",
                        "editing_silence_has_resolved_audio", "editing_sound_bridge_failed"}
                    if audio_failures.intersection(editing_gaps):
                        audio = "fail"
                    if any(gap.endswith("_failed") and gap not in audio_failures
                           or gap in {"editing_source_selection_mismatch", "pickup_required_return_to_director"}
                           for gap in editing_gaps):
                        visual = "fail"
        if decision == "trim" or visual == "fail" or audio == "fail":
            verdict = "fail"
        elif (
            finding is not None
            and decision == "retain_with_reason"
            and visual == "pass"
            and audio == "pass"
            and not gaps
        ):
            verdict = "pass"
        else:
            verdict = "not_evaluated"
        cuts.append(JunctionCutResult(
            junction_id=item.junction_id,
            from_shot_id=item.from_shot_id,
            to_shot_id=item.to_shot_id,
            frame=item.frame,
            verdict=verdict,
            edit_decision=decision,
            edit_reason=reason,
            visual_verdict=visual,
            visual_observation=visual_observation,
            audio_verdict=audio,
            audio_observation=audio_observation,
            audio_basis=audio_basis,
            audio_reason=audio_reason,
            viewing_mode=viewing_mode,
            viewing_speed_milli=viewing_speed_milli,
            evidence_gaps=tuple(dict.fromkeys(gaps)),
            editing_intent=finding.editing_intent if finding else None,
            source_selection=finding.source_selection if finding else None,
            editing_review=finding.editing_review if finding else None,
        ))
        global_gaps.extend(gaps)
    if not inventory:
        verdict = "pass"
    elif any(cut.verdict == "fail" for cut in cuts):
        verdict = "fail"
    elif any(cut.verdict != "pass" for cut in cuts):
        verdict = "not_evaluated"
    else:
        verdict = "pass"
    return JunctionReviewResult(
        verdict=verdict,
        evidence_gaps=tuple(dict.fromkeys(global_gaps)),
        cuts=tuple(cuts),
    )

