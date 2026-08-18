import hashlib
import os
import shutil
import socket
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.audio import VoiceCallAuthorization
from ai_video.production.hashing import (
    canonical_sha256,
    seal_artifact,
    verify_artifact_hash,
)
from ai_video.production.hyperframes import probe_clip_fd_with_executable
from ai_video.production.models import (
    DependencyGraphSnapshotPointer,
    CompositionSpec,
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
from ai_video.production.state_commit import recover_production_state
from production_e2e_support import (
    BaseAiComicCallCounts,
    DeterministicHyperFramesRunner,
    DeterministicReviewAnalyzer,
    DeterministicVoiceProvider,
    _install_manifest_write_counter,
    make_base_ai_comic_reopen_runtime,
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
    assert failed.measured_payload["caption_overflow_milli"] == 0
    assert failed.measured_payload["safe_area_inset_milli"] == 49
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
    assert passing.measured_payload["safe_area_inset_milli"] == 50


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
    assert set(voice.audio_asset_ids).issubset(
        {span.asset_id for span in initial.timeline.audio_spans}
    )
    assert set(voice.caption_asset_ids).issubset(
        {cue.caption_asset_id for cue in initial.timeline.caption_cues}
    )
    generated_audio_track_ids = {
        span.track_id
        for span in initial.timeline.audio_spans
        if span.asset_id in voice.audio_asset_ids
    }
    assert generated_audio_track_ids
    assert initial.probe.staged_audio_binding_ids == (
        f"p4-mix-{initial.timeline.composition_fingerprint}",
    )
    assert generated_audio_track_ids.issubset(
        set(initial.probe.staged_audio_track_ids)
    )
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
    assert initial.probe.audio_stream_count == 1
    assert initial.sha256 == hashlib.sha256(initial.path.read_bytes()).hexdigest()
    assert runtime.call_counts == BaseAiComicCallCounts(
        image_submit=2,
        voice_preview=3,
        voice_submit=1,
        renderer_version=1,
        renderer_doctor=1,
        renderer_run=3,
    )
    assert loaded.manifest.active_review_receipts == ()
    assert loaded.manifest.active_approved_repair is None
    assert loaded.manifest.repair_outcome_receipts == ()


def test_base_ai_comic_failed_layout_review_repairs_exact_closure_and_accepts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = project_factory.make_base_ai_comic_e2e_runtime(tmp_path)
    _forbid_network_and_secret_access(monkeypatch)

    initial = runtime.materialize_and_render_initial()
    stable_media = runtime.media_identity_snapshot()
    assert len(stable_media.image_asset_ids) == 2
    assert stable_media.audio_asset_ids
    assert stable_media.caption_asset_ids
    assert stable_media.caption_track_ids
    assert stable_media.character_references
    assert stable_media.scene_references
    assert len(stable_media.image_request_evidence) == 2
    assert len(stable_media.image_receipt_evidence) == 2

    failed = runtime.review_initial_render()
    approval = runtime.approve_exact_layout_repair(failed)
    before_repair = runtime.load_manifest()
    repaired_state = runtime.commit_layout_repair(approval)
    repaired_composition_path = tmp_path / repaired_state.composition_path
    repaired_composition_bytes = repaired_composition_path.read_bytes()
    repaired_composition = CompositionSpec.model_validate_json(
        repaired_composition_bytes
    )
    expected_repaired_composition = seal_artifact(
        initial.composition.model_copy(
            update={
                "revision": 2,
                "content_hash": "0" * 64,
                "creation_receipt_id": "base-ai-comic-composition-2",
                "layers": (
                    initial.composition.layers[0].model_copy(
                        update={
                            "transform": initial.composition.layers[
                                0
                            ].transform.model_copy(
                                update={"translate_x_px": 24}
                            )
                        }
                    ),
                    *initial.composition.layers[1:],
                ),
            }
        )
    )
    before_rerender = runtime.load_manifest()
    repaired = runtime.render_current_composition(
        composition=repaired_composition
    )
    after_rerender = runtime.load_manifest()
    passing = runtime.review_repaired_render()
    outcome = runtime.record_repair_outcome(approval, repaired, passing)
    accepted = runtime.record_final_acceptance(passing)

    assert failed.verdict == "fail"
    assert failed.issue_ids == ("layout.safe-area",)
    assert before_repair.active_review_receipts
    assert failed.pointer in before_repair.active_review_receipts
    assert set(repaired_state.invalidated_node_ids) == {
        "composition:main",
        "timeline:main",
        "renderer-source:main",
        "render:main",
    }
    assert repaired_composition_path.is_file()
    assert repaired_state.composition_file_sha256 == hashlib.sha256(
        repaired_composition_bytes
    ).hexdigest()
    assert verify_artifact_hash(repaired_composition)
    assert repaired_composition == repaired_state.composition
    assert repaired_composition == expected_repaired_composition
    assert repaired_composition.revision == 2
    assert repaired_composition.content_hash != initial.composition.content_hash
    assert repaired_composition.layers[0].transform.translate_x_px == 24
    assert before_rerender.active_review_receipts == ()
    stale_at_repair = next(
        state for state in before_rerender.review_states if state.layer is QaLayer.LAYOUT
    )
    assert stale_at_repair.lifecycle == "stale"
    assert stale_at_repair.active_receipt is None
    assert after_rerender.active_review_receipts == ()
    stale_after_rerender = next(
        state for state in after_rerender.review_states if state.layer is QaLayer.LAYOUT
    )
    assert stale_after_rerender.lifecycle == "stale"
    assert stale_after_rerender.active_receipt is None
    assert (
        after_rerender.final_acceptance_state is None
        or (
            after_rerender.final_acceptance_state.lifecycle == "stale"
            and after_rerender.final_acceptance_state.active_receipt is None
        )
    )
    assert runtime.media_identity_snapshot() == stable_media
    assert repaired.sha256 != initial.sha256
    assert repaired.probe.duration_milliseconds > 0
    assert repaired.composition == repaired_composition
    assert (
        repaired.timeline.composition_spec_id,
        repaired.timeline.composition_spec_revision,
        repaired.timeline.composition_spec_hash,
    ) == (
        repaired_composition.artifact_id,
        repaired_composition.revision,
        repaired_composition.content_hash,
    )
    assert all(receipt.verdict == "pass" for receipt in passing)
    assert outcome.actual_invalidation_node_ids == repaired_state.invalidated_node_ids
    assert accepted.render_state == repaired.render_state
    assert accepted.lifecycle == "fresh"


@pytest.mark.parametrize(
    "mutation", ["add_image_node", "blanket_all_nodes", "stale_render"]
)
def test_base_ai_comic_repair_rejects_scope_or_identity_drift_before_mutation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    runtime = project_factory.make_base_ai_comic_e2e_runtime(tmp_path)
    _forbid_network_and_secret_access(monkeypatch)
    before = runtime.materialize_review_and_approve()

    with pytest.raises(AiVideoError):
        runtime.commit_forged_repair(mutation)

    assert runtime.load_manifest() == before


def test_base_ai_comic_final_state_reopens_and_exact_replay_has_zero_effects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_manifest_write_counter(monkeypatch)
    runtime = project_factory.make_base_ai_comic_e2e_runtime(tmp_path)
    _forbid_network_and_secret_access(monkeypatch)

    final = runtime.run_full_acceptance()
    before_manifest_bytes = runtime.manifest_bytes()
    before_counts = runtime.call_counts
    baseline_manifest_temp_writes = before_counts.manifest_temp_write
    baseline_manifest_replaces = before_counts.manifest_replace
    final_mp4_bytes = final.output_path.read_bytes()
    final_mp4_sha = hashlib.sha256(final_mp4_bytes).hexdigest()
    assert baseline_manifest_temp_writes > 0, (
        "accepted baseline must durably write the Manifest temp file"
    )
    assert baseline_manifest_replaces > 0, (
        "accepted baseline must atomically promote the Manifest"
    )
    # ``manifest_temp_write`` counts only the canonical
    # ``.p2a-manifest.tmp`` durable temp-write effects, while
    # ``manifest_replace`` counts every atomic promotion of
    # ``state/manifest.json`` (including the render-specific
    # candidate/final Manifest promotions whose temp paths are
    # ``.p2a-render-{candidate,final}-manifest.tmp``). The replace
    # counter is therefore an upper bound on the temp-write counter for
    # the same shared Manifest file, but the two counters observe
    # different canonical seams and are kept independent.
    assert baseline_manifest_replaces >= baseline_manifest_temp_writes
    assert before_counts.voice_preview >= before_counts.voice_submit
    assert before_counts.renderer_version >= 1, (
        "accepted baseline must exercise the renderer version probe"
    )
    assert before_counts.renderer_doctor >= 1, (
        "accepted baseline must exercise the renderer doctor probe"
    )
    assert before_counts.renderer_run >= 1, (
        "accepted baseline must exercise the renderer run command"
    )

    recovery = recover_production_state(tmp_path)
    after_recovery_bytes = runtime.manifest_bytes()
    assert recovery.manifest_revision_after == recovery.manifest_revision_before
    assert after_recovery_bytes == before_manifest_bytes
    assert runtime.call_counts == before_counts, (
        "clean recovery must add zero call-count effects"
    )
    assert (
        before_counts.manifest_temp_write == baseline_manifest_temp_writes
    ), "clean recovery must not durably write the Manifest temp file"
    assert (
        before_counts.manifest_replace == baseline_manifest_replaces
    ), "clean recovery must not atomically promote the Manifest"

    recovery_repeat = recover_production_state(tmp_path)
    assert (
        recovery_repeat.manifest_revision_after
        == recovery_repeat.manifest_revision_before
    )
    assert runtime.manifest_bytes() == before_manifest_bytes
    assert runtime.call_counts == before_counts, (
        "repeated clean recovery must remain idempotent"
    )

    replay = runtime.run_full_acceptance()
    assert replay == final
    assert runtime.call_counts == before_counts, (
        "same-runtime replay must add zero call-count effects"
    )
    assert (
        before_counts.manifest_temp_write == baseline_manifest_temp_writes
    ), "same-runtime replay must not durably write the Manifest temp file"
    assert (
        before_counts.manifest_replace == baseline_manifest_replaces
    ), "same-runtime replay must not atomically promote the Manifest"
    assert runtime.manifest_bytes() == before_manifest_bytes

    fresh = make_base_ai_comic_reopen_runtime(tmp_path)
    fresh_baseline = fresh.call_counts
    # Fresh runtime creation observes the test-scoped counter without
    # mutating it, so the cumulative Manifest counters equal the
    # accepted baseline and the fresh fake effect fields start at zero.
    assert fresh_baseline.image_submit == 0
    assert fresh_baseline.voice_preview == 0
    assert fresh_baseline.voice_submit == 0
    assert fresh_baseline.review_analyze == 0
    assert fresh_baseline.renderer_version == 0
    assert fresh_baseline.renderer_doctor == 0
    assert fresh_baseline.renderer_run == 0
    assert (
        fresh_baseline.manifest_temp_write == baseline_manifest_temp_writes
    )
    assert fresh_baseline.manifest_replace == baseline_manifest_replaces
    fresh_replay = fresh.run_full_acceptance()
    assert fresh_replay == final
    assert fresh.call_counts == fresh_baseline, (
        "fresh-runtime replay must add zero call-count effects"
    )
    assert fresh.manifest_bytes() == before_manifest_bytes

    reopened = load_production_project(tmp_path / "project.yaml")
    assert reopened.manifest.final_acceptance_state is not None
    assert reopened.manifest.final_acceptance_state.active_receipt is not None
    assert (
        reopened.manifest.final_acceptance_state.active_receipt
        == final.acceptance_pointer
    )
    assert reopened.manifest.active_render_state == final.render_state
    assert final_mp4_sha == hashlib.sha256(final.output_path.read_bytes()).hexdigest()
    assert final.mp4_sha256 == final_mp4_sha
    assert final.render_output_sha256 == final_mp4_sha

    # TEST-008 — exact durable reopen of the final RepairOutcomeReceipt from
    # pointer.path, with file SHA, semantic content hash, repair_id, rerender
    # state, and rerender MP4 bound to the final accepted/current artifacts.
    pointer = final.repair_outcome_pointer
    receipt_bytes = (tmp_path / pointer.path).read_bytes()
    assert (
        hashlib.sha256(receipt_bytes).hexdigest() == pointer.file_sha256
    )
    assert pointer.content_hash == final.repair_outcome_receipt.content_hash
    assert pointer.repair_id == final.repair_outcome_repair_id
    assert verify_artifact_hash(final.repair_outcome_receipt)
    assert (
        final.repair_outcome_receipt.rerender_state
        == reopened.manifest.active_render_state
    )
    assert (
        final.repair_outcome_receipt.rerender_state
        == final.acceptance_receipt.render_state
    )
    assert (
        final.repair_outcome_receipt.rerender_output_sha256
        == final.mp4_sha256
    )
    assert (
        final.repair_outcome_receipt.rerender_output_sha256
        == final.acceptance_receipt.render_output_sha256
    )
    assert verify_artifact_hash(final.acceptance_receipt)
    assert final.acceptance_id == final.acceptance_receipt.acceptance_id


def test_base_ai_comic_replay_rejects_missing_or_tampered_repair_outcome(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime = project_factory.make_base_ai_comic_e2e_runtime(tmp_path)
    _forbid_network_and_secret_access(monkeypatch)
    final = runtime.run_full_acceptance()

    pointer = final.repair_outcome_pointer
    receipt_path = tmp_path / pointer.path
    receipt_bytes = receipt_path.read_bytes()

    # Case 1: missing repair outcome file -> reopen must fail because the
    # project loader does not verify repair outcome bytes itself.
    receipt_path.unlink()
    with pytest.raises(FileNotFoundError):
        runtime.run_full_acceptance()

    # Case 2: tampered repair outcome file with mismatched SHA -> reopen must
    # raise the exact reopened SHA binding assertion before model parsing.
    tampered = bytearray(receipt_bytes)
    tampered[0] = (tampered[0] + 1) % 256
    receipt_path.write_bytes(bytes(tampered))
    with pytest.raises(AssertionError, match="file SHA"):
        runtime.run_full_acceptance()
