"""Fail-closed Suno music direction. Timeline, activation, and captcha stay outside."""

from __future__ import annotations

import json
import os
import re
import uuid
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Literal, Protocol

from pydantic import Field, field_validator, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.composition_contracts import (
    AudioKind,
    AudioTrackSpec,
    DuckingSpec,
)
from ai_video.production.audio import AudioProbeResult
from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import (
    AUDIO_KIND_TO_ASSET_TYPE,
    AssetRecord,
    AssetSourceKind,
    AudioAssetMetadata,
    AudioSource,
    ToolIdentity,
)

_PROVIDER = "suno"
_CLI_VERSION = "0.10.1"
_MODEL_KEYS = {"v6": "chirp-hawk", "v6-wild": "chirp-hawk-wild", "v6-mini": "chirp-goose"}
_REQUEST_NAMESPACE = uuid.UUID("6d2e1a4a-7c1e-4c4a-9a1e-0c5b8f3e2a11")
_CUE_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_CLIP_ID = re.compile(r"^[A-Za-z0-9_-]{8,64}$")
_SECRET = re.compile(
    r"(?i)(bearer\s+\S+|eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}|__client|cookie\s*[:=]\s*\S+|jwt\s*[:=]\s*\S+)"
)
_FORBIDDEN_FLAGS = {
    "--token",
    "--cookie",
    "--jwt",
    "--cookie-stdin",
    "--jwt-stdin",
    "--force",
    "--max-mode",
    "--headless",
}
_SUSPENSE = ("悬疑", "紧张", "恐惧", "惊悚", "不安", "suspense", "dread", "tense", "thriller")
_THEME = ("主题", "动机", "theme", "leitmotif", "motif")
_PAID_COMMANDS = {"generate", "describe", "extend", "cover", "remaster", "concat", "stems"}


class MusicEditNeed(str, Enum):
    UNDERSCORE = "underscore"
    THEME_STATEMENT = "theme_statement"
    TRANSITION_STING = "transition_sting"
    DIEGETIC_SONG = "diegetic_song"
    SOURCE_ATMOSPHERE = "source_atmosphere"
    INTENTIONAL_SILENCE = "intentional_silence"


class MusicRole(str, Enum):
    SILENCE = "silence"
    INSTRUMENTAL_BED = "instrumental_bed"
    CHARACTER_THEME = "character_theme"
    SUSPENSE_ATMOSPHERE = "suspense_atmosphere"
    SUNG_CUE = "sung_cue"


class SceneMusicBrief(StrictModel):
    cue_id: str
    scene_id: str = Field(min_length=1, max_length=80)
    script_excerpt: str = Field(min_length=1, max_length=2000)
    emotion: str = Field(min_length=1, max_length=200)
    scene_facts: str = Field(min_length=1, max_length=500)
    edit_need: MusicEditNeed
    character_id: str | None = Field(default=None, max_length=80)
    dialogue_present: bool
    editorial_window_seconds: tuple[float, float] | None = None
    sung_lyrics: str | None = Field(default=None, max_length=5000)

    @field_validator("cue_id")
    @classmethod
    def _cue_id(cls, value: str) -> str:
        if _CUE_ID.fullmatch(value) is None:
            raise ValueError("cue_id must be a short lowercase identifier")
        return value

    @model_validator(mode="after")
    def _window(self) -> "SceneMusicBrief":
        window = self.editorial_window_seconds
        if window is not None and window[1] <= window[0]:
            raise ValueError("editorial window must be positive")
        if self.sung_lyrics is not None and "<" in self.sung_lyrics:
            raise ValueError("sung lyrics cannot contain scaffold placeholders")
        return self


class MusicDirection(StrictModel):
    cue_id: str
    role: MusicRole
    instrumental: bool
    title: str = Field(min_length=1, max_length=100)
    tags: str = ""
    exclude: str = ""
    lyrics: str = ""
    model: Literal["v6", "v6-wild", "v6-mini"] = "v6"
    duration_policy: Literal["phrase_then_timeline_trim"] = "phrase_then_timeline_trim"
    clock_owner: Literal["resolved_timeline"] = "resolved_timeline"
    editorial_hint_seconds: tuple[float, float] | None = None
    duck_under_dialogue: bool
    rationale: str = Field(min_length=1)
    generation_required: bool
    qa_findings: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _role_agrees(self) -> "MusicDirection":
        if self.role is MusicRole.SILENCE:
            if self.generation_required or self.instrumental or self.tags or self.lyrics:
                raise ValueError("silence does not generate music")
            return self
        if self.instrumental != (self.role is not MusicRole.SUNG_CUE):
            raise ValueError("vocal policy does not match the music role")
        if self.role is MusicRole.SUNG_CUE and not self.lyrics.strip():
            raise ValueError("a sung cue requires lyrics")
        if self.instrumental and self.lyrics:
            raise ValueError("instrumental music cannot carry lyrics")
        if not self.generation_required:
            raise ValueError("a sounding role requires generation")
        return self


class MusicQaRequirement(StrictModel):
    cue_id: str
    payload_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    required_findings: tuple[str, ...] = Field(min_length=1)
    verdict: Literal["NOT_EVALUATED"] = "NOT_EVALUATED"


class SunoMusicHandoff(StrictModel):
    activation: Literal["not_committed"] = "not_committed"
    committer: Literal["ProductionStateCommitter"] = "ProductionStateCommitter"
    asset_type: Literal["music"] = "music"
    audio_kind: Literal["bgm"] = "bgm"
    cue_id: str
    request_id: str
    payload_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    placement_owner: Literal["resolved_timeline"] = "resolved_timeline"
    mixer: Literal["hyperframes_p4"] = "hyperframes_p4"
    qa_verdict: Literal["NOT_EVALUATED"] = "NOT_EVALUATED"


class _Completed(Protocol):
    returncode: int
    stdout: str
    stderr: str


class SunoTransport(Protocol):
    def run(self, argv: Sequence[str], *, timeout_seconds: float) -> _Completed:
        """Run one already-validated suno argv without a shell."""


def direct_music(brief: SceneMusicBrief) -> MusicDirection:
    text = f"{brief.emotion} {brief.scene_facts}".casefold()
    suspense = any(token.casefold() in text for token in _SUSPENSE)
    theme = any(token.casefold() in text for token in _THEME)
    hint = brief.editorial_window_seconds
    if brief.edit_need is MusicEditNeed.INTENTIONAL_SILENCE:
        return MusicDirection(
            cue_id=brief.cue_id,
            role=MusicRole.SILENCE,
            instrumental=False,
            title=_title(brief, "silence"),
            duck_under_dialogue=False,
            rationale="剪辑要求留白，这一段不生成配乐。",
            generation_required=False,
            editorial_hint_seconds=hint,
            qa_findings=("确认成片该段没有新加入的配乐。", "不得把留白改成固定时长的空音频。"),
        )
    if brief.edit_need is MusicEditNeed.DIEGETIC_SONG:
        if not brief.sung_lyrics or not brief.sung_lyrics.strip():
            raise _invalid("画面内歌曲需要已写好的歌词，不能让模型临场写词。")
        return _sounding(
            brief,
            role=MusicRole.SUNG_CUE,
            title="diegetic song",
            tags=f"diegetic song, { _compact(brief.emotion) }, performed in scene",
            exclude="spoken advertisement, narrator voiceover",
            lyrics=brief.sung_lyrics.strip(),
            rationale="这一镜需要角色或场景里真实响起的歌曲，而不是底乐。",
        )
    if brief.edit_need is MusicEditNeed.THEME_STATEMENT:
        if not brief.character_id:
            raise _invalid("角色主题需要明确的角色，不能做成无人称的通用底乐。")
        return _sounding(
            brief,
            role=MusicRole.CHARACTER_THEME,
            title="character theme",
            tags=f"instrumental character leitmotif, recognizable motif, { _compact(brief.emotion) }",
            exclude="vocals, lyrics, choir, spoken word",
            lyrics="",
            rationale=f"用可辨认的器乐动机陈述角色 {brief.character_id}，不唱词。",
        )
    if brief.edit_need is MusicEditNeed.SOURCE_ATMOSPHERE or suspense:
        if suspense or brief.edit_need is MusicEditNeed.SOURCE_ATMOSPHERE:
            role = MusicRole.SUSPENSE_ATMOSPHERE if suspense else MusicRole.INSTRUMENTAL_BED
            label = "suspense atmosphere" if role is MusicRole.SUSPENSE_ATMOSPHERE else "atmosphere bed"
            tags = (
                "instrumental suspense underscore, low pulse, dissonant strings, restrained dynamics"
                if role is MusicRole.SUSPENSE_ATMOSPHERE
                else f"instrumental atmosphere, { _compact(brief.emotion) }, no melodic vocal"
            )
            return _sounding(
                brief,
                role=role,
                title=label,
                tags=tags,
                exclude="vocals, lyrics, bright pop, comedy stinger",
                lyrics="",
                rationale="气氛由场景情绪决定，生成完整乐句后再交给时间线裁切。",
            )
    if theme and brief.character_id:
        return _sounding(
            brief,
            role=MusicRole.CHARACTER_THEME,
            title="character theme",
            tags=f"instrumental character leitmotif, { _compact(brief.emotion) }",
            exclude="vocals, lyrics, spoken word",
            lyrics="",
            rationale=f"剧本点明角色动机，为 {brief.character_id} 配器乐主题。",
        )
    sting = brief.edit_need is MusicEditNeed.TRANSITION_STING
    return _sounding(
        brief,
        role=MusicRole.INSTRUMENTAL_BED,
        title="transition sting" if sting else "underscore",
        tags=(
            "instrumental transitional gesture, single musical phrase, no trailer impact"
            if sting
            else f"instrumental film underscore, supportive, { _compact(brief.emotion) }"
        ),
        exclude="vocals, lyrics, speech",
        lyrics="",
        rationale="配乐托住对白或转场，不规定成片秒数。",
    )


def generation_identity(direction: MusicDirection) -> str:
    lyrics_hash = canonical_sha256({"lyrics": direction.lyrics}) if direction.lyrics else ""
    return canonical_sha256(
        {
            "schema": "ai-video-suno-music/1",
            "cue_id": direction.cue_id,
            "role": direction.role.value,
            "model": direction.model,
            "title": direction.title,
            "tags": direction.tags,
            "exclude": direction.exclude,
            "instrumental": direction.instrumental,
            "lyrics_sha256": lyrics_hash,
        }
    )


def request_id_for(direction: MusicDirection) -> str:
    digest = generation_identity(direction)
    return str(uuid.uuid5(_REQUEST_NAMESPACE, f"{direction.cue_id}:{digest}"))


def build_generation_argv(direction: MusicDirection, *, dry_run: bool) -> tuple[str, ...]:
    if not direction.generation_required:
        raise _invalid("这条配乐决定不需要生成。")
    for label, value in (
        ("title", direction.title),
        ("tags", direction.tags),
        ("exclude", direction.exclude),
        ("lyrics", direction.lyrics),
    ):
        if value.startswith("-"):
            raise _invalid(f"{label} 不能以命令开关开头。")
    _reject_utf16(direction.title, 100, "title")
    _reject_utf16(direction.tags, 1000, "tags")
    _reject_utf16(direction.exclude, 1000, "exclude")
    _reject_utf16(direction.lyrics, 5000, "lyrics")
    argv = [
        "generate",
        "--model",
        direction.model,
        "--title",
        direction.title,
        "--tags",
        direction.tags,
        "--exclude",
        direction.exclude,
        "--request-id",
        request_id_for(direction),
        "--no-captcha",
    ]
    if direction.instrumental:
        argv.append("--instrumental")
    else:
        argv.extend(["--lyrics", direction.lyrics])
    if dry_run:
        argv.append("--dry-run")
    _reject_forbidden(argv)
    if "--wait" in argv or "--download" in argv:
        raise _invalid("生成命令不能在提交时等待或下载。")
    return tuple(argv)


class SunoReceipt(StrictModel):
    request_id: str
    payload_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    state: Literal["dry_ran", "submission_unknown", "submitted", "known_no_effect"]
    clip_ids: tuple[str, ...] = ()
    updated_at: str
    next_action: str

    @field_validator("clip_ids")
    @classmethod
    def _clips(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(_CLIP_ID.fullmatch(item) is None for item in value):
            raise ValueError("clip id is not a safe identifier")
        return value


class SunoCallResult(StrictModel):
    request_id: str
    payload_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    submitted: bool
    charged: Literal[False] = False
    model_verified_live: bool
    external_model_key: str | None = None
    clip_ids: tuple[str, ...] = ()
    state: Literal["dry_ran", "submission_unknown", "submitted", "known_no_effect"]
    detail: str


class SunoMusicService:
    def __init__(
        self,
        *,
        ledger_dir: Path,
        transport: SunoTransport,
        executable: str = "suno",
    ) -> None:
        self.ledger_dir = ledger_dir
        self.transport = transport
        self.executable = executable

    def dry_run(self, direction: MusicDirection) -> SunoCallResult:
        argv = build_generation_argv(direction, dry_run=True)
        identity = generation_identity(direction)
        request_id = request_id_for(direction)
        existing = self._read(request_id)
        if existing is not None and existing.payload_sha256 != identity:
            raise _unknown("同一请求编号已经绑定了另一份配乐，不能改写后重试。")
        completed = self._invoke(argv, timeout_seconds=30)
        payload = _envelope(completed)
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        if (
            payload.get("status") != "success"
            or data.get("dry_run") is not True
            or data.get("submitted") is not False
            or data.get("model_verified_live") is not False
        ):
            raise _failed("离线 dry-run 没有证明请求未提交、也未做在线模型校验。")
        request = data.get("request") if isinstance(data.get("request"), dict) else {}
        if request.get("mv") != _MODEL_KEYS[direction.model]:
            raise _failed("dry-run 的模型键与 v6 家族约定不一致。")
        if request.get("transaction_uuid") != request_id:
            raise _failed("dry-run 没有保留稳定请求编号。")
        if existing is None or existing.state == "dry_ran":
            self._write(
                SunoReceipt(
                    request_id=request_id,
                    payload_sha256=identity,
                    state="dry_ran",
                    updated_at=_now(),
                    next_action="等待明确的付费授权后再提交；不要去掉 --dry-run。",
                )
            )
        return SunoCallResult(
            request_id=request_id,
            payload_sha256=identity,
            submitted=False,
            model_verified_live=bool(data.get("model_verified_live")),
            external_model_key=str(request.get("mv")),
            state="dry_ran" if existing is None or existing.state == "dry_ran" else existing.state,
            detail="离线校验完成，没有认证、提交或扣费。",
        )

    def submit(self, direction: MusicDirection, *, paid_generation_authorized: bool = False) -> SunoCallResult:
        if not paid_generation_authorized:
            raise _live_required("真实 Suno 生成尚未授权，因此没有提交。")
        argv = build_generation_argv(direction, dry_run=False)
        identity = generation_identity(direction)
        request_id = request_id_for(direction)
        existing = self._read(request_id)
        if existing is not None and existing.payload_sha256 != identity:
            raise _unknown("配乐内容已变化。旧请求可能已经扣费，不能用同一编号再提交。")
        if existing is not None and existing.state == "submitted":
            return SunoCallResult(
                request_id=request_id,
                payload_sha256=identity,
                submitted=True,
                charged=False,
                model_verified_live=False,
                clip_ids=existing.clip_ids,
                state="submitted",
                detail="已有提交回执，本次没有再次调用 Suno。",
            )
        if existing is not None and existing.state == "submission_unknown":
            raise _unknown("上次提交结果未知。先用 status 核对，不能重新提交。")
        self._write(
            SunoReceipt(
                request_id=request_id,
                payload_sha256=identity,
                state="submission_unknown",
                updated_at=_now(),
                next_action="用 suno status 核对 clip；未知结果禁止再次 generate。",
            )
        )
        try:
            completed = self._invoke(argv, timeout_seconds=60)
            payload = _envelope(completed)
        except AiVideoError as exc:
            if exc.code is ErrorCode.PAID_PROVIDER_OUTCOME_UNKNOWN:
                raise
            self._write(
                SunoReceipt(
                    request_id=request_id,
                    payload_sha256=identity,
                    state="known_no_effect",
                    updated_at=_now(),
                    next_action="提交前失败，没有拿到任务编号。排除原因后需要新的授权。",
                )
            )
            raise
        return self._accept_submit(request_id, identity, payload)

    def status_argv(self, clip_ids: Sequence[str]) -> tuple[str, ...]:
        ids = _clip_ids(clip_ids)
        return ("status", *ids)

    def download_argv(self, clip_ids: Sequence[str], output_dir: Path) -> tuple[str, ...]:
        ids = _clip_ids(clip_ids)
        if output_dir.is_absolute() and ".." in output_dir.parts:
            raise _invalid("下载目录不合法。")
        text = str(output_dir)
        if text.startswith("-") or not text:
            raise _invalid("下载目录不能被解析成命令开关。")
        return ("download", *ids, "--format", "wav", "--output", text)

    def recover(self, request_id: str) -> SunoReceipt | None:
        return self._read(request_id)

    def _accept_submit(self, request_id: str, identity: str, payload: Mapping[str, object]) -> SunoCallResult:
        status = payload.get("status")
        error = payload.get("error") if isinstance(payload.get("error"), dict) else {}
        code = str(error.get("code") or "")
        data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
        if code in {"captcha_required", "auth_missing", "config_error"} or data.get("submitted") is False:
            self._write(
                SunoReceipt(
                    request_id=request_id,
                    payload_sha256=identity,
                    state="known_no_effect",
                    updated_at=_now(),
                    next_action="平台在提交前拒绝了请求。不要解验证码，也不要立刻重试。",
                )
            )
            raise _no_effect("Suno 在生成提交前拒绝了请求。")
        clips = _extract_clip_ids(data)
        if status != "success" or not clips:
            raise _unknown("Suno 响应无法证明任务编号。已封存为未知结果，禁止重试。")
        self._write(
            SunoReceipt(
                request_id=request_id,
                payload_sha256=identity,
                state="submitted",
                clip_ids=clips,
                updated_at=_now(),
                next_action="用 status 查询这些 clip，完成后再下载 WAV。",
            )
        )
        return SunoCallResult(
            request_id=request_id,
            payload_sha256=identity,
            submitted=True,
            charged=False,
            model_verified_live=False,
            clip_ids=clips,
            state="submitted",
            detail="提交回执已保存。是否扣费以账号账单为准，本回执不声称已结算。",
        )

    def _invoke(self, argv: Sequence[str], *, timeout_seconds: float) -> _Completed:
        command = ["--json", "--no-browser", *argv]
        _reject_forbidden(command)
        if argv[0] in _PAID_COMMANDS and "--no-captcha" not in argv and "--dry-run" not in argv:
            raise _invalid("付费命令必须关闭内置验证码求解。")
        if argv[0] == "generate" and "--no-captcha" not in argv:
            raise _invalid("生成命令必须关闭内置验证码求解。")
        try:
            completed = self.transport.run(command, timeout_seconds=timeout_seconds)
        except TimeoutError as exc:
            raise _unknown("Suno CLI 超时。结果按未知处理，不能再次提交。") from exc
        except OSError as exc:
            raise _failed("无法执行 Suno CLI。") from exc
        if completed.returncode not in {0, 2, 3, 4}:
            raise _unknown("Suno CLI 返回了无法分类的退出码。")
        return completed

    def _path(self, request_id: str) -> Path:
        try:
            parsed = uuid.UUID(request_id)
        except ValueError as exc:
            raise _invalid("请求编号不是 UUID。") from exc
        if str(parsed) != request_id:
            raise _invalid("请求编号必须是规范 UUID。")
        return self.ledger_dir / f"{request_id}.json"

    def _read(self, request_id: str) -> SunoReceipt | None:
        path = self._path(request_id)
        if not path.is_file():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            receipt = SunoReceipt.model_validate(payload)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            raise _unknown("本地恢复回执损坏，不能当作未提交。") from exc
        text = path.read_text(encoding="utf-8")
        if _SECRET.search(text):
            raise _invalid("恢复回执含有凭证样式文本，已拒绝读取。")
        return receipt

    def _write(self, receipt: SunoReceipt) -> None:
        self.ledger_dir.mkdir(parents=True, exist_ok=True)
        path = self._path(receipt.request_id)
        payload = receipt.model_dump(mode="json")
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        if _SECRET.search(encoded.decode("utf-8")):
            raise _invalid("拒绝写入含凭证样式文本的回执。")
        temporary = path.with_suffix(".json.tmp")
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            os.write(fd, encoded)
            os.fsync(fd)
        finally:
            os.close(fd)
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
        os.chmod(path, 0o600)


def music_qa_requirement(direction: MusicDirection) -> MusicQaRequirement:
    return MusicQaRequirement(
        cue_id=direction.cue_id,
        payload_sha256=generation_identity(direction),
        required_findings=direction.qa_findings,
    )


def music_handoff(direction: MusicDirection) -> SunoMusicHandoff:
    return SunoMusicHandoff(
        cue_id=direction.cue_id,
        request_id=request_id_for(direction),
        payload_sha256=generation_identity(direction),
    )


def music_asset_record(
    *,
    asset_id: str,
    probe: AudioProbeResult,
    direction: MusicDirection,
    usage_license: str = "suno-account-terms-unverified",
) -> AssetRecord:
    if not direction.generation_required:
        raise _invalid("留白不能登记成音乐资产。")
    if probe.mime_type not in {"audio/wav", "audio/x-wav"} or probe.codec_name != "pcm_s16le":
        raise _invalid("进入混音的 Suno 音频必须是已测量的 PCM WAV。")
    source = AudioSource(
        kind=AssetSourceKind.GENERATED,
        provider_or_tool=ToolIdentity(name=_PROVIDER, version=_CLI_VERSION),
        input_fingerprint=generation_identity(direction),
        original_reference=request_id_for(direction),
    )
    metadata = AudioAssetMetadata(
        audio_kind=AudioKind.BGM,
        source=source,
        duration_samples=probe.duration_samples,
        sample_rate_hz=probe.sample_rate_hz,
        channels=probe.channels,
        channel_layout=probe.channel_layout,
        codec_name=probe.codec_name,
        loudness=probe.loudness,
        provenance_receipt_id=request_id_for(direction),
    )
    return AssetRecord(
        asset_id=asset_id,
        asset_type=AUDIO_KIND_TO_ASSET_TYPE[AudioKind.BGM],
        artifact_path=Path(f"assets/audio/{probe.file_sha256}.wav"),
        sha256=probe.file_sha256,
        size_bytes=probe.size_bytes,
        mime_type=probe.mime_type,
        source_kind=AssetSourceKind.GENERATED,
        tool=source.provider_or_tool,
        input_fingerprint=source.input_fingerprint,
        creation_receipt_id=request_id_for(direction),
        usage_license=usage_license,
        audio_metadata=metadata,
    )


def bind_music_track(
    *,
    track_id: str,
    asset_id: str,
    start_sample: int,
    sample_rate_hz: int,
    trim_duration_samples: int | None = None,
    duck_dialogue_track_ids: Sequence[str] = (),
) -> AudioTrackSpec:
    if sample_rate_hz <= 0 or start_sample < 0:
        raise _invalid("混音起点必须由时间线给出。")
    ducking = None
    if duck_dialogue_track_ids:
        ducking = DuckingSpec(
            sidechain_track_ids=tuple(duck_dialogue_track_ids),
            attenuation_millidb=-12000,
            attack_samples=max(1, sample_rate_hz // 100),
            release_samples=sample_rate_hz // 2,
        )
    return AudioTrackSpec(
        track_id=track_id,
        audio_kind=AudioKind.BGM,
        asset_id=asset_id,
        start_sample=start_sample,
        trim_duration_samples=trim_duration_samples,
        gain_millidb=-600,
        ducking=ducking,
    )


class CliTransport:
    def __init__(self, executable: Path) -> None:
        self.executable = executable

    def run(self, argv: Sequence[str], *, timeout_seconds: float) -> _Completed:
        import subprocess

        env = {key: os.environ[key] for key in ("PATH", "HOME", "LANG", "LC_ALL", "USER") if key in os.environ}
        try:
            completed = subprocess.run(
                [str(self.executable), *argv],
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                env=env,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError("suno timed out") from exc
        return completed


def redact_provider_text(value: str) -> str:
    return _SECRET.sub("<redacted>", value)


def _sounding(
    brief: SceneMusicBrief,
    *,
    role: MusicRole,
    title: str,
    tags: str,
    exclude: str,
    lyrics: str,
    rationale: str,
) -> MusicDirection:
    findings = [
        "正常速度审听情绪、乐器和场景是否一致。",
        "技术检查通过不能代替成片听感验收。",
    ]
    if role is not MusicRole.SUNG_CUE:
        findings.append("成品不得出现人声、哼唱或歌词。")
    else:
        findings.append("歌词必须与提供的唱词一致，不能自行改词。")
    if brief.dialogue_present and role is not MusicRole.SUNG_CUE:
        findings.append("对白出现时配乐要让开，词义仍须听清。")
    if role is MusicRole.CHARACTER_THEME:
        findings.append("动机应能识别为该角色，而不是另一首无关曲子。")
    if role is MusicRole.SUSPENSE_ATMOSPHERE:
        findings.append("悬疑气氛应持续服务于场景，不能突然变成歌曲。")
    return MusicDirection(
        cue_id=brief.cue_id,
        role=role,
        instrumental=role is not MusicRole.SUNG_CUE,
        title=_title(brief, title),
        tags=tags,
        exclude=exclude,
        lyrics=lyrics,
        editorial_hint_seconds=brief.editorial_window_seconds,
        duck_under_dialogue=brief.dialogue_present and role is not MusicRole.SUNG_CUE,
        rationale=rationale,
        generation_required=True,
        qa_findings=tuple(findings),
    )


def _title(brief: SceneMusicBrief, label: str) -> str:
    raw = f"{brief.scene_id} {label}"
    compact = " ".join(raw.split())
    return compact[:80]


def _compact(value: str) -> str:
    cleaned = " ".join(value.replace(",", " ").split())
    return cleaned[:80]


def _reject_utf16(value: str, limit: int, label: str) -> None:
    if len(value.encode("utf-16-le")) // 2 > limit:
        raise _invalid(f"{label} 超过 Suno 字段上限。")


def _reject_forbidden(argv: Sequence[str]) -> None:
    if any(item in _FORBIDDEN_FLAGS or item.startswith("--token") for item in argv):
        raise _invalid("Suno 命令包含被禁止的验证码、凭证或强制重试开关。")


def _clip_ids(clip_ids: Sequence[str]) -> tuple[str, ...]:
    if not clip_ids or any(_CLIP_ID.fullmatch(item) is None for item in clip_ids):
        raise _invalid("clip id 不合法。")
    return tuple(clip_ids)


def _extract_clip_ids(data: Mapping[str, object]) -> tuple[str, ...]:
    raw = data.get("ids")
    if not isinstance(raw, list):
        clips = data.get("clips")
        if isinstance(clips, list):
            raw = [item.get("id") for item in clips if isinstance(item, dict)]
    if not isinstance(raw, list):
        return ()
    values = tuple(str(item) for item in raw)
    if any(_CLIP_ID.fullmatch(item) is None for item in values):
        return ()
    return values


def _envelope(completed: _Completed) -> dict[str, object]:
    text = completed.stdout.strip() or completed.stderr.strip()
    if _SECRET.search(completed.stdout) or _SECRET.search(completed.stderr):
        raise _unknown("Suno 输出含有凭证样式文本，已丢弃并按未知结果封存。")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise _unknown("Suno 输出不是可解析的 JSON。") from exc
    if not isinstance(payload, dict) or "status" not in payload:
        raise _unknown("Suno 输出缺少状态信封。")
    return payload


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _invalid(message: str) -> AiVideoError:
    return AiVideoError(ErrorCode.AUDIO_ASSET_INVALID, message, retryable=False)


def _failed(message: str) -> AiVideoError:
    return AiVideoError(ErrorCode.PAID_PROVIDER_KNOWN_NO_EFFECT, message, retryable=False)


def _no_effect(message: str) -> AiVideoError:
    return AiVideoError(ErrorCode.PAID_PROVIDER_KNOWN_NO_EFFECT, message, retryable=False)


def _unknown(message: str) -> AiVideoError:
    return AiVideoError(ErrorCode.PAID_PROVIDER_OUTCOME_UNKNOWN, message, retryable=False)


def _live_required(message: str) -> AiVideoError:
    return AiVideoError(ErrorCode.PAID_PROVIDER_LIVE_AUTHORIZATION_REQUIRED, message, retryable=False)
