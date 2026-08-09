from collections import UserDict
from pathlib import Path

import pytest
from pydantic import ValidationError

import ai_video.production as production
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256, seal_artifact, verify_artifact_hash
from ai_video.production.models import (
    CompositionLayerSpec,
    CompositionSpec,
    CompositionDirective,
    DeliveryProfile,
    DurationPolicy,
    MeasuredRenderMetadata,
    MotionDirective,
    ProductionManifest,
    ProjectSnapshotPointer,
    RecoveryDisposition,
    RecoveryItem,
    RecoveryReport,
    RegistrySnapshotPointer,
    RenderArtifactPointer,
    RenderOutputPointer,
    RenderReceipt,
    RendererAssetBinding,
    RendererCheckReceipt,
    RendererIdentity,
    RendererPolicy,
    RendererSelectionReceipt,
    RendererSourceReceipt,
    RenderSourceBundlePointer,
    RenderSourceFilePointer,
    RenderStateSnapshot,
    RenderStateSnapshotPointer,
    ResolvedTimeline,
    ResolvedVisualSpan,
    SourceReference,
    StateCommitAttempt,
    StateCommitStatus,
    Story,
    StoryBeat,
)


ZERO_HASH = "0" * 64
ONE_HASH = "1" * 64
TWO_HASH = "2" * 64
THREE_HASH = "3" * 64
FOUR_HASH = "4" * 64
FIVE_HASH = "5" * 64
SIX_HASH = "6" * 64
SEVEN_HASH = "7" * 64
EIGHT_HASH = "8" * 64
NINE_HASH = "9" * 64


def make_project_pointer() -> ProjectSnapshotPointer:
    return ProjectSnapshotPointer(
        path=Path("project.yaml"),
        revision=1,
        content_hash=ZERO_HASH,
        file_sha256=ONE_HASH,
    )


def make_registry_pointer() -> RegistrySnapshotPointer:
    return RegistrySnapshotPointer(
        path=Path(f"assets/registry.{ZERO_HASH}.json"),
        revision_id=ZERO_HASH,
        content_hash=ZERO_HASH,
        file_sha256=ONE_HASH,
    )


def make_canonical_project_pointer(
    *, content_hash: str = ZERO_HASH, file_sha256: str = ONE_HASH
) -> ProjectSnapshotPointer:
    return ProjectSnapshotPointer(
        path=Path(f"state/projects/project.1.{content_hash}.yaml"),
        revision=1,
        content_hash=content_hash,
        file_sha256=file_sha256,
    )


def make_alternate_registry_pointer() -> RegistrySnapshotPointer:
    return RegistrySnapshotPointer(
        path=Path(f"assets/registry.{TWO_HASH}.json"),
        revision_id=TWO_HASH,
        content_hash=TWO_HASH,
        file_sha256=THREE_HASH,
    )


def make_render_state_pointer(content_hash: str = THREE_HASH) -> RenderStateSnapshotPointer:
    return RenderStateSnapshotPointer(
        path=Path(f"state/render/states/{content_hash}.json"),
        revision=1,
        content_hash=content_hash,
        file_sha256=ZERO_HASH,
    )


def make_state_manifest(**overrides: object) -> ProductionManifest:
    data: dict[str, object] = {
        "project_id": "comic-demo",
        "manifest_revision": 1,
        "active_project": make_project_pointer(),
        "active_registry": make_registry_pointer(),
    }
    data.update(overrides)
    return ProductionManifest(**data)


def versioned_fields(artifact_id: str, content_hash: str) -> dict[str, object]:
    return {
        "artifact_id": artifact_id,
        "revision": 1,
        "content_hash": content_hash,
        "creation_receipt_id": f"receipt-{artifact_id}",
        "source_provenance": (
            SourceReference(kind="derived", reference="p3-test-fixture"),
        ),
    }


def make_renderer_selection() -> RendererSelectionReceipt:
    return RendererSelectionReceipt(
        receipt_id="select-1",
        attempt_id="attempt-1",
        requested_kind="hyperframes",
        selected_kinds=("hyperframes",),
        renderer_version="0.7.103",
        timeline_fingerprint=FOUR_HASH,
        current_project=make_project_pointer(),
        current_registry=make_registry_pointer(),
    )


def make_resolved_timeline() -> ResolvedTimeline:
    return ResolvedTimeline(
        **versioned_fields("timeline-1", TWO_HASH),
        timeline_id="timeline-1",
        composition_spec_id="composition-1",
        composition_spec_revision=1,
        composition_spec_hash=THREE_HASH,
        delivery_profile=DeliveryProfile(width=320, height=180, fps=24),
        sample_rate=48_000,
        renderer=RendererIdentity(kind="hyperframes", version="0.7.103"),
        visual_spans=(
            ResolvedVisualSpan(
                layer_id="layer-1",
                shot_id="shot-1",
                asset_role="primary_image",
                asset_id="asset-1",
                asset_sha256=FIVE_HASH,
                asset_mime_type="image/png",
                materialized_path=Path(f"assets/files/{FIVE_HASH}.png"),
                start_frame=0,
                duration_frames=48,
                start_sample=0,
                duration_samples=96_000,
                trim_start_frame=0,
                transform={},
                opacity_milli=1000,
                z_index=0,
            ),
        ),
        total_frames=48,
        total_samples=96_000,
        composition_fingerprint=FOUR_HASH,
    )


def make_source_bundle() -> RenderSourceBundlePointer:
    root = Path(f"state/render/sources/{SIX_HASH}")
    return RenderSourceBundlePointer(
        root_path=root,
        bundle_sha256=SIX_HASH,
        index=RenderSourceFilePointer(
            path=root / "index.html",
            file_sha256=SEVEN_HASH,
            size_bytes=100,
        ),
        assets=(
            RenderSourceFilePointer(
                path=root / "assets" / f"{FIVE_HASH}.png",
                file_sha256=FIVE_HASH,
                size_bytes=10,
            ),
        ),
    )


def make_source_receipt() -> RendererSourceReceipt:
    return RendererSourceReceipt(
        **versioned_fields("source-receipt-1", EIGHT_HASH),
        attempt_id="attempt-1",
        renderer=RendererIdentity(kind="hyperframes", version="0.7.103"),
        timeline_fingerprint=FOUR_HASH,
        source_bundle=make_source_bundle(),
        source_sha256=SEVEN_HASH,
        asset_bindings=(
            RendererAssetBinding(
                asset_id="asset-1",
                asset_sha256=FIVE_HASH,
                asset_mime_type="image/png",
                materialized_path=Path(
                    f"state/render/sources/{SIX_HASH}/assets/{FIVE_HASH}.png"
                ),
            ),
        ),
        checks=(
            RendererCheckReceipt(
                command="lint",
                tool_version="0.7.103",
                exit_code=0,
                stdout_sha256=ZERO_HASH,
                stderr_sha256=ZERO_HASH,
                error_count=0,
                warning_count=0,
            ),
            RendererCheckReceipt(
                command="check",
                tool_version="0.7.103",
                exit_code=0,
                stdout_sha256=ZERO_HASH,
                stderr_sha256=ZERO_HASH,
                error_count=0,
                warning_count=0,
            ),
        ),
    )


def make_render_receipt() -> RenderReceipt:
    return RenderReceipt(
        **versioned_fields("render-receipt-1", NINE_HASH),
        attempt_id="attempt-1",
        renderer=RendererIdentity(kind="hyperframes", version="0.7.103"),
        timeline_fingerprint=FOUR_HASH,
        source_sha256=SEVEN_HASH,
        source_bundle_sha256=SIX_HASH,
        asset_hashes=(FIVE_HASH,),
        output_path=Path(f"state/render/outputs/{ONE_HASH}.mp4"),
        output_sha256=ONE_HASH,
        output_size_bytes=200,
        measured=MeasuredRenderMetadata(
            width=320,
            height=180,
            fps_num=24,
            fps_den=1,
            duration_frames=48,
            codec_name="h264",
        ),
        decoded_frame_fingerprint=TWO_HASH,
    )


def make_render_state_snapshot() -> RenderStateSnapshot:
    return RenderStateSnapshot(
        **versioned_fields("render-state-1", THREE_HASH),
        attempt_id="attempt-1",
        project=make_project_pointer(),
        registry=make_registry_pointer(),
        renderer_selection=make_renderer_selection(),
        renderer=RendererIdentity(kind="hyperframes", version="0.7.103"),
        timeline_fingerprint=FOUR_HASH,
        source_sha256=SEVEN_HASH,
        source_bundle_sha256=SIX_HASH,
        asset_hashes=(FIVE_HASH,),
        timeline=RenderArtifactPointer(
            path=Path(f"state/render/timelines/{TWO_HASH}.json"),
            revision=1,
            content_hash=TWO_HASH,
            file_sha256=ZERO_HASH,
        ),
        source_bundle=make_source_bundle(),
        source_receipt=RenderArtifactPointer(
            path=Path(f"state/render/source-receipts/{EIGHT_HASH}.json"),
            revision=1,
            content_hash=EIGHT_HASH,
            file_sha256=ZERO_HASH,
        ),
        render_receipt=RenderArtifactPointer(
            path=Path(f"state/render/render-receipts/{NINE_HASH}.json"),
            revision=1,
            content_hash=NINE_HASH,
            file_sha256=ZERO_HASH,
        ),
        output=RenderOutputPointer(
            path=Path(f"state/render/outputs/{ONE_HASH}.mp4"),
            file_sha256=ONE_HASH,
            size_bytes=200,
        ),
    )


def test_resolved_timeline_requires_integer_boundaries():
    timeline = make_resolved_timeline()

    assert timeline.visual_spans[0].start_frame == 0
    assert timeline.visual_spans[0].duration_frames == 48
    assert timeline.visual_spans[0].start_sample == 0
    assert timeline.visual_spans[0].duration_samples == 96_000

    data = timeline.model_dump(mode="json")
    data["visual_spans"][0]["start_frame"] = 0.5
    with pytest.raises(ValidationError):
        ResolvedTimeline.model_validate(data)


def test_render_receipt_rejects_unknown_fields():
    data = make_render_receipt().model_dump(mode="json")
    data["renderer_fallback"] = "remotion"

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        RenderReceipt.model_validate(data)


def test_renderer_source_receipt_fixes_index_and_check_identity():
    receipt = make_source_receipt()

    assert receipt.source_sha256 == receipt.source_bundle.index.file_sha256
    assert tuple(item.command for item in receipt.checks) == ("lint", "check")


def test_renderer_selection_allows_one_selected_renderer():
    with pytest.raises(ValidationError):
        RendererSelectionReceipt(
            receipt_id="select-1",
            attempt_id="attempt-1",
            requested_kind="hyperframes",
            selected_kinds=("hyperframes", "remotion"),
            renderer_version="0.7.103",
            timeline_fingerprint=FOUR_HASH,
            current_project=make_project_pointer(),
            current_registry=make_registry_pointer(),
        )


def test_renderer_selection_rejects_a_selected_renderer_other_than_requested():
    data = make_renderer_selection().model_dump(mode="python")
    data["requested_kind"] = "remotion"

    with pytest.raises(ValidationError, match="requested"):
        RendererSelectionReceipt.model_validate(data)


def test_render_attempt_requires_selection_attempt_id_to_match():
    selection = make_renderer_selection().model_copy(
        update={"attempt_id": "attempt-other"}
    )

    with pytest.raises(ValidationError, match="attempt identity"):
        StateCommitAttempt(
            attempt_id="attempt-1",
            operation="render_state",
            status=StateCommitStatus.RUNNING,
            base_manifest_revision=1,
            base_project=make_project_pointer(),
            base_registry=make_registry_pointer(),
            candidate_artifacts_hash=ZERO_HASH,
            renderer_selection=selection,
            started_at="2026-08-09T00:00:00+00:00",
        )


@pytest.mark.parametrize(
    "candidate_fields",
    [
        {"candidate_render_state": make_render_state_pointer()},
        {"candidate_project": make_canonical_project_pointer()},
        {"candidate_registry": make_registry_pointer()},
        {
            "candidate_render_state": make_render_state_pointer(),
            "candidate_project": make_canonical_project_pointer(),
        },
        {
            "candidate_render_state": make_render_state_pointer(),
            "candidate_registry": make_registry_pointer(),
        },
        {
            "candidate_project": make_canonical_project_pointer(),
            "candidate_registry": make_registry_pointer(),
        },
    ],
)
def test_render_attempt_rejects_partial_candidate_bundle(candidate_fields):
    with pytest.raises(ValidationError, match="candidate bundle"):
        StateCommitAttempt(
            attempt_id="attempt-1",
            operation="render_state",
            status=StateCommitStatus.RUNNING,
            base_manifest_revision=1,
            base_project=make_canonical_project_pointer(),
            base_registry=make_registry_pointer(),
            candidate_artifacts_hash=ZERO_HASH,
            renderer_selection=make_renderer_selection().model_copy(
                update={"current_project": make_canonical_project_pointer()}
            ),
            started_at="2026-08-09T00:00:00+00:00",
            **candidate_fields,
        )


def test_render_attempt_candidate_bundle_requires_activate_phase():
    with pytest.raises(ValidationError, match="activate"):
        StateCommitAttempt(
            attempt_id="attempt-1",
            operation="render_state",
            status=StateCommitStatus.RUNNING,
            base_manifest_revision=1,
            base_project=make_canonical_project_pointer(),
            base_registry=make_registry_pointer(),
            candidate_project=make_canonical_project_pointer(),
            candidate_registry=make_registry_pointer(),
            candidate_artifacts_hash=ZERO_HASH,
            candidate_render_state=make_render_state_pointer(),
            renderer_selection=make_renderer_selection().model_copy(
                update={"current_project": make_canonical_project_pointer()}
            ),
            render_phase="render",
            started_at="2026-08-09T00:00:00+00:00",
        )


def test_render_attempt_accepts_complete_activate_candidate_bundle():
    attempt = StateCommitAttempt(
        attempt_id="attempt-1",
        operation="render_state",
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=1,
        base_project=make_canonical_project_pointer(),
        base_registry=make_registry_pointer(),
        candidate_project=make_canonical_project_pointer(),
        candidate_registry=make_registry_pointer(),
        candidate_artifacts_hash=ZERO_HASH,
        candidate_render_state=make_render_state_pointer(),
        renderer_selection=make_renderer_selection().model_copy(
            update={"current_project": make_canonical_project_pointer()}
        ),
        render_phase="activate",
        started_at="2026-08-09T00:00:00+00:00",
    )

    assert attempt.candidate_render_state == make_render_state_pointer()


@pytest.mark.parametrize("mismatch", ["project", "registry", "render_state"])
def test_manifest_running_render_attempt_requires_current_base_identity(mismatch):
    active_render = make_render_state_pointer()
    base_project = make_project_pointer()
    base_registry = make_registry_pointer()
    base_render = active_render
    if mismatch == "project":
        base_project = make_canonical_project_pointer(
            content_hash=TWO_HASH, file_sha256=THREE_HASH
        )
    elif mismatch == "registry":
        base_registry = make_alternate_registry_pointer()
    else:
        base_render = make_render_state_pointer(FOUR_HASH)
    selection = make_renderer_selection().model_copy(
        update={
            "current_project": base_project,
            "current_registry": base_registry,
        }
    )
    attempt = StateCommitAttempt(
        attempt_id="attempt-1",
        operation="render_state",
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=1,
        base_project=base_project,
        base_registry=base_registry,
        base_render_state=base_render,
        candidate_artifacts_hash=ZERO_HASH,
        renderer_selection=selection,
        render_phase="selection",
        started_at="2026-08-09T00:00:00+00:00",
    )

    with pytest.raises(ValidationError, match="active identity"):
        make_state_manifest(
            schema_version="2.1",
            active_render_state=active_render,
            attempts=(attempt,),
        )


def test_manifest_allows_historical_terminal_render_attempt_from_an_old_base():
    old_project = make_canonical_project_pointer(
        content_hash=TWO_HASH, file_sha256=THREE_HASH
    )
    old_registry = make_alternate_registry_pointer()
    attempt = StateCommitAttempt(
        attempt_id="attempt-1",
        operation="render_state",
        status=StateCommitStatus.FAILED,
        base_manifest_revision=1,
        base_project=old_project,
        base_registry=old_registry,
        base_render_state=make_render_state_pointer(FOUR_HASH),
        candidate_artifacts_hash=ZERO_HASH,
        renderer_selection=make_renderer_selection().model_copy(
            update={
                "current_project": old_project,
                "current_registry": old_registry,
            }
        ),
        render_phase="selection",
        started_at="2026-08-09T00:00:00+00:00",
        finished_at="2026-08-09T00:00:01+00:00",
        error_code="renderer_unavailable",
        error_message="safe",
    )

    manifest = make_state_manifest(
        schema_version="2.1",
        active_render_state=make_render_state_pointer(),
        attempts=(attempt,),
    )

    assert manifest.attempts == (attempt,)


def test_manifest_20_rejects_render_state_and_render_attempts():
    render_pointer = RenderStateSnapshotPointer(
        path=Path(f"state/render/states/{THREE_HASH}.json"),
        revision=1,
        content_hash=THREE_HASH,
        file_sha256=ZERO_HASH,
    )
    with pytest.raises(ValidationError, match="2.0"):
        make_state_manifest(active_render_state=render_pointer)

    render_attempt = StateCommitAttempt(
        attempt_id="attempt-1",
        operation="render_state",
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=1,
        base_project=make_project_pointer(),
        base_registry=make_registry_pointer(),
        candidate_artifacts_hash=ZERO_HASH,
        started_at="2026-08-09T00:00:00+00:00",
        renderer_selection=make_renderer_selection(),
    )
    with pytest.raises(ValidationError, match="2.0"):
        make_state_manifest(attempts=(render_attempt,))


def test_manifest_20_preserves_historical_custom_nonempty_operation_without_rewrite():
    attempt = StateCommitAttempt(
        attempt_id="attempt-custom",
        operation="historical_custom_commit",
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=1,
        base_project=make_project_pointer(),
        base_registry=make_registry_pointer(),
        candidate_artifacts_hash=ZERO_HASH,
        started_at="2026-08-09T00:00:00+00:00",
    )

    manifest = make_state_manifest(attempts=(attempt,))

    assert manifest.schema_version == "2.0"
    assert manifest.attempts[0].operation == "historical_custom_commit"
    assert manifest.model_dump(mode="json")["attempts"][0]["operation"] == (
        "historical_custom_commit"
    )
    assert "active_render_state" not in manifest.model_dump(mode="json")
    assert not {
        "base_render_state",
        "candidate_render_state",
        "renderer_selection",
        "render_phase",
    }.intersection(manifest.model_dump(mode="json")["attempts"][0])


def test_manifest_21_accepts_none_or_one_render_state_pointer():
    empty = make_state_manifest(schema_version="2.1", active_render_state=None)
    pointer = RenderStateSnapshotPointer(
        path=Path(f"state/render/states/{THREE_HASH}.json"),
        revision=1,
        content_hash=THREE_HASH,
        file_sha256=ZERO_HASH,
    )
    active = make_state_manifest(schema_version="2.1", active_render_state=pointer)

    assert empty.active_render_state is None
    assert active.active_render_state == pointer


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("attempt_id", "attempt-other"),
        (
            "renderer",
            RendererIdentity(kind="hyperframes", version="0.7.102"),
        ),
        ("timeline_fingerprint", ZERO_HASH),
        ("source_sha256", ZERO_HASH),
        ("source_bundle_sha256", ZERO_HASH),
        ("asset_hashes", (ZERO_HASH,)),
        (
            "output",
            {
                "path": Path(f"state/render/outputs/{ONE_HASH}.mp4"),
                "file_sha256": ZERO_HASH,
                "size_bytes": 200,
            },
        ),
    ],
)
def test_render_state_snapshot_rejects_mixed_attempt_renderer_timeline_source_asset_or_output_identity(
    field, replacement
):
    data = make_render_state_snapshot().model_dump(mode="python")
    data[field] = replacement

    with pytest.raises(ValidationError, match="identity|canonical"):
        RenderStateSnapshot.model_validate(data)


@pytest.mark.parametrize("field", ["asset_role", "asset_id"])
def test_composition_layer_requires_exact_declared_asset_role_and_id(field):
    data = {
        "layer_id": "layer-1",
        "shot_id": "shot-1",
        "asset_role": "primary_image",
        "asset_id": "asset-1",
    }
    data[field] = ""

    with pytest.raises(ValidationError):
        CompositionLayerSpec.model_validate(data)

    layer = CompositionLayerSpec.model_validate(
        {
            "layer_id": "layer-1",
            "shot_id": "shot-1",
            "asset_role": "primary_image",
            "asset_id": "asset-1",
        }
    )
    spec = CompositionSpec(
        **versioned_fields("composition-1", THREE_HASH),
        composition_id="composition-1",
        shot_ids=("shot-1",),
        layers=(layer,),
        delivery_profile=DeliveryProfile(width=320, height=180, fps=24),
    )
    assert (spec.layers[0].asset_role, spec.layers[0].asset_id) == (
        "primary_image",
        "asset-1",
    )


@pytest.mark.parametrize(
    "path",
    [
        Path("state/render/outputs/render.mp4"),
        Path(f"state/render/outputs/{ZERO_HASH}.mov"),
        Path(f"state/render/outputs/{ZERO_HASH[:32]}.mp4"),
        Path(f"state/render/outputs/{TWO_HASH}.mp4"),
    ],
)
def test_render_receipt_requires_canonical_durable_output_path(path):
    data = make_render_receipt().model_dump(mode="python")
    data["output_path"] = path

    with pytest.raises(ValidationError, match="canonical"):
        RenderReceipt.model_validate(data)


@pytest.mark.parametrize("field", ["project", "registry"])
def test_render_state_snapshot_fixes_project_registry_and_source_bundle_provenance(
    field,
):
    data = make_render_state_snapshot().model_dump(mode="python")
    if field == "project":
        data[field] = make_project_pointer().model_copy(
            update={"file_sha256": TWO_HASH}
        )
    else:
        data[field] = make_registry_pointer().model_copy(
            update={"file_sha256": TWO_HASH}
        )

    with pytest.raises(ValidationError, match="identity"):
        RenderStateSnapshot.model_validate(data)


def test_render_models_are_frozen_and_forbid_extra_fields():
    state = make_render_state_snapshot()
    with pytest.raises(ValidationError, match="Instance is frozen"):
        state.attempt_id = "attempt-other"  # type: ignore[misc]
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        RenderStateSnapshot.model_validate(
            {**state.model_dump(mode="python"), "unexpected": True}
        )


def test_package_exports_only_the_stable_p3_schema_surface():
    stable_p3_exports = {
        "CompositionSpec",
        "ResolvedTimeline",
        "RendererSelectionReceipt",
        "RendererSourceReceipt",
        "RenderReceipt",
        "RenderArtifactPointer",
        "RenderSourceFilePointer",
        "RenderSourceBundlePointer",
        "RenderOutputPointer",
        "RenderStateSnapshot",
        "RenderStateSnapshotPointer",
    }

    assert stable_p3_exports <= set(production.__all__)
    assert {
        "HyperFramesAdapter",
        "RendererRunner",
        "VerifiedRenderFile",
    }.isdisjoint(production.__all__)


def test_production_manifest_has_one_project_and_registry_pointer_owner():
    manifest = make_state_manifest()

    assert manifest.active_project.path == Path("project.yaml")
    assert manifest.active_registry.revision_id == ZERO_HASH
    assert not hasattr(manifest, "active_project_revision")
    assert not hasattr(manifest, "active_project_content_hash")
    assert not hasattr(manifest, "active_registry_revision")


@pytest.mark.parametrize(
    ("code", "name", "value"),
    [
        (ErrorCode.PRODUCTION_STATE_INVALID, "PRODUCTION_STATE_INVALID", "production_state_invalid"),
        (ErrorCode.PRODUCTION_STATE_BUSY, "PRODUCTION_STATE_BUSY", "production_state_busy"),
        (
            ErrorCode.PRODUCTION_STATE_COMMIT_FAILED,
            "PRODUCTION_STATE_COMMIT_FAILED",
            "production_state_commit_failed",
        ),
        (
            ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED,
            "PRODUCTION_STATE_RECOVERY_FAILED",
            "production_state_recovery_failed",
        ),
        (
            ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN,
            "PRODUCTION_STATE_OUTCOME_UNKNOWN",
            "production_state_outcome_unknown",
        ),
        (
            ErrorCode.PRODUCTION_STATE_UNSUPPORTED,
            "PRODUCTION_STATE_UNSUPPORTED",
            "production_state_unsupported",
        ),
    ],
)
def test_production_state_error_codes_are_non_retryable_by_default(code, name, value):
    assert code.name == name
    assert code.value == value
    assert AiVideoError(code=code, user_message="safe").retryable is False


@pytest.mark.parametrize(
    ("code", "value"),
    [
        (ErrorCode.COMPOSITION_INVALID, "composition_invalid"),
        (ErrorCode.RENDERER_UNAVAILABLE, "renderer_unavailable"),
        (ErrorCode.RENDERER_SOURCE_INVALID, "renderer_source_invalid"),
        (ErrorCode.RENDER_FAILED, "render_failed"),
    ],
)
def test_p3_error_codes_are_typed_and_non_retryable_by_default(code, value):
    assert code.value == value
    assert AiVideoError(code=code, user_message="safe").retryable is False


@pytest.mark.parametrize(
    ("pointer_type", "data"),
    [
        (
            ProjectSnapshotPointer,
            {
                "revision": 1,
                "content_hash": ZERO_HASH,
                "file_sha256": ONE_HASH,
            },
        ),
        (
            RegistrySnapshotPointer,
            {
                "revision_id": ZERO_HASH,
                "content_hash": ZERO_HASH,
                "file_sha256": ONE_HASH,
            },
        ),
    ],
)
@pytest.mark.parametrize(
    "path",
    [
        Path("/tmp/snapshot.yaml"),
        Path("state/../snapshot.yaml"),
        Path(""),
        Path("."),
    ],
)
def test_snapshot_pointers_reject_absolute_or_parent_relative_paths(pointer_type, data, path):
    with pytest.raises(ValidationError, match="clean and project-relative"):
        pointer_type(path=path, **data)


def test_registry_snapshot_pointer_requires_revision_to_match_content_hash():
    with pytest.raises(ValidationError, match="revision_id"):
        RegistrySnapshotPointer(
            path=Path("assets/registry.json"),
            revision_id=ZERO_HASH,
            content_hash=ONE_HASH,
            file_sha256=ONE_HASH,
        )


@pytest.mark.parametrize(
    "path",
    [
        Path("state/projects/arbitrary.yaml"),
        Path(f"state/projects/project.2.{ONE_HASH}.yaml"),
    ],
)
def test_project_snapshot_pointer_requires_entrypoint_or_identity_path(path):
    with pytest.raises(ValidationError, match="canonical project snapshot path"):
        ProjectSnapshotPointer(
            path=path,
            revision=2,
            content_hash=ZERO_HASH,
            file_sha256=ONE_HASH,
        )


@pytest.mark.parametrize(
    "path",
    [
        Path("assets/registry.json"),
        Path(f"assets/registry.{ONE_HASH}.json"),
    ],
)
def test_registry_snapshot_pointer_requires_identity_path(path):
    with pytest.raises(ValidationError, match="canonical registry snapshot path"):
        RegistrySnapshotPointer(
            path=path,
            revision_id=ZERO_HASH,
            content_hash=ZERO_HASH,
            file_sha256=ONE_HASH,
        )


def test_p2a_models_are_frozen_and_forbid_extra_fields():
    pointer = make_project_pointer()
    with pytest.raises(ValidationError, match="Instance is frozen"):
        pointer.revision = 2
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        ProjectSnapshotPointer.model_validate(
            {**pointer.model_dump(), "unexpected": True}
        )


def test_state_attempt_rejects_unknown_fallback_pointer():
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        StateCommitAttempt.model_validate(
            {
                "attempt_id": "attempt-1",
                "operation": "commit_project_registry",
                "status": "running",
                "base_manifest_revision": 1,
                "base_project": make_project_pointer().model_dump(mode="python"),
                "base_registry": make_registry_pointer().model_dump(mode="python"),
                "candidate_artifacts_hash": ZERO_HASH,
                "started_at": "2026-08-09T00:00:00+00:00",
                "fallback_manifest": "state/manifest.backup.json",
            }
        )


def test_state_attempt_requires_base_snapshot_pair():
    with pytest.raises(ValidationError, match="base_project"):
        StateCommitAttempt(
            attempt_id="attempt-1",
            operation="commit_project_registry",
            status=StateCommitStatus.RUNNING,
            base_manifest_revision=1,
            candidate_artifacts_hash=ZERO_HASH,
            started_at="2026-08-09T00:00:00+00:00",
        )
    attempt = StateCommitAttempt(
        attempt_id="attempt-1",
        operation="commit_project_registry",
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=1,
        base_project=make_project_pointer(),
        base_registry=make_registry_pointer(),
        candidate_artifacts_hash=ZERO_HASH,
        started_at="2026-08-09T00:00:00+00:00",
    )
    with pytest.raises(ValidationError, match="Instance is frozen"):
        attempt.base_project = make_project_pointer()  # type: ignore[misc]


def test_state_attempt_base_snapshot_pointers_must_be_clean():
    with pytest.raises(ValidationError, match="clean and project-relative"):
        StateCommitAttempt.model_validate(
            {
                "attempt_id": "attempt-1",
                "operation": "commit_project_registry",
                "status": "running",
                "base_manifest_revision": 1,
                "base_project": {
                    **make_project_pointer().model_dump(mode="json"),
                    "path": "state/../project.yaml",
                },
                "base_registry": make_registry_pointer().model_dump(mode="json"),
                "candidate_artifacts_hash": ZERO_HASH,
                "started_at": "2026-08-09T00:00:00+00:00",
            }
        )


@pytest.mark.parametrize(
    "status",
    [
        StateCommitStatus.FAILED,
        StateCommitStatus.INTERRUPTED,
        StateCommitStatus.OUTCOME_UNKNOWN,
    ],
)
def test_terminal_state_attempts_require_sanitized_typed_error_fields(status):
    with pytest.raises(ValidationError, match="typed error fields"):
        StateCommitAttempt(
            attempt_id="attempt-1",
            operation="commit_project_registry",
            status=status,
            base_manifest_revision=1,
            base_project=make_project_pointer(),
            base_registry=make_registry_pointer(),
            candidate_artifacts_hash=ZERO_HASH,
            started_at="2026-08-09T00:00:00+00:00",
            finished_at="2026-08-09T00:00:01+00:00",
        )


def test_succeeded_state_attempt_requires_finished_at():
    with pytest.raises(ValidationError, match="require finished_at"):
        StateCommitAttempt(
            attempt_id="attempt-1",
            operation="commit_project_registry",
            status=StateCommitStatus.SUCCEEDED,
            base_manifest_revision=1,
            base_project=make_project_pointer(),
            base_registry=make_registry_pointer(),
            candidate_artifacts_hash=ZERO_HASH,
            started_at="2026-08-09T00:00:00+00:00",
        )


def test_production_manifest_rejects_duplicate_attempt_ids():
    attempt = StateCommitAttempt(
        attempt_id="attempt-1",
        operation="commit_project_registry",
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=1,
        base_project=make_project_pointer(),
        base_registry=make_registry_pointer(),
        candidate_artifacts_hash=ZERO_HASH,
        started_at="2026-08-09T00:00:00+00:00",
    )
    with pytest.raises(ValidationError, match="attempt IDs must be unique"):
        make_state_manifest(attempts=(attempt, attempt))


def test_recovery_models_are_strict_and_immutable():
    item = RecoveryItem(
        path=Path("state/.p2a-attempt-1-project.tmp"),
        disposition=RecoveryDisposition.PARTIAL_REMOVED,
        sha256=ZERO_HASH,
    )
    report = RecoveryReport(
        manifest_revision_before=1,
        manifest_revision_after=2,
        items=(item,),
    )
    assert report.items == (item,)
    with pytest.raises(ValidationError, match="Instance is frozen"):
        report.manifest_revision_after = 3


@pytest.mark.parametrize(
    "path",
    [
        Path("/tmp/recovery.tmp"),
        Path("state/../recovery.tmp"),
        Path(""),
        Path("."),
    ],
)
def test_recovery_item_rejects_non_file_or_non_relative_paths(path):
    with pytest.raises(ValidationError, match="clean and project-relative"):
        RecoveryItem(path=path, disposition=RecoveryDisposition.PARTIAL_REMOVED)


@pytest.mark.parametrize("sha256", ["A" * 64, "0" * 63, "g" * 64])
def test_recovery_item_sha256_must_be_lowercase_hex(sha256):
    with pytest.raises(ValidationError):
        RecoveryItem(
            path=Path("state/.p2a-attempt-1-project.tmp"),
            disposition=RecoveryDisposition.PARTIAL_REMOVED,
            sha256=sha256,
        )


@pytest.mark.parametrize("before, after", [(0, 1), (1, 0), (2, 1)])
def test_recovery_report_requires_ordered_positive_manifest_revisions(before, after):
    with pytest.raises(ValidationError):
        RecoveryReport(
            manifest_revision_before=before,
            manifest_revision_after=after,
            items=(),
        )


def test_recovery_report_allows_an_unchanged_manifest_revision():
    report = RecoveryReport(
        manifest_revision_before=1,
        manifest_revision_after=1,
        items=(),
    )
    assert report.manifest_revision_after == report.manifest_revision_before


@pytest.mark.parametrize(
    "contradictory_fields",
    [
        {"finished_at": "2026-08-09T00:00:01+00:00"},
        {"error_code": "production_state_commit_failed"},
        {"error_message": "safe"},
    ],
)
def test_running_state_attempt_rejects_terminal_fields(contradictory_fields):
    with pytest.raises(ValidationError):
        StateCommitAttempt(
            attempt_id="attempt-1",
            operation="commit_project_registry",
            status=StateCommitStatus.RUNNING,
            base_manifest_revision=1,
            base_project=make_project_pointer(),
            base_registry=make_registry_pointer(),
            candidate_artifacts_hash=ZERO_HASH,
            started_at="2026-08-09T00:00:00+00:00",
            **contradictory_fields,
        )


def test_succeeded_state_attempt_rejects_error_fields():
    with pytest.raises(ValidationError):
        StateCommitAttempt(
            attempt_id="attempt-1",
            operation="commit_project_registry",
            status=StateCommitStatus.SUCCEEDED,
            base_manifest_revision=1,
            base_project=make_project_pointer(),
            base_registry=make_registry_pointer(),
            candidate_artifacts_hash=ZERO_HASH,
            started_at="2026-08-09T00:00:00+00:00",
            finished_at="2026-08-09T00:00:01+00:00",
            error_code="production_state_commit_failed",
            error_message="safe",
        )


def test_state_attempt_requires_immutable_canonical_artifact_set_hash():
    artifact_hash = "a" * 64
    attempt = StateCommitAttempt(
        attempt_id="attempt-artifacts",
        operation="commit_project_registry",
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=1,
        base_project=make_project_pointer(),
        base_registry=make_registry_pointer(),
        candidate_artifacts_hash=artifact_hash,
        started_at="2026-08-09T00:00:00+00:00",
    )

    assert attempt.candidate_artifacts_hash == artifact_hash
    with pytest.raises(ValidationError, match="Instance is frozen"):
        attempt.candidate_artifacts_hash = "b" * 64  # type: ignore[misc]
    with pytest.raises(ValidationError):
        StateCommitAttempt(
            attempt_id="invalid-artifacts",
            operation="commit_project_registry",
            status=StateCommitStatus.RUNNING,
            base_manifest_revision=1,
            base_project=make_project_pointer(),
            base_registry=make_registry_pointer(),
            candidate_artifacts_hash="INVALID",
            started_at="2026-08-09T00:00:00+00:00",
        )


def make_story() -> Story:
    return Story(
        artifact_id="story-main",
        revision=1,
        content_hash="0" * 64,
        creation_receipt_id="receipt-story-1",
        source_provenance=[SourceReference(kind="user_input", reference="brief-1")],
        language="zh-CN",
        logline="一位侦探追查失踪的记忆。",
        synopsis="侦探在三幕故事中找到真相。",
        beats=[StoryBeat(beat_id="beat-1", summary="案件出现")],
        source_references=["source-novel-1"],
    )


def test_semantic_hash_ignores_mapping_order_and_content_hash():
    assert canonical_sha256({"b": 2, "a": 1, "content_hash": "x"}) == canonical_sha256(
        {"content_hash": "y", "a": 1, "b": 2}
    )


def test_sealed_artifact_detects_content_change():
    sealed = seal_artifact(make_story())
    assert verify_artifact_hash(sealed)
    assert not verify_artifact_hash(sealed.model_copy(update={"logline": "不同内容"}))


def test_artifact_hash_covers_receipt_and_provenance_envelope():
    sealed = seal_artifact(make_story())
    assert not verify_artifact_hash(
        sealed.model_copy(update={"creation_receipt_id": "receipt-story-2"})
    )


def test_domain_models_reject_unknown_fields():
    data = make_story().model_dump()
    data["unexpected"] = True
    with pytest.raises(ValidationError):
        Story.model_validate(data)


def test_domain_models_are_frozen():
    story = make_story()
    with pytest.raises(ValidationError, match="Instance is frozen"):
        story.logline = "不允许就地修改"


@pytest.mark.parametrize(
    "directive",
    [
        CompositionDirective(kind="fit", parameters={"mode": "cover"}),
        MotionDirective(kind="pan", parameters={"x": 1}),
    ],
)
def test_parameter_mappings_are_immutable(directive):
    with pytest.raises(TypeError, match="immutable"):
        directive.parameters["changed"] = 1


def test_default_parameter_mapping_is_immutable():
    directive = CompositionDirective(kind="fit")
    with pytest.raises(TypeError, match="immutable"):
        directive.parameters["mode"] = "cover"


def test_motion_parameters_reject_boolean_as_numeric_value():
    with pytest.raises(ValidationError, match="boolean"):
        MotionDirective(kind="pan", parameters={"x": True})


def test_motion_parameters_reject_boolean_from_generic_mapping():
    with pytest.raises(ValidationError, match="boolean"):
        MotionDirective(kind="pan", parameters=UserDict({"x": True}))


def test_fixed_duration_requires_seconds():
    with pytest.raises(ValidationError, match="requires seconds"):
        DurationPolicy(mode="fixed")


def test_duration_bounds_must_be_ordered():
    with pytest.raises(ValidationError, match="cannot exceed"):
        DurationPolicy(mode="content_driven", minimum_seconds=5, maximum_seconds=4)


def test_renderer_default_must_be_allowed():
    with pytest.raises(ValidationError, match="must be present"):
        RendererPolicy(allowed=["remotion"], default_preference="hyperframes")
