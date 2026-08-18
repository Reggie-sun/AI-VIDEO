from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from dataclasses import dataclass, replace
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from ai_video.production.audio import (
    AudioProbeToolchain,
    VoiceCallAuthorization,
    VoiceCostReceipt,
    VoiceGenerationPreview,
    VoiceGenerationRequest,
    VoicePricingSnapshot,
    VoiceProviderResult,
    VoiceProvenanceReceipt,
    build_voice_generation_preview,
)
from ai_video.production.captions import (
    CaptionImportRequest,
    normalize_character_alignment,
)
from ai_video.production.hashing import (
    canonical_sha256,
    seal_artifact,
    verify_artifact_hash,
)
from ai_video.production.hyperframes import (
    RendererCommandResult,
    probe_clip_fd_with_executable,
)
from ai_video.production.image import (
    ImageGenerationRequest,
    ImageProvenanceReceipt,
)
from ai_video.production.models import (
    ActorIdentity,
    ApprovedRepairReceipt,
    AssetType,
    CompositionSpec,
    EvidenceStrength,
    FinalAcceptanceReceipt,
    NamedFingerprint,
    QaLayer,
    QaLayoutRules,
    QaPolicy,
    QaTechnicalThresholds,
    QaVerdict,
    RepairAction,
    RepairAuthorization,
    RepairOutcomeReceipt,
    RepairRequest,
    RenderStateSnapshot,
    ReviewEvidence,
    ReviewEvidencePointer,
    ReviewLifecycle,
    ReviewReceipt,
    ReviewReceiptPointer,
    ReviewRequest,
    SourceReference,
    StateCommitStatus,
    ToolIdentity,
)
from ai_video.production.paths import (
    canonical_image_receipt_path,
    canonical_image_request_path,
    canonical_review_evidence_path,
)
from ai_video.production.project import load_production_project
from ai_video.production.review import (
    adjudicate_review_evidence,
    build_technical_review_context,
)
from production_voice_e2e_support import (
    make_deterministic_voice_candidate_preparer,
)


_VOICE_FIXTURE = (
    Path(__file__).parent / "fixtures/voice_captions/dialogue-mono-48000.wav"
)


def _canonical_json_bytes(value) -> bytes:
    return (
        json.dumps(
            value.model_dump(mode="json"),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _install_manifest_write_counter(
    monkeypatch: pytest.MonkeyPatch,
) -> _ManifestWriteCounter:
    """Instrument the real ``ProductionStateCommitter`` file-ops seam.

    Patches ``_NativeFileOps`` so that two observable Manifest-write
    effects are counted independently:

    - ``manifest_temp_write`` increments on a completed ``fsync_file`` of
      the canonical ``.p2a-manifest.tmp`` path (the durable temp-file
      write effect inside ``_write_manifest_atomic``).
    - ``manifest_replace`` increments on a ``replace()`` whose
      destination is the canonical ``state/manifest.json`` path (the
      atomic manifest promotion effect).

    Same-bytes rewrites still increment because the counter is recorded
    inside ``_CountingFileOps`` before delegating to the real
    ``_NativeFileOps`` method. ``ProductionStateCommitter`` keeps sole
    ownership of the Manifest and still performs its atomic write path;
    the test only observes the seam without bypassing it.

    Each call returns a fresh ``_ManifestWriteCounter`` installed via
    ``monkeypatch``; ``monkeypatch`` restores the original
    ``_NativeFileOps`` and the module-level counter reference at
    teardown, so test isolation is automatic and the counter is
    cumulative for the lifetime of one test (initial acceptance, both
    clean recoveries, same-runtime replay, and fresh-runtime replay).
    """

    import sys

    from ai_video.production import _state_commit_io as io_module

    real_native = io_module._NativeFileOps
    counter = _ManifestWriteCounter()
    production_e2e_support = sys.modules[__name__]

    class _CountingFileOps(real_native):
        def fsync_file(self, handle, path: Path) -> None:
            counter.record_temp_write(path)
            real_native.fsync_file(self, handle, path)

        def replace(self, source: Path, destination: Path) -> None:
            counter.record_replace(source, destination)
            real_native.replace(self, source, destination)

    monkeypatch.setattr(io_module, "_NativeFileOps", _CountingFileOps)
    monkeypatch.setattr(
        "ai_video.production.state_commit._NativeFileOps", _CountingFileOps
    )
    monkeypatch.setattr(production_e2e_support, "_MANIFEST_WRITE_COUNTER", counter)
    return counter


@dataclass(frozen=True)
class BaseAiComicCallCounts:
    image_submit: int = 0
    voice_preview: int = 0
    voice_submit: int = 0
    review_analyze: int = 0
    renderer_version: int = 0
    renderer_doctor: int = 0
    renderer_run: int = 0
    manifest_temp_write: int = 0
    manifest_replace: int = 0


class _ManifestWriteCounter:
    """Test-only counter for observable Manifest file-ops effects.

    Each call to ``_install_manifest_write_counter`` returns a fresh
    instance; ``monkeypatch`` restores the previous module-level
    reference at teardown so tests share no state and never need to
    reset this counter. The two fields are independent:

    - ``temp_write`` increments only when ``fsync_file`` is called for
      the canonical ``.p2a-manifest.tmp`` path (the durable Manifest
      temp-write effect).
    - ``replace`` increments only when ``replace`` is called with a
      destination whose basename is ``manifest.json`` (the atomic
      Manifest promotion effect).
    """

    def __init__(self) -> None:
        self._temp_write = 0
        self._replace = 0

    def record_temp_write(self, path: Path) -> None:
        if path.name == ".p2a-manifest.tmp":
            self._temp_write += 1

    def record_replace(self, source: Path, destination: Path) -> None:
        if destination.name == "manifest.json":
            self._replace += 1

    @property
    def temp_write(self) -> int:
        return self._temp_write

    @property
    def replace(self) -> int:
        return self._replace


_MANIFEST_WRITE_COUNTER = _ManifestWriteCounter()


@dataclass(frozen=True)
class BaseAiComicVoiceResult:
    audio_asset_ids: tuple[str, ...]
    caption_asset_ids: tuple[str, ...]
    caption_track_ids: tuple[str, ...]


@dataclass(frozen=True)
class BaseAiComicRenderProbe:
    duration_milliseconds: int
    video_stream_count: int
    audio_stream_count: int
    staged_audio_binding_ids: tuple[str, ...]
    staged_audio_track_ids: tuple[str, ...]


@dataclass(frozen=True)
class BaseAiComicInitialRender:
    composition: object
    timeline: object
    render_state: object
    path: Path
    sha256: str
    probe: BaseAiComicRenderProbe


@dataclass(frozen=True)
class BaseAiComicMediaIdentitySnapshot:
    project: object
    registry: object
    image_asset_ids: tuple[str, ...]
    audio_asset_ids: tuple[str, ...]
    caption_asset_ids: tuple[str, ...]
    caption_track_ids: tuple[str, ...]
    character_references: tuple[tuple[object, ...], ...]
    scene_references: tuple[tuple[object, ...], ...]
    image_request_evidence: tuple[tuple[Path, str, str], ...]
    image_receipt_evidence: tuple[tuple[Path, str, str], ...]


@dataclass(frozen=True)
class BaseAiComicReviewResult:
    receipt: ReviewReceipt
    pointer: ReviewReceiptPointer
    evidence: tuple[ReviewEvidence, ...]

    @property
    def verdict(self) -> QaVerdict:
        return self.receipt.verdict

    @property
    def issue_ids(self) -> tuple[str, ...]:
        return self.receipt.issue_ids


@dataclass(frozen=True)
class BaseAiComicRepairApproval:
    request: RepairRequest
    receipt: ApprovedRepairReceipt
    pointer: object


@dataclass(frozen=True)
class BaseAiComicRepairCommit:
    composition: object
    composition_path: Path
    composition_file_sha256: str
    invalidated_node_ids: tuple[str, ...]
    manifest: object


@dataclass(frozen=True)
class BaseAiComicFinalAcceptance:
    receipt: FinalAcceptanceReceipt
    lifecycle: object

    @property
    def render_state(self):
        return self.receipt.render_state


@dataclass(frozen=True)
class BaseAiComicFullAcceptanceResult:
    render_state: object
    render_output_sha256: str
    output_path: Path
    mp4_sha256: str
    acceptance_pointer: object
    acceptance_id: str
    acceptance_receipt: FinalAcceptanceReceipt
    repair_outcome_pointer: object
    repair_outcome_repair_id: str
    repair_outcome_receipt: RepairOutcomeReceipt
    acceptance_lifecycle: ReviewLifecycle


class DeterministicVoiceProvider:
    """Offline VoiceAssetProvider fake with deterministic receipts and bytes."""

    def __init__(self) -> None:
        self.preview_calls = 0
        self.generate_calls = 0

    def preview(self, request: VoiceGenerationRequest) -> VoiceGenerationPreview:
        self.preview_calls += 1
        return build_voice_generation_preview(
            request,
            pricing=VoicePricingSnapshot(
                snapshot_id=request.pricing_snapshot_id,
                effective_date=date(2026, 8, 18),
                currency="USD",
                pricing_unit="character",
                unit_price_microunits=1,
                minimum_billable_units=1,
            ),
            destination="https://voice.fixture.invalid",
            credential_reference_kind="environment",
            timing_supported=True,
            output_supported=True,
        )

    def generate(
        self,
        request: VoiceGenerationRequest,
        authorization: VoiceCallAuthorization,
        permit,
    ) -> VoiceProviderResult:
        if not permit._consume_voice_submit_permit(
            attempt_id=request.attempt_id,
            request_fingerprint=request.voice_request_fingerprint,
            authorization_fingerprint=authorization.authorization_fingerprint,
            destination=authorization.destination,
            budget_reservation_receipt_id=(
                authorization.budget_reservation_receipt_id
            ),
            egress_authorization_receipt_id=(
                authorization.egress_authorization_receipt_id
            ),
        ):
            raise AssertionError("durable voice submit permit was not consumed")
        self.generate_calls += 1
        preview = self.preview(request)
        audio_bytes = _VOICE_FIXTURE.read_bytes()
        duration_samples = 96_000
        step_samples = duration_samples // (len(request.script_text) + 1)
        alignment = normalize_character_alignment(
            {
                "characters": list(request.script_text),
                "character_start_times_seconds": [
                    str(index * step_samples / request.output_sample_rate_hz)
                    for index in range(len(request.script_text))
                ],
                "character_end_times_seconds": [
                    str((index + 1) * step_samples / request.output_sample_rate_hz)
                    for index in range(len(request.script_text))
                ],
            },
            sample_rate_hz=request.output_sample_rate_hz,
            duration_samples=duration_samples,
            speaker_id=request.speaker_id,
        ).receipt_bytes
        provider_request_id = "base-ai-comic-voice-1"
        cost = VoiceCostReceipt(
            currency=preview.currency,
            pricing_unit=preview.pricing_unit,
            measured_billable_units=preview.billable_units_upper_bound,
            estimated_cost_upper_bound_microunits=(
                preview.estimated_cost_upper_bound_microunits
            ),
            provider_reported_cost_microunits=None,
            pricing_snapshot_id=preview.pricing_snapshot_id,
            request_id=request.request_id,
            provider_request_id=provider_request_id,
        )
        provenance = VoiceProvenanceReceipt(
            request_id=request.request_id,
            provider_kind=request.provider_kind,
            model_id=request.model_id,
            voice_id=request.voice_id,
            language=request.language,
            request_fingerprint=request.voice_request_fingerprint,
            script_hash=request.script_hash,
            output_container=request.output_container,
            output_codec=request.output_codec,
            output_sample_rate_hz=request.output_sample_rate_hz,
            output_channels=request.output_channels,
            alignment_mode="character",
            adapter=ToolIdentity(name="deterministic-voice", version="1"),
            egress_authorization_receipt_id=(
                request.egress_authorization_receipt_id
            ),
            license_policy_decision="fixture-only",
            policy_receipt_id="base-ai-comic-voice-policy",
            retention_mode="zero_retention",
            provider_request_id=provider_request_id,
            provider_trace_id="base-ai-comic-voice-trace-1",
        )
        return VoiceProviderResult.create(
            request=request,
            preview=preview,
            authorization=authorization,
            pricing=VoicePricingSnapshot(
                snapshot_id=preview.pricing_snapshot_id,
                effective_date=preview.pricing_effective_date,
                currency=preview.currency,
                pricing_unit=preview.pricing_unit,
                unit_price_microunits=preview.unit_price_microunits,
                minimum_billable_units=preview.minimum_billable_units,
            ),
            audio_bytes=audio_bytes,
            content_type="audio/wav",
            provider_request_id=provider_request_id,
            provider_trace_id="base-ai-comic-voice-trace-1",
            alignment_receipt_bytes=alignment,
            cost_receipt=cost,
            provenance_receipt=provenance,
            terminal_status="succeeded",
        )


@dataclass(frozen=True)
class _RendererCall:
    command: str


class DeterministicHyperFramesRunner:
    """RendererRunner fake that produces a small, probeable local MP4."""

    def __init__(self, ffmpeg_path: Path) -> None:
        self.ffmpeg_path = ffmpeg_path
        self.calls: list[_RendererCall] = []

    @property
    def version_calls(self) -> int:
        return sum(call.command == "version" for call in self.calls)

    @property
    def doctor_calls(self) -> int:
        return sum(call.command == "doctor" for call in self.calls)

    @property
    def run_calls(self) -> int:
        return sum(call.command not in {"version", "doctor"} for call in self.calls)

    @property
    def render_calls(self) -> int:
        return sum(call.command == "render" for call in self.calls)

    def version(self, *, env: dict[str, str]) -> str:
        assert env["HYPERFRAMES_NO_TELEMETRY"] == "1"
        self.calls.append(_RendererCall("version"))
        return "0.7.103"

    def doctor(self, *, env: dict[str, str]) -> RendererCommandResult:
        assert env["HYPERFRAMES_NO_TELEMETRY"] == "1"
        self.calls.append(_RendererCall("doctor"))
        return RendererCommandResult(
            returncode=0,
            stdout=json.dumps(
                {
                    "ok": False,
                    "checks": [
                        {"name": "Node.js", "ok": True},
                        {"name": "FFmpeg", "ok": True},
                        {"name": "FFprobe", "ok": True},
                        {"name": "Chrome", "ok": True},
                        {"name": "Whisper", "ok": False},
                    ],
                }
            ),
            stderr="",
        )

    def run(
        self,
        command: str,
        args: tuple[str, ...],
        *,
        cwd: Path,
        env: dict[str, str],
        timeout_seconds: int,
    ) -> RendererCommandResult:
        assert env["HYPERFRAMES_NO_TELEMETRY"] == "1"
        self.calls.append(_RendererCall(command))
        if command != "render":
            payload: dict[str, object]
            if command == "lint":
                payload = {"errorCount": 0, "warningCount": 0}
            else:
                payload = {"ok": True}
                for section in ("lint", "runtime", "layout", "motion", "contrast"):
                    payload[section] = {"errorCount": 0, "warningCount": 0}
            return RendererCommandResult(
                returncode=0, stdout=json.dumps(payload), stderr=""
            )

        output = Path(args[args.index("-o") + 1])
        mixed_wavs = tuple(sorted((cwd / "assets").glob("*.wav")))
        source_sha256 = hashlib.sha256((cwd / "index.html").read_bytes()).hexdigest()
        command_line = [
            str(self.ffmpeg_path),
            "-nostdin",
            "-v",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c=0x{source_sha256[:6]}:s=1280x720:r=24:d=4",
        ]
        if mixed_wavs:
            command_line.extend(("-i", str(mixed_wavs[0])))
        command_line.extend(("-map", "0:v:0"))
        if mixed_wavs:
            command_line.extend(("-map", "1:a:0"))
        command_line.extend(
            (
                "-t",
                "4",
                "-c:v",
                "libx264",
                "-preset",
                "ultrafast",
                "-pix_fmt",
                "yuv420p",
                "-threads",
                "1",
            )
        )
        if mixed_wavs:
            command_line.extend(
                ("-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2")
            )
        command_line.extend(
            ("-map_metadata", "-1", "-movflags", "+faststart", str(output))
        )
        completed = subprocess.run(
            command_line,
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
            check=False,
            timeout=timeout_seconds,
            env=env,
        )
        return RendererCommandResult(
            returncode=completed.returncode,
            stdout=completed.stdout.decode(errors="replace"),
            stderr=completed.stderr.decode(errors="replace"),
        )


class DeterministicReviewAnalyzer:
    """Script one initial layout failure and one exact repaired-render pass."""

    tool_identity = ToolIdentity(name="deterministic-review-analyzer", version="1")

    def __init__(self) -> None:
        self.calls = 0
        self.initial_render_state = None
        self.repaired_render_state = None

    def bind_repaired_render_state(self, render_state) -> None:
        if (
            self.initial_render_state is None
            or render_state == self.initial_render_state
        ):
            raise AssertionError("repaired render must differ from the initial render")
        self.repaired_render_state = render_state

    def analyze(self, request: ReviewRequest, permit) -> ReviewEvidence:
        consume = getattr(permit, "_consume_review_analysis_permit", None)
        if consume is None or not consume(
            request_content_hash=request.content_hash,
            render_output_sha256=request.render_output_sha256,
            technical_context_hash=canonical_sha256(
                request.technical_context.model_dump(mode="json")
            ),
        ):
            raise AssertionError("durable review analysis permit was not consumed")
        self.calls += 1
        if self.initial_render_state is None:
            self.initial_render_state = request.render_state
        if request.render_state == self.initial_render_state:
            return self._layout_evidence(request, passes=False)
        if request.render_state != self.repaired_render_state:
            raise AssertionError(
                "review request is not bound to the exact repaired render"
            )
        return self._layout_evidence(request, passes=True)

    def _layout_evidence(
        self, request: ReviewRequest, *, passes: bool
    ) -> ReviewEvidence:
        if request.requested_layers != (QaLayer.LAYOUT,):
            raise AssertionError("deterministic analyzer only supports layout review")
        identity = "pass" if passes else "fail"
        return seal_artifact(
            ReviewEvidence(
                artifact_id=f"base-ai-comic-layout-{identity}-{request.request_id}",
                revision=1,
                content_hash="0" * 64,
                creation_receipt_id=f"base-ai-comic-layout-{identity}",
                source_provenance=(
                    SourceReference(
                        kind="derived", reference="deterministic-review-analyzer"
                    ),
                ),
                evidence_id=f"base-ai-comic-layout-{identity}-{request.request_id}",
                layer=QaLayer.LAYOUT,
                strength=EvidenceStrength.RENDERER_BOUND,
                render_output_sha256=request.render_output_sha256,
                timeline_fingerprint=request.timeline_fingerprint,
                dependency_graph_revision_id=request.dependency_graph.revision_id,
                tool_identity=self.tool_identity,
                measurement_contract_version="1",
                subject_ids=tuple(
                    window.shot_id for window in request.technical_context.windows
                ),
                measured_payload={
                    "coverage_complete": True,
                    "caption_overflow_milli": 0,
                    "safe_area_inset_milli": 50 if passes else 49,
                    "layer_collision_count": 0,
                    "transition_boundary_violation_count": 0,
                },
            )
        )


def require_audio_toolchain() -> AudioProbeToolchain:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if ffmpeg is None or ffprobe is None:
        pytest.skip("base AI comic deterministic support requires ffmpeg and ffprobe")
    return AudioProbeToolchain(
        ffmpeg_path=Path(ffmpeg).resolve(strict=True),
        ffprobe_path=Path(ffprobe).resolve(strict=True),
        ffmpeg=ToolIdentity(name="ffmpeg", version="fixture-system"),
        ffprobe=ToolIdentity(name="ffprobe", version="fixture-system"),
    )


def _required_system_executable(name: str) -> Path:
    executable = shutil.which(name)
    if executable is None:
        pytest.skip(f"base AI comic deterministic support requires {name}")
    return Path(executable).resolve(strict=True)


def _base_ai_comic_voice_candidate_preparer(
    root: Path, toolchain: AudioProbeToolchain
):
    base_prepare = make_deterministic_voice_candidate_preparer(root, toolchain)

    def prepare(request, preview, authorization, result, paths):
        candidate = base_prepare(
            request, preview, authorization, result, paths
        )
        assert candidate.caption is not None
        assert candidate.caption_asset_record is not None
        style_bytes = (
            b'{"font_family":"Base AI Comic Sans","schema_version":"1"}'
        )
        style_hash = hashlib.sha256(style_bytes).hexdigest()
        base_style = candidate.caption.style_reference
        assert base_style is not None
        style = base_style.model_copy(
            update={
                "content_hash": style_hash,
                "path": Path(f"assets/styles/{style_hash}.json"),
            }
        )
        caption = CaptionImportRequest.create(
            caption_track=candidate.caption.caption_track,
            style_reference=style,
            style_bytes=style_bytes,
        ).prepare()
        metadata = candidate.caption_asset_record.caption_metadata
        assert metadata is not None
        record = candidate.caption_asset_record.model_copy(
            update={
                "artifact_path": Path(
                    f"assets/captions/{caption.track_sha256}.json"
                ),
                "sha256": caption.track_sha256,
                "size_bytes": len(caption.track_bytes),
                "caption_metadata": metadata.model_copy(
                    update={
                        "style_reference_id": style.artifact_id,
                        "style_reference_revision": style.revision,
                        "style_content_hash": style.content_hash,
                    }
                ),
            }
        )
        return replace(
            candidate,
            caption=caption,
            caption_asset_record=record,
        )

    return prepare


class BaseAiComicE2ERuntime:
    """Test-only composition root; flow methods are introduced by later tasks."""

    def __init__(
        self,
        *,
        root: Path,
        image_runtime,
        voice_provider: DeterministicVoiceProvider,
        renderer: DeterministicHyperFramesRunner,
        analyzer: DeterministicReviewAnalyzer,
    ) -> None:
        self.root = root
        self.image_runtime = image_runtime
        self.voice_provider = voice_provider
        self.renderer = renderer
        self.analyzer = analyzer
        self._voice_request = None
        self._voice_result = None
        self._initial_render = None
        self._repair_commit = None
        self._trusted_repair_authority = ActorIdentity(
            actor_id="base-ai-comic-reviewer", actor_kind="human"
        )
        loaded = load_production_project(root / "project.yaml")
        if loaded.dependency_graph is None:
            raise AssertionError(
                "base AI comic support requires the P7 dependency graph"
            )
        self.synthetic_inputs_hash = canonical_sha256(
            {
                "project": loaded.project.content_hash,
                "registry": loaded.registry.content_hash,
                "dependency_graph": loaded.dependency_graph.content_hash,
                "voice_adapter": "deterministic-voice@1",
                "renderer": "hyperframes@0.7.103",
                "review_analyzer": self.analyzer.tool_identity.model_dump(mode="json"),
            }
        )

    @property
    def call_counts(self) -> BaseAiComicCallCounts:
        return BaseAiComicCallCounts(
            image_submit=len(self.image_runtime.provider_requests),
            voice_preview=self.voice_provider.preview_calls,
            voice_submit=self.voice_provider.generate_calls,
            review_analyze=self.analyzer.calls,
            renderer_version=self.renderer.version_calls,
            renderer_doctor=self.renderer.doctor_calls,
            renderer_run=self.renderer.run_calls,
            manifest_temp_write=_MANIFEST_WRITE_COUNTER.temp_write,
            manifest_replace=_MANIFEST_WRITE_COUNTER.replace,
        )

    def generate_two_shot_images(self):
        return self.image_runtime.generate_all()

    def generate_voice_and_captions(self) -> BaseAiComicVoiceResult:
        from ai_video.production.state_commit import ProductionStateCommitter
        import production_project_factory as project_factory

        toolchain = require_audio_toolchain()
        request = project_factory.make_base_ai_comic_voice_request(self.root)
        preview = self.voice_provider.preview(request)
        authorization = VoiceCallAuthorization.create(
            request_fingerprint=request.voice_request_fingerprint,
            preview_fingerprint=preview.preview_fingerprint,
            pricing_snapshot_id=request.pricing_snapshot_id,
            budget_reservation_receipt_id=request.budget_reservation_receipt_id,
            egress_authorization_receipt_id=(
                request.egress_authorization_receipt_id
            ),
            destination=preview.destination,
            payload_categories=preview.payload_categories,
            cost_ceiling_microunits=(
                preview.estimated_cost_upper_bound_microunits
            ),
            provider_enabled=True,
        )
        committer = ProductionStateCommitter(
            self.root,
            voice_candidate_preparer=_base_ai_comic_voice_candidate_preparer(
                self.root, toolchain
            ),
        )
        committer.generate_voice_asset(
            request,
            self.voice_provider,
            authorization,
            dependency_transition_preparer=lambda candidate: (
                project_factory.attach_base_ai_comic_voice_dependency_transition(
                    self.root,
                    candidate,
                    self.image_runtime.base_inputs,
                    request,
                )
            ),
        )
        loaded = load_production_project(self.root / "project.yaml")
        audio_ids = tuple(
            item.asset_id
            for item in loaded.registry.assets
            if item.asset_id == f"voice-{request.attempt_id}"
        )
        caption_ids = tuple(
            item.asset_id
            for item in loaded.registry.assets
            if item.asset_id == f"caption-{request.attempt_id}"
        )
        if len(audio_ids) != 1 or len(caption_ids) != 1:
            raise AssertionError("voice/caption activation did not reopen exact assets")
        caption_track_ids = tuple(
            item.caption_metadata.caption_track_id
            for item in loaded.registry.assets
            if item.asset_id in caption_ids and item.caption_metadata is not None
        )
        if len(caption_track_ids) != 1:
            raise AssertionError("caption track provenance did not reopen")
        self._voice_request = request
        result = BaseAiComicVoiceResult(audio_ids, caption_ids, caption_track_ids)
        self._voice_result = result
        return result

    def render_current_composition(
        self,
        *,
        revision: int | None = None,
        composition=None,
    ) -> BaseAiComicInitialRender:
        from ai_video.production import render_with_hyperframes
        from ai_video.production.composition import resolve_composition
        from ai_video.production.models import (
            RendererKind,
            RendererSelectionReceipt,
            RendererSourceReceipt,
            RenderReceipt,
        )
        from ai_video.production.state_commit import (
            BeginRenderAttemptRequest,
            ProductionStateCommitter,
        )
        import production_project_factory as project_factory

        if self._voice_request is None:
            raise AssertionError("voice/captions must be generated before render")
        loaded = load_production_project(self.root / "project.yaml")
        if composition is None:
            if revision is None:
                raise AssertionError("render requires a revision or exact composition")
            composition, caption_style_fingerprints = (
                project_factory.make_base_ai_comic_current_composition(
                    loaded,
                    self.image_runtime.base_inputs,
                    revision=revision,
                    voice_request=self._voice_request,
                )
            )
        else:
            if revision is not None:
                raise AssertionError("exact composition render must not rebuild by revision")
            caption_style_fingerprints = (
                project_factory.make_base_ai_comic_caption_style_fingerprints(
                    loaded,
                    self.image_runtime.base_inputs,
                    composition,
                )
            )
            revision = composition.revision
        timeline = resolve_composition(
            loaded, composition, renderer_version="0.7.103"
        )
        asset_sources = {
            span.asset_id: loaded.asset_paths[span.asset_id]
            for span in (*timeline.visual_spans, *timeline.audio_spans)
        }
        asset_sources.update(
            {
                cue.caption_asset_id: loaded.asset_paths[cue.caption_asset_id]
                for cue in timeline.caption_cues
            }
        )
        for binding in composition.caption_tracks:
            style = binding.style_reference
            if style is not None:
                asset_sources[style.artifact_id] = self.root / style.path
        selection = RendererSelectionReceipt(
            receipt_id=f"base-ai-comic-render-selection-{revision}",
            attempt_id=f"base-ai-comic-render-{revision}",
            requested_kind=RendererKind.HYPERFRAMES,
            selected_kinds=(RendererKind.HYPERFRAMES,),
            renderer_version="0.7.103",
            timeline_fingerprint=timeline.composition_fingerprint,
            current_project=loaded.manifest.active_project,
            current_registry=loaded.manifest.active_registry,
        )
        committer = ProductionStateCommitter(self.root)
        begin = BeginRenderAttemptRequest(
            loaded.manifest.manifest_revision,
            loaded.manifest.active_render_state,
            selection,
        )
        transition = project_factory.make_base_ai_comic_render_transition_preparer(
            self.root,
            self.image_runtime.base_inputs,
            composition,
            self._voice_request,
            caption_style_fingerprints,
        )
        toolchain = require_audio_toolchain()
        tool_root = self.root / "test-tools/hyperframes"
        binary = tool_root / "node_modules/.bin/hyperframes"
        browser = _required_system_executable("true")
        unshare = _required_system_executable("unshare")
        ip_path = _required_system_executable("ip")
        bash = _required_system_executable("bash")
        with patch(
            "ai_video.production.hyperframes._NetworkIsolatedHyperFramesRunner",
            return_value=self.renderer,
        ):
            manifest = render_with_hyperframes(
                committer=committer,
                begin_request=begin,
                timeline=timeline,
                asset_sources=asset_sources,
                allowed_asset_root=self.root,
                binary_path=binary,
                browser_path=browser,
                unshare_path=unshare,
                ip_path=ip_path,
                bash_path=bash,
                ffmpeg_path=toolchain.ffmpeg_path,
                ffprobe_path=toolchain.ffprobe_path,
                dependency_transition_preparer=transition,
            )
        reopened = load_production_project(self.root / "project.yaml")
        state = reopened.render_state
        if state is None or manifest.active_render_state is None:
            raise AssertionError("render state did not reopen after activation")
        receipt = RenderReceipt.model_validate_json(
            (self.root / state.render_receipt.path).read_bytes()
        )
        source_receipt = RendererSourceReceipt.model_validate_json(
            (self.root / state.source_receipt.path).read_bytes()
        )
        output = self.root / state.output.path
        with output.open("rb") as source:
            probe_payload = probe_clip_fd_with_executable(
                source.fileno(), toolchain.ffprobe_path
            )
        duration_milliseconds = round(
            float(probe_payload["format"]["duration"]) * 1000
        )
        result = BaseAiComicInitialRender(
            composition=composition,
            timeline=timeline,
            render_state=manifest.active_render_state,
            path=output,
            sha256=receipt.output_sha256,
            probe=BaseAiComicRenderProbe(
                duration_milliseconds=duration_milliseconds,
                video_stream_count=sum(
                    item.get("codec_type") == "video"
                    for item in probe_payload["streams"]
                ),
                audio_stream_count=sum(
                    item.get("codec_type") == "audio"
                    for item in probe_payload["streams"]
                ),
                staged_audio_binding_ids=tuple(
                    item.asset_id for item in source_receipt.audio_bindings
                ),
                staged_audio_track_ids=tuple(
                    track_id
                    for item in source_receipt.audio_bindings
                    for track_id in item.resolved_track_ids
                ),
            ),
        )
        if revision == 1:
            self._initial_render = result
        return result

    def load_manifest(self):
        return load_production_project(self.root / "project.yaml").manifest

    def manifest_bytes(self) -> bytes:
        return (self.root / "state/manifest.json").read_bytes()

    def _reopen_full_acceptance_result(
        self, bundle, manifest
    ) -> BaseAiComicFullAcceptanceResult:
        acceptance_state = manifest.final_acceptance_state
        if (
            acceptance_state is None
            or acceptance_state.active_receipt is None
            or acceptance_state.lifecycle is not ReviewLifecycle.FRESH
        ):
            raise AssertionError(
                "replay requires a fresh final acceptance with an active receipt"
            )
        if manifest.active_render_state is None:
            raise AssertionError("replay requires an active render state")
        if not manifest.repair_outcome_receipts:
            raise AssertionError("replay requires an active repair outcome receipt")

        # Bind the repair outcome from durable reopened state first so the
        # final acceptance and render identity can be re-verified against it.
        repair_outcome_pointer = manifest.repair_outcome_receipts[-1]
        repair_outcome_path = self.root / repair_outcome_pointer.path
        repair_outcome_bytes = repair_outcome_path.read_bytes()
        if (
            hashlib.sha256(repair_outcome_bytes).hexdigest()
            != repair_outcome_pointer.file_sha256
        ):
            raise AssertionError(
                "repair outcome receipt file SHA does not match pointer"
            )
        repair_outcome_receipt = RepairOutcomeReceipt.model_validate_json(
            repair_outcome_bytes
        )
        if not verify_artifact_hash(repair_outcome_receipt):
            raise AssertionError(
                "repair outcome receipt semantic content hash did not validate"
            )
        if (
            repair_outcome_receipt.repair_id != repair_outcome_pointer.repair_id
            or repair_outcome_receipt.content_hash
            != repair_outcome_pointer.content_hash
        ):
            raise AssertionError(
                "repair outcome receipt identity does not match its pointer"
            )
        if (
            repair_outcome_receipt.rerender_state
            != manifest.active_render_state
        ):
            raise AssertionError(
                "repair outcome rerender_state does not match active render state"
            )
        rerender_snapshot = RenderStateSnapshot.model_validate_json(
            (self.root / repair_outcome_receipt.rerender_state.path).read_bytes()
        )
        rerender_output_sha256 = hashlib.sha256(
            (self.root / rerender_snapshot.output.path).read_bytes()
        ).hexdigest()
        if (
            repair_outcome_receipt.rerender_output_sha256
            != rerender_output_sha256
        ):
            raise AssertionError(
                "repair outcome rerender_output_sha256 does not match "
                "reopened MP4"
            )

        # Bind the final acceptance receipt from durable reopened state.
        acceptance_pointer = acceptance_state.active_receipt
        acceptance_path = self.root / acceptance_pointer.path
        acceptance_bytes = acceptance_path.read_bytes()
        if (
            hashlib.sha256(acceptance_bytes).hexdigest()
            != acceptance_pointer.file_sha256
        ):
            raise AssertionError(
                "final acceptance receipt file SHA does not match pointer"
            )
        receipt = FinalAcceptanceReceipt.model_validate_json(acceptance_bytes)
        if not verify_artifact_hash(receipt):
            raise AssertionError(
                "final acceptance receipt semantic content hash did not validate"
            )
        if (
            receipt.render_state != manifest.active_render_state
            or receipt.render_output_sha256 != rerender_output_sha256
        ):
            raise AssertionError(
                "final acceptance receipt does not bind current render/MP4"
            )

        render_state_snapshot = bundle.render_state
        if render_state_snapshot is None:
            raise AssertionError("reopened bundle missing active render state")
        output_path = self.root / render_state_snapshot.output.path
        mp4_sha256 = hashlib.sha256(output_path.read_bytes()).hexdigest()
        return BaseAiComicFullAcceptanceResult(
            render_state=manifest.active_render_state,
            render_output_sha256=render_state_snapshot.output.file_sha256,
            output_path=output_path,
            mp4_sha256=mp4_sha256,
            acceptance_pointer=acceptance_pointer,
            acceptance_id=receipt.acceptance_id,
            acceptance_receipt=receipt,
            repair_outcome_pointer=repair_outcome_pointer,
            repair_outcome_repair_id=repair_outcome_receipt.repair_id,
            repair_outcome_receipt=repair_outcome_receipt,
            acceptance_lifecycle=acceptance_state.lifecycle,
        )

    def run_full_acceptance(self) -> BaseAiComicFullAcceptanceResult:
        bundle = load_production_project(self.root / "project.yaml")
        manifest = bundle.manifest
        if (
            manifest.final_acceptance_state is not None
            and manifest.final_acceptance_state.active_receipt is not None
            and manifest.final_acceptance_state.lifecycle is ReviewLifecycle.FRESH
        ):
            return self._reopen_full_acceptance_result(bundle, manifest)
        self.materialize_and_render_initial()
        failed = self.review_initial_render()
        approval = self.approve_exact_layout_repair(failed)
        repair_commit = self.commit_layout_repair(approval)
        repaired_composition_path = self.root / repair_commit.composition_path
        repaired_composition = CompositionSpec.model_validate_json(
            repaired_composition_path.read_bytes()
        )
        repaired = self.render_current_composition(composition=repaired_composition)
        passing = self.review_repaired_render()
        self.record_repair_outcome(approval, repaired, passing)
        self.record_final_acceptance(passing)
        reopened = load_production_project(self.root / "project.yaml")
        return self._reopen_full_acceptance_result(reopened, reopened.manifest)

    def materialize_and_render_initial(self) -> BaseAiComicInitialRender:
        self.generate_two_shot_images()
        self.generate_voice_and_captions()
        return self.render_current_composition(revision=1)

    def media_identity_snapshot(self) -> BaseAiComicMediaIdentitySnapshot:
        loaded = load_production_project(self.root / "project.yaml")
        assets = {item.asset_id: item for item in loaded.registry.assets}
        image_asset_ids: list[str] = []
        character_references: set[tuple[object, ...]] = set()
        scene_references: set[tuple[object, ...]] = set()
        request_evidence: list[tuple[Path, str, str]] = []
        receipt_evidence: list[tuple[Path, str, str]] = []
        image_attempts = tuple(
            item
            for item in loaded.manifest.attempts
            if item.operation == "image_generation"
            and item.status is StateCommitStatus.SUCCEEDED
        )
        for attempt in image_attempts:
            summary = attempt.image_request
            if summary is None or not attempt.candidate_image_asset_ids:
                raise AssertionError("durable image attempt evidence is incomplete")
            request_path = canonical_image_request_path(
                summary.request_fingerprint
            )
            request_bytes = (self.root / request_path).read_bytes()
            request = ImageGenerationRequest.model_validate_json(request_bytes)
            if (
                request.request_fingerprint != summary.request_fingerprint
                or request.attempt_id != attempt.attempt_id
                or request.output_asset_id not in attempt.candidate_image_asset_ids
            ):
                raise AssertionError("durable image request does not match attempt")
            request_evidence.append(
                (
                    request_path,
                    hashlib.sha256(request_bytes).hexdigest(),
                    request.request_fingerprint,
                )
            )
            for reference in request.references:
                identity = (
                    reference.creative_artifact_id,
                    reference.creative_revision,
                    reference.creative_content_hash,
                    reference.asset_id,
                    reference.asset_sha256,
                )
                if reference.role == "character":
                    character_references.add(identity)
                elif reference.role == "scene":
                    scene_references.add(identity)
            for asset_id in attempt.candidate_image_asset_ids:
                asset = assets.get(asset_id)
                if asset is None or asset.asset_type is not AssetType.IMAGE:
                    raise AssertionError("durable image attempt asset is not active")
                receipt_path = canonical_image_receipt_path(
                    asset.creation_receipt_id
                )
                receipt_bytes = (self.root / receipt_path).read_bytes()
                receipt = ImageProvenanceReceipt.model_validate_json(
                    receipt_bytes
                )
                if (
                    receipt.output_asset_id != asset_id
                    or receipt.output_sha256 != asset.sha256
                    or receipt.request_fingerprint != request.request_fingerprint
                    or receipt.references != request.references
                ):
                    raise AssertionError(
                        "durable image provenance does not match request and Registry"
                    )
                image_asset_ids.append(asset_id)
                receipt_evidence.append(
                    (
                        receipt_path,
                        hashlib.sha256(receipt_bytes).hexdigest(),
                        receipt.content_hash,
                    )
                )
        audio_assets = tuple(
            sorted(
                item.asset_id
                for item in loaded.registry.assets
                if item.asset_type is AssetType.VOICE
            )
        )
        caption_assets = tuple(
            sorted(
                item.asset_id
                for item in loaded.registry.assets
                if item.asset_type is AssetType.CAPTION
            )
        )
        caption_track_ids = tuple(
            sorted(
                item.caption_metadata.caption_track_id
                for item in loaded.registry.assets
                if item.asset_id in caption_assets
                and item.caption_metadata is not None
            )
        )
        return BaseAiComicMediaIdentitySnapshot(
            project=loaded.manifest.active_project,
            registry=loaded.manifest.active_registry,
            image_asset_ids=tuple(sorted(image_asset_ids)),
            audio_asset_ids=audio_assets,
            caption_asset_ids=caption_assets,
            caption_track_ids=caption_track_ids,
            character_references=tuple(sorted(character_references)),
            scene_references=tuple(sorted(scene_references)),
            image_request_evidence=tuple(
                sorted(request_evidence, key=lambda item: item[0].as_posix())
            ),
            image_receipt_evidence=tuple(
                sorted(receipt_evidence, key=lambda item: item[0].as_posix())
            ),
        )

    def _committer(self):
        from ai_video.production.state_commit import ProductionStateCommitter

        return ProductionStateCommitter(
            self.root,
            repair_authorizer=lambda _request: self._trusted_repair_authority,
        )

    def _qa_policy(self) -> QaPolicy:
        return seal_artifact(
            QaPolicy(
                artifact_id="qa-policy-base-ai-comic-layout",
                revision=1,
                content_hash="0" * 64,
                creation_receipt_id="qa-policy-base-ai-comic-layout",
                source_provenance=(
                    SourceReference(
                        kind="derived", reference="base-ai-comic-e2e"
                    ),
                ),
                policy_id="base-ai-comic-layout",
                policy_version="1",
                required_layers=(QaLayer.LAYOUT,),
                technical_thresholds=QaTechnicalThresholds(
                    black_luma_max_milli=10,
                    silence_peak_max_millidb=-60_000,
                    clipping_peak_min_millidb=-100,
                ),
                layout_rules=QaLayoutRules(
                    safe_area_inset_milli=50,
                    caption_overflow_tolerance_milli=0,
                ),
                strategy_rules_version="1",
                semantic_requirement="optional",
                repair_authorities=(self._trusted_repair_authority,),
            )
        )

    def _review_current_render(self, *, label: str) -> BaseAiComicReviewResult:
        from ai_video.production.models import ResolvedTimeline

        bundle = load_production_project(self.root / "project.yaml")
        manifest = bundle.manifest
        if (
            manifest.active_dependency_graph is None
            or manifest.active_render_state is None
            or manifest.active_qa_policy is None
            or bundle.render_state is None
            or bundle.qa_policy is None
        ):
            raise AssertionError("review requires current graph, render, and policy")
        timeline = ResolvedTimeline.model_validate_json(
            (self.root / bundle.render_state.timeline.path).read_bytes()
        )
        context = build_technical_review_context(
            bundle,
            timeline,
            render_output_sha256=bundle.render_state.output.file_sha256,
            measurement_contract_version="1",
        )
        request = seal_artifact(
            ReviewRequest(
                artifact_id=f"review-request-base-ai-comic-{label}",
                revision=1,
                content_hash="0" * 64,
                creation_receipt_id=f"review-request-base-ai-comic-{label}",
                source_provenance=(
                    SourceReference(kind="derived", reference="base-ai-comic-e2e"),
                ),
                request_id=f"review-request-base-ai-comic-{label}",
                base_manifest_revision=manifest.manifest_revision,
                dependency_graph=manifest.active_dependency_graph,
                dependency_states_hash=canonical_sha256(
                    {
                        "dependency_states": [
                            item.model_dump(mode="json")
                            for item in manifest.dependency_states
                        ]
                    }
                ),
                render_state=manifest.active_render_state,
                render_output_sha256=bundle.render_state.output.file_sha256,
                timeline_fingerprint=bundle.render_state.timeline_fingerprint,
                qa_policy=manifest.active_qa_policy,
                requested_layers=(QaLayer.LAYOUT,),
                evidence_tool_identities=(self.analyzer.tool_identity,),
                technical_context=context,
            )
        )
        committer = self._committer()
        attempt_id = f"base-ai-comic-layout-review-{label}"
        begun = committer.begin_review(request, attempt_id=attempt_id)
        attempt = next(
            item for item in begun.attempts if item.attempt_id == attempt_id
        )
        if attempt.review_request is None:
            raise AssertionError("review request pointer was not persisted")
        evidence = committer.run_review_analysis(
            review_request=attempt.review_request,
            expected_manifest_revision=begun.manifest_revision,
            analyzer=self.analyzer.analyze,
        )
        if not isinstance(evidence, ReviewEvidence):
            raise AssertionError("review analyzer returned invalid evidence")
        evidence_payload = _canonical_json_bytes(evidence)
        evidence_pointer = ReviewEvidencePointer(
            path=canonical_review_evidence_path(evidence.content_hash),
            evidence_id=evidence.evidence_id,
            layer=evidence.layer,
            strength=evidence.strength,
            content_hash=evidence.content_hash,
            file_sha256=hashlib.sha256(evidence_payload).hexdigest(),
        )
        verdict = adjudicate_review_evidence(
            bundle.qa_policy, QaLayer.LAYOUT, (evidence,)
        )
        receipt = seal_artifact(
            ReviewReceipt(
                artifact_id=f"review-receipt-base-ai-comic-{label}",
                revision=1,
                content_hash="0" * 64,
                creation_receipt_id=f"review-receipt-base-ai-comic-{label}",
                source_provenance=(
                    SourceReference(kind="derived", reference=evidence.evidence_id),
                ),
                review_id=f"review-base-ai-comic-{label}",
                layer=QaLayer.LAYOUT,
                review_request=attempt.review_request,
                render_state=request.render_state,
                render_output_sha256=request.render_output_sha256,
                timeline_fingerprint=request.timeline_fingerprint,
                dependency_graph_revision_id=(
                    request.dependency_graph.revision_id
                ),
                qa_policy=request.qa_policy,
                evidence=(evidence_pointer,),
                evidence_ids=(evidence.evidence_id,),
                tool_identities=(self.analyzer.tool_identity,),
                issue_ids=("layout.safe-area",) if verdict is QaVerdict.FAIL else (),
                verdict=verdict,
            )
        )
        measured = self.load_manifest()
        reviewed = committer.record_review_receipt(
            receipt,
            (evidence,),
            expected_manifest_revision=measured.manifest_revision,
            attempt_id=attempt_id,
        )
        pointer = next(
            item
            for item in reviewed.active_review_receipts
            if item.layer is QaLayer.LAYOUT
        )
        return BaseAiComicReviewResult(receipt, pointer, (evidence,))

    def review_initial_render(self) -> BaseAiComicReviewResult:
        manifest = self.load_manifest()
        self._committer().activate_qa_policy(
            self._qa_policy(),
            expected_manifest_revision=manifest.manifest_revision,
            attempt_id="base-ai-comic-layout-policy",
        )
        return self._review_current_render(label="initial")

    def review_repaired_render(self) -> tuple[BaseAiComicReviewResult, ...]:
        current = self.load_manifest()
        if current.active_render_state is None:
            raise AssertionError("repaired render is not active")
        self.analyzer.bind_repaired_render_state(current.active_render_state)
        result = self._review_current_render(label="repaired")
        return (result,)

    def approve_exact_layout_repair(
        self, failed: BaseAiComicReviewResult
    ) -> BaseAiComicRepairApproval:
        bundle = load_production_project(self.root / "project.yaml")
        manifest = bundle.manifest
        if (
            failed.verdict is not QaVerdict.FAIL
            or failed.issue_ids != ("layout.safe-area",)
            or manifest.active_dependency_graph is None
            or manifest.active_render_state is None
            or manifest.active_qa_policy is None
            or bundle.render_state is None
        ):
            raise AssertionError("repair approval requires the exact current layout fail")
        actor = ActorIdentity(actor_id="codex", actor_kind="codex")
        action = RepairAction(
            kind="composition_layout",
            parameters_fingerprint=canonical_sha256(
                {"translate_x_px": 24, "issue_id": "layout.safe-area"}
            ),
        )
        closure = (
            "composition:main",
            "timeline:main",
            "renderer-source:main",
            "render:main",
        )
        target_artifact = (
            self._initial_render.composition.artifact_id
            if self._initial_render is not None
            else "composition-main"
        )
        scope = canonical_sha256(
            {
                "repair_id": "base-ai-comic-layout-repair",
                "actor": actor.model_dump(mode="json"),
                "action": action.model_dump(mode="json"),
                "target_artifact_ids": [target_artifact],
                "target_node_ids": ["composition:main"],
                "expected_invalidation_node_ids": list(closure),
            }
        )
        state_by_id = {item.node_id: item for item in manifest.dependency_states}
        request = seal_artifact(
            RepairRequest(
                artifact_id="repair-request-base-ai-comic-layout",
                revision=1,
                content_hash="0" * 64,
                creation_receipt_id="repair-request-base-ai-comic-layout",
                source_provenance=(
                    SourceReference(kind="derived", reference=failed.receipt.review_id),
                ),
                repair_id="base-ai-comic-layout-repair",
                base_manifest_revision=manifest.manifest_revision,
                dependency_graph=manifest.active_dependency_graph,
                dependency_states_hash=canonical_sha256(
                    {
                        "dependency_states": [
                            item.model_dump(mode="json")
                            for item in manifest.dependency_states
                        ]
                    }
                ),
                render_state=manifest.active_render_state,
                render_output_sha256=bundle.render_state.output.file_sha256,
                timeline_fingerprint=bundle.render_state.timeline_fingerprint,
                qa_policy=manifest.active_qa_policy,
                review_receipt_ids=(failed.receipt.review_id,),
                issue_ids=failed.issue_ids,
                evidence_ids=failed.receipt.evidence_ids,
                root_cause_hypothesis="layout safe area requires deterministic inset",
                selected_repair_action=action,
                exact_target_artifact_ids=(target_artifact,),
                exact_target_node_ids=("composition:main",),
                expected_invalidation_node_ids=closure,
                actor=actor,
                authorization=RepairAuthorization(
                    authorization_id="base-ai-comic-layout-authorization",
                    authorized=True,
                    authorized_by=self._trusted_repair_authority,
                    scope_fingerprint=scope,
                ),
                before_fingerprints=(
                    NamedFingerprint(
                        name="composition:main",
                        fingerprint=state_by_id[
                            "composition:main"
                        ].desired_fingerprint,
                    ),
                ),
            )
        )
        receipt = seal_artifact(
            ApprovedRepairReceipt.model_validate(
                {
                    **request.model_dump(mode="python"),
                    "artifact_id": "approved-repair-base-ai-comic-layout",
                    "content_hash": "0" * 64,
                    "request_content_hash": request.content_hash,
                }
            )
        )
        approved = self._committer().record_approved_repair_receipt(
            request,
            receipt,
            expected_manifest_revision=manifest.manifest_revision,
            attempt_id="base-ai-comic-layout-repair-approval",
        )
        if approved.active_approved_repair is None:
            raise AssertionError("approved repair pointer was not activated")
        return BaseAiComicRepairApproval(
            request, receipt, approved.active_approved_repair
        )

    def _layout_repair_commit_request(
        self,
        approval: BaseAiComicRepairApproval,
        *,
        mutation: str | None = None,
    ):
        from ai_video.production.dependency import (
            build_dependency_graph,
            build_production_dependency_graph,
            desired_fingerprints,
            resolve_dependency_state,
        )
        from ai_video.production.state_commit import (
            StateCommitRequest,
            prepare_dependency_graph_transition,
        )
        import production_project_factory as project_factory

        if self._voice_request is None:
            raise AssertionError("repair requires generated voice state")
        loaded = load_production_project(self.root / "project.yaml")
        manifest = loaded.manifest
        composition, styles = project_factory.make_base_ai_comic_current_composition(
            loaded,
            self.image_runtime.base_inputs,
            revision=2,
            voice_request=self._voice_request,
        )
        inputs = replace(
            self.image_runtime.base_inputs,
            project=loaded,
            composition_spec=composition,
            voice_requests=(
                *self.image_runtime.base_inputs.voice_requests,
                self._voice_request,
            ),
            caption_style_fingerprints=styles,
        )
        graph = build_production_dependency_graph(inputs)
        if mutation in {"add_image_node", "blanket_all_nodes"}:
            changed_nodes = []
            image_changed = False
            for node in graph.nodes:
                should_change = mutation == "blanket_all_nodes" or (
                    mutation == "add_image_node"
                    and not image_changed
                    and node.node_id.startswith("asset:")
                    and "image" in node.artifact_id
                )
                if not should_change:
                    changed_nodes.append(node)
                    continue
                image_changed = image_changed or mutation == "add_image_node"
                first, *rest = node.contributions
                changed_nodes.append(
                    node.model_copy(
                        update={
                            "contributions": (
                                first.model_copy(
                                    update={
                                        "fingerprint": canonical_sha256(
                                            {
                                                "forged": mutation,
                                                "node": node.node_id,
                                                "before": first.fingerprint,
                                            }
                                        )
                                    }
                                ),
                                *rest,
                            )
                        }
                    )
                )
            graph = build_dependency_graph(changed_nodes, graph.edges)
        states = resolve_dependency_state(graph, manifest.dependency_states).states
        transition = prepare_dependency_graph_transition(
            expected_manifest_revision=manifest.manifest_revision,
            base_dependency_graph=manifest.active_dependency_graph,
            candidate_graph=graph,
            candidate_dependency_states=states,
            expected_desired_fingerprints=desired_fingerprints(graph),
        )
        committer = self._committer()
        graph_payload = _canonical_json_bytes(graph)
        composition_payload = _canonical_json_bytes(composition)
        composition_path = Path(
            "state/repairs/candidates/"
            f"composition.{composition.content_hash}.json"
        )
        artifacts = tuple(
            sorted(
                (
                    committer.prepare_artifact(
                        f"base-ai-comic-{mutation or 'layout'}-repair",
                        manifest.active_project.path,
                        (self.root / manifest.active_project.path).read_bytes(),
                    ),
                    committer.prepare_artifact(
                        f"base-ai-comic-{mutation or 'layout'}-repair",
                        manifest.active_registry.path,
                        (self.root / manifest.active_registry.path).read_bytes(),
                    ),
                    committer.prepare_artifact(
                        f"base-ai-comic-{mutation or 'layout'}-repair",
                        transition.candidate_dependency_graph.path,
                        graph_payload,
                    ),
                    committer.prepare_artifact(
                        f"base-ai-comic-{mutation or 'layout'}-repair",
                        composition_path,
                        composition_payload,
                    ),
                ),
                key=lambda item: item.relative_path.as_posix(),
            )
        )
        before = {
            item.node_id: item.desired_fingerprint
            for item in manifest.dependency_states
        }
        after = {item.node_id: item.desired_fingerprint for item in states}
        changed = {
            node_id
            for node_id in set(before) | set(after)
            if before.get(node_id) != after.get(node_id)
        }
        approved_order = approval.receipt.expected_invalidation_node_ids
        invalidated = tuple(item for item in approved_order if item in changed) + tuple(
            sorted(changed.difference(approved_order))
        )
        return (
            StateCommitRequest(
                attempt_id=f"base-ai-comic-{mutation or 'layout'}-repair",
                operation="repair",
                expected_manifest_revision=manifest.manifest_revision,
                artifacts=artifacts,
                next_project=manifest.active_project,
                next_registry=manifest.active_registry,
                dependency_graph_transition=transition,
                approved_repair_receipt=approval.pointer,
            ),
            composition,
            composition_path,
            hashlib.sha256(composition_payload).hexdigest(),
            invalidated,
        )

    def commit_layout_repair(
        self, approval: BaseAiComicRepairApproval
    ) -> BaseAiComicRepairCommit:
        (
            request,
            composition,
            composition_path,
            composition_file_sha256,
            invalidated,
        ) = self._layout_repair_commit_request(approval)
        manifest = self._committer().commit(request)
        committed_bytes = (self.root / composition_path).read_bytes()
        committed_composition = type(composition).model_validate_json(committed_bytes)
        if (
            hashlib.sha256(committed_bytes).hexdigest()
            != composition_file_sha256
            or not verify_artifact_hash(committed_composition)
            or committed_composition != composition
        ):
            raise AssertionError("committed repair composition did not reopen exactly")
        result = BaseAiComicRepairCommit(
            committed_composition,
            composition_path,
            composition_file_sha256,
            invalidated,
            manifest,
        )
        self._repair_commit = result
        return result

    def record_repair_outcome(
        self,
        approval: BaseAiComicRepairApproval,
        repaired: BaseAiComicInitialRender,
        passing: tuple[BaseAiComicReviewResult, ...],
    ) -> RepairOutcomeReceipt:
        if self._repair_commit is None:
            raise AssertionError("repair outcome requires a committed repair")
        manifest = self.load_manifest()
        state_by_id = {item.node_id: item for item in manifest.dependency_states}
        receipt = seal_artifact(
            RepairOutcomeReceipt(
                artifact_id="repair-outcome-base-ai-comic-layout",
                revision=1,
                content_hash="0" * 64,
                creation_receipt_id="repair-outcome-base-ai-comic-layout",
                source_provenance=(
                    SourceReference(
                        kind="derived", reference=passing[0].receipt.review_id
                    ),
                ),
                repair_id=approval.receipt.repair_id,
                approved_receipt=approval.pointer,
                review_receipt_ids=approval.receipt.review_receipt_ids,
                issue_ids=approval.receipt.issue_ids,
                evidence_ids=approval.receipt.evidence_ids,
                root_cause_hypothesis=approval.receipt.root_cause_hypothesis,
                selected_repair_action=approval.receipt.selected_repair_action,
                exact_target_artifact_ids=approval.receipt.exact_target_artifact_ids,
                exact_target_node_ids=approval.receipt.exact_target_node_ids,
                expected_invalidation_node_ids=(
                    approval.receipt.expected_invalidation_node_ids
                ),
                actor=approval.receipt.actor,
                authorization=approval.receipt.authorization,
                before_fingerprints=approval.receipt.before_fingerprints,
                after_fingerprints=(
                    NamedFingerprint(
                        name="composition:main",
                        fingerprint=state_by_id[
                            "composition:main"
                        ].desired_fingerprint,
                    ),
                ),
                actual_invalidation_node_ids=(
                    self._repair_commit.invalidated_node_ids
                ),
                rerender_state=repaired.render_state,
                rerender_output_sha256=repaired.sha256,
                rerender_timeline_fingerprint=(
                    repaired.timeline.composition_fingerprint
                ),
                fresh_review_receipts=tuple(item.pointer for item in passing),
            )
        )
        self._committer().record_repair_outcome(
            receipt,
            expected_manifest_revision=manifest.manifest_revision,
            attempt_id="base-ai-comic-layout-repair-outcome",
        )
        return receipt

    def record_final_acceptance(
        self, passing: tuple[BaseAiComicReviewResult, ...]
    ) -> BaseAiComicFinalAcceptance:
        bundle = load_production_project(self.root / "project.yaml")
        manifest = bundle.manifest
        if (
            manifest.active_dependency_graph is None
            or manifest.active_render_state is None
            or manifest.active_qa_policy is None
            or bundle.render_state is None
        ):
            raise AssertionError("final acceptance requires current production state")
        receipt = seal_artifact(
            FinalAcceptanceReceipt(
                artifact_id="final-acceptance-base-ai-comic",
                revision=1,
                content_hash="0" * 64,
                creation_receipt_id="final-acceptance-base-ai-comic",
                source_provenance=(
                    SourceReference(
                        kind="derived", reference=passing[0].receipt.review_id
                    ),
                ),
                acceptance_id="final-acceptance-base-ai-comic",
                dependency_graph=manifest.active_dependency_graph,
                dependency_states_hash=canonical_sha256(
                    {
                        "dependency_states": [
                            item.model_dump(mode="json")
                            for item in manifest.dependency_states
                        ]
                    }
                ),
                render_state=manifest.active_render_state,
                render_output_sha256=bundle.render_state.output.file_sha256,
                timeline_fingerprint=bundle.render_state.timeline_fingerprint,
                qa_policy=manifest.active_qa_policy,
                required_review_receipts=tuple(item.pointer for item in passing),
                verdict=QaVerdict.PASS,
            )
        )
        accepted = self._committer().record_final_acceptance(
            receipt,
            expected_manifest_revision=manifest.manifest_revision,
            attempt_id="base-ai-comic-final-acceptance",
        )
        state = accepted.final_acceptance_state
        if state is None:
            raise AssertionError("final acceptance state was not activated")
        return BaseAiComicFinalAcceptance(receipt, state.lifecycle)

    def materialize_review_and_approve(self):
        self.materialize_and_render_initial()
        failed = self.review_initial_render()
        self._last_approval = self.approve_exact_layout_repair(failed)
        return self.load_manifest()

    def commit_forged_repair(self, mutation: str) -> None:
        if not hasattr(self, "_last_approval"):
            raise AssertionError("forged repair requires a current approval")
        approval = self._last_approval
        if mutation == "stale_render":
            manifest = self.load_manifest()
            stale_request = seal_artifact(
                approval.request.model_copy(
                    update={
                        "content_hash": "0" * 64,
                        "base_manifest_revision": manifest.manifest_revision,
                        "render_state": approval.request.render_state.model_copy(
                            update={"file_sha256": "f" * 64}
                        ),
                    }
                )
            )
            stale_receipt = seal_artifact(
                ApprovedRepairReceipt.model_validate(
                    {
                        **stale_request.model_dump(mode="python"),
                        "artifact_id": "approved-repair-base-ai-comic-stale",
                        "content_hash": "0" * 64,
                        "request_content_hash": stale_request.content_hash,
                    }
                )
            )
            self._committer().record_approved_repair_receipt(
                stale_request,
                stale_receipt,
                expected_manifest_revision=manifest.manifest_revision,
                attempt_id="base-ai-comic-stale-render-repair",
            )
            return
        request, _, _, _, _ = self._layout_repair_commit_request(
            approval, mutation=mutation
        )
        self._committer().commit(request)


class _ReopenImageRuntime:
    """Test-only image runtime stub that reuses existing durable state.

    The reopen runtime never calls provider side effects; it exists so a
    fresh ``BaseAiComicE2ERuntime`` can reopen the accepted project without
    re-running the image setup and overwriting the final acceptance state.
    """

    def __init__(self, root: Path, base_inputs: object) -> None:
        self.root = root
        self.base_inputs = base_inputs
        self.provider_requests: list[object] = []
        self.request_binding_counts: dict[str, int] = {}
        self._first_result = None
        self.writer = None

    def generate_all(self):
        raise AssertionError(
            "reopen image runtime must not generate new images; "
            "exact replay must short-circuit before any provider call"
        )

    def change_only_shot_1_prompt_and_generate(self):
        raise AssertionError(
            "reopen image runtime must not regenerate images; "
            "exact replay must short-circuit before any provider call"
        )


def make_base_ai_comic_reopen_runtime(
    root: Path,
) -> BaseAiComicE2ERuntime:
    """Create a fresh ``BaseAiComicE2ERuntime`` against an existing project.

    The factory reuses the already-committed durable state and never
    invokes image/voice/analyzer/renderer side effects, so a fresh process
    can reopen the accepted final state and exact replay short-circuits
    through durable evidence only.
    """

    toolchain = require_audio_toolchain()
    loaded = load_production_project(root / "project.yaml")
    image_runtime = _ReopenImageRuntime(root, loaded)
    return BaseAiComicE2ERuntime(
        root=root,
        image_runtime=image_runtime,
        voice_provider=DeterministicVoiceProvider(),
        renderer=DeterministicHyperFramesRunner(toolchain.ffmpeg_path),
        analyzer=DeterministicReviewAnalyzer(),
    )
