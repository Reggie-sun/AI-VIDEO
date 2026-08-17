from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import (
    AssetRegistrySnapshot,
    DependencyLifecycle,
    ProductionManifest,
    RecoveryDisposition,
    RegistrySnapshotPointer,
    StateCommitAttempt,
    StateCommitStatus,
    RendererKind,
    RendererSelectionReceipt,
)
from ai_video.production.project import load_production_project_candidate
from ai_video.production.paths import canonical_image_request_path
from ai_video.production.registry import registry_semantic_sha256
import ai_video.production.state_commit as state_commit
from ai_video.production.state_commit import (
    BeginRenderAttemptRequest,
    CommitPhase,
    ProductionStateCommitter,
    _owned_temp_name,
)
import production_project_factory as project_factory
from test_production_state_commit import (
    make_image_call_bundle,
    make_image_provider_result,
    make_qa_policy,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ZERO_HASH = "0" * 64


def _recover(root: Path):
    return state_commit.recover_production_state(root)


def _read_manifest(root: Path) -> ProductionManifest:
    return ProductionManifest.model_validate_json(
        (root / "state/manifest.json").read_text(encoding="utf-8")
    )


def _write_manifest(root: Path, manifest: ProductionManifest) -> None:
    (root / "state/manifest.json").write_text(
        manifest.model_dump_json(indent=2), encoding="utf-8"
    )


def _durable_tree_snapshot(root: Path) -> dict[Path, bytes]:
    return {
        path.relative_to(root): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file() and path.relative_to(root) != Path("state/commit.lock")
    }


def _make_inactive_image_candidate(root: Path) -> ProductionManifest:
    base_inputs = project_factory.make_p7_image_generation_base(root)
    request, preview, authorization = make_image_call_bundle(root)

    class _Provider:
        def generate(self, candidate, candidate_authorization, permit):
            assert permit._consume_image_generation_permit(
                request_fingerprint=candidate.request_fingerprint
            )
            return make_image_provider_result(
                candidate, candidate_authorization, project_factory._p7_png()
            )

    class _FailBeforeFinalReplace(ProductionStateCommitter):
        def _write_manifest_atomic(self, manifest, *, on_replace=None):
            attempt = next(
                (
                    item
                    for item in manifest.attempts
                    if item.attempt_id == request.attempt_id
                ),
                None,
            )
            if attempt is not None and attempt.image_phase == "activate":
                raise RuntimeError("injected before final image activation")
            return super()._write_manifest_atomic(manifest, on_replace=on_replace)

    with pytest.raises(AiVideoError):
        _FailBeforeFinalReplace(
            root,
            image_candidate_preparer=project_factory.make_p7_image_candidate_preparer(
                base_inputs
            ),
        ).generate_image_asset(request, preview, authorization, _Provider())
    return _read_manifest(root)


def test_recovery_marks_r1_voice_interrupted_without_submit(
    committed_project: Path,
) -> None:
    request = project_factory.make_voice_request(committed_project)
    preview, authorization = project_factory.make_voice_preview_and_authorization(request)
    writer = ProductionStateCommitter(committed_project)
    writer.begin_voice_generation(request, preview, authorization)

    report = writer.recover()
    recovered = _read_manifest(committed_project)

    assert report.manifest_revision_after == 3
    assert recovered.attempts[-1].status is StateCommitStatus.INTERRUPTED
    assert recovered.attempts[-1].voice_phase == "request"


def test_recovery_preserves_complete_inactive_image_candidate_and_interrupts(
    committed_project: Path,
) -> None:
    """Skipping exact eight-artifact proof must make this recovery test fail."""

    candidate = _make_inactive_image_candidate(committed_project)

    report = ProductionStateCommitter(committed_project).recover()
    recovered = _read_manifest(committed_project)
    attempt = recovered.attempts[-1]

    assert attempt.status is StateCommitStatus.INTERRUPTED
    assert attempt.image_phase == "candidate"
    assert attempt.error_code == ErrorCode.IMAGE_PROVIDER_OUTCOME_UNKNOWN.value
    assert (
        recovered.active_project,
        recovered.active_registry,
        recovered.active_dependency_graph,
    ) == (
        attempt.base_project,
        attempt.base_registry,
        attempt.base_dependency_graph,
    )
    for field in type(candidate).model_fields:
        if field not in {"manifest_revision", "attempts"}:
            assert getattr(recovered, field) == getattr(candidate, field)
    preserved = {
        item.path
        for item in report.items
        if item.disposition is RecoveryDisposition.INTERRUPTED_RECORDED
    }
    assert {
        attempt.candidate_project.path,
        attempt.candidate_registry.path,
        attempt.candidate_dependency_graph.path,
    }.issubset(preserved)


def test_recovery_rejects_mixed_image_project_registry_graph_tuple(
    committed_project: Path,
) -> None:
    candidate = _make_inactive_image_candidate(committed_project)
    attempt = candidate.attempts[-1]
    mixed = candidate.model_copy(
        update={"active_project": attempt.candidate_project}
    )
    _write_manifest(committed_project, mixed)

    with pytest.raises(AiVideoError) as exc_info:
        ProductionStateCommitter(committed_project).recover()

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED
    assert _read_manifest(committed_project) == mixed


def test_recovery_rejects_tampered_inactive_image_png(
    committed_project: Path,
) -> None:
    candidate = _make_inactive_image_candidate(committed_project)
    attempt = candidate.attempts[-1]
    registry = AssetRegistrySnapshot.model_validate_json(
        (committed_project / attempt.candidate_registry.path).read_bytes()
    )
    image = next(
        item for item in registry.assets if item.asset_id in attempt.candidate_image_asset_ids
    )
    (committed_project / image.artifact_path).write_bytes(b"tampered")

    with pytest.raises(AiVideoError) as exc_info:
        ProductionStateCommitter(committed_project).recover()

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED
    assert _read_manifest(committed_project) == candidate


def test_recovery_rejects_tampered_active_image_request_evidence(
    committed_project: Path,
) -> None:
    """Removing active P7 evidence reopen must make this tamper test fail."""

    base_inputs = project_factory.make_p7_image_generation_base(committed_project)
    request, preview, authorization = make_image_call_bundle(committed_project)

    class _Provider:
        def generate(self, candidate, candidate_authorization, permit):
            assert permit._consume_image_generation_permit(
                request_fingerprint=candidate.request_fingerprint
            )
            return make_image_provider_result(
                candidate,
                candidate_authorization,
                project_factory._p7_png(),
            )

    final = ProductionStateCommitter(
        committed_project,
        image_candidate_preparer=project_factory.make_p7_image_candidate_preparer(
            base_inputs
        ),
    ).generate_image_asset(request, preview, authorization, _Provider())
    request_path = committed_project / canonical_image_request_path(
        request.request_fingerprint
    )
    request_path.write_bytes(b"{}\n")

    with pytest.raises(AiVideoError) as exc_info:
        ProductionStateCommitter(committed_project).recover()

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED
    assert _read_manifest(committed_project) == final


@pytest.mark.parametrize(
    "artifact_key",
    ("preview_path", "authorization_path", "submit_intent_path"),
)
@pytest.mark.parametrize("mutation", ("missing", "tampered"))
def test_recovery_rejects_missing_or_tampered_active_image_submit_audit_evidence(
    tmp_path: Path,
    artifact_key: str,
    mutation: str,
) -> None:
    fixture = project_factory.make_p7_committed_project(tmp_path)
    artifact_path = tmp_path / fixture[artifact_key]
    if mutation == "missing":
        artifact_path.unlink()
    else:
        artifact_path.write_bytes(artifact_path.read_bytes() + b" ")
    manifest_path = tmp_path / "state/manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest_revision = _read_manifest(tmp_path).manifest_revision

    with pytest.raises(AiVideoError) as exc_info:
        ProductionStateCommitter(tmp_path).recover()

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED
    assert manifest_path.read_bytes() == manifest_bytes
    assert _read_manifest(tmp_path).manifest_revision == manifest_revision


def test_recovery_reopens_active_image_submit_audit_without_durable_writes(
    tmp_path: Path,
) -> None:
    fixture = project_factory.make_p7_committed_project(tmp_path)
    writer = ProductionStateCommitter(tmp_path)
    before = _durable_tree_snapshot(tmp_path)

    report = writer.recover()

    assert report.manifest_revision_before == fixture["manifest"].manifest_revision
    assert report.manifest_revision_after == fixture["manifest"].manifest_revision
    assert _durable_tree_snapshot(tmp_path) == before


def test_recovery_marks_image_submit_outcome_unknown_and_same_request_never_resubmits(
    committed_project: Path,
) -> None:
    project_factory.make_p7_image_generation_base(committed_project)
    request, preview, authorization = make_image_call_bundle(committed_project)
    writer = ProductionStateCommitter(committed_project)
    writer.begin_image_generation(request, preview, authorization)
    writer.record_image_submit_intent(request, preview, authorization)

    writer.recover()
    first = _read_manifest(committed_project)
    attempt = first.attempts[-1]
    assert attempt.status is StateCommitStatus.OUTCOME_UNKNOWN
    assert attempt.error_code == ErrorCode.IMAGE_PROVIDER_OUTCOME_UNKNOWN.value

    class _Provider:
        calls = 0

        def generate(self, candidate, candidate_authorization, permit):
            self.calls += 1
            raise AssertionError("same-request recovery replay must not call Provider")

    provider = _Provider()
    with pytest.raises(AiVideoError) as exc_info:
        writer.generate_image_asset(request, preview, authorization, provider)

    assert exc_info.value.code is ErrorCode.IMAGE_PROVIDER_OUTCOME_UNKNOWN
    assert provider.calls == 0
    assert _read_manifest(committed_project) == first


def test_recovery_preserves_p6_plus_p7_policy_and_stale_retained_render(
    committed_project: Path,
) -> None:
    base_inputs = project_factory.make_p7_image_generation_base(committed_project)
    writer = ProductionStateCommitter(committed_project)
    before = _read_manifest(committed_project)
    with_policy = writer.activate_qa_policy(
        make_qa_policy(),
        expected_manifest_revision=before.manifest_revision,
        attempt_id="p7-recovery-policy",
    )
    request, preview, authorization = make_image_call_bundle(committed_project)

    class _Provider:
        def generate(self, candidate, candidate_authorization, permit):
            assert permit._consume_image_generation_permit(
                request_fingerprint=candidate.request_fingerprint
            )
            return make_image_provider_result(
                candidate, candidate_authorization, project_factory._p7_png()
            )

    final = ProductionStateCommitter(
        committed_project,
        image_candidate_preparer=project_factory.make_p7_image_candidate_preparer(
            base_inputs
        ),
    ).generate_image_asset(request, preview, authorization, _Provider())
    assert final.active_qa_policy == with_policy.active_qa_policy
    assert final.active_render_state == with_policy.active_render_state
    render_states = tuple(
        item.lifecycle
        for item in final.dependency_states
        if item.node_id.startswith(
            ("composition:", "timeline:", "renderer-source:", "render:")
        )
    )
    assert render_states and all(
        lifecycle in {DependencyLifecycle.STALE, DependencyLifecycle.BLOCKED}
        for lifecycle in render_states
    )

    report = ProductionStateCommitter(committed_project).recover()

    assert report.manifest_revision_before == report.manifest_revision_after
    assert _read_manifest(committed_project) == final


def _crash_image_and_recover(
    root: Path,
    phase: CommitPhase,
    occurrence: int,
) -> StateCommitStatus | None:
    result = subprocess.run(
        [
            sys.executable,
            "tests/helpers/p2a_crash_worker.py",
            str(root),
            phase.value,
            str(occurrence),
            "image",
        ],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 91
    ProductionStateCommitter(root).recover()
    recovered = _read_manifest(root)
    image_attempts = tuple(
        item for item in recovered.attempts if item.operation == "image_generation"
    )
    first_recovery = recovered
    assert not tuple(root.rglob(".p2a-*.tmp"))
    repeated = ProductionStateCommitter(root).recover()
    assert repeated.manifest_revision_before == repeated.manifest_revision_after
    assert _read_manifest(root) == first_recovery
    return image_attempts[-1].status if image_attempts else None


@pytest.mark.parametrize(
    ("phase", "expected_status"),
    (
        (CommitPhase.BEFORE_IMAGE_PROVIDER_CALL, StateCommitStatus.OUTCOME_UNKNOWN),
        (CommitPhase.AFTER_IMAGE_PERMIT_CONSUMED, StateCommitStatus.OUTCOME_UNKNOWN),
        (CommitPhase.AFTER_IMAGE_PROVIDER_RESULT, StateCommitStatus.OUTCOME_UNKNOWN),
        (
            CommitPhase.AFTER_IMAGE_CANDIDATE_MANIFEST_REPLACE,
            StateCommitStatus.INTERRUPTED,
        ),
        (
            CommitPhase.AFTER_IMAGE_CANDIDATE_MANIFEST_VERIFICATION,
            StateCommitStatus.INTERRUPTED,
        ),
        (CommitPhase.AFTER_IMAGE_FINAL_MANIFEST_REPLACE, StateCommitStatus.SUCCEEDED),
        (
            CommitPhase.AFTER_IMAGE_FINAL_MANIFEST_VERIFICATION,
            StateCommitStatus.SUCCEEDED,
        ),
    ),
)
def test_image_specific_process_crash_recovery_is_fail_closed(
    committed_project: Path,
    phase: CommitPhase,
    expected_status: StateCommitStatus,
) -> None:
    assert _crash_image_and_recover(committed_project, phase, 1) is expected_status


@pytest.mark.parametrize(
    "phase",
    (
        CommitPhase.AFTER_ARTIFACT_TEMP_WRITE,
        CommitPhase.AFTER_ARTIFACT_FILE_FSYNC,
        CommitPhase.AFTER_ARTIFACT_PROMOTION,
        CommitPhase.AFTER_ARTIFACT_DIRECTORY_FSYNC,
        CommitPhase.AFTER_ARTIFACT_VERIFICATION,
    ),
)
@pytest.mark.parametrize(
    ("occurrence", "expected_status"),
    (
        (1, None),
        (4, StateCommitStatus.INTERRUPTED),
        (5, StateCommitStatus.OUTCOME_UNKNOWN),
        (6, StateCommitStatus.OUTCOME_UNKNOWN),
        (7, StateCommitStatus.OUTCOME_UNKNOWN),
        (8, StateCommitStatus.OUTCOME_UNKNOWN),
        (9, StateCommitStatus.OUTCOME_UNKNOWN),
        (10, StateCommitStatus.OUTCOME_UNKNOWN),
        (11, StateCommitStatus.OUTCOME_UNKNOWN),
    ),
)
def test_image_artifact_byte_window_process_crash_matrix(
    committed_project: Path,
    phase: CommitPhase,
    occurrence: int,
    expected_status: StateCommitStatus | None,
) -> None:
    assert (
        _crash_image_and_recover(committed_project, phase, occurrence)
        is expected_status
    )


@pytest.mark.parametrize(
    "phase",
    (
        CommitPhase.AFTER_MANIFEST_TEMP_WRITE,
        CommitPhase.AFTER_MANIFEST_FILE_FSYNC,
        CommitPhase.AFTER_MANIFEST_REPLACE,
        CommitPhase.AFTER_MANIFEST_DIRECTORY_FSYNC,
    ),
)
@pytest.mark.parametrize("occurrence", (1, 2, 3, 4))
def test_image_manifest_byte_window_process_crash_matrix(
    committed_project: Path,
    phase: CommitPhase,
    occurrence: int,
) -> None:
    before_replace = phase in {
        CommitPhase.AFTER_MANIFEST_TEMP_WRITE,
        CommitPhase.AFTER_MANIFEST_FILE_FSYNC,
    }
    expected = (
        (None, StateCommitStatus.INTERRUPTED, StateCommitStatus.OUTCOME_UNKNOWN,
         StateCommitStatus.INTERRUPTED)
        if before_replace
        else (
            StateCommitStatus.INTERRUPTED,
            StateCommitStatus.OUTCOME_UNKNOWN,
            StateCommitStatus.INTERRUPTED,
            StateCommitStatus.SUCCEEDED,
        )
    )[occurrence - 1]
    assert _crash_image_and_recover(committed_project, phase, occurrence) is expected


def test_recovery_marks_r2_voice_outcome_unknown_and_never_remints(
    committed_project: Path,
) -> None:
    request = project_factory.make_voice_request(committed_project)
    preview, authorization = project_factory.make_voice_preview_and_authorization(request)
    writer = ProductionStateCommitter(committed_project)
    writer.begin_voice_generation(request, preview, authorization)
    writer.record_voice_submit_intent(request, preview, authorization)

    writer.recover()
    recovered = _read_manifest(committed_project)

    assert recovered.attempts[-1].status is StateCommitStatus.OUTCOME_UNKNOWN
    assert recovered.attempts[-1].voice_phase == "submit_intent"
    with pytest.raises(AiVideoError):
        writer.record_voice_submit_intent(request, preview, authorization)


def test_recovery_preserves_r3_voice_candidate_for_explicit_activation(
    committed_project: Path,
) -> None:
    class _CrashAfterCandidate:
        def checkpoint(self, phase: CommitPhase) -> None:
            if phase is CommitPhase.AFTER_VOICE_CANDIDATE_MANIFEST:
                raise RuntimeError("fixture crash after R+3")

    request = project_factory.make_voice_request(committed_project)
    preview, authorization = project_factory.make_voice_preview_and_authorization(request)
    writer = ProductionStateCommitter(committed_project)
    writer.begin_voice_generation(request, preview, authorization)
    writer.record_voice_submit_intent(request, preview, authorization)
    activation, audio_ids = project_factory.make_voice_activation_request(
        committed_project, request, authorization, expected_manifest_revision=3
    )
    crashing = ProductionStateCommitter(
        committed_project, crash_injector=_CrashAfterCandidate()
    )
    with pytest.raises(RuntimeError, match=r"R\+3"):
        crashing.activate_voice_assets(activation, audio_asset_ids=audio_ids)

    crashing.recover()
    recovered = _read_manifest(committed_project)
    assert recovered.attempts[-1].status is StateCommitStatus.INTERRUPTED
    assert recovered.attempts[-1].voice_phase == "candidate"
    activated = ProductionStateCommitter(committed_project).activate_voice_assets(
        activation, audio_asset_ids=audio_ids
    )
    assert activated.attempts[-1].status is StateCommitStatus.SUCCEEDED


@pytest.mark.parametrize(
    "tamper_target",
    ("outcome", "audio", "caption", "alignment", "cost", "provenance", "registry"),
)
def test_recovery_rejects_tampered_r3_voice_graph_without_activation(
    committed_project: Path,
    tamper_target: str,
) -> None:
    class _CrashAfterCandidate:
        def checkpoint(self, phase: CommitPhase) -> None:
            if phase is CommitPhase.AFTER_VOICE_CANDIDATE_MANIFEST:
                raise RuntimeError("fixture crash after R+3")

    before = _read_manifest(committed_project)
    request = project_factory.make_voice_request(committed_project)
    preview, authorization = project_factory.make_voice_preview_and_authorization(request)
    writer = ProductionStateCommitter(committed_project)
    writer.begin_voice_generation(request, preview, authorization)
    writer.record_voice_submit_intent(request, preview, authorization)
    activation, audio_ids = project_factory.make_voice_activation_request(
        committed_project,
        request,
        authorization,
        expected_manifest_revision=3,
        include_caption=True,
    )
    caption_ids = (f"caption-{request.attempt_id}",)
    crashing = ProductionStateCommitter(
        committed_project, crash_injector=_CrashAfterCandidate()
    )
    with pytest.raises(RuntimeError, match=r"R\+3"):
        crashing.activate_voice_assets(
            activation,
            audio_asset_ids=audio_ids,
            caption_asset_ids=caption_ids,
        )
    candidate = _read_manifest(committed_project)
    if tamper_target == "outcome":
        target = crashing.voice_attempt_paths(request.attempt_id).outcome_path
    elif tamper_target == "audio":
        registry = AssetRegistrySnapshot.model_validate_json(
            (committed_project / candidate.attempts[-1].candidate_registry.path).read_bytes()
        )
        target = committed_project / next(
            item.artifact_path for item in registry.assets if item.asset_id == audio_ids[0]
        )
    elif tamper_target == "caption":
        registry = AssetRegistrySnapshot.model_validate_json(
            (committed_project / candidate.attempts[-1].candidate_registry.path).read_bytes()
        )
        target = committed_project / next(
            item.artifact_path for item in registry.assets if item.asset_id == caption_ids[0]
        )
    elif tamper_target in {"alignment", "cost", "provenance"}:
        paths = crashing.voice_attempt_paths(request.attempt_id)
        target = {
            "alignment": paths.alignment_path,
            "cost": paths.cost_path,
            "provenance": paths.provenance_path,
        }[tamper_target]
    else:
        target = committed_project / candidate.attempts[-1].candidate_registry.path
    target.write_bytes(b"tampered")

    with pytest.raises(AiVideoError) as exc_info:
        ProductionStateCommitter(committed_project).recover()

    after = _read_manifest(committed_project)
    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED
    assert after.active_project == before.active_project
    assert after.active_registry == before.active_registry
    assert after.attempts[-1].status is StateCommitStatus.RUNNING
    assert after.attempts[-1].voice_phase == "candidate"


@pytest.mark.parametrize(
    ("phase", "expected_status"),
    (
        (CommitPhase.BEFORE_VOICE_SUBMIT_INTENT, StateCommitStatus.INTERRUPTED),
        (CommitPhase.AFTER_VOICE_SUBMIT_INTENT, StateCommitStatus.OUTCOME_UNKNOWN),
        (CommitPhase.AFTER_VOICE_PROVIDER_RESULT, StateCommitStatus.OUTCOME_UNKNOWN),
        (CommitPhase.AFTER_VOICE_CANDIDATE_MANIFEST, StateCommitStatus.INTERRUPTED),
        (CommitPhase.AFTER_VOICE_FINAL_MANIFEST_REPLACE, StateCommitStatus.SUCCEEDED),
    ),
)
def test_voice_process_crash_recovery_never_blind_resubmits(
    committed_project: Path,
    phase: CommitPhase,
    expected_status: StateCommitStatus,
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tests/helpers/p2a_crash_worker.py",
            str(committed_project),
            phase.value,
            "1",
            "voice",
        ],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 91

    ProductionStateCommitter(committed_project).recover()
    recovered = _read_manifest(committed_project)
    assert recovered.attempts[-1].status is expected_status


@pytest.mark.parametrize(
    "phase",
    (CommitPhase.AFTER_MANIFEST_REPLACE, CommitPhase.AFTER_MANIFEST_DIRECTORY_FSYNC),
)
@pytest.mark.parametrize(
    ("occurrence", "expected_status"),
    (
        (1, StateCommitStatus.INTERRUPTED),
        (2, StateCommitStatus.OUTCOME_UNKNOWN),
        (3, StateCommitStatus.INTERRUPTED),
        (4, StateCommitStatus.SUCCEEDED),
    ),
)
def test_voice_manifest_durability_occurrences_recover_without_transport_replay(
    committed_project: Path,
    phase: CommitPhase,
    occurrence: int,
    expected_status: StateCommitStatus,
) -> None:
    before = _read_manifest(committed_project)
    result = subprocess.run(
        [
            sys.executable,
            "tests/helpers/p2a_crash_worker.py",
            str(committed_project),
            phase.value,
            str(occurrence),
            "voice",
        ],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 91

    report = ProductionStateCommitter(committed_project).recover()
    recovered = _read_manifest(committed_project)
    attempt = recovered.attempts[-1]
    assert attempt.status is expected_status
    assert attempt.provider_request_id in {None, "fixture-provider-request"}
    if occurrence < 4:
        assert recovered.active_project == before.active_project
        assert recovered.active_registry == before.active_registry
    else:
        assert recovered.active_registry != before.active_registry
    assert all(item.path != Path("runs") for item in report.items)


@pytest.mark.parametrize(
    "phase",
    (
        CommitPhase.AFTER_ARTIFACT_TEMP_WRITE,
        CommitPhase.AFTER_ARTIFACT_FILE_FSYNC,
        CommitPhase.AFTER_ARTIFACT_PROMOTION,
        CommitPhase.AFTER_ARTIFACT_DIRECTORY_FSYNC,
        CommitPhase.AFTER_ARTIFACT_VERIFICATION,
    ),
)
def test_audio_import_artifact_crash_never_selects_partial_registry(
    committed_project: Path,
    phase: CommitPhase,
) -> None:
    before = _read_manifest(committed_project)
    request = project_factory.make_audio_import_upgrade_request(
        committed_project,
        attempt_id="audio-import-process-crash",
        include_assets=True,
    )
    result = subprocess.run(
        [
            sys.executable,
            "tests/helpers/p2a_crash_worker.py",
            str(committed_project),
            phase.value,
            "1",
            "audio_import",
        ],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 91

    report = ProductionStateCommitter(committed_project).recover()
    recovered = _read_manifest(committed_project)
    assert recovered.schema_version == "2.2"
    assert recovered.active_project == before.active_project
    assert recovered.active_registry == before.active_registry
    assert recovered.active_render_state == before.active_render_state
    assert recovered.attempts[-1].status is StateCommitStatus.INTERRUPTED
    assert report.manifest_revision_after > report.manifest_revision_before
    for artifact in request.artifacts:
        path = committed_project / artifact.relative_path
        if path.exists():
            assert path.read_bytes() == artifact.payload
    assert not tuple(committed_project.rglob("*.p2a-*.tmp"))


@pytest.mark.parametrize(
    "phase",
    (
        CommitPhase.AFTER_MANIFEST_TEMP_WRITE,
        CommitPhase.AFTER_MANIFEST_FILE_FSYNC,
        CommitPhase.AFTER_MANIFEST_REPLACE,
        CommitPhase.AFTER_MANIFEST_DIRECTORY_FSYNC,
    ),
)
@pytest.mark.parametrize("occurrence", (1, 2))
def test_audio_import_manifest_crash_has_exact_old_or_new_pair(
    committed_project: Path,
    phase: CommitPhase,
    occurrence: int,
) -> None:
    before = _read_manifest(committed_project)
    expected_request = project_factory.make_audio_import_upgrade_request(
        committed_project,
        attempt_id="audio-import-process-crash",
        include_assets=True,
    )
    expected_registry = expected_request.next_registry
    result = subprocess.run(
        [
            sys.executable,
            "tests/helpers/p2a_crash_worker.py",
            str(committed_project),
            phase.value,
            str(occurrence),
            "audio_import",
        ],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 91

    ProductionStateCommitter(committed_project).recover()
    recovered = _read_manifest(committed_project)
    assert recovered.active_project == before.active_project
    assert recovered.active_registry in (before.active_registry, expected_registry)
    assert recovered.active_render_state is None
    if recovered.active_registry == before.active_registry:
        assert recovered.schema_version in {before.schema_version, "2.2"}
        assert not recovered.attempts or recovered.attempts[-1].status in {
            StateCommitStatus.INTERRUPTED,
            StateCommitStatus.FAILED,
        }
    else:
        assert recovered.schema_version == "2.2"
        assert recovered.attempts[-1].status is StateCommitStatus.SUCCEEDED
        active_registry = AssetRegistrySnapshot.model_validate_json(
            (committed_project / recovered.active_registry.path).read_bytes()
        )
        assert active_registry.schema_version == "2.1"
        for artifact in expected_request.artifacts:
            assert (committed_project / artifact.relative_path).read_bytes() == artifact.payload


@pytest.fixture
def committed_project(tmp_path: Path) -> Path:
    project_factory.write_production_project(tmp_path)
    return tmp_path


def test_recovery_marks_begun_render_without_candidate_interrupted(
    committed_project: Path,
) -> None:
    before = _read_manifest(committed_project)
    selection = RendererSelectionReceipt(
        receipt_id="selection-interrupted-render",
        attempt_id="interrupted-render",
        requested_kind=RendererKind.HYPERFRAMES,
        selected_kinds=(RendererKind.HYPERFRAMES,),
        renderer_version="0.7.103",
        timeline_fingerprint="a" * 64,
        current_project=before.active_project,
        current_registry=before.active_registry,
    )
    writer = ProductionStateCommitter(committed_project)
    begun = writer.begin_render_attempt(
        BeginRenderAttemptRequest(before.manifest_revision, None, selection)
    )

    report = writer.recover()
    recovered = _read_manifest(committed_project)

    assert report.manifest_revision_after == begun.manifest_revision + 1
    assert recovered.active_project == before.active_project
    assert recovered.active_registry == before.active_registry
    assert recovered.active_render_state is None
    assert recovered.attempts[-1].status is StateCommitStatus.INTERRUPTED


def _assert_active_bundle(root: Path, manifest: ProductionManifest) -> None:
    project_path = root / manifest.active_project.path
    registry_path = root / manifest.active_registry.path
    assert hashlib.sha256(project_path.read_bytes()).hexdigest() == manifest.active_project.file_sha256
    assert hashlib.sha256(registry_path.read_bytes()).hexdigest() == manifest.active_registry.file_sha256
    bundle = load_production_project_candidate(
        root,
        manifest,
        manifest.active_project.path,
        manifest.active_registry.path,
    )
    assert bundle.project.revision == manifest.active_project.revision
    assert bundle.project.content_hash == manifest.active_project.content_hash
    assert bundle.registry.revision_id == manifest.active_registry.revision_id
    assert bundle.registry.content_hash == manifest.active_registry.content_hash


def _active_p5_tuple(manifest: ProductionManifest):
    return (
        manifest.active_project,
        manifest.active_registry,
        manifest.active_render_state,
        manifest.active_dependency_graph,
        manifest.dependency_states,
    )


_GRAPH_CRASH_PHASES = (
    CommitPhase.AFTER_GRAPH_CANDIDATE_TEMP_WRITE,
    CommitPhase.AFTER_GRAPH_CANDIDATE_FILE_FSYNC,
    CommitPhase.AFTER_GRAPH_CANDIDATE_PROMOTION,
    CommitPhase.AFTER_GRAPH_CANDIDATE_DIRECTORY_FSYNC,
    CommitPhase.AFTER_GRAPH_CANDIDATE_VERIFICATION,
    CommitPhase.AFTER_GRAPH_FINAL_MANIFEST_REPLACE,
)


@pytest.mark.parametrize(
    "mode",
    (
        "graph_bootstrap",
        "graph_project_commit",
        "graph_voice_activate",
        "graph_render_activate",
    ),
)
@pytest.mark.parametrize("phase", _GRAPH_CRASH_PHASES)
def test_graph_activation_crash_recovers_only_exact_old_or_new_tuple(
    committed_project: Path,
    mode: str,
    phase: CommitPhase,
) -> None:
    if mode == "graph_bootstrap":
        project_factory.make_p5_bootstrap_transition(committed_project)
    else:
        project_factory.make_manifest_23_project(committed_project)
    before = _read_manifest(committed_project)

    result = subprocess.run(
        [
            sys.executable,
            "tests/helpers/p2a_crash_worker.py",
            str(committed_project),
            phase.value,
            "1",
            mode,
        ],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 91

    report = _recover(committed_project)
    recovered = _read_manifest(committed_project)
    selects_candidate = phase is CommitPhase.AFTER_GRAPH_FINAL_MANIFEST_REPLACE
    if selects_candidate:
        assert _active_p5_tuple(recovered) != _active_p5_tuple(before)
        assert recovered.attempts[-1].status is StateCommitStatus.SUCCEEDED
    else:
        assert _active_p5_tuple(recovered) == _active_p5_tuple(before)
        expected_status = (
            StateCommitStatus.OUTCOME_UNKNOWN
            if mode == "graph_voice_activate"
            else StateCommitStatus.INTERRUPTED
        )
        assert recovered.attempts[-1].status is expected_status
    assert recovered.schema_version == "2.3"
    assert not any(item.status is StateCommitStatus.RUNNING for item in recovered.attempts)
    if mode != "graph_voice_activate" or selects_candidate:
        assert not any(
            item.status is StateCommitStatus.OUTCOME_UNKNOWN
            for item in recovered.attempts
        )
    assert not tuple(committed_project.rglob(".p2a-*.tmp"))
    assert report.manifest_revision_after >= report.manifest_revision_before
    graph_items = [
        item
        for item in report.items
        if "dependency_graph" in item.path.as_posix()
        and item.disposition is not RecoveryDisposition.ACTIVE
    ]
    if phase in {
        CommitPhase.AFTER_GRAPH_CANDIDATE_TEMP_WRITE,
        CommitPhase.AFTER_GRAPH_CANDIDATE_FILE_FSYNC,
    }:
        assert any(
            item.disposition is RecoveryDisposition.PARTIAL_REMOVED
            for item in graph_items
        )
        assert not any(
            item.disposition is RecoveryDisposition.INTERRUPTED_RECORDED
            for item in graph_items
        )

    repeated = _recover(committed_project)
    assert repeated.manifest_revision_before == repeated.manifest_revision_after
    assert _read_manifest(committed_project) == recovered


@pytest.mark.parametrize(
    "phase",
    (
        CommitPhase.AFTER_ARTIFACT_TEMP_WRITE,
        CommitPhase.AFTER_ARTIFACT_FILE_FSYNC,
    ),
)
@pytest.mark.parametrize("occurrence", (7, 8))
def test_graph_voice_generic_artifact_crash_keeps_base_and_provider_unknown(
    committed_project: Path,
    phase: CommitPhase,
    occurrence: int,
) -> None:
    project_factory.make_manifest_23_project(committed_project)
    before = _read_manifest(committed_project)

    result = subprocess.run(
        [
            sys.executable,
            "tests/helpers/p2a_crash_worker.py",
            str(committed_project),
            phase.value,
            str(occurrence),
            "graph_voice_activate",
        ],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 91

    report = _recover(committed_project)
    recovered = _read_manifest(committed_project)
    assert _active_p5_tuple(recovered) == _active_p5_tuple(before)
    assert recovered.attempts[-1].status is StateCommitStatus.OUTCOME_UNKNOWN
    graph_items = [
        item
        for item in report.items
        if "dependency_graph" in item.path.as_posix()
        and item.disposition is not RecoveryDisposition.ACTIVE
    ]
    assert not any(
        item.disposition is RecoveryDisposition.INTERRUPTED_RECORDED
        for item in graph_items
    )
    if occurrence == 8:
        assert any(
            item.disposition is RecoveryDisposition.PARTIAL_REMOVED
            for item in graph_items
        )
    else:
        assert not graph_items


def test_recovery_preserves_complete_unselected_dependency_graph_only(
    committed_project: Path,
) -> None:
    project_factory.make_manifest_23_project(committed_project)
    before = _read_manifest(committed_project)
    from ai_video.production.dependency import build_dependency_graph
    from ai_video.production.models import DependencyGraphSnapshot

    active_graph = DependencyGraphSnapshot.model_validate_json(
        (committed_project / before.active_dependency_graph.path).read_bytes()
    )
    selected = active_graph.nodes[0]
    selected_contribution = selected.contributions[0]
    changed_contribution = selected_contribution.model_copy(
        update={"fingerprint": "f" * 64}
    )
    changed_node = selected.model_copy(
        update={
            "contributions": (
                changed_contribution,
                *selected.contributions[1:],
            )
        }
    )
    graph = build_dependency_graph(
        (changed_node, *active_graph.nodes[1:]), active_graph.edges
    )
    graph_payload = state_commit._canonical_json_bytes(graph)
    graph_relative = state_commit.canonical_dependency_graph_snapshot_path(
        graph.revision_id
    )
    graph_sha256 = hashlib.sha256(graph_payload).hexdigest()
    graph_path = committed_project / graph_relative
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    graph_path.write_bytes(graph_payload)
    decoy = committed_project / "state/dependency_graph.latest.json"
    decoy.write_bytes(graph_payload)
    tampered = committed_project / f"state/dependency_graph.{'f' * 64}.json"
    tampered.write_bytes(b"not-a-graph")

    report = _recover(committed_project)
    recovered = _read_manifest(committed_project)

    assert graph_relative != before.active_dependency_graph.path
    assert _active_p5_tuple(recovered) == _active_p5_tuple(before)
    assert graph_path.read_bytes() == graph_payload
    assert decoy.read_bytes() == graph_payload
    assert tampered.read_bytes() == b"not-a-graph"
    assert any(
        item.path == graph_relative
        and item.disposition is RecoveryDisposition.ORPHAN_PRESERVED
        and item.sha256 == graph_sha256
        for item in report.items
    )
    ignored = {
        decoy.relative_to(committed_project),
        tampered.relative_to(committed_project),
    }
    assert not any(item.path in ignored for item in report.items)


def test_recovery_rejects_tampered_promoted_graph_even_with_owned_temp(
    committed_project: Path,
) -> None:
    project_factory.make_manifest_23_project(committed_project)
    result = subprocess.run(
        [
            sys.executable,
            "tests/helpers/p2a_crash_worker.py",
            str(committed_project),
            CommitPhase.AFTER_GRAPH_CANDIDATE_PROMOTION.value,
            "1",
            "graph_project_commit",
        ],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 91
    interrupted = _read_manifest(committed_project)
    attempt = interrupted.attempts[-1]
    candidate = attempt.candidate_dependency_graph
    assert candidate is not None
    candidate_path = committed_project / candidate.path
    owned_temp = candidate_path.parent / _owned_temp_name(
        attempt.attempt_id, candidate_path
    )
    assert candidate_path.is_file()
    assert owned_temp.is_file()
    candidate_path.write_bytes(b"tampered-promoted-graph")

    with pytest.raises(AiVideoError) as exc_info:
        _recover(committed_project)

    assert exc_info.value.code is ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED
    assert _read_manifest(committed_project) == interrupted
    assert owned_temp.is_file()


@pytest.mark.parametrize("schema_version", ("2.0", "2.1", "2.2"))
def test_recovery_keeps_pre_p5_schema_forward_compatible(
    committed_project: Path, schema_version: str
) -> None:
    manifest_path = committed_project / "state/manifest.json"
    before = _read_manifest(committed_project).model_copy(
        update={"schema_version": schema_version}
    )
    manifest_path.write_text(before.model_dump_json(indent=2), encoding="utf-8")

    report = _recover(committed_project)

    assert report.manifest_revision_before == report.manifest_revision_after
    assert _read_manifest(committed_project) == before


def test_manifest_23_reader_and_recovery_work_without_rebuild_execution(
    committed_project: Path,
) -> None:
    project_factory.make_manifest_23_project(committed_project)
    before = _read_manifest(committed_project)

    loaded = project_factory.load_production_project(
        committed_project / "project.yaml"
    )
    report = _recover(committed_project)

    assert loaded.manifest == before
    assert loaded.dependency_graph is not None
    assert report.manifest_revision_before == report.manifest_revision_after
    assert _read_manifest(committed_project) == before


def _failed_attempt(root: Path, attempt_id: str) -> tuple[ProductionManifest, object]:
    manifest = _read_manifest(root)
    request = project_factory.make_revision_two_request(root, attempt_id=attempt_id)
    attempt = StateCommitAttempt(
        attempt_id=attempt_id,
        operation=request.operation,
        status=StateCommitStatus.FAILED,
        base_manifest_revision=manifest.manifest_revision,
        base_project=manifest.active_project,
        base_registry=manifest.active_registry,
        candidate_project=request.next_project,
        candidate_registry=request.next_registry,
        candidate_artifacts_hash=ZERO_HASH,
        started_at="2026-08-09T00:00:00+00:00",
        finished_at="2026-08-09T00:01:00+00:00",
        error_code=ErrorCode.PRODUCTION_STATE_COMMIT_FAILED.value,
        error_message="injected failed attempt",
    )
    with_attempt = ProductionManifest.model_validate(
        {
            **manifest.model_dump(mode="python"),
            "manifest_revision": manifest.manifest_revision + 1,
            "attempts": manifest.attempts + (attempt,),
        }
    )
    _write_manifest(root, with_attempt)
    return with_attempt, request


def _selected_incomplete_with_project_temp(
    root: Path, status: StateCommitStatus
) -> tuple[ProductionManifest, Path]:
    request = project_factory.make_revision_two_request(root)
    ProductionStateCommitter(root).commit(request)
    succeeded_manifest = _read_manifest(root)
    incomplete = StateCommitAttempt.model_validate(
        {
            **succeeded_manifest.attempts[-1].model_dump(mode="python"),
            "status": status,
            "finished_at": None,
            "error_code": (
                ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN.value
                if status is StateCommitStatus.OUTCOME_UNKNOWN
                else None
            ),
            "error_message": (
                "injected unknown outcome"
                if status is StateCommitStatus.OUTCOME_UNKNOWN
                else None
            ),
        }
    )
    unresolved_manifest = ProductionManifest.model_validate(
        {
            **succeeded_manifest.model_dump(mode="python"),
            "attempts": (incomplete,),
        }
    )
    _write_manifest(root, unresolved_manifest)
    final_path = root / request.next_project.path
    owned = final_path.parent / _owned_temp_name(incomplete.attempt_id, final_path)
    return unresolved_manifest, owned


@pytest.mark.parametrize(
    ("phase", "occurrence", "selects_candidate"),
    tuple(
        (phase, occurrence, occurrence == 2 and phase in {
            CommitPhase.AFTER_MANIFEST_REPLACE,
            CommitPhase.AFTER_MANIFEST_DIRECTORY_FSYNC,
        })
            for phase in CommitPhase
            if not phase.value.startswith(
                (
                    "before_render_",
                    "after_render_",
                        "before_voice_",
                        "after_voice_",
                        "after_graph_",
                        "before_image_",
                        "after_image_",
                    )
            )
        for occurrence in (
            (1, 2)
            if phase in {
                CommitPhase.AFTER_MANIFEST_TEMP_WRITE,
                CommitPhase.AFTER_MANIFEST_FILE_FSYNC,
                CommitPhase.AFTER_MANIFEST_REPLACE,
                CommitPhase.AFTER_MANIFEST_DIRECTORY_FSYNC,
            }
            else (1,)
        )
    ),
)
def test_restart_after_process_crash_has_one_valid_active_state(
    committed_project: Path, phase: CommitPhase, occurrence: int, selects_candidate: bool
) -> None:
    before = _read_manifest(committed_project)
    request = project_factory.make_revision_two_request(committed_project)

    result = subprocess.run(
        [
            sys.executable,
            "tests/helpers/p2a_crash_worker.py",
            str(committed_project),
            phase.value,
            str(occurrence),
        ],
        cwd=REPO_ROOT,
        check=False,
    )

    assert result.returncode == 91
    report = _recover(committed_project)
    after = _read_manifest(committed_project)
    expected_pair = (
        (request.next_project, request.next_registry)
        if selects_candidate
        else (before.active_project, before.active_registry)
    )
    assert (after.active_project, after.active_registry) == expected_pair
    _assert_active_bundle(committed_project, after)
    assert report.manifest_revision_after >= report.manifest_revision_before

    repeated = _recover(committed_project)
    assert repeated.manifest_revision_before == repeated.manifest_revision_after
    assert _read_manifest(committed_project) == after


@pytest.mark.parametrize(
    "phase",
    [
        CommitPhase.BEFORE_RENDER_CANDIDATE_MANIFEST_SERIALIZATION,
        CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_TEMP_OPEN,
        CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_TEMP_WRITE,
        CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_FILE_FSYNC,
        CommitPhase.BEFORE_RENDER_CANDIDATE_MANIFEST_REPLACE,
        CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_REPLACE,
        CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_DIRECTORY_FSYNC,
        CommitPhase.AFTER_RENDER_CANDIDATE_MANIFEST_VERIFICATION,
        CommitPhase.AFTER_RENDER_FINAL_MANIFEST_TEMP_WRITE,
        CommitPhase.AFTER_RENDER_FINAL_MANIFEST_FILE_FSYNC,
        CommitPhase.BEFORE_RENDER_FINAL_MANIFEST_REPLACE,
        CommitPhase.AFTER_RENDER_FINAL_MANIFEST_REPLACE,
        CommitPhase.AFTER_RENDER_FINAL_MANIFEST_DIRECTORY_FSYNC,
    ],
)
def test_render_process_crash_recovers_only_exact_old_or_new_triple(
    committed_project: Path, phase: CommitPhase
) -> None:
    before = _read_manifest(committed_project)
    result = subprocess.run(
        [
            sys.executable,
            "tests/helpers/p2a_crash_worker.py",
            str(committed_project),
            phase.value,
            "1",
            "render",
        ],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 91

    report = _recover(committed_project)
    recovered = _read_manifest(committed_project)
    assert (recovered.active_project, recovered.active_registry) == (
        before.active_project,
        before.active_registry,
    )
    final_replaced = phase in {
        CommitPhase.AFTER_RENDER_FINAL_MANIFEST_REPLACE,
        CommitPhase.AFTER_RENDER_FINAL_MANIFEST_DIRECTORY_FSYNC,
    }
    if final_replaced:
        assert recovered.active_render_state is not None
        assert recovered.attempts[-1].status is StateCommitStatus.SUCCEEDED
    else:
        assert recovered.active_render_state is None
        assert recovered.attempts[-1].status is StateCommitStatus.INTERRUPTED
        assert any(
            item.disposition is RecoveryDisposition.ORPHAN_PRESERVED
            and item.path.parts[:3] == ("state", "render", "states")
            for item in report.items
        )
    assert not any(
        item.status in {StateCommitStatus.RUNNING, StateCommitStatus.OUTCOME_UNKNOWN}
        for item in recovered.attempts
    )


@pytest.mark.parametrize(
    ("phase", "occurrence"),
    [
        (phase, occurrence)
        for phase in (
            CommitPhase.AFTER_ARTIFACT_TEMP_WRITE,
            CommitPhase.AFTER_ARTIFACT_FILE_FSYNC,
            CommitPhase.AFTER_ARTIFACT_PROMOTION,
            CommitPhase.AFTER_ARTIFACT_DIRECTORY_FSYNC,
            CommitPhase.AFTER_ARTIFACT_VERIFICATION,
        )
        for occurrence in range(1, 9)
    ],
)
def test_render_process_crash_at_each_n_plus_6_artifact_checkpoint_is_recoverable(
    committed_project: Path, phase: CommitPhase, occurrence: int
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tests/helpers/p2a_crash_worker.py",
            str(committed_project),
            phase.value,
            str(occurrence),
            "render",
        ],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 91
    _recover(committed_project)
    recovered = _read_manifest(committed_project)
    assert recovered.active_render_state is None
    assert recovered.attempts[-1].status is StateCommitStatus.INTERRUPTED
    assert not list((committed_project / "state/render").rglob(".p2a-*.tmp"))


@pytest.mark.parametrize(
    "phase",
    [
        CommitPhase.AFTER_MANIFEST_TEMP_WRITE,
        CommitPhase.AFTER_MANIFEST_FILE_FSYNC,
        CommitPhase.AFTER_MANIFEST_REPLACE,
        CommitPhase.AFTER_MANIFEST_DIRECTORY_FSYNC,
    ],
)
def test_render_begin_manifest_process_crash_is_explicitly_recoverable(
    committed_project: Path, phase: CommitPhase
) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tests/helpers/p2a_crash_worker.py",
            str(committed_project),
            phase.value,
            "1",
            "render",
        ],
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 91
    _recover(committed_project)
    recovered = _read_manifest(committed_project)
    assert recovered.active_render_state is None
    assert not any(
        item.status in {StateCommitStatus.RUNNING, StateCommitStatus.OUTCOME_UNKNOWN}
        for item in recovered.attempts
    )


@pytest.mark.parametrize(
    "unresolved_status", [StateCommitStatus.RUNNING, StateCommitStatus.OUTCOME_UNKNOWN]
)
def test_new_attempt_is_blocked_until_real_crash_is_explicitly_recovered(
    committed_project: Path, unresolved_status: StateCommitStatus
) -> None:
    before = _read_manifest(committed_project)
    result = subprocess.run(
        [
            sys.executable,
            "tests/helpers/p2a_crash_worker.py",
            str(committed_project),
            CommitPhase.AFTER_ATTEMPT_STARTED.value,
            "1",
        ],
        cwd=REPO_ROOT,
        check=False,
    )

    assert result.returncode == 91
    manifest_path = committed_project / "state/manifest.json"
    unresolved = _read_manifest(committed_project)
    assert unresolved.attempts[-1].status is StateCommitStatus.RUNNING
    if unresolved_status is StateCommitStatus.OUTCOME_UNKNOWN:
        unknown_attempt = StateCommitAttempt.model_validate(
            {
                **unresolved.attempts[-1].model_dump(mode="python"),
                "status": StateCommitStatus.OUTCOME_UNKNOWN,
                "error_code": ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN.value,
                "error_message": "injected unknown outcome",
            }
        )
        unresolved = ProductionManifest.model_validate(
            {
                **unresolved.model_dump(mode="python"),
                "attempts": unresolved.attempts[:-1] + (unknown_attempt,),
            }
        )
        _write_manifest(committed_project, unresolved)
    unresolved_bytes = manifest_path.read_bytes()
    assert unresolved.attempts[-1].status is unresolved_status
    second_request = project_factory.make_revision_two_request(
        committed_project, attempt_id="different-attempt"
    )

    with pytest.raises(AiVideoError) as exc:
        ProductionStateCommitter(committed_project).commit(second_request)

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    assert "recovery" in exc.value.user_message.lower()
    assert manifest_path.read_bytes() == unresolved_bytes

    report = _recover(committed_project)
    recovered = _read_manifest(committed_project)
    assert report.manifest_revision_after == unresolved.manifest_revision + 1
    assert recovered.attempts[-1].status is StateCommitStatus.INTERRUPTED
    assert recovered.active_project == before.active_project
    assert recovered.active_registry == before.active_registry


def test_recovery_refuses_active_project_pointer_identity_tamper(
    committed_project: Path,
) -> None:
    before = _read_manifest(committed_project)
    tampered = before.active_project.model_copy(update={"revision": before.active_project.revision + 1})
    _write_manifest(
        committed_project,
        ProductionManifest.model_validate(
            {**before.model_dump(mode="python"), "active_project": tampered}
        ),
    )

    with pytest.raises(AiVideoError) as exc:
        _recover(committed_project)

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED


def test_recovery_refuses_active_registry_pointer_identity_tamper(
    committed_project: Path,
) -> None:
    before = _read_manifest(committed_project)
    manifest_path = committed_project / "state/manifest.json"
    manifest_data = before.model_dump(mode="json")
    manifest_data["active_registry"].update(
        {"revision_id": "f" * 64, "content_hash": "f" * 64}
    )
    manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

    with pytest.raises(AiVideoError) as exc:
        _recover(committed_project)

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED


@pytest.mark.parametrize(
    ("pointer_name", "path"),
    [
        ("active_project", "state/projects/arbitrary.yaml"),
        ("active_registry", "assets/arbitrary.json"),
    ],
)
def test_recovery_refuses_noncanonical_manifest_snapshot_pointer(
    committed_project: Path, pointer_name: str, path: str
) -> None:
    manifest_path = committed_project / "state/manifest.json"
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    source_path = committed_project / manifest_data[pointer_name]["path"]
    target_path = committed_project / path
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(source_path.read_bytes())
    manifest_data[pointer_name]["path"] = path
    manifest_path.write_text(json.dumps(manifest_data), encoding="utf-8")

    with pytest.raises(AiVideoError) as exc:
        _recover(committed_project)

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED


def test_recovery_skips_project_orphan_with_filename_pointer_identity_tamper(
    committed_project: Path,
) -> None:
    request = project_factory.make_revision_two_request(committed_project)
    original = committed_project / request.next_project.path
    tampered = original.with_name(
        original.name.replace("project.2.", "project.3.", 1)
    )
    tampered.parent.mkdir(parents=True, exist_ok=True)
    tampered.write_bytes(
        next(
            artifact.payload
            for artifact in request.artifacts
            if artifact.relative_path == request.next_project.path
        )
    )

    report = _recover(committed_project)

    assert not any(item.path == tampered.relative_to(committed_project) for item in report.items)


def test_recovery_skips_registry_orphan_with_filename_pointer_identity_tamper(
    committed_project: Path,
) -> None:
    before = _read_manifest(committed_project)
    original = committed_project / before.active_registry.path
    tampered = original.with_name(f"registry.{'f' * 64}.json")
    tampered.write_bytes(original.read_bytes())

    report = _recover(committed_project)

    assert not any(item.path == tampered.relative_to(committed_project) for item in report.items)


def test_recovery_removes_only_exact_owned_temp_for_non_succeeded_attempt(
    committed_project: Path,
) -> None:
    _manifest, request = _failed_attempt(committed_project, "failed-attempt")
    final_path = committed_project / request.next_project.path
    final_path.parent.mkdir(parents=True, exist_ok=True)
    owned = final_path.parent / _owned_temp_name("failed-attempt", final_path)
    owned.write_bytes(b"partial")
    unrelated = committed_project / "assets/.user-file.tmp"
    unrelated.write_bytes(b"preserve")

    report = _recover(committed_project)

    assert not owned.exists()
    assert unrelated.read_bytes() == b"preserve"
    assert any(
        item.path == owned.relative_to(committed_project)
        and item.disposition is RecoveryDisposition.PARTIAL_REMOVED
        for item in report.items
    )


def test_recovery_refuses_owned_temp_swapped_to_symlink_after_open(
    committed_project: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _manifest, request = _failed_attempt(committed_project, "swap-attempt")
    final_path = committed_project / request.next_project.path
    final_path.parent.mkdir(parents=True, exist_ok=True)
    owned = final_path.parent / _owned_temp_name("swap-attempt", final_path)
    owned.write_bytes(b"partial")
    outside = tmp_path / "outside-temp"
    outside.write_bytes(b"external")
    original_read = state_commit.os.read
    swapped = False

    def swap_after_open(descriptor: int, size: int) -> bytes:
        nonlocal swapped
        payload = original_read(descriptor, size)
        if not swapped:
            swapped = True
            owned.unlink()
            owned.symlink_to(outside)
        return payload

    monkeypatch.setattr(state_commit.os, "read", swap_after_open)

    with pytest.raises(AiVideoError) as exc:
        _recover(committed_project)

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED
    assert swapped
    assert owned.is_symlink()
    assert outside.read_bytes() == b"external"


def test_recovery_skips_orphan_swapped_to_symlink_after_open(
    committed_project: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request = project_factory.make_revision_two_request(committed_project)
    orphan = committed_project / request.next_project.path
    orphan.parent.mkdir(parents=True, exist_ok=True)
    orphan.write_bytes(
        next(
            artifact.payload
            for artifact in request.artifacts
            if artifact.relative_path == request.next_project.path
        )
    )
    outside = tmp_path / "outside-orphan"
    outside.write_bytes(b"external orphan")
    original_read = state_commit.os.read
    swapped = False

    def swap_after_open(descriptor: int, size: int) -> bytes:
        nonlocal swapped
        payload = original_read(descriptor, size)
        if not swapped:
            swapped = True
            orphan.unlink()
            orphan.symlink_to(outside)
        return payload

    monkeypatch.setattr(state_commit.os, "read", swap_after_open)

    report = _recover(committed_project)

    assert swapped
    assert orphan.is_symlink()
    assert outside.read_bytes() == b"external orphan"
    assert not any(item.path == orphan.relative_to(committed_project) for item in report.items)


def test_recovery_removes_fixed_manifest_temp_left_before_running_attempt(
    committed_project: Path,
) -> None:
    fixed_temp = committed_project / "state/.p2a-manifest.tmp"
    fixed_temp.write_bytes(b"partial manifest")

    report = _recover(committed_project)

    assert not fixed_temp.exists()
    assert any(
        item.path == Path("state/.p2a-manifest.tmp")
        and item.disposition is RecoveryDisposition.PARTIAL_REMOVED
        for item in report.items
    )


def test_recovery_preserves_and_reports_complete_orphan_project_snapshot(
    committed_project: Path,
) -> None:
    request = project_factory.make_revision_two_request(committed_project)
    orphan = committed_project / request.next_project.path
    orphan.parent.mkdir(parents=True, exist_ok=True)
    payload = next(
        artifact.payload
        for artifact in request.artifacts
        if artifact.relative_path == request.next_project.path
    )
    orphan.write_bytes(payload)

    before = _read_manifest(committed_project)
    report = _recover(committed_project)

    assert orphan.read_bytes() == payload
    assert _read_manifest(committed_project) == before
    assert any(
        item.path == orphan.relative_to(committed_project)
        and item.disposition is RecoveryDisposition.ORPHAN_PRESERVED
        and item.sha256 == hashlib.sha256(payload).hexdigest()
        for item in report.items
    )


def test_recovery_refuses_corrupt_active_snapshot_without_guessing_orphan(
    committed_project: Path,
) -> None:
    before = _read_manifest(committed_project)
    orphan = committed_project / project_factory.make_revision_two_request(
        committed_project
    ).next_project.path
    orphan.parent.mkdir(parents=True, exist_ok=True)
    orphan.write_bytes(b"untrusted orphan")
    (committed_project / before.active_project.path).write_bytes(b"corrupt active")

    with pytest.raises(AiVideoError) as exc:
        _recover(committed_project)

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED
    assert orphan.read_bytes() == b"untrusted orphan"
    assert _read_manifest(committed_project) == before


def test_recovery_keeps_busy_lock_error_caller_actionable(committed_project: Path) -> None:
    lock_path = committed_project / "state/commit.lock"
    lock_process = subprocess.Popen(
        [
            sys.executable,
            "-c",
            (
                "import fcntl, pathlib, sys, time; "
                "handle = pathlib.Path(sys.argv[1]).open('a+b'); "
                "fcntl.flock(handle.fileno(), fcntl.LOCK_EX); "
                "print('locked', flush=True); time.sleep(30)"
            ),
            str(lock_path),
        ],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert lock_process.stdout is not None
        assert lock_process.stdout.readline().strip() == "locked"
        with pytest.raises(AiVideoError) as exc:
            _recover(committed_project)
        assert exc.value.code is ErrorCode.PRODUCTION_STATE_BUSY
    finally:
        lock_process.terminate()
        lock_process.wait(timeout=5)


def test_recovery_records_running_attempt_as_interrupted_once(
    committed_project: Path,
) -> None:
    before = _read_manifest(committed_project)
    request = project_factory.make_revision_two_request(committed_project)
    running = StateCommitAttempt(
        attempt_id="crashed-attempt",
        operation=request.operation,
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=before.manifest_revision,
        base_project=before.active_project,
        base_registry=before.active_registry,
        candidate_project=request.next_project,
        candidate_registry=request.next_registry,
        candidate_artifacts_hash=ZERO_HASH,
        started_at="2026-08-09T00:00:00+00:00",
    )
    manifest = ProductionManifest.model_validate(
        {
            **before.model_dump(mode="python"),
            "manifest_revision": before.manifest_revision + 1,
            "attempts": (running,),
        }
    )
    _write_manifest(committed_project, manifest)

    report = _recover(committed_project)
    repaired = _read_manifest(committed_project)

    assert repaired.manifest_revision == manifest.manifest_revision + 1
    assert repaired.attempts[-1].status is StateCommitStatus.INTERRUPTED
    assert repaired.active_project == before.active_project
    assert repaired.active_registry == before.active_registry
    assert any(
        item.disposition is RecoveryDisposition.INTERRUPTED_RECORDED for item in report.items
    )
    repeated = _recover(committed_project)
    assert repeated.manifest_revision_before == repeated.manifest_revision_after
    assert _read_manifest(committed_project) == repaired


@pytest.mark.parametrize(
    "status", [StateCommitStatus.RUNNING, StateCommitStatus.OUTCOME_UNKNOWN]
)
def test_recovery_marks_selected_incomplete_attempt_succeeded(
    committed_project: Path, status: StateCommitStatus
) -> None:
    request = project_factory.make_revision_two_request(committed_project)
    ProductionStateCommitter(committed_project).commit(request)
    succeeded_manifest = _read_manifest(committed_project)
    succeeded_attempt = succeeded_manifest.attempts[-1]
    running = StateCommitAttempt.model_validate(
        {
            **succeeded_attempt.model_dump(mode="python"),
            "attempt_id": f"selected-{status.value}",
            "status": status,
            "finished_at": None,
            "error_code": (
                ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN.value
                if status is StateCommitStatus.OUTCOME_UNKNOWN
                else None
            ),
            "error_message": "unknown outcome" if status is StateCommitStatus.OUTCOME_UNKNOWN else None,
        }
    )
    unknown_manifest = ProductionManifest.model_validate(
        {
            **succeeded_manifest.model_dump(mode="python"),
            "attempts": (succeeded_attempt, running),
        }
    )
    _write_manifest(committed_project, unknown_manifest)
    owned_temps = []
    for pointer in (request.next_project, request.next_registry):
        final_path = committed_project / pointer.path
        owned = final_path.parent / _owned_temp_name(running.attempt_id, final_path)
        owned.write_bytes(b"selected incomplete residue")
        owned_temps.append(owned)
    succeeded_temp = (
        committed_project / request.next_project.path
    ).parent / _owned_temp_name(
        succeeded_attempt.attempt_id, committed_project / request.next_project.path
    )
    succeeded_temp.write_bytes(b"pre-existing succeeded temp")
    unrelated = committed_project / "assets/.user-file.tmp"
    unrelated.write_bytes(b"untracked user temp")

    report = _recover(committed_project)
    repaired = _read_manifest(committed_project)

    assert repaired.manifest_revision == unknown_manifest.manifest_revision + 1
    assert repaired.attempts[-1].status is StateCommitStatus.SUCCEEDED
    assert repaired.active_project == request.next_project
    assert repaired.active_registry == request.next_registry
    _assert_active_bundle(committed_project, repaired)
    assert report.manifest_revision_after == repaired.manifest_revision
    for owned in owned_temps:
        assert not owned.exists()
        assert any(
            item.path == owned.relative_to(committed_project)
            and item.disposition is RecoveryDisposition.PARTIAL_REMOVED
            for item in report.items
        )
    assert succeeded_temp.read_bytes() == b"pre-existing succeeded temp"
    assert unrelated.read_bytes() == b"untracked user temp"


def test_selected_incomplete_cleanup_failure_keeps_attempt_retryable(
    committed_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    unresolved_manifest, owned = _selected_incomplete_with_project_temp(
        committed_project, StateCommitStatus.OUTCOME_UNKNOWN
    )
    manifest_path = committed_project / "state/manifest.json"
    unresolved_bytes = manifest_path.read_bytes()
    owned.write_bytes(b"retryable residue")
    committer = ProductionStateCommitter(committed_project)
    remove_recovery_temp = committer._remove_recovery_temp

    def fail_owned_cleanup(path: Path):
        if path == owned:
            raise OSError("injected owned temp cleanup failure")
        return remove_recovery_temp(path)

    monkeypatch.setattr(committer, "_remove_recovery_temp", fail_owned_cleanup)

    with pytest.raises(AiVideoError) as exc:
        committer.recover()

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED
    assert manifest_path.read_bytes() == unresolved_bytes
    assert owned.read_bytes() == b"retryable residue"

    monkeypatch.setattr(committer, "_remove_recovery_temp", remove_recovery_temp)
    report = committer.recover()
    repaired = _read_manifest(committed_project)

    assert repaired.attempts[-1].status is StateCommitStatus.SUCCEEDED
    assert not owned.exists()
    assert any(
        item.path == owned.relative_to(committed_project)
        and item.disposition is RecoveryDisposition.PARTIAL_REMOVED
        for item in report.items
    )


def test_selected_incomplete_manifest_write_failure_retries_after_cleanup(
    committed_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    unresolved_manifest, owned = _selected_incomplete_with_project_temp(
        committed_project, StateCommitStatus.RUNNING
    )
    manifest_path = committed_project / "state/manifest.json"
    unresolved_bytes = manifest_path.read_bytes()
    owned.write_bytes(b"cleaned before manifest retry")
    committer = ProductionStateCommitter(committed_project)
    write_manifest_atomic = committer._write_manifest_atomic

    def fail_repaired_manifest(*args: object, **kwargs: object) -> None:
        assert not owned.exists()
        raise OSError("injected repaired Manifest write failure")

    monkeypatch.setattr(committer, "_write_manifest_atomic", fail_repaired_manifest)

    with pytest.raises(AiVideoError) as exc:
        committer.recover()

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED
    assert manifest_path.read_bytes() == unresolved_bytes
    assert not owned.exists()

    monkeypatch.setattr(committer, "_write_manifest_atomic", write_manifest_atomic)
    report = committer.recover()
    repaired = _read_manifest(committed_project)

    assert repaired.attempts[-1].status is StateCommitStatus.SUCCEEDED
    assert report.manifest_revision_after == unresolved_manifest.manifest_revision + 1


def test_recovery_refuses_missing_active_registry_snapshot(committed_project: Path) -> None:
    before = _read_manifest(committed_project)
    active_registry = committed_project / before.active_registry.path
    active_registry.unlink()

    with pytest.raises(AiVideoError) as exc:
        _recover(committed_project)

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED
    assert _read_manifest(committed_project) == before


def test_recovery_refuses_mixed_candidate_and_old_active_pair(committed_project: Path) -> None:
    before = _read_manifest(committed_project)
    request = project_factory.make_revision_two_request(committed_project)
    project_path = committed_project / request.next_project.path
    project_path.parent.mkdir(parents=True, exist_ok=True)
    project_path.write_bytes(
        next(
            artifact.payload
            for artifact in request.artifacts
            if artifact.relative_path == request.next_project.path
        )
    )
    original_registry = AssetRegistrySnapshot.model_validate_json(
        (committed_project / before.active_registry.path).read_text(encoding="utf-8")
    )
    changed_asset = original_registry.assets[0].model_copy(
        update={"usage_license": "test-only-revised"}
    )
    candidate_registry = original_registry.model_copy(
        update={"revision_id": ZERO_HASH, "content_hash": ZERO_HASH, "assets": (changed_asset,)}
    )
    registry_hash = registry_semantic_sha256(candidate_registry)
    candidate_registry = candidate_registry.model_copy(
        update={"revision_id": registry_hash, "content_hash": registry_hash}
    )
    registry_path = committed_project / f"assets/registry.{registry_hash}.json"
    registry_payload = (
        json.dumps(
            candidate_registry.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    registry_path.write_bytes(registry_payload)
    candidate_pointer = RegistrySnapshotPointer(
        path=registry_path.relative_to(committed_project),
        revision_id=registry_hash,
        content_hash=registry_hash,
        file_sha256=hashlib.sha256(registry_payload).hexdigest(),
    )
    running = StateCommitAttempt(
        attempt_id="mixed-attempt",
        operation=request.operation,
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=before.manifest_revision,
        base_project=before.active_project,
        base_registry=before.active_registry,
        candidate_project=request.next_project,
        candidate_registry=candidate_pointer,
        candidate_artifacts_hash=ZERO_HASH,
        started_at="2026-08-09T00:00:00+00:00",
    )
    mixed_manifest = ProductionManifest.model_validate(
        {
            **before.model_dump(mode="python"),
            "manifest_revision": before.manifest_revision + 1,
            "active_project": request.next_project,
            "attempts": (running,),
        }
    )
    _write_manifest(committed_project, mixed_manifest)

    with pytest.raises(AiVideoError) as exc:
        _recover(committed_project)

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED
    assert _read_manifest(committed_project) == mixed_manifest


def test_recovery_refuses_old_project_and_changed_candidate_registry_pair(
    committed_project: Path,
) -> None:
    before = _read_manifest(committed_project)
    request = project_factory.make_revision_two_request(committed_project)
    original_registry = AssetRegistrySnapshot.model_validate_json(
        (committed_project / before.active_registry.path).read_text(encoding="utf-8")
    )
    changed_asset = original_registry.assets[0].model_copy(
        update={"usage_license": "test-only-reversed-mix"}
    )
    candidate_registry = original_registry.model_copy(
        update={"revision_id": ZERO_HASH, "content_hash": ZERO_HASH, "assets": (changed_asset,)}
    )
    registry_hash = registry_semantic_sha256(candidate_registry)
    candidate_registry = candidate_registry.model_copy(
        update={"revision_id": registry_hash, "content_hash": registry_hash}
    )
    registry_path = committed_project / f"assets/registry.{registry_hash}.json"
    registry_payload = (
        json.dumps(
            candidate_registry.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    registry_path.write_bytes(registry_payload)
    candidate_pointer = RegistrySnapshotPointer(
        path=registry_path.relative_to(committed_project),
        revision_id=registry_hash,
        content_hash=registry_hash,
        file_sha256=hashlib.sha256(registry_payload).hexdigest(),
    )
    running = StateCommitAttempt(
        attempt_id="reversed-mixed-attempt",
        operation=request.operation,
        status=StateCommitStatus.RUNNING,
        base_manifest_revision=before.manifest_revision,
        base_project=before.active_project,
        base_registry=before.active_registry,
        candidate_project=request.next_project,
        candidate_registry=candidate_pointer,
        candidate_artifacts_hash=ZERO_HASH,
        started_at="2026-08-09T00:00:00+00:00",
    )
    mixed_manifest = ProductionManifest.model_validate(
        {
            **before.model_dump(mode="python"),
            "manifest_revision": before.manifest_revision + 1,
            "active_registry": candidate_pointer,
            "attempts": (running,),
        }
    )
    _write_manifest(committed_project, mixed_manifest)

    with pytest.raises(AiVideoError) as exc:
        _recover(committed_project)

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED
    assert _read_manifest(committed_project) == mixed_manifest


def test_recovery_reports_complete_non_active_attempt_candidate_pair(
    committed_project: Path,
) -> None:
    before = _read_manifest(committed_project)
    request = project_factory.make_revision_two_request(committed_project)
    project_path = committed_project / request.next_project.path
    project_path.parent.mkdir(parents=True, exist_ok=True)
    project_payload = next(
        artifact.payload
        for artifact in request.artifacts
        if artifact.relative_path == request.next_project.path
    )
    project_path.write_bytes(project_payload)
    original_registry = AssetRegistrySnapshot.model_validate_json(
        (committed_project / before.active_registry.path).read_text(encoding="utf-8")
    )
    changed_asset = original_registry.assets[0].model_copy(
        update={"usage_license": "test-only-orphan"}
    )
    orphan_registry = original_registry.model_copy(
        update={"revision_id": ZERO_HASH, "content_hash": ZERO_HASH, "assets": (changed_asset,)}
    )
    registry_hash = registry_semantic_sha256(orphan_registry)
    orphan_registry = orphan_registry.model_copy(
        update={"revision_id": registry_hash, "content_hash": registry_hash}
    )
    registry_path = committed_project / f"assets/registry.{registry_hash}.json"
    registry_payload = (
        json.dumps(
            orphan_registry.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    registry_path.write_bytes(registry_payload)
    registry_pointer = RegistrySnapshotPointer(
        path=registry_path.relative_to(committed_project),
        revision_id=registry_hash,
        content_hash=registry_hash,
        file_sha256=hashlib.sha256(registry_payload).hexdigest(),
    )
    interrupted = StateCommitAttempt(
        attempt_id="complete-orphan-pair",
        operation=request.operation,
        status=StateCommitStatus.INTERRUPTED,
        base_manifest_revision=before.manifest_revision,
        base_project=before.active_project,
        base_registry=before.active_registry,
        candidate_project=request.next_project,
        candidate_registry=registry_pointer,
        candidate_artifacts_hash=ZERO_HASH,
        started_at="2026-08-09T00:00:00+00:00",
        finished_at="2026-08-09T00:01:00+00:00",
        error_code=ErrorCode.PRODUCTION_STATE_OUTCOME_UNKNOWN.value,
        error_message="injected interrupted attempt",
    )
    manifest = ProductionManifest.model_validate(
        {
            **before.model_dump(mode="python"),
            "manifest_revision": before.manifest_revision + 1,
            "attempts": (interrupted,),
        }
    )
    _write_manifest(committed_project, manifest)

    report = _recover(committed_project)

    assert _read_manifest(committed_project) == manifest
    for path, payload in ((project_path, project_payload), (registry_path, registry_payload)):
        assert path.read_bytes() == payload
        assert any(
            item.path == path.relative_to(committed_project)
            and item.disposition is RecoveryDisposition.ORPHAN_PRESERVED
            and item.sha256 == hashlib.sha256(payload).hexdigest()
            for item in report.items
        )


def test_recovery_fails_closed_for_owned_temp_symlink(committed_project: Path, tmp_path: Path) -> None:
    _manifest, request = _failed_attempt(committed_project, "failed-attempt")
    final_path = committed_project / request.next_registry.path
    outside = tmp_path / "outside-temp"
    outside.write_bytes(b"external")
    owned = final_path.parent / _owned_temp_name("failed-attempt", final_path)
    owned.symlink_to(outside)

    with pytest.raises(AiVideoError) as exc:
        _recover(committed_project)

    assert exc.value.code is ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED
    assert owned.is_symlink()
    assert outside.read_bytes() == b"external"


def test_recovery_skips_versioned_orphan_symlink(
    committed_project: Path, tmp_path: Path
) -> None:
    request = project_factory.make_revision_two_request(committed_project)
    outside = tmp_path / "outside-orphan"
    outside.write_bytes(b"external orphan")
    orphan = committed_project / request.next_project.path
    orphan.parent.mkdir(parents=True, exist_ok=True)
    orphan.symlink_to(outside)

    report = _recover(committed_project)

    assert orphan.is_symlink()
    assert outside.read_bytes() == b"external orphan"
    assert not any(item.path == orphan.relative_to(committed_project) for item in report.items)


@pytest.mark.parametrize("process_error", (KeyboardInterrupt, SystemExit))
@pytest.mark.parametrize("operation", ("namespace", "digest", "unlink"))
def test_recovery_descriptor_cleanup_preserves_process_exception_and_closes_all_fds(
    committed_project: Path,
    monkeypatch: pytest.MonkeyPatch,
    process_error: type[BaseException],
    operation: str,
) -> None:
    """A failed descriptor close must not hide an interruption from recovery work."""
    committer = ProductionStateCommitter(committed_project)
    original_open = state_commit.os.open
    original_close = state_commit.os.close
    opened: list[int] = []
    closed: list[int] = []
    process_started = False

    def track_open(*args: object, **kwargs: object) -> int:
        descriptor = original_open(*args, **kwargs)
        opened.append(descriptor)
        return descriptor

    def close_after_interruption(descriptor: int) -> None:
        closed.append(descriptor)
        original_close(descriptor)
        if process_started:
            raise OSError("injected descriptor close failure")

    monkeypatch.setattr(state_commit.os, "open", track_open)
    monkeypatch.setattr(state_commit.os, "close", close_after_interruption)

    if operation == "namespace":
        (committed_project / "state/projects").mkdir()

        def interrupt_listdir(_descriptor: int) -> list[str]:
            nonlocal process_started
            process_started = True
            raise process_error()

        monkeypatch.setattr(state_commit.os, "listdir", interrupt_listdir)
        def invoke():
            return committer._recovery_namespace_entries(
                committed_project / "state/projects", re.compile(r".*")
            )
    elif operation == "digest":
        def interrupt_read(_descriptor: int, _size: int) -> bytes:
            nonlocal process_started
            process_started = True
            raise process_error()

        monkeypatch.setattr(state_commit.os, "read", interrupt_read)
        def invoke():
            return committer._recovery_file_digest(
                committed_project
                / _read_manifest(committed_project).active_project.path
            )
    else:
        temporary = committed_project / "state/.p2a-manifest.tmp"
        temporary.write_bytes(b"partial manifest")

        def interrupt_unlink(_name: str, *, dir_fd: int) -> None:
            nonlocal process_started
            process_started = True
            raise process_error()

        monkeypatch.setattr(state_commit.os, "unlink", interrupt_unlink)
        def invoke():
            return committer._unlink_recovery_file(temporary, temporary.stat())

    with pytest.raises(process_error) as exc:
        invoke()

    assert process_started
    assert set(opened).issubset(closed)
    assert any("recovery descriptor cleanup failed" in note for note in exc.value.__notes__)


def test_recovery_rejects_active_project_swapped_after_first_digest(
    committed_project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Recovery rechecks active bytes after candidate loading without a timing race."""
    manifest = _read_manifest(committed_project)
    request = project_factory.make_revision_two_request(committed_project)
    active_path = committed_project / manifest.active_project.path
    revision_two_payload = next(
        artifact.payload
        for artifact in request.artifacts
        if artifact.relative_path == request.next_project.path
    )
    committer = ProductionStateCommitter(committed_project)
    original_require_hash = committer._require_recovery_file_hash
    swapped = False

    def swap_after_first_project_digest(path: Path, expected_hash: str) -> str:
        nonlocal swapped
        actual_hash = original_require_hash(path, expected_hash)
        if not swapped and path == active_path:
            swapped = True
            active_path.write_bytes(revision_two_payload)
        return actual_hash

    monkeypatch.setattr(
        committer, "_require_recovery_file_hash", swap_after_first_project_digest
    )

    with pytest.raises(AiVideoError) as exc:
        committer.recover()

    assert swapped
    assert exc.value.code is ErrorCode.PRODUCTION_STATE_RECOVERY_FAILED
