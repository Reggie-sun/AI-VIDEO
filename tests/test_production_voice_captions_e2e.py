from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.audio import (
    AudioImportRequest,
    AudioProbeToolchain,
    VoiceGenerationRequest,
    VoiceGenerationPreview,
    VoicePricingSnapshot,
    VoiceProviderResult,
)
from ai_video.production.captions import normalize_character_alignment
from ai_video.production.composition import resolve_composition
from ai_video.production.hashing import seal_artifact
from ai_video.production.hyperframes import (
    RendererCommandResult,
    _render_with_hyperframes,
    decoded_audio_sha256_fd_with_executable,
    decoded_frame_sha256_fd,
    probe_clip_fd_with_executable,
)
from ai_video.production.models import (
    AssetRegistrySnapshot,
    AssetSourceKind,
    AudioKind,
    AudioSource,
    AudioTrackSpec,
    CaptionStyleReference,
    CaptionTrackBinding,
    ProductionManifest,
    RendererKind,
    RendererSelectionReceipt,
    RendererSourceReceipt,
    RenderReceipt,
    ResolvedTimeline,
    StateCommitAttempt,
    StateCommitStatus,
    ToolIdentity,
)
from ai_video.production.project import load_production_project
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import (
    BeginRenderAttemptRequest,
    PreparedArtifact,
    ProductionStateCommitter,
    prepare_audio_registry_commit,
    recover_production_state,
)

import production_project_factory as project_factory
from production_voice_e2e_support import (
    make_deterministic_voice_candidate_preparer,
)


FIXTURE_ROOT = Path(__file__).parent / "fixtures/voice_captions"
DIALOGUE = FIXTURE_ROOT / "dialogue-mono-48000.wav"
AMBIENCE = FIXTURE_ROOT / "ambience-stereo-48000.wav"
ZERO_HASH = "0" * 64
MIXED_PCM_SHA256 = "592b598a4f1efe892556506364e8304730eb6573a0d58ee89ed1997f6e920b33"
OUTPUT_DECODED_PCM_SHA256 = (
    "7489b97d0668d8a283e37ae47eded722450e010a60030818f0c303d64141916f"
)
OUTPUT_DECODED_FRAMES_SHA256 = (
    "5f25f0842e8658f71d6d9653264637592151f82b185fccc23d189efd7d18bcd5"
)
EXPECTED_AUDIO_SPANS = (
    (
        "dialogue",
        "dialogue",
        "voice-voice-e2e",
        "f72a3208e25253873858b9f9161e0851e336eb5e97d717a01679df729c428a63",
        0,
        96_000,
        0,
        96_000,
        0,
        0,
        0,
        None,
    ),
    (
        "ambience",
        "ambience",
        "ambience-room",
        "e58b991cd53fb90d79f3482957a51a56bf56d8cfb6cbdf40152bd39ac9102dca",
        0,
        48_000,
        0,
        48_000,
        0,
        480,
        0,
        None,
    ),
    (
        "sfx",
        "sfx",
        "sfx-hit",
        "e58b991cd53fb90d79f3482957a51a56bf56d8cfb6cbdf40152bd39ac9102dca",
        96_000,
        48_000,
        0,
        48_000,
        0,
        0,
        0,
        None,
    ),
    (
        "bgm",
        "bgm",
        "bgm-theme",
        "e58b991cd53fb90d79f3482957a51a56bf56d8cfb6cbdf40152bd39ac9102dca",
        0,
        48_000,
        0,
        48_000,
        -6_000,
        480,
        480,
        (("dialogue",), -12_000, 240, 480),
    ),
)
EXPECTED_CAPTION_CUES = (
    (
        "caption-voice-e2e",
        "caption-track-voice-e2e",
        "segment-0001",
        0,
        88_608,
        0,
        45,
    ),
)


def _manifest(root: Path) -> ProductionManifest:
    return ProductionManifest.model_validate_json(
        (root / "state/manifest.json").read_bytes()
    )


def _toolchain() -> AudioProbeToolchain:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if ffmpeg is None or ffprobe is None:
        pytest.skip("P4 deterministic audio acceptance requires ffmpeg and ffprobe")
    return AudioProbeToolchain(
        ffmpeg_path=Path(ffmpeg).resolve(strict=True),
        ffprobe_path=Path(ffprobe).resolve(strict=True),
        ffmpeg=ToolIdentity(name="ffmpeg", version="fixture-system"),
        ffprobe=ToolIdentity(name="ffprobe", version="fixture-system"),
    )


def _permit_binding(request, authorization) -> dict[str, str]:
    return {
        "attempt_id": request.attempt_id,
        "request_fingerprint": request.voice_request_fingerprint,
        "authorization_fingerprint": authorization.authorization_fingerprint,
        "destination": authorization.destination,
        "budget_reservation_receipt_id": (authorization.budget_reservation_receipt_id),
        "egress_authorization_receipt_id": (
            authorization.egress_authorization_receipt_id
        ),
    }


def _sanitized_alignment(script: str, duration_samples: int) -> bytes:
    step_samples = duration_samples // (len(script) + 1)
    payload = {
        "characters": list(script),
        "character_start_times_seconds": [
            str(index * step_samples / 48_000) for index in range(len(script))
        ],
        "character_end_times_seconds": [
            str((index + 1) * step_samples / 48_000) for index in range(len(script))
        ],
    }
    return normalize_character_alignment(
        payload,
        sample_rate_hz=48_000,
        duration_samples=duration_samples,
        speaker_id="speaker-1",
    ).receipt_bytes


class _FakeDialogueProvider:
    def __init__(
        self, root: Path, preview: VoiceGenerationPreview, authorization
    ) -> None:
        self.root = root
        self.expected_preview = preview
        self.authorization = authorization
        self.preview_calls = 0
        self.generate_calls = 0

    def preview(self, request: VoiceGenerationRequest) -> VoiceGenerationPreview:
        self.preview_calls += 1
        return self.expected_preview

    def generate(self, request, authorization, permit) -> VoiceProviderResult:
        assert authorization == self.authorization
        current = _manifest(self.root)
        attempt = next(
            item for item in current.attempts if item.attempt_id == request.attempt_id
        )
        assert attempt.voice_phase == "submit_intent"
        assert current.manifest_revision == 3
        paths = ProductionStateCommitter(self.root).voice_attempt_paths(
            request.attempt_id
        )
        assert paths.request_path.is_file()
        assert paths.preview_path.is_file()
        assert paths.authorization_path.is_file()
        assert paths.submit_intent_path.is_file()
        assert permit._consume_voice_submit_permit(
            **_permit_binding(request, authorization)
        )
        self.generate_calls += 1
        base = project_factory.make_voice_provider_result(
            request,
            self.expected_preview,
            authorization,
            audio_bytes=DIALOGUE.read_bytes(),
        )
        alignment = _sanitized_alignment(request.script_text, 96_000)
        return VoiceProviderResult.create(
            request=request,
            preview=self.expected_preview,
            authorization=authorization,
            pricing=VoicePricingSnapshot(
                snapshot_id=base.cost_receipt.pricing_snapshot_id,
                effective_date=self.expected_preview.pricing_effective_date,
                currency=self.expected_preview.currency,
                pricing_unit=self.expected_preview.pricing_unit,
                unit_price_microunits=self.expected_preview.unit_price_microunits,
                minimum_billable_units=self.expected_preview.minimum_billable_units,
            ),
            audio_bytes=DIALOGUE.read_bytes(),
            content_type="audio/wav",
            provider_request_id=base.provider_request_id,
            provider_trace_id=base.provider_trace_id,
            alignment_receipt_bytes=alignment,
            cost_receipt=base.cost_receipt,
            provenance_receipt=base.provenance_receipt,
            terminal_status="succeeded",
        )


def _import_local_mix_assets(
    root: Path, toolchain: AudioProbeToolchain
) -> ProductionManifest:
    loaded = load_production_project(root / "project.yaml")
    prepared = []
    for asset_id, kind in (
        ("ambience-room", AudioKind.AMBIENCE),
        ("bgm-theme", AudioKind.BGM),
        ("sfx-hit", AudioKind.SFX),
    ):
        source = AudioSource(
            kind=AssetSourceKind.IMPORTED,
            provider_or_tool=ToolIdentity(name="fixture-import", version="1"),
            input_fingerprint=hashlib.sha256(asset_id.encode()).hexdigest(),
            original_reference=f"fixture:{asset_id}",
        )
        request = AudioImportRequest(
            asset_id=asset_id,
            audio_kind=kind,
            mime_type="audio/wav",
            source=source,
            provenance_receipt_id=f"provenance-{asset_id}",
            creation_receipt_id=f"creation-{asset_id}",
            usage_license="fixture-only",
        )
        with AMBIENCE.open("rb") as handle:
            prepared.append(
                request.prepare(
                    handle.fileno(), toolchain=toolchain, measure_loudness=False
                )
            )
    records = tuple(
        sorted((item.asset_record for item in prepared), key=lambda item: item.asset_id)
    )
    candidate = AssetRegistrySnapshot(
        schema_version="2.1",
        revision_id=ZERO_HASH,
        content_hash=ZERO_HASH,
        assets=loaded.registry.assets + records,
    )
    revision = registry_semantic_sha256(candidate)
    candidate = candidate.model_copy(
        update={"revision_id": revision, "content_hash": revision}
    )
    artifact_by_path = {
        item.asset_record.artifact_path: PreparedArtifact(
            item.asset_record.artifact_path,
            item.payload,
            item.asset_record.sha256,
        )
        for item in prepared
    }
    manifest = loaded.manifest
    request = prepare_audio_registry_commit(
        manifest=manifest,
        project=loaded.project,
        base_registry=loaded.registry,
        registry=candidate,
        attempt_id="import-local-mix",
        artifacts=tuple(artifact_by_path.values()),
        active_project_artifact=PreparedArtifact(
            manifest.active_project.path,
            (root / manifest.active_project.path).read_bytes(),
            manifest.active_project.file_sha256,
        ),
    )
    return ProductionStateCommitter(root).commit(request)


@dataclass(frozen=True)
class _RenderCall:
    command: str


class _FakeHyperFramesRunner:
    def __init__(self, ffmpeg_path: Path) -> None:
        self.ffmpeg_path = ffmpeg_path
        self.calls: list[_RenderCall] = []
        self.mixed_pcm_sha256: str | None = None
        self.caption_frame_windows: tuple[tuple[int, int], ...] = ()

    def version(self, *, env) -> str:
        assert env["HYPERFRAMES_NO_TELEMETRY"] == "1"
        self.calls.append(_RenderCall("version"))
        return "0.7.103"

    def doctor(self, *, env) -> RendererCommandResult:
        assert env["HYPERFRAMES_NO_TELEMETRY"] == "1"
        self.calls.append(_RenderCall("doctor"))
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

    def run(self, command, args, *, cwd, env, timeout_seconds) -> RendererCommandResult:
        assert env["HYPERFRAMES_NO_TELEMETRY"] == "1"
        self.calls.append(_RenderCall(command))
        if command == "render":
            source = (cwd / "index.html").read_text(encoding="utf-8")
            caption_elements = re.findall(
                r'<div[^>]*class="[^"]*\bclip\b[^"]*\bcaption\b[^"]*"[^>]*>',
                source,
            )
            self.caption_frame_windows = tuple(
                (
                    int(re.search(r'data-start-frame="(\d+)"', element).group(1)),
                    int(
                        re.search(r'data-end-frame-exclusive="(\d+)"', element).group(1)
                    ),
                )
                for element in caption_elements
            )
            mixed_wavs = tuple((cwd / "assets").glob("*.wav"))
            assert len(mixed_wavs) == 1
            mixed_wav = mixed_wavs[0]
            with wave.open(str(mixed_wav), "rb") as handle:
                assert (
                    handle.getnframes(),
                    handle.getframerate(),
                    handle.getnchannels(),
                    handle.getsampwidth(),
                ) == (192_000, 48_000, 2, 2)
                self.mixed_pcm_sha256 = hashlib.sha256(
                    handle.readframes(handle.getnframes())
                ).hexdigest()
            drawboxes = ",".join(
                (
                    "drawbox=x=64:y=600:w=1152:h=80:color=cyan:t=fill:"
                    f"enable=gte(n\\,{start})*lt(n\\,{end})"
                )
                for start, end in self.caption_frame_windows
            )
            output = Path(args[args.index("-o") + 1])
            completed = subprocess.run(
                [
                    str(self.ffmpeg_path),
                    "-nostdin",
                    "-v",
                    "error",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "color=c=black:s=1280x720:r=24:d=4",
                    "-i",
                    str(mixed_wav),
                    "-vf",
                    drawboxes,
                    "-map",
                    "0:v:0",
                    "-map",
                    "1:a:0",
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
                    "-c:a",
                    "aac",
                    "-b:a",
                    "192k",
                    "-ar",
                    "48000",
                    "-ac",
                    "2",
                    "-map_metadata",
                    "-1",
                    "-movflags",
                    "+faststart",
                    str(output),
                ],
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
        if command == "lint":
            payload = {"errorCount": 0, "warningCount": 0}
        else:
            payload = {"ok": True}
            for section in ("lint", "runtime", "layout", "motion", "contrast"):
                payload[section] = {"errorCount": 0, "warningCount": 0}
        return RendererCommandResult(
            returncode=0, stdout=json.dumps(payload), stderr=""
        )


def _executable(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o700)
    return path.resolve(strict=True)


def _sample_rgb_frame(held_fd: int, frame: int, *, ffmpeg_path: Path) -> bytes:
    duplicate = os.dup(held_fd)
    try:
        os.lseek(duplicate, 0, os.SEEK_SET)
        completed = subprocess.run(
            [
                str(ffmpeg_path),
                "-v",
                "error",
                "-i",
                f"/proc/self/fd/{duplicate}",
                "-vf",
                f"select=eq(n\\,{frame}),crop=2:2:640:640",
                "-frames:v",
                "1",
                "-pix_fmt",
                "rgb24",
                "-f",
                "rawvideo",
                "-",
            ],
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
            pass_fds=(duplicate,),
            check=False,
            timeout=120,
        )
    finally:
        os.close(duplicate)
    assert completed.returncode == 0, completed.stderr.decode(errors="replace")
    assert len(completed.stdout) == 12
    return completed.stdout[:3]


def test_manifest_210_voice_generation_preserves_latest_schema(
    tmp_path: Path,
) -> None:
    project_factory.write_and_load_two_shot_project(tmp_path)
    before = load_production_project(tmp_path / "project.yaml").manifest.model_copy(
        update={"schema_version": "2.10"}
    )
    (tmp_path / "state/manifest.json").write_text(
        before.model_dump_json(indent=2), encoding="utf-8"
    )
    request = project_factory.make_voice_request(
        tmp_path, attempt_id="voice-manifest-210"
    )
    preview, authorization = project_factory.make_voice_preview_and_authorization(
        request
    )
    committer = ProductionStateCommitter(tmp_path)

    after = committer.begin_voice_generation(
        request,
        preview,
        authorization,
        dependency_transition_preparer_available=True,
    )

    assert after.schema_version == "2.10"
    assert after.attempts[-1].voice_phase == "request"
    assert after.attempts[-1].status is StateCommitStatus.RUNNING


def test_p4_fake_voice_captions_end_to_end_is_durable_offline_and_replay_safe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    StateCommitAttempt.model_rebuild()
    network_calls: list[object] = []
    secret_lookups: list[object] = []

    def reject_network(*args, **kwargs):
        network_calls.append((args, kwargs))
        raise AssertionError("P4 default acceptance must not use a socket")

    def reject_secret(*args, **kwargs):
        secret_lookups.append((args, kwargs))
        raise AssertionError("P4 default acceptance must not read environment secrets")

    environ_type = type(os.environ)
    original_environ_getitem = environ_type.__getitem__

    def guard_secret_environ(environ, key):
        if "ELEVENLABS" in str(key).upper() or "API_KEY" in str(key).upper():
            return reject_secret(key)
        return original_environ_getitem(environ, key)

    monkeypatch.setattr(socket, "create_connection", reject_network)
    monkeypatch.setattr(socket.socket, "connect", reject_network)
    monkeypatch.setattr(socket.socket, "connect_ex", reject_network)
    monkeypatch.setattr(os, "getenv", reject_secret)
    monkeypatch.setattr(environ_type, "__getitem__", guard_secret_environ)
    original_environ_get = environ_type.get

    def guard_secret_environ_get(environ, key, default=None):
        if "ELEVENLABS" in str(key).upper() or "API_KEY" in str(key).upper():
            return reject_secret(key)
        return original_environ_get(environ, key, default)

    monkeypatch.setattr(environ_type, "get", guard_secret_environ_get)

    project_factory.write_and_load_two_shot_project(tmp_path)
    toolchain = _toolchain()
    request = project_factory.make_voice_request(tmp_path, attempt_id="voice-e2e")
    preview, authorization = project_factory.make_voice_preview_and_authorization(
        request
    )
    provider = _FakeDialogueProvider(tmp_path, preview, authorization)
    committer = ProductionStateCommitter(
        tmp_path,
        voice_candidate_preparer=make_deterministic_voice_candidate_preparer(
            tmp_path, toolchain
        ),
    )

    voice_manifest = committer.generate_voice_asset(request, provider, authorization)
    assert provider.generate_calls == 1
    assert voice_manifest.attempts[-1].voice_phase == "activate"
    assert voice_manifest.attempts[-1].status is StateCommitStatus.SUCCEEDED
    imported_manifest = _import_local_mix_assets(tmp_path, toolchain)
    assert imported_manifest.active_project == voice_manifest.active_project

    loaded = load_production_project(tmp_path / "project.yaml")
    generated_audio = next(
        item for item in loaded.registry.assets if item.asset_id == "voice-voice-e2e"
    )
    generated_caption = next(
        item for item in loaded.registry.assets if item.asset_id == "caption-voice-e2e"
    )
    assert generated_audio.egress is not None
    assert generated_audio.cost_receipt_id is not None
    assert generated_caption.caption_metadata is not None
    track = json.loads(loaded.asset_paths[generated_caption.asset_id].read_bytes())
    style_hash = generated_caption.caption_metadata.style_content_hash
    assert style_hash is not None
    style = CaptionStyleReference(
        artifact_id=generated_caption.caption_metadata.style_reference_id,
        revision=1,
        content_hash=style_hash,
        path=Path(f"assets/styles/{style_hash}.json"),
    )
    spec = project_factory.make_composition_spec().model_copy(
        update={
            "schema_version": "2.1",
            "content_hash": ZERO_HASH,
            "audio_tracks": (
                AudioTrackSpec(
                    track_id="dialogue",
                    audio_kind=AudioKind.DIALOGUE,
                    asset_id=generated_audio.asset_id,
                    shot_id="shot-1",
                ),
                AudioTrackSpec(
                    track_id="ambience",
                    audio_kind=AudioKind.AMBIENCE,
                    asset_id="ambience-room",
                    start_sample=0,
                    fade_in_samples=480,
                ),
                AudioTrackSpec(
                    track_id="sfx",
                    audio_kind=AudioKind.SFX,
                    asset_id="sfx-hit",
                    shot_id="shot-2",
                ),
                AudioTrackSpec(
                    track_id="bgm",
                    audio_kind=AudioKind.BGM,
                    asset_id="bgm-theme",
                    start_sample=0,
                    gain_millidb=-6_000,
                    fade_in_samples=480,
                    fade_out_samples=480,
                    ducking={
                        "sidechain_track_ids": ("dialogue",),
                        "attenuation_millidb": -12_000,
                        "attack_samples": 240,
                        "release_samples": 480,
                    },
                ),
            ),
            "caption_tracks": (
                CaptionTrackBinding(
                    binding_id="dialogue-captions",
                    caption_asset_id=generated_caption.asset_id,
                    source_audio_track_id="dialogue",
                    shot_id="shot-1",
                    style_reference=style,
                ),
            ),
        }
    )
    timeline = resolve_composition(
        loaded, seal_artifact(spec), renderer_version="0.7.103"
    )
    assert timeline.schema_version == "2.1"
    assert (
        tuple(
            (
                span.track_id,
                span.audio_kind.value,
                span.asset_id,
                span.asset_sha256,
                span.start_sample,
                span.duration_samples,
                span.source_start_sample,
                span.source_duration_samples,
                span.gain_millidb,
                span.fade_in_samples,
                span.fade_out_samples,
                (
                    (
                        span.ducking.sidechain_track_ids,
                        span.ducking.attenuation_millidb,
                        span.ducking.attack_samples,
                        span.ducking.release_samples,
                    )
                    if span.ducking is not None
                    else None
                ),
            )
            for span in timeline.audio_spans
        )
        == EXPECTED_AUDIO_SPANS
    )
    assert timeline.total_samples == 192_000
    assert timeline.total_frames == 96
    assert (
        tuple(
            (
                cue.caption_asset_id,
                cue.caption_track_id,
                cue.segment_id,
                cue.start_sample,
                cue.end_sample,
                cue.start_frame,
                cue.end_frame_exclusive,
            )
            for cue in timeline.caption_cues
        )
        == EXPECTED_CAPTION_CUES
    )
    assert tuple(
        (segment["start_sample"], segment["end_sample"])
        for segment in track["segments"]
    ) == ((0, 88_608),)

    sources = {
        span.asset_id: loaded.asset_paths[span.asset_id]
        for span in timeline.visual_spans
    }
    sources.update(
        {
            span.asset_id: loaded.asset_paths[span.asset_id]
            for span in timeline.audio_spans
        }
    )
    sources.update(
        {
            cue.caption_asset_id: loaded.asset_paths[cue.caption_asset_id]
            for cue in timeline.caption_cues
        }
    )
    sources[style.artifact_id] = tmp_path / style.path
    selection = RendererSelectionReceipt(
        receipt_id="selection-p4-e2e",
        attempt_id="render-p4-e2e",
        requested_kind=RendererKind.HYPERFRAMES,
        selected_kinds=(RendererKind.HYPERFRAMES,),
        renderer_version="0.7.103",
        timeline_fingerprint=timeline.composition_fingerprint,
        current_project=loaded.manifest.active_project,
        current_registry=loaded.manifest.active_registry,
    )
    begin = BeginRenderAttemptRequest(
        loaded.manifest.manifest_revision,
        loaded.manifest.active_render_state,
        selection,
    )
    runner = _FakeHyperFramesRunner(toolchain.ffmpeg_path)
    browser = _executable(tmp_path / "tools/chrome")
    ip_path = _executable(tmp_path / "tools/ip")
    runner_factories = 0

    def runner_factory():
        nonlocal runner_factories
        runner_factories += 1
        return runner

    rendered = _render_with_hyperframes(
        committer=committer,
        begin_request=begin,
        timeline=timeline,
        asset_sources=sources,
        allowed_asset_root=tmp_path,
        runner_factory=runner_factory,
        browser_path=browser,
        ip_path=ip_path,
        expected_version="0.7.103",
        probe=lambda fd: probe_clip_fd_with_executable(fd, toolchain.ffprobe_path),
        decoded_frames=decoded_frame_sha256_fd,
        decoded_audio=lambda fd, rate, channels: (
            decoded_audio_sha256_fd_with_executable(
                fd, rate, channels, toolchain.ffmpeg_path
            )
        ),
    )
    assert rendered.active_render_state is not None
    assert runner_factories == 1
    assert [item.command for item in runner.calls] == [
        "version",
        "doctor",
        "lint",
        "check",
        "render",
    ]
    assert runner.caption_frame_windows == ((0, 45),)
    assert runner.mixed_pcm_sha256 == MIXED_PCM_SHA256

    reopened = load_production_project(tmp_path / "project.yaml")
    assert reopened.render_state is not None
    assert (
        reopened.render_state.timeline_fingerprint == timeline.composition_fingerprint
    )
    source_receipt = RendererSourceReceipt.model_validate_json(
        (tmp_path / reopened.render_state.source_receipt.path).read_bytes()
    )
    render_receipt = RenderReceipt.model_validate_json(
        (tmp_path / reopened.render_state.render_receipt.path).read_bytes()
    )
    assert len(source_receipt.audio_bindings) == 1
    assert source_receipt.audio_bindings[0].resolved_track_ids == tuple(
        span.track_id for span in timeline.audio_spans
    )
    durable_timeline = ResolvedTimeline.model_validate_json(
        (tmp_path / reopened.render_state.timeline.path).read_bytes()
    )
    assert tuple(
        (item.start_sample, item.end_sample) for item in durable_timeline.caption_cues
    ) == tuple((item.start_sample, item.end_sample) for item in timeline.caption_cues)
    assert source_receipt.caption_bindings[0].resolved_cue_ids == tuple(
        cue.segment_id for cue in timeline.caption_cues
    )
    assert render_receipt.measured.audio is not None
    assert (
        render_receipt.measured.width,
        render_receipt.measured.height,
        render_receipt.measured.fps_num,
        render_receipt.measured.fps_den,
        render_receipt.measured.duration_frames,
        render_receipt.measured.codec_name,
    ) == (1280, 720, 24, 1, 96, "h264")
    assert (
        render_receipt.measured.audio.stream_count,
        render_receipt.measured.audio.codec_name,
        render_receipt.measured.audio.sample_rate_hz,
        render_receipt.measured.audio.channels,
        render_receipt.measured.audio.channel_layout.value,
        render_receipt.measured.audio.decoded_samples,
        render_receipt.measured.audio.encoder_priming_samples,
        render_receipt.measured.audio.encoder_padding_samples,
    ) == (1, "aac", 48_000, 2, "stereo", 192_512, 1_024, 512)
    assert render_receipt.decoded_audio_fingerprint == OUTPUT_DECODED_PCM_SHA256
    assert render_receipt.decoded_frame_fingerprint == OUTPUT_DECODED_FRAMES_SHA256
    output_path = tmp_path / reopened.render_state.output.path
    with output_path.open("rb") as output:
        caption_present = _sample_rgb_frame(
            output.fileno(), 44, ffmpeg_path=toolchain.ffmpeg_path
        )
        caption_absent = _sample_rgb_frame(
            output.fileno(), 45, ffmpeg_path=toolchain.ffmpeg_path
        )
    assert caption_present[1] > 200 and caption_present[2] > 200
    assert max(caption_absent) < 20
    corrupt = tmp_path / "corrupt-render.mp4"
    corrupt.write_bytes(b"not-an-mp4")
    with corrupt.open("rb") as invalid:
        with pytest.raises(AiVideoError) as corrupt_error:
            probe_clip_fd_with_executable(invalid.fileno(), toolchain.ffprobe_path)
    assert corrupt_error.value.code is ErrorCode.RENDER_FAILED
    assert selection.selected_kinds == (RendererKind.HYPERFRAMES,)
    assert list(tmp_path.rglob("manifest.json")) == [tmp_path / "state/manifest.json"]

    calls_before_replay = (provider.generate_calls, len(runner.calls), runner_factories)
    with pytest.raises(AiVideoError) as replay_error:
        committer.generate_voice_asset(request, provider, authorization)
    assert replay_error.value.code is ErrorCode.PRODUCTION_STATE_INVALID
    replayed = _render_with_hyperframes(
        committer=committer,
        begin_request=begin,
        timeline=timeline,
        asset_sources=sources,
        allowed_asset_root=tmp_path,
        runner_factory=runner_factory,
        browser_path=browser,
        ip_path=ip_path,
        expected_version="0.7.103",
        probe=lambda fd: probe_clip_fd_with_executable(fd, toolchain.ffprobe_path),
        decoded_frames=decoded_frame_sha256_fd,
        decoded_audio=lambda fd, rate, channels: (
            decoded_audio_sha256_fd_with_executable(
                fd, rate, channels, toolchain.ffmpeg_path
            )
        ),
    )
    assert replayed == rendered
    assert (
        provider.generate_calls,
        len(runner.calls),
        runner_factories,
    ) == calls_before_replay
    assert network_calls == []
    assert secret_lookups == []


def test_p4_timeout_after_submit_intent_recovers_without_resubmit(
    tmp_path: Path,
) -> None:
    project_factory.write_production_project(tmp_path)
    before = _manifest(tmp_path)
    request = project_factory.make_voice_request(
        tmp_path, attempt_id="voice-timeout-e2e"
    )
    preview, authorization = project_factory.make_voice_preview_and_authorization(
        request
    )

    class _TimeoutProvider:
        calls = 0

        def preview(self, candidate):
            assert candidate == request
            return preview

        def generate(self, candidate, candidate_authorization, permit):
            assert permit._consume_voice_submit_permit(
                **_permit_binding(candidate, candidate_authorization)
            )
            self.calls += 1
            raise TimeoutError("fixture submit timeout")

    provider = _TimeoutProvider()
    writer = ProductionStateCommitter(tmp_path)
    with pytest.raises(TimeoutError, match="fixture submit timeout"):
        writer.generate_voice_asset(request, provider, authorization)

    unknown = _manifest(tmp_path)
    attempt = unknown.attempts[-1]
    assert provider.calls == 1
    assert attempt.status is StateCommitStatus.OUTCOME_UNKNOWN
    assert attempt.voice_phase == "provider_call"
    assert unknown.active_project == before.active_project
    assert unknown.active_registry == before.active_registry
    assert unknown.active_render_state == before.active_render_state
    paths = writer.voice_attempt_paths(request.attempt_id)
    assert paths.request_path.is_file()
    assert paths.preview_path.is_file()
    assert paths.authorization_path.is_file()
    assert paths.submit_intent_path.is_file()

    report = recover_production_state(tmp_path)
    recovered = _manifest(tmp_path)
    assert report.manifest_revision_after == recovered.manifest_revision
    assert provider.calls == 1
    assert recovered.attempts[-1].status is StateCommitStatus.OUTCOME_UNKNOWN
    assert recovered.active_project == before.active_project
    assert recovered.active_registry == before.active_registry
    assert recovered.active_render_state == before.active_render_state
    assert paths.submit_intent_path.read_bytes()
