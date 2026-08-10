from __future__ import annotations

import hashlib
import fcntl
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest
from pydantic import ValidationError

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.audio import (
    AudioImportRequest,
    AudioProbeToolchain,
    ClaimedAudioMetadata,
    VoiceGenerationRequest,
    VoiceProviderParameters,
    audio_content_fingerprint,
    materialize_audio_candidate,
    probe_audio_candidate,
)
from ai_video.production.models import (
    AssetSourceKind,
    AssetType,
    AudioKind,
    AudioSource,
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    ToolIdentity,
)
from ai_video.production.paths import canonical_voice_audio_candidate_path


FIXTURE_ROOT = Path(__file__).parent / "fixtures/voice_captions"
DIALOGUE = FIXTURE_ROOT / "dialogue-mono-48000.wav"
AMBIENCE = FIXTURE_ROOT / "ambience-stereo-48000.wav"
ZERO_HASH = "0" * 64
ONE_HASH = "1" * 64


def _toolchain() -> AudioProbeToolchain:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if ffmpeg is None or ffprobe is None:
        pytest.skip("ffmpeg and ffprobe are required for deterministic audio probes")
    return AudioProbeToolchain(
        ffmpeg_path=Path(ffmpeg).resolve(strict=True),
        ffprobe_path=Path(ffprobe).resolve(strict=True),
        ffmpeg=ToolIdentity(name="ffmpeg", version="test-pinned"),
        ffprobe=ToolIdentity(name="ffprobe", version="test-pinned"),
    )


def _source(kind: AssetSourceKind = AssetSourceKind.IMPORTED) -> AudioSource:
    return AudioSource(
        kind=kind,
        provider_or_tool=ToolIdentity(name="fixture-import", version="1"),
        input_artifact_ids=("source-1",),
        input_fingerprint=ONE_HASH,
        original_reference="fixture://audio",
    )


def _import_request(kind: AudioKind) -> AudioImportRequest:
    speech = kind in {AudioKind.DIALOGUE, AudioKind.NARRATION}
    return AudioImportRequest(
        asset_id=f"audio-{kind.value}-1",
        audio_kind=kind,
        mime_type="audio/wav",
        source=_source(),
        speaker_id="speaker-1" if speech else None,
        language="en" if speech else None,
        script_hash=hashlib.sha256(b"fixture script").hexdigest() if speech else None,
        provenance_receipt_id="receipt-audio-provenance-1",
        creation_receipt_id="receipt-audio-create-1",
        usage_license="fixture-generated",
    )


def test_fixture_identities_are_frozen():
    assert hashlib.sha256(DIALOGUE.read_bytes()).hexdigest() == (
        "f72a3208e25253873858b9f9161e0851e336eb5e97d717a01679df729c428a63"
    )
    assert hashlib.sha256(AMBIENCE.read_bytes()).hexdigest() == (
        "e58b991cd53fb90d79f3482957a51a56bf56d8cfb6cbdf40152bd39ac9102dca"
    )


def test_voice_generation_request_is_immutable_and_self_sealing():
    request = VoiceGenerationRequest.create(
        request_id="request-1",
        attempt_id="attempt-1",
        provider_kind="fake",
        model_id="model-1",
        audio_kind=AudioKind.DIALOGUE,
        script_text="Exact script",
        speaker_id="speaker-1",
        voice_id="voice-1",
        language="en",
        output_container="wav",
        output_codec="pcm_s16le",
        output_sample_rate_hz=48_000,
        output_channels=1,
        provider_parameters=VoiceProviderParameters(stability_milli=500),
        base_project=ProjectSnapshotPointer(
            path=Path(f"state/projects/project.1.{ZERO_HASH}.yaml"),
            revision=1,
            content_hash=ZERO_HASH,
            file_sha256=ONE_HASH,
        ),
        base_registry=RegistrySnapshotPointer(
            path=Path(f"assets/registry.{ONE_HASH}.json"),
            revision_id=ONE_HASH,
            content_hash=ONE_HASH,
            file_sha256=ZERO_HASH,
        ),
        input_artifact_ids=("shot-1",),
        input_fingerprint=ONE_HASH,
        pricing_snapshot_id="pricing-1",
        budget_reservation_receipt_id="budget-1",
        egress_authorization_receipt_id="egress-1",
    )
    assert request.script_hash == hashlib.sha256(b"Exact script").hexdigest()
    assert len(request.provider_parameters_hash) == 64
    assert len(request.voice_request_fingerprint) == 64
    with pytest.raises(ValidationError):
        request.model_copy(update={"audio_kind": AudioKind.BGM}, deep=True).model_validate(
            {**request.model_dump(), "audio_kind": "bgm"}
        )
    with pytest.raises(ValidationError, match="script_hash"):
        VoiceGenerationRequest.model_validate(
            {**request.model_dump(mode="python"), "script_hash": ZERO_HASH}
        )


def test_candidate_path_is_exact_contained_and_rejects_symlink(tmp_path):
    attempt_root = tmp_path / "state/voice/attempts/attempt-1"
    attempt_root.mkdir(parents=True)
    candidate = canonical_voice_audio_candidate_path(tmp_path, "attempt-1")
    assert candidate == attempt_root / "candidate.wav"
    materialize_audio_candidate(
        DIALOGUE.read_bytes(),
        candidate_path=candidate,
        project_root=tmp_path,
        attempt_id="attempt-1",
    )
    assert candidate.read_bytes() == DIALOGUE.read_bytes()

    with pytest.raises(AiVideoError, match="exact attempt-owned"):
        materialize_audio_candidate(
            b"bad",
            candidate_path=attempt_root / "other.wav",
            project_root=tmp_path,
            attempt_id="attempt-1",
        )

    escaped = tmp_path / "escaped"
    escaped.mkdir()
    symlink_root = tmp_path / "state/voice/attempts/attempt-2"
    symlink_root.symlink_to(escaped, target_is_directory=True)
    with pytest.raises(AiVideoError):
        materialize_audio_candidate(
            b"bad",
            candidate_path=symlink_root / "candidate.wav",
            project_root=tmp_path,
            attempt_id="attempt-2",
        )
    assert not (escaped / "candidate.wav").exists()

    attempt_three = tmp_path / "state/voice/attempts/attempt-3"
    attempt_three.mkdir(parents=True)
    protected = escaped / "protected.wav"
    protected.write_bytes(b"protected")
    (attempt_three / "candidate.wav").symlink_to(protected)
    with pytest.raises(AiVideoError):
        materialize_audio_candidate(
            DIALOGUE.read_bytes(),
            candidate_path=attempt_three / "candidate.wav",
            project_root=tmp_path,
            attempt_id="attempt-3",
        )
    assert protected.read_bytes() == b"protected"


@pytest.mark.parametrize("symlink_component", ["state", "voice", "attempts"])
def test_candidate_rejects_symlink_in_parent_chain(tmp_path, symlink_component):
    project_root = tmp_path / "project"
    project_root.mkdir()
    components = ("state", "voice", "attempts")
    link_index = components.index(symlink_component)
    link_parent = project_root.joinpath(*components[:link_index])
    link_parent.mkdir(parents=True, exist_ok=True)
    outside_root = tmp_path / f"outside-{symlink_component}"
    outside_attempt = outside_root.joinpath(
        *components[link_index + 1 :], "attempt-parent-link"
    )
    outside_attempt.mkdir(parents=True)
    (link_parent / symlink_component).symlink_to(
        outside_root, target_is_directory=True
    )
    candidate = canonical_voice_audio_candidate_path(
        project_root, "attempt-parent-link"
    )

    with pytest.raises(AiVideoError) as caught:
        materialize_audio_candidate(
            DIALOGUE.read_bytes(),
            candidate_path=candidate,
            project_root=project_root,
            attempt_id="attempt-parent-link",
        )

    assert caught.value.code is ErrorCode.AUDIO_ASSET_INVALID
    assert not (outside_attempt / "candidate.wav").exists()


def test_materialization_is_idempotent_for_same_bytes_and_conflicts_otherwise(tmp_path):
    attempt_root = tmp_path / "state/voice/attempts/attempt-replay"
    attempt_root.mkdir(parents=True)
    candidate = canonical_voice_audio_candidate_path(tmp_path, "attempt-replay")
    first = materialize_audio_candidate(
        AMBIENCE.read_bytes(),
        candidate_path=candidate,
        project_root=tmp_path,
        attempt_id="attempt-replay",
    )
    second = materialize_audio_candidate(
        AMBIENCE.read_bytes(),
        candidate_path=candidate,
        project_root=tmp_path,
        attempt_id="attempt-replay",
    )
    assert first == second
    assert not list(attempt_root.glob("*.tmp-*"))
    with pytest.raises(AiVideoError) as caught:
        materialize_audio_candidate(
            DIALOGUE.read_bytes(),
            candidate_path=candidate,
            project_root=tmp_path,
            attempt_id="attempt-replay",
        )
    assert caught.value.code is ErrorCode.AUDIO_ASSET_INVALID
    assert candidate.read_bytes() == AMBIENCE.read_bytes()


def test_same_byte_target_hardlink_is_rejected_before_replay(tmp_path):
    project_root = tmp_path / "project"
    attempt_root = project_root / "state/voice/attempts/attempt-hardlink-target"
    attempt_root.mkdir(parents=True)
    candidate = canonical_voice_audio_candidate_path(
        project_root, "attempt-hardlink-target"
    )
    candidate.write_bytes(AMBIENCE.read_bytes())
    external_alias = tmp_path / "external-target-alias.wav"
    os.link(candidate, external_alias)
    assert candidate.stat().st_nlink == 2

    with pytest.raises(AiVideoError) as caught:
        materialize_audio_candidate(
            AMBIENCE.read_bytes(),
            candidate_path=candidate,
            project_root=project_root,
            attempt_id="attempt-hardlink-target",
        )

    assert caught.value.code is ErrorCode.AUDIO_ASSET_INVALID
    assert candidate.stat().st_nlink == 2
    candidate.unlink()
    accepted = materialize_audio_candidate(
        AMBIENCE.read_bytes(),
        candidate_path=candidate,
        project_root=project_root,
        attempt_id="attempt-hardlink-target",
    )
    external_alias.write_bytes(DIALOGUE.read_bytes())
    assert accepted.link_count == 1
    assert candidate.read_bytes() == AMBIENCE.read_bytes()


def test_preexisting_candidate_temp_hardlink_is_rejected(tmp_path):
    project_root = tmp_path / "project"
    attempt_root = project_root / "state/voice/attempts/attempt-hardlink-temp"
    attempt_root.mkdir(parents=True)
    payload = AMBIENCE.read_bytes()
    candidate = canonical_voice_audio_candidate_path(
        project_root, "attempt-hardlink-temp"
    )
    digest = hashlib.sha256(payload).hexdigest()
    temporary = attempt_root / f".candidate.wav.tmp-{digest}"
    temporary.write_bytes(payload)
    external_alias = tmp_path / "external-temp-alias.wav"
    os.link(temporary, external_alias)

    with pytest.raises(AiVideoError) as caught:
        materialize_audio_candidate(
            payload,
            candidate_path=candidate,
            project_root=project_root,
            attempt_id="attempt-hardlink-temp",
        )

    assert caught.value.code is ErrorCode.AUDIO_ASSET_INVALID
    assert not candidate.exists()
    assert temporary.stat().st_nlink == 2
    assert external_alias.read_bytes() == payload


def test_probe_freezes_samples_channels_pcm_hash_and_loudness():
    with AMBIENCE.open("rb") as source:
        probe = probe_audio_candidate(
            source.fileno(), mime_type="audio/wav", toolchain=_toolchain()
        )
    assert probe.file_sha256 == "e58b991cd53fb90d79f3482957a51a56bf56d8cfb6cbdf40152bd39ac9102dca"
    assert probe.duration_samples == 48_000
    assert probe.sample_rate_hz == 48_000
    assert probe.channels == 2
    assert probe.channel_layout.value == "stereo"
    assert probe.codec_name == "pcm_s16le"
    assert probe.decoded_pcm_sha256 == (
        "5465d350919ea264287d66d036bf9ee4ddc6b43959a32f2e6d06075fbccafc51"
    )
    assert probe.loudness.measurement_standard == "ebu_r128"
    assert probe.loudness_receipt_id
    assert audio_content_fingerprint(probe) == probe.content_fingerprint

    with DIALOGUE.open("rb") as source:
        dialogue = probe_audio_candidate(
            source.fileno(),
            mime_type="audio/wav",
            toolchain=_toolchain(),
            measure_loudness=False,
        )
    assert (dialogue.duration_samples, dialogue.sample_rate_hz, dialogue.channels) == (
        96_000,
        48_000,
        1,
    )


def test_probe_rejects_wrong_mime_truncation_and_claimed_metadata(tmp_path):
    with DIALOGUE.open("rb") as source:
        with pytest.raises(AiVideoError) as caught:
            probe_audio_candidate(
                source.fileno(), mime_type="audio/mpeg", toolchain=_toolchain()
            )
    assert caught.value.code is ErrorCode.AUDIO_ASSET_INVALID

    truncated = tmp_path / "truncated.wav"
    truncated.write_bytes(DIALOGUE.read_bytes()[:32])
    with truncated.open("rb") as source:
        with pytest.raises(AiVideoError) as caught:
            probe_audio_candidate(
                source.fileno(), mime_type="audio/wav", toolchain=_toolchain()
            )
    assert caught.value.code is ErrorCode.AUDIO_PROBE_FAILED

    def wrong_container_runner(argv, **kwargs):
        return subprocess.CompletedProcess(
            argv,
            0,
            stdout=json.dumps(
                {
                    "streams": [
                        {
                            "codec_type": "audio",
                            "codec_name": "pcm_s16le",
                            "sample_rate": "48000",
                            "channels": 1,
                        }
                    ],
                    "format": {"format_name": "aiff"},
                }
            ),
            stderr="",
        )

    with DIALOGUE.open("rb") as source:
        with pytest.raises(AiVideoError, match="container"):
            probe_audio_candidate(
                source.fileno(),
                mime_type="audio/wav",
                toolchain=_toolchain(),
                runner=wrong_container_runner,
            )

    with DIALOGUE.open("rb") as source:
        with pytest.raises(AiVideoError, match="provider metadata"):
            probe_audio_candidate(
                source.fileno(),
                mime_type="audio/wav",
                toolchain=_toolchain(),
                claimed_metadata=ClaimedAudioMetadata(
                    codec_name="pcm_s16le",
                    duration_samples=96_000,
                    sample_rate_hz=44_100,
                    channels=1,
                ),
            )


def test_probe_unknown_loudness_policy_is_explicit():
    with DIALOGUE.open("rb") as source:
        probe = probe_audio_candidate(
            source.fileno(),
            mime_type="audio/wav",
            toolchain=_toolchain(),
            measure_loudness=False,
        )
    assert probe.loudness.integrated_lufs_milli is None
    assert probe.loudness.true_peak_dbfs_milli is None
    assert probe.loudness.measurement_standard is None


def test_probe_binds_tool_reads_to_held_fd_during_path_replacement(tmp_path):
    source_path = tmp_path / "source.wav"
    source_path.write_bytes(DIALOGUE.read_bytes())
    original_stat = source_path.stat()
    calls = 0

    def replacing_runner(*args, **kwargs):
        nonlocal calls
        result = subprocess.run(*args, **kwargs)
        calls += 1
        if calls == 1:
            replacement = tmp_path / "replacement.wav"
            replacement.write_bytes(AMBIENCE.read_bytes())
            replacement.replace(source_path)
        return result

    with source_path.open("rb") as source:
        probe = probe_audio_candidate(
            source.fileno(),
            mime_type="audio/wav",
            toolchain=_toolchain(),
            runner=replacing_runner,
        )
    assert probe.file_device == original_stat.st_dev
    assert probe.file_inode == original_stat.st_ino
    assert probe.file_sha256 == hashlib.sha256(DIALOGUE.read_bytes()).hexdigest()
    assert hashlib.sha256(source_path.read_bytes()).hexdigest() != probe.file_sha256


def test_probe_uses_private_snapshot_against_mutation_restore(tmp_path):
    source_path = tmp_path / "source.wav"
    dialogue_bytes = DIALOGUE.read_bytes()
    ambience_bytes = AMBIENCE.read_bytes()
    assert len(dialogue_bytes) == len(ambience_bytes)
    source_path.write_bytes(dialogue_bytes)
    original_stat = source_path.stat()
    calls = 0
    tool_snapshot_stats: list[os.stat_result] = []
    tool_snapshot_access_modes: list[int] = []

    def mutation_restore_runner(argv, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            source_path.write_bytes(ambience_bytes)
        held_path = next(item for item in argv if item.startswith("/proc/self/fd/"))
        snapshot_fd = int(Path(held_path).name)
        tool_snapshot_stats.append(os.fstat(snapshot_fd))
        tool_snapshot_access_modes.append(fcntl.fcntl(snapshot_fd, fcntl.F_GETFL))
        result = subprocess.run(argv, **kwargs)
        if calls == 3:
            source_path.write_bytes(dialogue_bytes)
        return result

    with source_path.open("rb") as source:
        probe = probe_audio_candidate(
            source.fileno(),
            mime_type="audio/wav",
            toolchain=_toolchain(),
            runner=mutation_restore_runner,
        )

    assert calls == 3
    assert probe.file_sha256 == hashlib.sha256(dialogue_bytes).hexdigest()
    assert probe.decoded_pcm_sha256 == (
        "eeaaf0bf8c11cf327ac65f7e8f7279757cefd11513a3137e35ee769426e1a329"
    )
    assert (probe.duration_samples, probe.channels) == (96_000, 1)
    assert all(item.st_ino != original_stat.st_ino for item in tool_snapshot_stats)
    assert all(item.st_nlink == 0 for item in tool_snapshot_stats)
    assert all((mode & os.O_ACCMODE) == os.O_RDONLY for mode in tool_snapshot_access_modes)
    assert source_path.read_bytes() == dialogue_bytes


def test_content_fingerprint_is_independent_of_machine_inode(tmp_path):
    copy = tmp_path / "ambience-copy.wav"
    copy.write_bytes(AMBIENCE.read_bytes())
    with AMBIENCE.open("rb") as left, copy.open("rb") as right:
        left_probe = probe_audio_candidate(
            left.fileno(),
            mime_type="audio/wav",
            toolchain=_toolchain(),
            measure_loudness=False,
        )
        right_probe = probe_audio_candidate(
            right.fileno(),
            mime_type="audio/wav",
            toolchain=_toolchain(),
            measure_loudness=False,
        )
    assert (left_probe.file_device, left_probe.file_inode) != (
        right_probe.file_device,
        right_probe.file_inode,
    )
    assert left_probe.content_fingerprint == right_probe.content_fingerprint


@pytest.mark.parametrize(
    ("ffmpeg_name", "ffprobe_name"),
    [("ffprobe", "ffmpeg"), ("forged", "ffprobe"), ("ffmpeg", "forged")],
)
def test_audio_toolchain_rejects_swapped_or_forged_identity_names(
    ffmpeg_name, ffprobe_name
):
    toolchain = _toolchain()
    with pytest.raises(ValidationError, match="identity name"):
        AudioProbeToolchain(
            ffmpeg_path=toolchain.ffmpeg_path,
            ffprobe_path=toolchain.ffprobe_path,
            ffmpeg=ToolIdentity(name=ffmpeg_name, version="test-pinned"),
            ffprobe=ToolIdentity(name=ffprobe_name, version="test-pinned"),
        )


@pytest.mark.parametrize(
    ("kind", "expected_type", "fixture"),
    [
        (AudioKind.DIALOGUE, AssetType.VOICE, DIALOGUE),
        (AudioKind.BGM, AssetType.MUSIC, AMBIENCE),
        (AudioKind.SFX, AssetType.SFX, AMBIENCE),
    ],
)
def test_provider_free_import_prepares_typed_bytes_without_active_write(
    tmp_path, kind, expected_type, fixture
):
    manifest = tmp_path / "manifest.json"
    manifest.write_text("unchanged", encoding="utf-8")
    with fixture.open("rb") as source:
        prepared = _import_request(kind).prepare(source.fileno(), toolchain=_toolchain())
    assert prepared.payload == fixture.read_bytes()
    assert prepared.asset_record.asset_type is expected_type
    assert prepared.asset_record.audio_metadata is not None
    assert prepared.asset_record.sha256 == hashlib.sha256(prepared.payload).hexdigest()
    assert prepared.asset_record.artifact_path == Path(
        f"assets/audio/{prepared.asset_record.sha256}.wav"
    )
    assert manifest.read_text(encoding="utf-8") == "unchanged"
    assert list(tmp_path.iterdir()) == [manifest]
