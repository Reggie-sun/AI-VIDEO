import hashlib
import os
import shutil
import socket
from pathlib import Path

import pytest

from ai_video.production.audio import VoiceCallAuthorization
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.hyperframes import probe_clip_fd_with_executable
from ai_video.production.models import (
    DependencyGraphSnapshotPointer,
    QaLayer,
    QaPolicyPointer,
    RenderStateSnapshotPointer,
    ReviewRequest,
    SourceReference,
    StateCommitStatus,
    TechnicalReviewContext,
    TechnicalReviewWindow,
    VisualStrategy,
)
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import ProductionStateCommitter
from production_e2e_support import (
    BaseAiComicCallCounts,
    DeterministicHyperFramesRunner,
    DeterministicReviewAnalyzer,
    DeterministicVoiceProvider,
    require_audio_toolchain,
)
import production_project_factory as project_factory


def _forbid_network_and_secret_access(monkeypatch: pytest.MonkeyPatch) -> None:
    def reject(*_args, **_kwargs):
        raise AssertionError("deterministic support must not access network or secrets")

    monkeypatch.setattr(socket.socket, "connect", reject)
    monkeypatch.setattr(os, "getenv", reject)


def test_base_ai_comic_support_is_deterministic_and_has_no_direct_state_writer(
    tmp_path: Path,
) -> None:
    first = project_factory.make_base_ai_comic_e2e_runtime(tmp_path / "first")
    second = project_factory.make_base_ai_comic_e2e_runtime(tmp_path / "second")

    assert first.synthetic_inputs_hash == second.synthetic_inputs_hash
    assert first.call_counts == BaseAiComicCallCounts()
    assert not hasattr(first, "write_manifest")
    assert not hasattr(first, "activate_registry")


def test_deterministic_voice_provider_consumes_real_permit_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project_factory.write_and_load_two_shot_project(tmp_path)
    request = project_factory.make_voice_request(tmp_path)
    provider = DeterministicVoiceProvider()
    preview = provider.preview(request)
    authorization = VoiceCallAuthorization.create(
        request_fingerprint=request.voice_request_fingerprint,
        preview_fingerprint=preview.preview_fingerprint,
        pricing_snapshot_id=request.pricing_snapshot_id,
        budget_reservation_receipt_id=request.budget_reservation_receipt_id,
        egress_authorization_receipt_id=request.egress_authorization_receipt_id,
        destination=preview.destination,
        payload_categories=preview.payload_categories,
        cost_ceiling_microunits=preview.estimated_cost_upper_bound_microunits,
        provider_enabled=True,
    )
    committer = ProductionStateCommitter(tmp_path)
    committer.begin_voice_generation(request, preview, authorization)
    permit = committer.record_voice_submit_intent(request, preview, authorization)
    _forbid_network_and_secret_access(monkeypatch)

    result = provider.generate(request, authorization, permit)

    assert result.audio_bytes
    assert provider.generate_calls == 1
    with pytest.raises(AssertionError, match="permit"):
        provider.generate(request, authorization, permit)
    assert provider.generate_calls == 1


class _OneUseReviewPermit:
    def __init__(self, binding: dict[str, str]) -> None:
        self.binding = binding
        self.consumed = False

    def _consume_review_analysis_permit(self, **binding: str) -> bool:
        if self.consumed or binding != self.binding:
            return False
        self.consumed = True
        return True


def _review_request(identity: str) -> ReviewRequest:
    render_hash = hashlib.sha256(identity.encode()).hexdigest()
    timeline_hash = "3" * 64
    graph_hash = "4" * 64
    policy_hash = "5" * 64
    context = TechnicalReviewContext(
        render_output_sha256=render_hash,
        timeline_fingerprint=timeline_hash,
        windows=(
            TechnicalReviewWindow(
                shot_id="shot-1",
                visual_strategy=VisualStrategy.STATIC_IMAGE,
                start_frame=0,
                end_frame_exclusive=24,
                expects_audio=True,
                visual_span_ids=("layer-shot-1",),
            ),
        ),
        measurement_contract_version="1",
    )
    return seal_artifact(
        ReviewRequest(
            artifact_id=f"review-request-{identity}",
            revision=1,
            content_hash="0" * 64,
            creation_receipt_id=f"review-request-{identity}",
            source_provenance=(
                SourceReference(kind="derived", reference="base-ai-comic-test"),
            ),
            request_id=f"review-request-{identity}",
            base_manifest_revision=1,
            dependency_graph=DependencyGraphSnapshotPointer(
                revision_id=graph_hash,
                content_hash=graph_hash,
                path=Path(f"state/dependency_graph.{graph_hash}.json"),
                file_sha256="6" * 64,
            ),
            dependency_states_hash="7" * 64,
            render_state=RenderStateSnapshotPointer(
                path=Path(f"state/render/states/{render_hash}.json"),
                revision=1,
                content_hash=render_hash,
                file_sha256="8" * 64,
            ),
            render_output_sha256=render_hash,
            timeline_fingerprint=timeline_hash,
            qa_policy=QaPolicyPointer(
                path=Path(f"state/reviews/policy.{policy_hash}.json"),
                policy_id="base-ai-comic-layout",
                policy_version="1",
                content_hash=policy_hash,
                file_sha256="9" * 64,
            ),
            requested_layers=(QaLayer.LAYOUT,),
            evidence_tool_identities=(DeterministicReviewAnalyzer.tool_identity,),
            technical_context=context,
        )
    )


def _review_permit(request: ReviewRequest) -> _OneUseReviewPermit:
    return _OneUseReviewPermit(
        {
            "request_content_hash": request.content_hash,
            "render_output_sha256": request.render_output_sha256,
            "technical_context_hash": canonical_sha256(
                request.technical_context.model_dump(mode="json")
            ),
        }
    )


def test_deterministic_review_analyzer_consumes_permit_and_fails_unknown_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    analyzer = DeterministicReviewAnalyzer()
    initial = _review_request("initial")
    initial_permit = _review_permit(initial)
    invalid_permit = _review_permit(initial)
    invalid_permit.binding["request_content_hash"] = "f" * 64
    _forbid_network_and_secret_access(monkeypatch)

    with pytest.raises(AssertionError, match="permit"):
        analyzer.analyze(initial, invalid_permit)
    assert not invalid_permit.consumed
    assert analyzer.calls == 0

    failed = analyzer.analyze(initial, initial_permit)

    assert initial_permit.consumed
    assert failed.measured_payload["caption_overflow_milli"] == 1
    with pytest.raises(AssertionError, match="permit"):
        analyzer.analyze(initial, initial_permit)
    assert analyzer.calls == 1

    unknown = _review_request("unknown")
    unknown_permit = _review_permit(unknown)
    with pytest.raises(AssertionError, match="exact repaired render"):
        analyzer.analyze(unknown, unknown_permit)
    assert unknown_permit.consumed

    analyzer.bind_repaired_render_state(unknown.render_state)
    passing_permit = _review_permit(unknown)
    passing = analyzer.analyze(unknown, passing_permit)
    assert passing_permit.consumed
    assert passing.measured_payload["caption_overflow_milli"] == 0


def _run_deterministic_renderer(
    runner: DeterministicHyperFramesRunner,
    root: Path,
    name: str,
    *,
    env: dict[str, str],
) -> Path:
    output = root / f"{name}.mp4"
    result = runner.run(
        "render",
        ("-o", str(output)),
        cwd=root,
        env=env,
        timeout_seconds=30,
    )
    assert result.returncode == 0, result.stderr
    return output


def test_deterministic_runner_is_probeable_repeatable_and_source_sensitive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    toolchain = require_audio_toolchain()
    inherited_env = {**os.environ, "HYPERFRAMES_NO_TELEMETRY": "1"}
    assets = tmp_path / "assets"
    assets.mkdir()
    shutil.copyfile(
        Path(__file__).parent
        / "fixtures/voice_captions/dialogue-mono-48000.wav",
        assets / "mix.wav",
    )
    source = tmp_path / "index.html"
    source.write_text("<main data-layout='initial'>comic</main>", encoding="utf-8")
    runner = DeterministicHyperFramesRunner(toolchain.ffmpeg_path)
    _forbid_network_and_secret_access(monkeypatch)

    first = _run_deterministic_renderer(
        runner, tmp_path, "first", env=inherited_env
    )
    second = _run_deterministic_renderer(
        runner, tmp_path, "second", env=inherited_env
    )
    first_hash = hashlib.sha256(first.read_bytes()).hexdigest()
    second_hash = hashlib.sha256(second.read_bytes()).hexdigest()
    with first.open("rb") as handle:
        probe = probe_clip_fd_with_executable(
            handle.fileno(), toolchain.ffprobe_path
        )

    source.write_text("<main data-layout='repaired'>comic</main>", encoding="utf-8")
    repaired = _run_deterministic_renderer(
        runner, tmp_path, "repaired", env=inherited_env
    )
    repaired_hash = hashlib.sha256(repaired.read_bytes()).hexdigest()

    assert {stream["codec_type"] for stream in probe["streams"]} == {
        "audio",
        "video",
    }
    assert first_hash == second_hash
    assert repaired_hash != first_hash
    assert runner.render_calls == 3


def test_base_ai_comic_materializes_and_renders_from_current_active_assets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = project_factory.make_base_ai_comic_e2e_runtime(tmp_path)
    _forbid_network_and_secret_access(monkeypatch)

    images = runtime.generate_two_shot_images()
    after_images = load_production_project(tmp_path / "project.yaml")
    voice = runtime.generate_voice_and_captions()
    after_voice = load_production_project(tmp_path / "project.yaml")
    initial = runtime.render_current_composition(revision=1)
    loaded = load_production_project(tmp_path / "project.yaml")
    shot_visuals = {
        shot.shot_id: next(
            role.asset_ids[0]
            for role in shot.required_asset_roles
            if role.role == "still"
        )
        for shot in loaded.shots
    }
    registry = {item.asset_id: item for item in loaded.registry.assets}
    composition_visuals = {
        layer.shot_id: layer.asset_id for layer in initial.composition.layers
    }
    image_attempts = tuple(
        item
        for item in after_voice.manifest.attempts
        if item.operation == "image_generation"
    )
    voice_attempts = tuple(
        item
        for item in after_voice.manifest.attempts
        if item.operation == "voice_generation"
    )

    assert images.requests[0].references == images.requests[1].references
    assert images.shot_1_asset_id != images.shot_2_asset_id
    assert after_images.manifest.schema_version == "2.5"
    assert (
        after_voice.manifest.manifest_revision
        > after_images.manifest.manifest_revision
    )
    assert len(image_attempts) == 2
    assert all(
        item.status is StateCommitStatus.SUCCEEDED for item in image_attempts
    )
    assert len(voice_attempts) == 1
    assert voice_attempts[0].status is StateCommitStatus.SUCCEEDED
    assert loaded.manifest.schema_version == "2.5"
    assert shot_visuals == {
        "shot-1": images.shot_1_asset_id,
        "shot-2": images.shot_2_asset_id,
    }
    assert composition_visuals == shot_visuals
    assert voice.audio_asset_ids
    assert voice.caption_asset_ids
    assert voice.caption_track_ids
    generated_audio = registry[voice.audio_asset_ids[0]]
    generated_caption = registry[voice.caption_asset_ids[0]]
    assert generated_audio.audio_metadata is not None
    assert generated_audio.audio_metadata.provenance_receipt_id
    assert generated_audio.egress is not None
    assert generated_caption.caption_metadata is not None
    assert (
        generated_caption.caption_metadata.caption_track_id
        == voice.caption_track_ids[0]
    )
    assert generated_caption.caption_metadata.source_audio_asset_id in (
        voice.audio_asset_ids
    )
    assert loaded.asset_paths[voice.audio_asset_ids[0]].is_file()
    assert loaded.asset_paths[voice.caption_asset_ids[0]].is_file()
    assert (
        initial.timeline.composition_spec_id,
        initial.timeline.composition_spec_revision,
        initial.timeline.composition_spec_hash,
    ) == (
        initial.composition.artifact_id,
        initial.composition.revision,
        initial.composition.content_hash,
    )
    assert initial.render_state == loaded.manifest.active_render_state
    assert initial.probe.duration_milliseconds > 0
    assert initial.probe.video_stream_count == 1
    assert initial.sha256 == hashlib.sha256(initial.path.read_bytes()).hexdigest()
    assert runtime.call_counts == BaseAiComicCallCounts(
        image_submit=2,
        voice_submit=1,
        renderer_run=1,
    )
    assert loaded.manifest.active_review_receipts == ()
    assert loaded.manifest.active_approved_repair is None
    assert loaded.manifest.repair_outcome_receipts == ()
