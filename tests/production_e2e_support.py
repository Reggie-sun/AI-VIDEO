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
from ai_video.production.captions import normalize_character_alignment
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.hyperframes import (
    RendererCommandResult,
    probe_clip_fd_with_executable,
)
from ai_video.production.models import (
    EvidenceStrength,
    QaLayer,
    ReviewEvidence,
    ReviewRequest,
    SourceReference,
    ToolIdentity,
)
from ai_video.production.project import load_production_project


_VOICE_FIXTURE = (
    Path(__file__).parent / "fixtures/voice_captions/dialogue-mono-48000.wav"
)


@dataclass(frozen=True)
class BaseAiComicCallCounts:
    image_submit: int = 0
    voice_submit: int = 0
    review_analyze: int = 0
    renderer_run: int = 0


@dataclass(frozen=True)
class BaseAiComicVoiceResult:
    audio_asset_ids: tuple[str, ...]
    caption_asset_ids: tuple[str, ...]
    caption_track_ids: tuple[str, ...]


@dataclass(frozen=True)
class BaseAiComicRenderProbe:
    duration_milliseconds: int
    video_stream_count: int


@dataclass(frozen=True)
class BaseAiComicInitialRender:
    composition: object
    timeline: object
    render_state: object
    path: Path
    sha256: str
    probe: BaseAiComicRenderProbe


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
                    "caption_overflow_milli": 0 if passes else 1,
                    "safe_area_inset_milli": 50,
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
    from ai_video.production.captions import CaptionImportRequest
    from test_production_voice_captions_e2e import _voice_candidate_preparer

    base_prepare = _voice_candidate_preparer(root, toolchain)

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
            voice_submit=self.voice_provider.generate_calls,
            review_analyze=self.analyzer.calls,
            renderer_run=self.renderer.render_calls,
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
        return BaseAiComicVoiceResult(audio_ids, caption_ids, caption_track_ids)

    def render_current_composition(
        self, *, revision: int
    ) -> BaseAiComicInitialRender:
        from ai_video.production import render_with_hyperframes
        from ai_video.production.composition import resolve_composition
        from ai_video.production.models import (
            RendererKind,
            RendererSelectionReceipt,
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
        composition, caption_style_fingerprints = (
            project_factory.make_base_ai_comic_current_composition(
                loaded,
                self.image_runtime.base_inputs,
                revision=revision,
                voice_request=self._voice_request,
            )
        )
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
        output = self.root / state.output.path
        with output.open("rb") as source:
            probe_payload = probe_clip_fd_with_executable(
                source.fileno(), toolchain.ffprobe_path
            )
        duration_milliseconds = round(
            float(probe_payload["format"]["duration"]) * 1000
        )
        return BaseAiComicInitialRender(
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
            ),
        )
