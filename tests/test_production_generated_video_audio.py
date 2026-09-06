from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import time
import wave
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.audio import AudioProbeToolchain
from ai_video.production.generated_video_audio import (
    GeneratedVideoAudioRequest,
    _extract_wav,
    _probe_wav,
)
from ai_video.production._generated_video_audio_contracts import (
    GeneratedVideoAudioReceipt,
    canonical_generated_video_audio_receipt_path,
    generated_video_audio_derivation_identity,
)
from ai_video.production._state_commit_common import (
    _candidate_artifacts_evidence_hash,
    _canonical_json_bytes,
)
from ai_video.production._state_commit_contracts import PreparedArtifact
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import (
    AssetRegistrySnapshot,
    AudioKind,
    AssetSourceKind,
    RegistrySnapshotPointer,
    ToolIdentity,
    canonical_registry_snapshot_path,
)
from ai_video.production.project import load_production_project
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import ProductionStateCommitter
from ai_video.production.video_generation import VideoGenerationService
from tests import production_project_factory as project_factory


def _wav_bytes() -> bytes:
    output = BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(24_000)
        writer.writeframes(b"\x00\x00" * 24)
    return output.getvalue()


class _AudioToolRunner:
    def __init__(self) -> None:
        self.extract_calls = 0
        self.wav = _wav_bytes()

    def __call__(self, argv, **kwargs):
        if "-show_streams" in argv:
            return subprocess.CompletedProcess(
                argv,
                0,
                stdout=json.dumps(
                    {
                        "streams": [
                            {
                                "codec_type": "audio",
                                "codec_name": "pcm_s16le",
                                "sample_rate": "24000",
                                "channels": 1,
                            }
                        ],
                        "format": {"format_name": "wav"},
                    }
                ),
                stderr="",
            )
        if "ebur128=peak=true" in argv:
            return subprocess.CompletedProcess(
                argv, 0, stdout="", stderr="I: -20.0 LUFS\nPeak: -1.0 dBFS\n"
            )
        if "-f" in argv and "s16le" in argv:
            return subprocess.CompletedProcess(argv, 0, stdout=b"\x00\x00" * 24, stderr=b"")
        self.extract_calls += 1
        output_fd = int(argv[-1].rsplit("/", 1)[-1])
        os.lseek(output_fd, 0, os.SEEK_SET)
        os.write(output_fd, self.wav)
        return subprocess.CompletedProcess(argv, 0, stdout=None, stderr=b"")


class _SlowAudioToolRunner(_AudioToolRunner):
    def __call__(self, argv, **kwargs):
        if "-show_streams" not in argv and "ebur128=peak=true" not in argv and "s16le" not in argv:
            time.sleep(0.1)
        return super().__call__(argv, **kwargs)


def _toolchain(tmp_path: Path) -> AudioProbeToolchain:
    ffmpeg = tmp_path / "ffmpeg"
    ffprobe = tmp_path / "ffprobe"
    ffmpeg.write_text("#!/bin/sh\n", encoding="utf-8")
    ffprobe.write_text("#!/bin/sh\n", encoding="utf-8")
    ffmpeg.chmod(0o700)
    ffprobe.chmod(0o700)
    return AudioProbeToolchain(
        ffmpeg_path=ffmpeg.resolve(),
        ffprobe_path=ffprobe.resolve(),
        ffmpeg=ToolIdentity(name="ffmpeg", version="fixture-1"),
        ffprobe=ToolIdentity(name="ffprobe", version="fixture-1"),
    )


def _write_audio_target(root: Path) -> None:
    project_factory.write_production_project(root)
    ProductionStateCommitter(root).commit(
        project_factory.make_audio_import_upgrade_request(root)
    )


def _settled_source(root: Path) -> str:
    from tests.test_production_generated_video_e2e import ATTEMPT_ID, _reach_fetch

    _inputs, provider, _resolved, committer = _reach_fetch(root, settle=True)
    VideoGenerationService(committer=committer, provider=provider).fetch_once(
        attempt_id=ATTEMPT_ID
    )
    return ATTEMPT_ID


def _request(source_root: Path, source_attempt_id: str) -> GeneratedVideoAudioRequest:
    return GeneratedVideoAudioRequest(
        attempt_id="native-audio-import-1",
        asset_id="native-dialogue-1",
        source_project_root=source_root.resolve(),
        source_attempt_id=source_attempt_id,
        audio_kind=AudioKind.DIALOGUE,
        speaker_id="speaker-lin-yan",
        voice_id=f"native-video-{source_attempt_id}",
        language="zh-CN",
        script_hash="a" * 64,
        usage_license="provider-generated-video-audio",
    )


def test_registers_exact_settled_video_audio_as_generated_and_replays_without_extract(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    project_factory.write_production_project(source_root)
    _write_audio_target(target_root)
    source_attempt_id = _settled_source(source_root)
    runner = _AudioToolRunner()
    request = _request(source_root, source_attempt_id)
    committer = ProductionStateCommitter(target_root)

    committed = committer.register_generated_video_audio(
        request, toolchain=_toolchain(tmp_path), runner=runner
    )
    record = next(
        item
        for item in load_production_project(target_root / "project.yaml").registry.assets
        if item.asset_id == request.asset_id
    )
    assert record.source_kind is AssetSourceKind.GENERATED
    assert record.audio_metadata is not None
    assert record.audio_metadata.source.kind is AssetSourceKind.GENERATED
    assert record.audio_metadata.voice_id == request.voice_id
    assert committed.attempts[-1].operation == "audio_import"

    extracted = runner.extract_calls
    assert committer.register_generated_video_audio(
        request, toolchain=_toolchain(tmp_path), runner=runner
    ) == committed
    assert runner.extract_calls == extracted


def test_replay_rejects_current_speech_metadata_drift_without_extract(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    project_factory.write_production_project(source_root)
    _write_audio_target(target_root)
    request = _request(source_root, _settled_source(source_root))
    runner = _AudioToolRunner()
    committer = ProductionStateCommitter(target_root)
    committer.register_generated_video_audio(request, toolchain=_toolchain(tmp_path), runner=runner)

    with pytest.raises(AiVideoError, match="replay identity changed"):
        committer.register_generated_video_audio(
            request.model_copy(update={"language": "en-US"}),
            toolchain=_toolchain(tmp_path),
            runner=runner,
        )
    assert runner.extract_calls == 1


def test_same_target_effect_lock_prevents_duplicate_extract(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    project_factory.write_production_project(source_root)
    _write_audio_target(target_root)
    request = _request(source_root, _settled_source(source_root))
    runner = _SlowAudioToolRunner()

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(
                ProductionStateCommitter(target_root).register_generated_video_audio,
                request,
                toolchain=_toolchain(tmp_path),
                runner=runner,
            )
            for _ in range(2)
        ]
        for future in futures:
            future.result()
    assert runner.extract_calls == 1


def test_same_attempt_different_asset_waits_then_rejects_before_duplicate_extract(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    project_factory.write_production_project(source_root)
    _write_audio_target(target_root)
    request = _request(source_root, _settled_source(source_root))
    runner = _SlowAudioToolRunner()

    with ThreadPoolExecutor(max_workers=2) as executor:
        primary = executor.submit(
            ProductionStateCommitter(target_root).register_generated_video_audio,
            request,
            toolchain=_toolchain(tmp_path),
            runner=runner,
        )
        conflicting = executor.submit(
            ProductionStateCommitter(target_root).register_generated_video_audio,
            request.model_copy(update={"asset_id": "native-dialogue-other"}),
            toolchain=_toolchain(tmp_path),
            runner=runner,
        )
        outcomes = []
        for future in (primary, conflicting):
            try:
                outcomes.append(future.result())
            except AiVideoError as exc:
                outcomes.append(exc)
    assert sum(not isinstance(item, AiVideoError) for item in outcomes) == 1
    assert sum(isinstance(item, AiVideoError) for item in outcomes) == 1
    assert runner.extract_calls == 1


def test_rejects_unsettled_source_before_ffmpeg(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    project_factory.write_production_project(source_root)
    _write_audio_target(target_root)
    from tests.test_production_generated_video_e2e import ATTEMPT_ID, _reach_fetch

    _reach_fetch(source_root, settle=False)
    runner = _AudioToolRunner()

    with pytest.raises(AiVideoError, match="settled"):
        ProductionStateCommitter(target_root).register_generated_video_audio(
            _request(source_root, ATTEMPT_ID), toolchain=_toolchain(tmp_path), runner=runner
        )
    assert runner.extract_calls == 0


def test_rejects_changed_fetched_bytes_before_ffmpeg(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    project_factory.write_production_project(source_root)
    _write_audio_target(target_root)
    source_attempt_id = _settled_source(source_root)
    manifest = load_production_project(source_root / "project.yaml").manifest
    state = manifest.attempts[-1].video_generation_state
    assert state is not None and state.fetch_receipt is not None
    fetched = source_root / state.fetch_receipt.artifact_path
    fetched.write_bytes(b"mutated")
    runner = _AudioToolRunner()

    with pytest.raises(AiVideoError):
        ProductionStateCommitter(target_root).register_generated_video_audio(
            _request(source_root, source_attempt_id), toolchain=_toolchain(tmp_path), runner=runner
        )
    assert runner.extract_calls == 0


def test_rejects_missing_audio_without_registering(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    project_factory.write_production_project(source_root)
    _write_audio_target(target_root)
    source_attempt_id = _settled_source(source_root)
    runner = _AudioToolRunner()
    runner.wav = b""

    with pytest.raises(AiVideoError):
        ProductionStateCommitter(target_root).register_generated_video_audio(
            _request(source_root, source_attempt_id), toolchain=_toolchain(tmp_path), runner=runner
        )
    assert all(
        item.asset_id != "native-dialogue-1"
        for item in load_production_project(target_root / "project.yaml").registry.assets
    )


def test_strict_reload_rejects_semantic_tamper_after_resealing_receipt_closure(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    project_factory.write_production_project(source_root)
    _write_audio_target(target_root)
    request = _request(source_root, _settled_source(source_root))
    ProductionStateCommitter(target_root).register_generated_video_audio(
        request, toolchain=_toolchain(tmp_path), runner=_AudioToolRunner()
    )
    loaded = load_production_project(target_root / "project.yaml")
    asset = next(item for item in loaded.registry.assets if item.asset_id == request.asset_id)
    assert asset.audio_metadata is not None
    old_receipt = GeneratedVideoAudioReceipt.model_validate_json(
        (
            target_root
            / canonical_generated_video_audio_receipt_path(
                asset.audio_metadata.provenance_receipt_id
            )
        ).read_bytes()
    )
    forged_identity = generated_video_audio_derivation_identity(
        target_project_id=old_receipt.target_project_id,
        target_attempt_id=old_receipt.target_attempt_id,
        target_asset_id="other-asset",
        target_base_project=old_receipt.target_base_project,
        target_base_registry=old_receipt.target_base_registry,
        target_audio_metadata=old_receipt.target_audio_metadata,
        target_usage_license=old_receipt.target_usage_license,
        source_project_id=old_receipt.source_project_id,
        source_attempt_id=old_receipt.source_attempt_id,
        source_request=old_receipt.source_request,
        source_observation=old_receipt.source_observation,
        source_fetch=old_receipt.source_fetch,
        source_gate=old_receipt.source_gate,
        source_submit=old_receipt.source_submit,
        source_budget_pointer=old_receipt.source_budget_pointer,
        source_budget=old_receipt.source_budget,
        source_reservation=old_receipt.source_reservation,
        extraction_ffmpeg=old_receipt.extraction_ffmpeg,
        probe_ffprobe=old_receipt.probe_ffprobe,
    )
    forged_receipt = GeneratedVideoAudioReceipt.create(
        derivation_identity=forged_identity,
        target_project_id=old_receipt.target_project_id,
        target_attempt_id=old_receipt.target_attempt_id,
        target_asset_id="other-asset",
        target_base_project=old_receipt.target_base_project,
        target_base_registry=old_receipt.target_base_registry,
        target_audio_metadata=old_receipt.target_audio_metadata,
        target_usage_license=old_receipt.target_usage_license,
        source_project_id=old_receipt.source_project_id,
        source_attempt_id=old_receipt.source_attempt_id,
        source_request=old_receipt.source_request,
        source_observation=old_receipt.source_observation,
        source_fetch=old_receipt.source_fetch,
        source_gate=old_receipt.source_gate,
        source_submit=old_receipt.source_submit,
        source_budget_pointer=old_receipt.source_budget_pointer,
        source_budget=old_receipt.source_budget,
        source_reservation=old_receipt.source_reservation,
        extraction_ffmpeg=old_receipt.extraction_ffmpeg,
        probe_ffprobe=old_receipt.probe_ffprobe,
        probe=old_receipt.probe,
    )
    receipt_payload = _canonical_json_bytes(forged_receipt)
    receipt_sha256 = hashlib.sha256(receipt_payload).hexdigest()
    forged_asset = asset.model_copy(
        update={
            "creation_receipt_id": f"generated-video-audio-{receipt_sha256}",
            "audio_metadata": asset.audio_metadata.model_copy(
                update={"provenance_receipt_id": receipt_sha256}
            ),
        }
    )
    forged_registry = AssetRegistrySnapshot(
        schema_version=loaded.registry.schema_version,
        revision_id="0" * 64,
        content_hash="0" * 64,
        assets=tuple(
            forged_asset if item.asset_id == forged_asset.asset_id else item
            for item in loaded.registry.assets
        ),
    )
    registry_hash = registry_semantic_sha256(forged_registry)
    forged_registry = forged_registry.model_copy(
        update={"revision_id": registry_hash, "content_hash": registry_hash}
    )
    registry_payload = _canonical_json_bytes(forged_registry)
    registry_pointer = RegistrySnapshotPointer(
        path=canonical_registry_snapshot_path(registry_hash),
        revision_id=registry_hash,
        content_hash=registry_hash,
        file_sha256=hashlib.sha256(registry_payload).hexdigest(),
    )
    attempt = next(item for item in loaded.manifest.attempts if item.attempt_id == request.attempt_id)
    artifacts = (
        PreparedArtifact(attempt.base_project.path, b"", attempt.base_project.file_sha256),
        PreparedArtifact(registry_pointer.path, b"", registry_pointer.file_sha256),
        PreparedArtifact(forged_asset.artifact_path, b"", forged_asset.sha256),
        PreparedArtifact(
            canonical_generated_video_audio_receipt_path(receipt_sha256), b"", receipt_sha256
        ),
    )
    forged_attempt = attempt.model_copy(
        update={
            "candidate_registry": registry_pointer,
            "candidate_artifacts_hash": _candidate_artifacts_evidence_hash(artifacts),
        }
    )
    forged_manifest = loaded.manifest.model_copy(
        update={
            "active_registry": registry_pointer,
            "attempts": tuple(
                forged_attempt if item.attempt_id == request.attempt_id else item
                for item in loaded.manifest.attempts
            ),
        }
    )
    (target_root / canonical_generated_video_audio_receipt_path(receipt_sha256)).parent.mkdir(
        parents=True, exist_ok=True
    )
    (target_root / canonical_generated_video_audio_receipt_path(receipt_sha256)).write_bytes(
        receipt_payload
    )
    (target_root / registry_pointer.path).write_bytes(registry_payload)
    (target_root / "state/manifest.json").write_bytes(_canonical_json_bytes(forged_manifest))

    with pytest.raises(AiVideoError, match="Active generated voice assets"):
        load_production_project(target_root / "project.yaml")


@pytest.mark.parametrize("mutation", ("wrong_target", "missing_submit"))
def test_strict_reload_rejects_forged_or_incomplete_derived_receipt(
    tmp_path: Path, mutation: str
) -> None:
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    project_factory.write_production_project(source_root)
    _write_audio_target(target_root)
    source_attempt_id = _settled_source(source_root)
    request = _request(source_root, source_attempt_id)
    committer = ProductionStateCommitter(target_root)
    committer.register_generated_video_audio(
        request, toolchain=_toolchain(tmp_path), runner=_AudioToolRunner()
    )
    record = next(
        item
        for item in load_production_project(target_root / "project.yaml").registry.assets
        if item.asset_id == request.asset_id
    )
    receipt_path = target_root / canonical_generated_video_audio_receipt_path(
        record.audio_metadata.provenance_receipt_id  # type: ignore[union-attr]
    )
    data = json.loads(receipt_path.read_text(encoding="utf-8"))
    if mutation == "wrong_target":
        data["target_asset_id"] = "other-asset"
        data["content_hash"] = canonical_sha256(
            {key: value for key, value in data.items() if key != "content_hash"}
        )
    else:
        del data["source_submit"]
    receipt_path.write_text(
        json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(AiVideoError):
        load_production_project(target_root / "project.yaml")


def test_extracts_pcm_wav_with_real_ffmpeg_temp_fixture(tmp_path: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if ffmpeg is None or ffprobe is None:
        pytest.skip("ffmpeg and ffprobe are required for this local fixture test")
    video_path = tmp_path / "fixture.mp4"
    subprocess.run(
        [
            ffmpeg,
            "-nostdin",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=size=16x16:rate=24:color=black",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=24000",
            "-t",
            "0.04",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            str(video_path),
        ],
        check=True,
    )
    toolchain = AudioProbeToolchain(
        ffmpeg_path=Path(ffmpeg).resolve(),
        ffprobe_path=Path(ffprobe).resolve(),
        ffmpeg=ToolIdentity(name="ffmpeg", version="local-fixture"),
        ffprobe=ToolIdentity(name="ffprobe", version="local-fixture"),
    )
    wav = _extract_wav(video_path.read_bytes(), toolchain, subprocess.run)
    probe = _probe_wav(wav, toolchain, subprocess.run)
    assert probe.codec_name == "pcm_s16le"
    assert probe.sample_rate_hz == 24_000


def test_registers_and_strictly_reopens_real_ffmpeg_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if ffmpeg is None or ffprobe is None:
        pytest.skip("ffmpeg and ffprobe are required for this local fixture test")
    fixture = tmp_path / "source-with-audio.mp4"
    subprocess.run(
        [
            ffmpeg,
            "-nostdin",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=size=16x16:rate=24:color=black",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=24000",
            "-t",
            "0.04",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            str(fixture),
        ],
        check=True,
    )
    from tests import test_production_generated_video_e2e as generated_video_e2e

    monkeypatch.setattr(generated_video_e2e, "FIXTURE", fixture)
    source_root = tmp_path / "source"
    target_root = tmp_path / "target"
    source_root.mkdir()
    target_root.mkdir()
    project_factory.write_production_project(source_root)
    _write_audio_target(target_root)
    source_attempt_id = _settled_source(source_root)
    toolchain = AudioProbeToolchain(
        ffmpeg_path=Path(ffmpeg).resolve(),
        ffprobe_path=Path(ffprobe).resolve(),
        ffmpeg=ToolIdentity(name="ffmpeg", version="local-fixture"),
        ffprobe=ToolIdentity(name="ffprobe", version="local-fixture"),
    )
    ProductionStateCommitter(target_root).register_generated_video_audio(
        _request(source_root, source_attempt_id),
        toolchain=toolchain,
        runner=subprocess.run,
    )
    reopened = load_production_project(target_root / "project.yaml")
    assert any(item.asset_id == "native-dialogue-1" for item in reopened.registry.assets)
