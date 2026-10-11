from pathlib import Path

import pytest
from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import ActorIdentity
from ai_video.production.video import ResolvedVideoGenerationRequest
from ai_video.production.video_artifact import (
    VideoProbeReceipt,
    _probe_generated_video_candidate,
    probe_generated_video_candidate,
)
from ai_video.production.video_contracts import (
    VideoFlexibleOutputRequirement,
    VideoOutputCapability,
)
from ai_video.production.video_timing_recovery import VideoNominalEndpointRecovery
from test_production_video import _continuity_fetch_receipt, _request, _variant


ACTOR = ActorIdentity(actor_id="canvas-task-parent", actor_kind="codex")


def _evidence(tmp_path: Path):
    output = VideoFlexibleOutputRequirement(
        timing_mode="exact_seconds", duration_seconds=15,
        dimension_mode="exact", width=1280, height=720,
        resolution_label="720p", ratio="16:9", fps=24,
        container="mp4", mime_type="video/mp4", native_audio=False,
    )
    capability = VideoOutputCapability(
        min_duration_seconds=15, max_duration_seconds=15,
        provider_selected_duration=False, timing_modes=("exact_seconds",),
        dimension_modes=("exact",), min_width=1280, max_width=1280,
        min_height=720, max_height=720, dimension_multiple=1,
        resolution_labels=("720p",), ratios=("16:9",), fps_values=(24,),
        containers=("mp4",), native_audio_options=(False,),
    )
    request = ResolvedVideoGenerationRequest.create(
        request=_request(output_requirement=output),
        capability=_variant(output=None, output_capability=capability),
        effective_output=output, effective_seed=17,
        effective_negative_prompt_text="flicker",
    )
    raw = b"exact-retained-provider-bytes"
    source = tmp_path / "raw.mp4"
    source.write_bytes(raw)
    fetch = _continuity_fetch_receipt(request, raw)
    probe = {
        "streams": [{"codec_type": "video", "codec_name": "h264",
                     "width": 1280, "height": 720, "avg_frame_rate": "24/1",
                     "duration": "15.041667", "nb_frames": "361"}],
        "format": {"format_name": "mov,mp4", "duration": "15.104"},
    }
    return request, source, fetch, probe


def _recover(source, request, fetch, probe):
    with source.open("rb") as held:
        return _probe_generated_video_candidate(
            held.fileno(), request, fetch, probe=lambda _: probe,
            defer_continuity_review=False,
            nominal_endpoint_recovery=(ACTOR, "Original canvas requested a nominal 15 seconds."),
        )


def test_explicit_recovery_preserves_request_bytes_measurements_and_strict_default(tmp_path):
    request, source, fetch, probe = _evidence(tmp_path)
    sealed = request.model_dump_json()
    with source.open("rb") as held, pytest.raises(AiVideoError) as error:
        probe_generated_video_candidate(held.fileno(), request, fetch, probe=lambda _: probe)
    assert error.value.code is ErrorCode.VIDEO_ARTIFACT_INVALID
    raw, measured, receipt = _recover(source, request, fetch, probe)
    assert raw == source.read_bytes()
    assert measured.frame_count == 361
    assert measured.duration_milliseconds == 15042
    assert request.model_dump_json() == sealed
    recovery = receipt.nominal_endpoint_recovery
    assert recovery is not None
    assert recovery.original_output.timing_mode == "exact_seconds"
    recovery.validate_binding(request=request, fetch_receipt=fetch, measured=measured)
    assert VideoProbeReceipt.model_validate_json(receipt.model_dump_json()) == receipt
    with source.open("rb") as held, pytest.raises(AiVideoError):
        probe_generated_video_candidate(held.fileno(), request, fetch, probe=lambda _: probe)


@pytest.mark.parametrize("patch", [
    {"nb_frames": "363", "duration": "15.125"},
    {"nb_frames": "361", "duration": "15.083333"},
    {"nb_frames": "360", "duration": "15"},
    {"width": 1278},
    {"avg_frame_rate": "25/1"},
])
def test_recovery_rejects_non_endpoint_or_other_contract_failures(tmp_path, patch):
    request, source, fetch, probe = _evidence(tmp_path)
    probe["streams"][0].update(patch)
    with pytest.raises(AiVideoError):
        _recover(source, request, fetch, probe)


def test_recovery_cannot_transfer_to_another_request_fetch_or_measurement(tmp_path):
    request, source, fetch, probe = _evidence(tmp_path)
    _, measured, receipt = _recover(source, request, fetch, probe)
    recovery = receipt.nominal_endpoint_recovery
    assert recovery is not None
    for changed in (
        {"request": request.model_copy(update={"resolved_generation_hash": "a" * 64})},
        {"fetch_receipt": fetch.model_copy(update={"fetch_fingerprint": "a" * 64})},
        {"measured": measured.model_copy(update={"frame_count": 362})},
    ):
        arguments = {"request": request, "fetch_receipt": fetch, "measured": measured}
        arguments.update(changed)
        with pytest.raises(ValueError):
            recovery.validate_binding(**arguments)
    tampered = recovery.model_dump(mode="json")
    tampered["reason"] = "different authorization"
    with pytest.raises(ValidationError):
        VideoNominalEndpointRecovery.model_validate(tampered)


def test_committer_recovers_candidate_activates_and_replays_without_provider_calls(tmp_path):
    from ai_video.production.project import load_production_project
    from ai_video.production.models import StateCommitStatus, VideoAttemptPhase
    from ai_video.production.paths import canonical_video_probe_receipt_path
    from ai_video.production.state_commit import ProductionStateCommitter
    from ai_video.production.video import VideoTaskState
    from ai_video.production.video_generation import VideoGenerationService
    from test_production_generated_video_e2e import _runtime, ATTEMPT_ID
    from production_generation_execution_factory import NativeFixtureVideoProvider

    class FlexibleFixtureProvider(NativeFixtureVideoProvider):
        def resolve(self, request):
            self._resolve_calls += 1
            return ResolvedVideoGenerationRequest.create(
                request=request, capability=self.capabilities().variants[0],
                effective_output=request.output_requirement,
                effective_seed=request.seed,
                effective_negative_prompt_text=request.negative_prompt_text,
            )

    inputs, provider, resolved, binding, paid_preview, committer = _runtime(
        tmp_path, flexible_output=True, status_events=(VideoTaskState.SUCCEEDED,),
        provider_factory=FlexibleFixtureProvider,
    )
    service = VideoGenerationService(committer=committer, provider=provider)
    service.start(attempt_id=ATTEMPT_ID, request=resolved, execution_binding=binding)
    service.submit_once(attempt_id=ATTEMPT_ID, paid_preview=paid_preview,
                        reservation_id="endpoint-recovery-fixture")
    service.refresh_once(attempt_id=ATTEMPT_ID)
    service.fetch_once(attempt_id=ATTEMPT_ID)
    before = committer._read_manifest()
    request_pointer = before.attempts[-1].video_generation_state.request
    original_request = (tmp_path / request_pointer.path).read_bytes()
    counters = provider.call_counts
    inclusive = {
        "streams": [{"codec_type": "video", "codec_name": "h264",
                     "width": 64, "height": 64, "avg_frame_rate": "24/1",
                     "duration": "1.041667", "nb_frames": "25"}],
        "format": {"format_name": "mov,mp4", "duration": "1.104"},
    }
    with pytest.raises(AiVideoError) as failed:
        service.validate_once(attempt_id=ATTEMPT_ID, probe=lambda _: inclusive)
    assert failed.value.code is ErrorCode.VIDEO_ARTIFACT_INVALID
    assert committer._read_manifest() == before
    candidate = committer.recover_nominal_video_endpoint(
        attempt_id=ATTEMPT_ID, actor=ACTOR,
        reason="Keep the original nominal one-second provider output.",
        probe=lambda _: inclusive,
    )
    assert candidate.attempts[-1].video_generation_state.phase is VideoAttemptPhase.CANDIDATE
    assert candidate.active_project == before.active_project
    assert (tmp_path / request_pointer.path).read_bytes() == original_request
    committer.recover()
    active = committer.activate_video_candidate(attempt_id=ATTEMPT_ID)
    assert active.attempts[-1].status is StateCommitStatus.SUCCEEDED
    loaded = load_production_project(tmp_path / "project.yaml")
    asset = next(a for a in loaded.registry.assets if a.asset_id == resolved.output_asset_id)
    assert asset.video_metadata.frame_count == 25
    assert asset.video_metadata.duration_milliseconds == 1042
    receipt = VideoProbeReceipt.model_validate_json(
        (tmp_path / canonical_video_probe_receipt_path(asset.video_metadata.probe_receipt_id)).read_bytes()
    )
    assert receipt.nominal_endpoint_recovery is not None
    restarted = ProductionStateCommitter(tmp_path)
    assert restarted.replay_active_video_generation(attempt_id=ATTEMPT_ID) == active
    assert provider.call_counts == counters
    assert (tmp_path / request_pointer.path).read_bytes() == original_request
