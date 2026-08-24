from __future__ import annotations

import copy
import hashlib
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import ai_video.production.shot_continuity_m0_caller as caller_module
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.local_video import LocalVideoSubmitIntent
from ai_video.production.models import StateCommitStatus, VideoAttemptPhase
from ai_video.production.shot_continuity_m0_caller import (
    M0AcceptedUpstreamSnapshot,
    M0QualificationCaller,
    M0QualificationInput,
    M0QualificationProvider,
)
from ai_video.production.shot_continuity_m0_qualification import (
    load_m0_qualification_execution_sources,
)
from ai_video.production.video import (
    BillingKind,
    VideoExecutionKind,
    VideoGenerationMode,
)
from ai_video.production.video_execution_stack import (
    GenerationExecutionStackIdentity,
    StackComponentIdentity,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = REPO_ROOT / (
    "workflows/qualification/"
    "minimax_h3_t8_c4_m0_candidate_v1_profile.json"
)
NOW = datetime(2026, 8, 24, tzinfo=UTC)
FROZEN_PROMPT = """For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced as the exact first frame; the ending frame aligns with <Picture 2>; <Picture 3> fully defines identity and wardrobe; <Video 1> supplies the opening gait phase and parallel camera velocity.

integrated_multimodal_description: [Shot 1] Live-action, photorealistic cinematic medium right-facing side-profile shot on the same rain-soaked railway platform at blue hour. The exact same lone adult East Asian woman with a short blunt black bob, mustard-yellow hooded raincoat, black trousers, black boots and the same red cross-body leather satchel walks steadily screen-right toward the clock. A chest-height 50mm-equivalent camera tracks parallel with small amplitude at slow constant speed, keeping a level horizon and stable body scale. She preserves the supplied gait phase, decelerates naturally, and arrives at the exact approved last-frame pose. Exactly one person; no cut, zoom, axis reversal, teleport, text, logo, wardrobe change or unmotivated camera movement.
overall_soundscape: Steady rain strikes the platform roof and wet concrete. Measured boot footsteps and a small physical leather-satchel movement remain synchronized with the walk; distant station ambience stays restrained.
non_diegetic_music: No non-diegetic music."""


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _error(message: str) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.VIDEO_REQUEST_INVALID,
        user_message=message,
        retryable=False,
    )


def _materialized_m0(sources: Any) -> GenerationExecutionStackIdentity:
    profile = sources.profile
    initial = GenerationExecutionStackIdentity.create(
        materialization_status="unmaterialized",
        candidate_id=profile.candidate_id,
        contract_version=profile.contract_version,
        provider_kind=profile.provider_kind,
        deployment_identity=profile.deployment_identity,
        model_id=profile.model_id,
        capability_id=profile.capability_id,
        profile_hash="none",
        compiler_hash="none",
        workflow_hash="none",
        components=tuple(
            StackComponentIdentity(
                ordinal=ordinal,
                kind=item.kind,
                component_id=item.component_id,
                content_hash=item.sha256,
            )
            for ordinal, item in enumerate(profile.components)
        ),
        sampler_identity=profile.sampler,
        scheduler_identity=profile.scheduler,
        runtime_seals=profile.runtime_seals,
        output_contract_hash=profile.output_contract_hash,
    )
    return initial.materialize(sources.materialization)


def _bundle(sources: Any) -> tuple[Any, ...]:
    profile = sources.profile
    m0 = _materialized_m0(sources)
    m1 = SimpleNamespace(
        execution_stack_hash=profile.m1_execution_stack_hash,
        materialization_status="unmaterialized",
        components=(
            SimpleNamespace(
                component_id="hybrid-artifact-candidate-v1",
                presence="absent",
                content_hash="none",
            ),
        ),
    )
    receipt = SimpleNamespace(
        content_hash="d" * 64,
        project=SimpleNamespace(content_hash=profile.project_content_hash),
        registry=SimpleNamespace(content_hash=profile.registry_content_hash),
    )
    policies = tuple(
        SimpleNamespace(policy_hash=token * 64) for token in ("b", "c", "d")
    )
    inputs = (
        SimpleNamespace(
            input_kind="calibration_fixture",
            content_hash="e" * 64,
            execution_stack_hashes=(m0.execution_stack_hash,),
            payload={
                "prompt_sha256": profile.prompt_sha256,
                "task_type": profile.task_type,
                "steps": profile.steps,
                "sampler": profile.sampler,
                "scheduler": profile.scheduler,
                "turbo_lora": profile.turbo_lora,
            },
        ),
        SimpleNamespace(
            input_kind="effect_budget",
            content_hash="f" * 64,
            execution_stack_hashes=(m0.execution_stack_hash,),
            payload={},
        ),
    )
    return receipt, (m0, m1), policies, SimpleNamespace(content_hash="1" * 64), inputs


class _Permit:
    def __init__(self, intent: LocalVideoSubmitIntent) -> None:
        self.intent = intent
        self.used = False

    def _consume_local_video_submit_permit(
        self,
        *,
        intent_fingerprint: str,
        request_fingerprint: str,
    ) -> bool:
        if (
            self.used
            or intent_fingerprint != self.intent.intent_fingerprint
            or request_fingerprint != self.intent.request_fingerprint
        ):
            return False
        self.used = True
        return True


class _Transport:
    def __init__(self) -> None:
        self.deployment_identity = "loopback-127.0.0.1-8188"
        self.object_info: dict[str, object] = {"schemas": "exact"}
        self.object_info_calls = 0
        self.uploads: list[M0QualificationInput] = []
        self.workflows: list[dict[str, Any]] = []
        self.fail_submit = False
        self.before_first_upload: Any = None

    def get_object_info(self) -> dict[str, object]:
        self.object_info_calls += 1
        return copy.deepcopy(self.object_info)

    def upload_input(self, item: M0QualificationInput) -> str:
        if self.before_first_upload is not None and not self.uploads:
            self.before_first_upload()
        assert _sha(item.data) == item.file_sha256
        assert len(item.data) == item.size_bytes
        self.uploads.append(item)
        return item.file_name

    def submit_prompt(self, workflow: dict[str, Any]) -> str:
        self.workflows.append(copy.deepcopy(workflow))
        if self.fail_submit:
            raise RuntimeError("simulated queue uncertainty")
        return "m0-prompt-1"


class _Committer:
    def __init__(self, bundle: tuple[Any, ...], request: Any) -> None:
        self.bundle = bundle
        self.bundle_after_first_reopen: tuple[Any, ...] | None = None
        self.request = request
        self.qualification_reopens = 0
        self.intent_writes = 0
        self.result_writes = 0
        self.failure_writes = 0

    def reopen_p0_qualification_prepared(
        self,
        *,
        required_materialized_candidates: tuple[str, ...],
    ) -> tuple[Any, ...]:
        assert required_materialized_candidates == ("m0",)
        self.qualification_reopens += 1
        if (
            self.bundle_after_first_reopen is not None
            and self.qualification_reopens > 2
        ):
            return self.bundle_after_first_reopen
        return self.bundle

    def _read_manifest(self) -> object:
        return object()

    def _video_attempt(self, manifest: object, attempt_id: str) -> Any:
        assert attempt_id == "m0-attempt"
        return SimpleNamespace(
            status=StateCommitStatus.RUNNING,
            paid_provider_state=None,
            video_generation_state=SimpleNamespace(
                phase=VideoAttemptPhase.REQUEST,
                request=SimpleNamespace(),
            ),
        )

    def _reopen_video_request(self, pointer: object) -> Any:
        return self.request

    def record_local_video_submit_intent(
        self,
        *,
        attempt_id: str,
        preview: Any,
        pre_submit_guard: Any,
    ) -> tuple[LocalVideoSubmitIntent, _Permit]:
        pre_submit_guard(self.request)
        intent = LocalVideoSubmitIntent.create(
            attempt_id=attempt_id,
            request=self.request,
            preview=preview,
            recorded_at=NOW,
        )
        self.intent_writes += 1
        return intent, _Permit(intent)

    def record_local_video_submit_result(self, *, attempt_id: str, result: Any) -> None:
        self.result_writes += 1

    def record_video_provider_failure(
        self,
        *,
        attempt_id: str,
        error_code: ErrorCode,
        message: str,
    ) -> None:
        self.failure_writes += 1


@dataclass
class _Case:
    caller: M0QualificationCaller
    provider: M0QualificationProvider
    committer: _Committer
    transport: _Transport
    request: Any
    paths: dict[str, Path]
    payloads: dict[str, bytes]
    upstream_snapshot: M0AcceptedUpstreamSnapshot
    sources: Any


def _make_case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> _Case:
    sources = load_m0_qualification_execution_sources(
        profile_path=PROFILE_PATH,
        artifact_root=REPO_ROOT,
    )
    input_root = tmp_path / "inputs"
    input_root.mkdir()
    payloads = {
        "source-video": b"\x00\x00\x00\x18ftypmp42accepted-upstream",
        "terminal-frame": b"\x89PNG\r\n\x1a\nterminal",
        "approved-endpoint": b"\x89PNG\r\n\x1a\nendpoint",
        "identity-anchor": b"\x89PNG\r\n\x1a\nidentity",
        "motion-tail": b"\x00\x00\x00\x18ftypmp42motion-tail",
    }
    paths: dict[str, Path] = {}
    for asset_id, payload in payloads.items():
        suffix = ".mp4" if b"ftyp" in payload[:64] else ".png"
        path = input_root / f"{asset_id}{suffix}"
        path.write_bytes(payload)
        paths[asset_id] = path

    terminal = SimpleNamespace(
        source_video_asset_id="source-video",
        source_video_sha256=_sha(payloads["source-video"]),
        extracted_asset_id="terminal-frame",
        extracted_sha256=_sha(payloads["terminal-frame"]),
        content_hash="2" * 64,
    )
    tail = SimpleNamespace(
        source_shot_id="source-shot",
        source_shot_revision=2,
        source_shot_content_hash="4" * 64,
        source_video_asset_id=terminal.source_video_asset_id,
        source_video_sha256=terminal.source_video_sha256,
        source_registry_revision_id="5" * 64,
        source_generation_id="source-generation",
        source_request_input_hash="6" * 64,
        source_resolved_generation_hash="7" * 64,
        source_provenance_receipt_id="source-provenance",
        source_provenance_receipt_sha256="8" * 64,
        source_p6_acceptance_evidence_id="source-p6-acceptance",
        source_p6_acceptance_evidence_sha256="9" * 64,
        registry_revision_id="a" * 64,
        extraction_receipt_id="motion-tail-extraction",
        extraction_receipt_sha256="b" * 64,
        materialization_receipt_id="motion-tail-materialization",
        materialization_receipt_sha256="c" * 64,
        extracted_asset_id="motion-tail",
        extracted_sha256=_sha(payloads["motion-tail"]),
        terminal_frame_evidence=terminal,
    )
    upstream_snapshot = M0AcceptedUpstreamSnapshot(
        terminal_evidence_hash=terminal.content_hash,
        source_shot_id=tail.source_shot_id,
        source_shot_revision=tail.source_shot_revision,
        source_shot_content_hash=tail.source_shot_content_hash,
        source_video_asset_id=tail.source_video_asset_id,
        source_video_sha256=tail.source_video_sha256,
        source_registry_revision_id=tail.source_registry_revision_id,
        source_generation_id=tail.source_generation_id,
        source_request_input_hash=tail.source_request_input_hash,
        source_resolved_generation_hash=tail.source_resolved_generation_hash,
        source_provenance_receipt_id=tail.source_provenance_receipt_id,
        source_provenance_receipt_sha256=tail.source_provenance_receipt_sha256,
        source_p6_acceptance_evidence_id=tail.source_p6_acceptance_evidence_id,
        source_p6_acceptance_evidence_sha256=(
            tail.source_p6_acceptance_evidence_sha256
        ),
        motion_tail_registry_revision_id=tail.registry_revision_id,
        motion_tail_extraction_receipt_id=tail.extraction_receipt_id,
        motion_tail_extraction_receipt_sha256=tail.extraction_receipt_sha256,
        motion_tail_materialization_receipt_id=tail.materialization_receipt_id,
        motion_tail_materialization_receipt_sha256=(
            tail.materialization_receipt_sha256
        ),
        motion_tail_asset_id=tail.extracted_asset_id,
        motion_tail_asset_sha256=tail.extracted_sha256,
    )
    profile = sources.profile
    request = SimpleNamespace(
        generation_id="m0-generation",
        resolved_generation_hash="3" * 64,
        execution_stack_hash=_materialized_m0(sources).execution_stack_hash,
        provider_name=profile.provider_kind,
        provider_kind=profile.provider_kind,
        model_id=profile.model_id,
        capability_id=profile.capability_id,
        provider_profile=SimpleNamespace(
            profile_id=profile.candidate_id,
            profile_version=f"v{profile.contract_version}",
            profile_sha256=sources.profile_document_hash,
        ),
        adapter_compiler_hash=sources.materialization.compiler_hash,
        execution_kind=VideoExecutionKind.LOCAL,
        billing_kind=BillingKind.LOCAL_UNMETERED,
        mode=VideoGenerationMode.IMAGE_TO_VIDEO,
        prompt_text=FROZEN_PROMPT,
        effective_seed=profile.sealed_seed,
        effective_negative_prompt_text="",
        image_bindings=(
            SimpleNamespace(
                role="first_frame",
                asset_id="terminal-frame",
                asset_sha256=_sha(payloads["terminal-frame"]),
                mime_type="image/png",
                size_bytes=len(payloads["terminal-frame"]),
            ),
            SimpleNamespace(
                role="last_frame",
                asset_id="approved-endpoint",
                asset_sha256=_sha(payloads["approved-endpoint"]),
                mime_type="image/png",
                size_bytes=len(payloads["approved-endpoint"]),
            ),
            SimpleNamespace(
                role="reference",
                asset_id="identity-anchor",
                asset_sha256=_sha(payloads["identity-anchor"]),
                mime_type="image/png",
                size_bytes=len(payloads["identity-anchor"]),
            ),
        ),
        media_bindings=(
            SimpleNamespace(
                kind="video",
                role="reference_video",
                asset_id="motion-tail",
                asset_sha256=_sha(payloads["motion-tail"]),
                mime_type="video/mp4",
                size_bytes=len(payloads["motion-tail"]),
            ),
        ),
        c4_multi_anchor_binding=SimpleNamespace(
            tier=SimpleNamespace(value="motion_boundary"),
            terminal=terminal,
            approved_endpoint=SimpleNamespace(
                asset_id="approved-endpoint",
                asset_sha256=_sha(payloads["approved-endpoint"]),
            ),
            identity_anchor=SimpleNamespace(
                asset_id="identity-anchor",
                asset_sha256=_sha(payloads["identity-anchor"]),
            ),
            motion_tail=tail,
        ),
        effective_output=SimpleNamespace(
            timing_mode="frame_count",
            frame_count=profile.frame_count,
            duration_seconds=None,
            dimension_mode="exact",
            width=profile.width,
            height=profile.height,
            fps=profile.fps,
            container=profile.output_container,
            mime_type="video/mp4",
            native_audio=profile.native_audio,
        ),
    )
    bundle = _bundle(sources)
    committer = _Committer(bundle, request)
    transport = _Transport()
    active_project = SimpleNamespace(accepted_upstream=upstream_snapshot)

    def validate_schemas(object_info: dict[str, object], current_sources: Any) -> None:
        if object_info != {"schemas": "exact"}:
            raise _error("live node schema drift")
        assert current_sources.profile.node_schema_seals == sources.profile.node_schema_seals

    monkeypatch.setattr(caller_module, "validate_m0_live_node_schemas", validate_schemas)
    monkeypatch.setattr(
        caller_module,
        "validate_terminal_frame_evidence_against_project",
        lambda terminal_evidence, project: (
            None
            if project is active_project
            else (_ for _ in ()).throw(ValueError("source activation missing"))
        ),
    )

    def reopen_accepted_upstream(
        *,
        project: Any,
        source_video_asset_id: str,
        motion_tail_asset_id: str,
    ) -> M0AcceptedUpstreamSnapshot:
        if (
            project is not active_project
            or source_video_asset_id != "source-video"
            or motion_tail_asset_id != "motion-tail"
        ):
            raise ValueError("accepted upstream selector is not exact")
        return project.accepted_upstream

    path_by_identity = {
        (asset_id, _sha(payload)): paths[asset_id]
        for asset_id, payload in payloads.items()
    }
    provider = M0QualificationProvider(
        profile_path=PROFILE_PATH,
        artifact_root=REPO_ROOT,
        input_root=input_root,
        transport=transport,
        asset_resolver=lambda asset_id, asset_sha256: path_by_identity[
            (asset_id, asset_sha256)
        ],
        clock=lambda: NOW,
    )
    caller = M0QualificationCaller(
        committer=committer,
        provider=provider,
        profile_path=PROFILE_PATH,
        artifact_root=REPO_ROOT,
        project_loader=lambda: active_project,
        accepted_upstream_reopener=reopen_accepted_upstream,
    )
    return _Case(
        caller,
        provider,
        committer,
        transport,
        request,
        paths,
        payloads,
        upstream_snapshot,
        sources,
    )


def _qualify(case: _Case) -> Any:
    return case.caller.qualify(
        attempt_id="m0-attempt",
        resolved_request=case.request,
    )


def _assert_zero_effect(case: _Case) -> None:
    assert case.committer.intent_writes == 0
    assert case.committer.result_writes == 0
    assert case.committer.failure_writes == 0
    assert case.transport.uploads == []
    assert case.transport.workflows == []


def test_qualification_caller_submits_once_with_exact_four_anchor_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = _make_case(tmp_path, monkeypatch)
    assert (
        case.committer.bundle[0].content_hash
        != case.sources.profile.prepared_receipt_hash
    )

    outcome = _qualify(case)

    assert outcome.provider_request_id == "m0-prompt-1"
    assert outcome.source_video_sha256 == (
        case.request.c4_multi_anchor_binding.terminal.source_video_sha256
    )
    assert [item.file_name for item in case.transport.uploads] == [
        "terminal-frame.png",
        "approved-endpoint.png",
        "identity-anchor.png",
        "motion-tail.mp4",
    ]
    assert all(
        item.file_name != case.paths["source-video"].name
        for item in case.transport.uploads
    )
    assert len(case.transport.workflows) == 1
    assert case.transport.workflows[0]["8"]["inputs"]["noise_seed"] == (
        case.sources.profile.sealed_seed
    )
    assert case.transport.object_info_calls == 4
    assert case.committer.intent_writes == 1
    assert case.committer.result_writes == 1
    assert case.committer.failure_writes == 0


def test_upload_uses_pre_permit_immutable_validated_bytes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = _make_case(tmp_path, monkeypatch)
    original = case.payloads["identity-anchor"]
    case.transport.before_first_upload = lambda: case.paths[
        "identity-anchor"
    ].write_bytes(b"\x89PNG\r\n\x1a\nreplaced-after-validation")

    _qualify(case)

    uploaded_identity = next(
        item
        for item in case.transport.uploads
        if item.file_name == "identity-anchor.png"
    )
    assert uploaded_identity.data == original
    assert uploaded_identity.file_sha256 == _sha(original)
    assert case.paths["identity-anchor"].read_bytes() != uploaded_identity.data
    assert len(case.transport.workflows) == 1


@pytest.mark.parametrize(
    "drift",
    (
        "missing_source",
        "missing_seed",
        "negative_seed",
        "boolean_seed",
        "oversized_seed",
        "different_valid_seed",
        "schema",
        "transport_identity",
        "stack",
        "dependent_evidence",
        "cardinality",
        "order",
        "anchor_lineage",
        "source_lineage",
        "missing_p6",
        "p6_evidence",
        "extraction_evidence",
        "materialization_evidence",
        "source_bytes",
        "anchor_bytes",
    ),
)
def test_pre_effect_denials_are_zero_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    drift: str,
) -> None:
    case = _make_case(tmp_path, monkeypatch)
    if drift == "missing_source":
        case.paths["source-video"].unlink()
    elif drift == "missing_seed":
        case.request.effective_seed = None
    elif drift == "negative_seed":
        case.request.effective_seed = -1
    elif drift == "boolean_seed":
        case.request.effective_seed = True
    elif drift == "oversized_seed":
        case.request.effective_seed = 1 << 63
    elif drift == "different_valid_seed":
        case.request.effective_seed += 1
    elif drift == "schema":
        case.transport.object_info = {"schemas": "drifted"}
    elif drift == "transport_identity":
        case.transport.deployment_identity = "remote-not-authorized"
    elif drift == "stack":
        receipt, stacks, policies, validation, inputs = case.committer.bundle
        case.committer.bundle = (
            receipt,
            (
                stacks[0].model_copy(update={"workflow_hash": "9" * 64}),
                stacks[1],
            ),
            policies,
            validation,
            inputs,
        )
    elif drift == "dependent_evidence":
        receipt, stacks, policies, validation, inputs = case.committer.bundle
        changed = copy.deepcopy(inputs)
        changed[0].execution_stack_hashes = ("9" * 64,)
        case.committer.bundle = receipt, stacks, policies, validation, changed
    elif drift == "cardinality":
        case.request.image_bindings = case.request.image_bindings[:2]
    elif drift == "order":
        first, last, identity = case.request.image_bindings
        case.request.image_bindings = last, first, identity
    elif drift == "anchor_lineage":
        case.request.image_bindings[0].asset_sha256 = "9" * 64
    elif drift == "source_lineage":
        case.request.c4_multi_anchor_binding.motion_tail.source_video_sha256 = "9" * 64
    elif drift == "missing_p6":
        del case.request.c4_multi_anchor_binding.motion_tail.source_p6_acceptance_evidence_id
    elif drift == "p6_evidence":
        tail = case.request.c4_multi_anchor_binding.motion_tail
        tail.source_p6_acceptance_evidence_sha256 = "0" * 64
    elif drift == "extraction_evidence":
        case.request.c4_multi_anchor_binding.motion_tail.extraction_receipt_sha256 = "0" * 64
    elif drift == "materialization_evidence":
        case.request.c4_multi_anchor_binding.motion_tail.materialization_receipt_sha256 = "0" * 64
    elif drift == "source_bytes":
        case.paths["source-video"].write_bytes(
            b"\x00\x00\x00\x18ftypmp42drifted-source"
        )
    elif drift == "anchor_bytes":
        case.paths["identity-anchor"].write_bytes(b"\x89PNG\r\n\x1a\ndrift")

    with pytest.raises((AiVideoError, ValueError)):
        _qualify(case)

    _assert_zero_effect(case)


@pytest.mark.parametrize(
    "drift",
    ("receipt", "policy", "validation", "qualification_input"),
)
def test_full_p0_snapshot_drift_is_denied_before_intent_or_provider_effect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    drift: str,
) -> None:
    case = _make_case(tmp_path, monkeypatch)
    changed = copy.deepcopy(case.committer.bundle)
    if drift == "receipt":
        changed[0].content_hash = "0" * 64
    elif drift == "policy":
        changed[2][0].policy_hash = "0" * 64
    elif drift == "validation":
        changed[3].content_hash = "0" * 64
    else:
        changed[4][0].content_hash = "0" * 64
    case.committer.bundle_after_first_reopen = changed

    with pytest.raises(AiVideoError):
        _qualify(case)

    _assert_zero_effect(case)


def test_execution_source_drift_is_denied_before_any_effect(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = _make_case(tmp_path, monkeypatch)
    original = caller_module.load_m0_qualification_execution_sources
    current = original(profile_path=PROFILE_PATH, artifact_root=REPO_ROOT)
    drifted = replace(
        current,
        materialization=current.materialization.model_copy(
            update={"compiler_hash": "9" * 64}
        ),
    )
    monkeypatch.setattr(
        caller_module,
        "load_m0_qualification_execution_sources",
        lambda **kwargs: drifted,
    )

    with pytest.raises(AiVideoError):
        _qualify(case)

    _assert_zero_effect(case)


def test_replayed_local_permit_is_denied_before_upload_or_queue(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = _make_case(tmp_path, monkeypatch)
    preview = case.provider.preview(case.request)
    intent = LocalVideoSubmitIntent.create(
        attempt_id="m0-attempt",
        request=case.request,
        preview=preview,
        recorded_at=NOW,
    )
    permit = _Permit(intent)
    assert permit._consume_local_video_submit_permit(
        intent_fingerprint=intent.intent_fingerprint,
        request_fingerprint=intent.request_fingerprint,
    )

    with pytest.raises(AiVideoError, match="fresh local permit"):
        case.provider.submit_local(case.request, preview, intent, permit)

    assert case.transport.uploads == []
    assert case.transport.workflows == []


def test_unknown_submit_outcome_is_never_retried_or_fallen_back(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case = _make_case(tmp_path, monkeypatch)
    case.transport.fail_submit = True

    with pytest.raises(AiVideoError) as raised:
        _qualify(case)

    assert raised.value.code is ErrorCode.VIDEO_PROVIDER_OUTCOME_UNKNOWN
    assert raised.value.retryable is False
    assert "do not retry or fall back" in raised.value.user_message
    assert len(case.transport.uploads) == 4
    assert len(case.transport.workflows) == 1
    assert case.committer.intent_writes == 1
    assert case.committer.result_writes == 0
    assert case.committer.failure_writes == 1
