from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path

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
from ai_video.production.hyperframes import RendererCommandResult
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
