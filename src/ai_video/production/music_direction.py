"""Provider-neutral music direction; authored musical choices precede transport.

The legacy heuristic remains a fallback. This module never generates, places,
listens to, or accepts media. Timeline and QA stay with their existing owners.
"""
from __future__ import annotations

import re
from enum import Enum
from typing import Literal

from pydantic import Field, field_validator, model_validator

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.artifact_contracts import StrictModel

_CUE_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_SUSPENSE = ("悬疑", "紧张", "恐惧", "惊悚", "不安", "suspense", "dread", "tense", "thriller")
_THEME = ("主题", "动机", "theme", "leitmotif", "motif")


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


class MusicalDesign(StrictModel):
    """Codex-authored choices, not a genre preset or a second timeline.

    Free prose permits rubato, evolving meter, through-composition, counterpoint
    and sparse arrangements. Continuity is guidance, never proof of source use.
    """

    role: MusicRole
    narrative_function: str = Field(min_length=1, max_length=500)
    style: str = Field(min_length=1, max_length=500)
    instrumentation: str = Field(min_length=1, max_length=2000)
    pulse: str = Field(min_length=1, max_length=500)
    development: str = Field(min_length=1, max_length=1000)
    mix_intent: str = Field(min_length=1, max_length=500)
    continuity: str = Field(default="", max_length=1000)
    vocal_direction: str = Field(default="", max_length=500)
    exclusions: str = Field(default="", max_length=1000)
    listening_checks: tuple[str, ...] = ()

    @field_validator(
        "narrative_function", "style", "instrumentation", "pulse", "development", "mix_intent",
    )
    @classmethod
    def _not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("musical choices cannot be blank")
        return value

    @model_validator(mode="after")
    def _sounding_only(self) -> "MusicalDesign":
        if self.role is MusicRole.SILENCE:
            raise ValueError("use intentional_silence without a sounding design")
        if self.role is not MusicRole.SUNG_CUE and self.vocal_direction.strip():
            raise ValueError("instrumental design cannot direct a singer")
        if any(not item.strip() for item in self.listening_checks):
            raise ValueError("listening checks cannot be blank")
        return self


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
    musical_design: MusicalDesign | None = None

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


def direct_music(brief: SceneMusicBrief) -> MusicDirection:
    if brief.musical_design is not None:
        return _direct_authored(brief, brief.musical_design)
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


def _direct_authored(brief: SceneMusicBrief, design: MusicalDesign) -> MusicDirection:
    if brief.edit_need is MusicEditNeed.INTENTIONAL_SILENCE:
        raise _invalid("留白不接受发声设计，不能自动改为配乐。")
    sung = design.role is MusicRole.SUNG_CUE
    if sung != (brief.edit_need is MusicEditNeed.DIEGETIC_SONG):
        raise _invalid("唱词角色与已批准的音乐用途不一致。")
    if sung and (not brief.sung_lyrics or not brief.sung_lyrics.strip()):
        raise _invalid("画面内歌曲必须保留已写好的唱词。")
    if brief.edit_need is MusicEditNeed.THEME_STATEMENT and design.role is not MusicRole.CHARACTER_THEME:
        raise _invalid("角色主题不能静默改成其他音乐用途。")
    if design.role is MusicRole.CHARACTER_THEME and not brief.character_id:
        raise _invalid("角色主题需要明确角色。")
    # No keyword inference, timing conversion, source binding, or hidden truncation.
    parts = [
        "diegetic song" if sung else "instrumental score",
        design.style, design.instrumentation, design.pulse, design.development,
        design.mix_intent, design.continuity, design.vocal_direction,
    ]
    direction = _sounding(
        brief, role=design.role, title=design.role.value,
        tags=". ".join(part.strip() for part in parts if part.strip()),
        exclude=", ".join(part for part in (
            "" if sung else "vocals, lyrics, choir, spoken word", design.exclusions.strip(),
        ) if part),
        lyrics=brief.sung_lyrics.strip() if sung else "",
        rationale=design.narrative_function,
    )
    checks = [
        f"结合画面核验叙事作用：{design.narrative_function}",
        f"审听音乐发展与表演/切点的关系：{design.development}",
        f"在exact成片中核验声音层次：{design.mix_intent}",
    ]
    if design.continuity.strip():
        checks.append(f"与实际选定前段对听，不凭文字认定主题延续：{design.continuity}")
    return direction.model_copy(update={
        "qa_findings": (*direction.qa_findings, *checks, *design.listening_checks),
    })


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


def _invalid(message: str) -> AiVideoError:
    return AiVideoError(ErrorCode.AUDIO_ASSET_INVALID, message, retryable=False)
