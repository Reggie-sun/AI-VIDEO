from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.composition_contracts import AudioKind
from ai_video.production.audio import AudioLoudnessMetadata, AudioProbeResult
from ai_video.production.models import (
    AssetSourceKind,
    AssetType,
    AudioChannelLayout,
    ToolIdentity,
)
from ai_video.production.suno_music import (
    MusicEditNeed,
    MusicRole,
    SceneMusicBrief,
    SunoMusicService,
    bind_music_track,
    build_generation_argv,
    direct_music,
    generation_identity,
    music_asset_record,
    music_handoff,
    music_qa_requirement,
    redact_provider_text,
)


class _Result:
    def __init__(self, returncode: int, stdout: str, stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class _Transport:
    def __init__(
        self,
        result: _Result | list[_Result] | None = None,
        *,
        error: BaseException | None = None,
    ) -> None:
        self.calls: list[list[str]] = []
        self.results = list(result) if isinstance(result, list) else [result]
        self.error = error

    def run(self, argv, *, timeout_seconds: float):
        self.calls.append(list(argv))
        if self.error is not None:
            raise self.error
        result = self.results.pop(0) if len(self.results) > 1 else self.results[0]
        assert result is not None
        return result


def _brief(**overrides) -> SceneMusicBrief:
    payload = {
        "cue_id": "corridor-01",
        "scene_id": "走廊",
        "script_excerpt": "她停在门前，没有说话。",
        "emotion": "压抑",
        "scene_facts": "夜，窄走廊，远处有灯",
        "edit_need": MusicEditNeed.UNDERSCORE,
        "character_id": "lin",
        "dialogue_present": True,
        "editorial_window_seconds": (4.0, 11.5),
    }
    payload.update(overrides)
    return SceneMusicBrief.model_validate(payload)


def _dry_payload(direction) -> str:
    from ai_video.production.suno_music import request_id_for

    body = {
        "version": "1",
        "status": "success",
        "data": {
            "dry_run": True,
            "submitted": False,
            "model_verified_live": False,
            "request": {
                "mv": "chirp-hawk",
                "transaction_uuid": request_id_for(direction),
                "make_instrumental": True,
            },
        },
    }
    return json.dumps(body)


def _probe() -> AudioProbeResult:
    digest = "a" * 64
    return AudioProbeResult(
        mime_type="audio/wav",
        container_name="wav",
        file_sha256=digest,
        size_bytes=16,
        file_device=1,
        file_inode=2,
        codec_name="pcm_s16le",
        duration_samples=48000,
        sample_rate_hz=48000,
        channels=2,
        channel_layout=AudioChannelLayout.STEREO,
        decoded_pcm_sha256="b" * 64,
        loudness=AudioLoudnessMetadata(),
        loudness_receipt_id="c" * 64,
        ffmpeg=ToolIdentity(name="ffmpeg", version="test"),
        ffprobe=ToolIdentity(name="ffprobe", version="test"),
        content_fingerprint="d" * 64,
    )


def test_director_uses_scene_and_does_not_freeze_duration():
    direction = direct_music(_brief(emotion="悬疑", scene_facts="门后有脚步"))
    assert direction.role is MusicRole.SUSPENSE_ATMOSPHERE
    assert direction.instrumental is True
    assert direction.duck_under_dialogue is True
    assert direction.clock_owner == "resolved_timeline"
    assert direction.duration_policy == "phrase_then_timeline_trim"
    argv = build_generation_argv(direction, dry_run=True)
    assert "--instrumental" in argv
    assert "--dry-run" in argv
    assert "--no-captcha" in argv
    assert "--model" in argv and argv[argv.index("--model") + 1] == "v6"
    assert "4.0" not in argv
    assert "11.5" not in argv
    assert "--wait" not in argv
    assert "--download" not in argv


def test_cli_clip_array_success_preserves_ids_for_recovery_and_replay(tmp_path):
    direction = direct_music(_brief())
    transport = _Transport(_Result(0, json.dumps({
        "version": "1", "status": "success", "data": [
            {"id": "clip_0001", "status": "submitted"},
            {"id": "clip_0002", "status": "submitted"},
        ],
    })))
    service = SunoMusicService(ledger_dir=tmp_path, transport=transport)
    submitted = service.submit(direction, paid_generation_authorized=True)
    assert submitted.clip_ids == ("clip_0001", "clip_0002")
    assert service.recover(submitted.request_id).clip_ids == submitted.clip_ids
    assert service.submit(direction, paid_generation_authorized=True).clip_ids == submitted.clip_ids
    assert len(transport.calls) == 1


@pytest.mark.parametrize("data", [[], [{"id": "clip_0001"}, "not-a-clip"], [{"status": "submitted"}]])
def test_malformed_cli_clip_array_stays_unknown_without_resubmission(tmp_path, data):
    direction = direct_music(_brief())
    transport = _Transport(_Result(0, json.dumps({"version": "1", "status": "success", "data": data})))
    service = SunoMusicService(ledger_dir=tmp_path, transport=transport)
    for _ in range(2):
        with pytest.raises(AiVideoError) as error:
            service.submit(direction, paid_generation_authorized=True)
        assert error.value.code is ErrorCode.PAID_PROVIDER_OUTCOME_UNKNOWN
    assert len(transport.calls) == 1


def test_auth_expired_without_no_submit_proof_preserves_unknown_and_blocks_retry(tmp_path):
    direction = direct_music(_brief())
    transport = _Transport(_Result(2, "", json.dumps({
        "version": "1", "status": "error", "error": {"code": "auth_expired"},
    })))
    service = SunoMusicService(ledger_dir=tmp_path, transport=transport)
    for _ in range(2):
        with pytest.raises(AiVideoError) as error:
            service.submit(direction, paid_generation_authorized=True)
        assert error.value.code is ErrorCode.PAID_PROVIDER_OUTCOME_UNKNOWN
    assert len(transport.calls) == 1
    assert service.recover(blocked_request(direction)).state == "submission_unknown"


def test_character_theme_silence_and_song_choices():
    theme = direct_music(_brief(edit_need=MusicEditNeed.THEME_STATEMENT, emotion="克制的主题"))
    assert theme.role is MusicRole.CHARACTER_THEME
    assert "vocals" in theme.exclude
    with pytest.raises(AiVideoError):
        direct_music(_brief(edit_need=MusicEditNeed.THEME_STATEMENT, character_id=None))
    silence = direct_music(_brief(edit_need=MusicEditNeed.INTENTIONAL_SILENCE, dialogue_present=False))
    assert silence.generation_required is False
    with pytest.raises(AiVideoError):
        build_generation_argv(silence, dry_run=True)
    song = direct_music(
        _brief(
            edit_need=MusicEditNeed.DIEGETIC_SONG,
            dialogue_present=True,
            sung_lyrics="[Verse]\n门没有开",
        )
    )
    assert song.role is MusicRole.SUNG_CUE
    assert song.duck_under_dialogue is False
    assert "--instrumental" not in build_generation_argv(song, dry_run=True)


def test_dry_run_ledger_omits_lyrics_and_replays_without_resubmit(tmp_path: Path):
    direction = direct_music(
        _brief(edit_need=MusicEditNeed.DIEGETIC_SONG, sung_lyrics="[Verse]\n只唱这一句")
    )
    submitted = json.dumps(
        {
            "version": "1",
            "status": "success",
            "data": {"submitted": True, "ids": ["clip_0001", "clip_0002"]},
        }
    )
    transport = _Transport(
        [
            _Result(0, _dry_payload(direction).replace('"make_instrumental": true', '"make_instrumental": false')),
            _Result(0, submitted),
        ]
    )
    service = SunoMusicService(ledger_dir=tmp_path, transport=transport)
    first = service.dry_run(direction)
    assert first.submitted is False
    assert first.charged is False
    assert first.external_model_key == "chirp-hawk"
    assert "--no-browser" in transport.calls[0]
    assert "--dry-run" in transport.calls[0]
    stored = (tmp_path / f"{first.request_id}.json").read_text(encoding="utf-8")
    assert "只唱这一句" not in stored
    assert stat.S_IMODE((tmp_path / f"{first.request_id}.json").stat().st_mode) == 0o600
    service.submit(direction, paid_generation_authorized=True)
    assert len(transport.calls) == 2
    replay = service.submit(direction, paid_generation_authorized=True)
    assert replay.clip_ids
    assert len(transport.calls) == 2


def test_unauthorized_unknown_and_changed_payload_do_not_spend_again(tmp_path: Path):
    direction = direct_music(_brief())
    transport = _Transport(_Result(0, _dry_payload(direction)))
    service = SunoMusicService(ledger_dir=tmp_path, transport=transport)
    with pytest.raises(AiVideoError) as denied:
        service.submit(direction)
    assert denied.value.code is ErrorCode.PAID_PROVIDER_LIVE_AUTHORIZATION_REQUIRED
    assert transport.calls == []

    service.dry_run(direction)
    receipt = tmp_path / f"{service.dry_run(direction).request_id}.json"
    payload = json.loads(receipt.read_text(encoding="utf-8"))
    payload["state"] = "submission_unknown"
    receipt.write_text(json.dumps(payload), encoding="utf-8")
    os.chmod(receipt, 0o600)
    before = len(transport.calls)
    with pytest.raises(AiVideoError) as unknown:
        service.submit(direction, paid_generation_authorized=True)
    assert unknown.value.code is ErrorCode.PAID_PROVIDER_OUTCOME_UNKNOWN
    assert len(transport.calls) == before

    payload["payload_sha256"] = "e" * 64
    payload["state"] = "submitted"
    receipt.write_text(json.dumps(payload), encoding="utf-8")
    os.chmod(receipt, 0o600)
    with pytest.raises(AiVideoError):
        service.submit(direction, paid_generation_authorized=True)
    assert len(transport.calls) == before


def test_captcha_and_timeout_stay_isolated(tmp_path: Path):
    direction = direct_music(_brief())
    captcha = _Transport(
        _Result(
            3,
            json.dumps(
                {
                    "version": "1",
                    "status": "error",
                    "error": {"code": "captcha_required", "message": "challenge"},
                    "data": {"submitted": False},
                }
            ),
        )
    )
    service = SunoMusicService(ledger_dir=tmp_path, transport=captcha)
    with pytest.raises(AiVideoError) as blocked:
        service.submit(direction, paid_generation_authorized=True)
    assert blocked.value.code is ErrorCode.PAID_PROVIDER_KNOWN_NO_EFFECT
    stored = service.recover(blocked_request(direction))
    assert stored is not None and stored.state == "known_no_effect"
    assert "--token" not in captcha.calls[0]

    timed = _Transport(error=TimeoutError("late"))
    other = SunoMusicService(ledger_dir=tmp_path / "other", transport=timed)
    with pytest.raises(AiVideoError) as timeout:
        other.submit(direction, paid_generation_authorized=True)
    assert timeout.value.code is ErrorCode.PAID_PROVIDER_OUTCOME_UNKNOWN
    assert other.recover(blocked_request(direction)).state == "submission_unknown"


def test_asset_handoff_uses_existing_music_and_mixer_contracts():
    direction = direct_music(_brief(dialogue_present=False, editorial_window_seconds=None))
    record = music_asset_record(asset_id="music-corridor", probe=_probe(), direction=direction)
    assert record.asset_type is AssetType.MUSIC
    assert record.audio_metadata is not None
    assert record.audio_metadata.audio_kind is AudioKind.BGM
    assert record.source_kind is AssetSourceKind.GENERATED
    assert record.egress.remote is False
    assert record.audio_metadata.voice_id is None
    handoff = music_handoff(direction)
    assert handoff.activation == "not_committed"
    assert handoff.committer == "ProductionStateCommitter"
    assert handoff.payload_sha256 == generation_identity(direction)
    qa = music_qa_requirement(direction)
    assert qa.verdict == "NOT_EVALUATED"
    track = bind_music_track(
        track_id="bed",
        asset_id=record.asset_id,
        start_sample=48000,
        sample_rate_hz=48000,
        duck_dialogue_track_ids=("dialogue-lin",),
    )
    assert track.audio_kind is AudioKind.BGM
    assert track.start_sample == 48000
    assert track.ducking is not None
    assert "4" not in track.model_dump(mode="json").get("track_id", "")


def test_provider_text_redaction_removes_credential_shapes():
    hidden = redact_provider_text("Authorization: Bearer eyJabc.def.ghi and cookie=abc")
    assert "eyJ" not in hidden
    assert "cookie=abc" not in hidden


def blocked_request(direction) -> str:
    from ai_video.production.suno_music import request_id_for

    return request_id_for(direction)


def test_installed_cli_dry_run_does_not_submit(tmp_path: Path):
    executable = Path.home() / ".local/bin/suno"
    if not executable.is_file():
        pytest.skip("suno CLI is not installed")
    from ai_video.production.suno_music import CliTransport

    direction = direct_music(_brief())
    service = SunoMusicService(ledger_dir=tmp_path, transport=CliTransport(executable))
    result = service.dry_run(direction)
    assert result.submitted is False
    assert result.model_verified_live is False
    assert result.external_model_key == "chirp-hawk"
    assert result.charged is False
