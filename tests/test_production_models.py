from collections import UserDict
from pathlib import Path

import pytest
from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import canonical_sha256, seal_artifact, verify_artifact_hash
from ai_video.production.models import (
    CompositionDirective,
    DurationPolicy,
    MotionDirective,
    ProductionManifest,
    ProjectSnapshotPointer,
    RecoveryDisposition,
    RecoveryItem,
    RecoveryReport,
    RegistrySnapshotPointer,
    RendererPolicy,
    SourceReference,
    StateCommitAttempt,
    StateCommitStatus,
    Story,
    StoryBeat,
)


ZERO_HASH = "0" * 64
ONE_HASH = "1" * 64


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


def make_state_manifest(**overrides: object) -> ProductionManifest:
    data: dict[str, object] = {
        "project_id": "comic-demo",
        "manifest_revision": 1,
        "active_project": make_project_pointer(),
        "active_registry": make_registry_pointer(),
    }
    data.update(overrides)
    return ProductionManifest(**data)


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
