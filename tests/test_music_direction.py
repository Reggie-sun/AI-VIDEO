from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai_video.errors import AiVideoError
from ai_video.production.music_direction import (
    MusicalDesign, MusicEditNeed, MusicRole, SceneMusicBrief, direct_music,
)
from ai_video.production.suno_music import build_generation_argv, generation_identity


def brief(design=None, **changes):
    values = dict(
        cue_id="door", scene_id="corridor", script_excerpt="她把钥匙放下。",
        emotion="紧张", scene_facts="她终于决定离开。", dialogue_present=True,
        edit_need=MusicEditNeed.UNDERSCORE, musical_design=design,
    )
    values.update(changes)
    return SceneMusicBrief(**values)


def design(**changes):
    values = dict(
        role=MusicRole.INSTRUMENTAL_BED,
        narrative_function="让离开的决定保持开放，不提前替观众悲伤",
        style="室内乐与稀疏电子织体",
        instrumentation="中提琴延长音承接呼吸，钢琴单音回应视线",
        pulse="自由速度，跟随呼吸，不设固定拍点",
        development="起初稀疏，决定后减少音符，开放尾音",
        mix_intent="近而干的音色，避开对白重音",
        continuity="沿用已选主题的下行三音轮廓，改变配器",
        exclusions="drum fill, trailer impact",
        listening_checks=("钥匙落地声与停顿仍可辨认",),
    )
    values.update(changes)
    return MusicalDesign(**values)


def test_authored_design_wins_over_keyword_template_and_reaches_suno():
    direction = direct_music(brief(design()))
    assert direction.role is MusicRole.INSTRUMENTAL_BED
    assert "dissonant strings" not in direction.tags
    for text in ("自由速度", "中提琴", "开放尾音", "下行三音"):
        assert text in direction.tags
    argv = build_generation_argv(direction, dry_run=True)
    assert argv[argv.index("--tags") + 1] == direction.tags
    assert "trailer impact" in argv[argv.index("--exclude") + 1]
    assert direction.duck_under_dialogue
    assert any("钥匙落地" in finding for finding in direction.qa_findings)


@pytest.mark.parametrize("style,pulse", [
    ("历史剧的古琴独奏", "散板"),
    ("漫剧的俏皮木管", "轻巧切分，笑点前停顿"),
    ("广告的极简电子律动", "四拍稳定脉冲，产品动作后收束"),
])
def test_no_genre_or_tempo_preset_overrides_director(style, pulse):
    direction = direct_music(brief(design(style=style, pulse=pulse)))
    assert style in direction.tags and pulse in direction.tags
    assert "--duration" not in build_generation_argv(direction, dry_run=True)


def test_revision_changes_request_but_editorial_window_does_not():
    original = direct_music(brief(design()))
    revised = direct_music(brief(design(instrumentation="保留钢琴轮廓，移除中提琴以免遮对白")))
    moved = direct_music(brief(design(), editorial_window_seconds=(2, 8)))
    assert generation_identity(original) != generation_identity(revised)
    assert generation_identity(original) == generation_identity(moved)


def test_silence_and_vocal_policy_cannot_be_overridden_by_design():
    silence = direct_music(brief(edit_need=MusicEditNeed.INTENTIONAL_SILENCE))
    assert not silence.generation_required
    with pytest.raises((AiVideoError, ValidationError)):
        direct_music(brief(design(), edit_need=MusicEditNeed.INTENTIONAL_SILENCE))
    with pytest.raises((AiVideoError, ValidationError)):
        direct_music(brief(design(vocal_direction="温暖的人声")))
    with pytest.raises((AiVideoError, ValidationError)):
        direct_music(brief(design(role=MusicRole.SUNG_CUE)))


def test_song_keeps_authored_words_and_performance_separate():
    direction = direct_music(brief(
        design(role=MusicRole.SUNG_CUE, vocal_direction="普通话低声独唱，短句清晰"),
        edit_need=MusicEditNeed.DIEGETIC_SONG, sung_lyrics="[Verse]\n等门开",
    ))
    assert direction.lyrics == "[Verse]\n等门开"
    assert "普通话低声独唱" in direction.tags
    assert "等门开" not in direction.tags
    assert not direction.instrumental


def test_oversized_prompt_is_rejected_without_silent_truncation():
    direction = direct_music(brief(design(instrumentation="钢琴" * 500)))
    with pytest.raises(AiVideoError):
        build_generation_argv(direction, dry_run=True)


def test_existing_imports_are_the_same_director():
    from ai_video.production import suno_music
    assert suno_music.SceneMusicBrief is SceneMusicBrief
    neutral = direct_music(brief())
    adapted = suno_music.direct_music(brief())
    assert adapted.model_dump(exclude={"model"}) == neutral.model_dump()
    assert adapted.model == "v6"
    assert "model" not in neutral.model_dump()
    assert generation_identity(adapted) == generation_identity(neutral)


def test_blank_design_is_not_a_substitute_for_a_musical_choice():
    with pytest.raises(ValidationError):
        design(pulse="  ")


def test_character_theme_and_model_choice_stay_at_their_owners():
    with pytest.raises(AiVideoError):
        direct_music(brief(design(role=MusicRole.CHARACTER_THEME)))
    from ai_video.production.suno_music import MusicDirection
    neutral = direct_music(brief(design()))
    wild = MusicDirection(**neutral.model_dump(), model="v6-wild")
    argv = build_generation_argv(wild, dry_run=True)
    assert argv[argv.index("--model") + 1] == "v6-wild"
    assert generation_identity(wild) != generation_identity(neutral)


def test_installed_cli_accepts_authored_direction_offline(tmp_path):
    from pathlib import Path
    from ai_video.production.suno_music import (
        CliTransport, SunoMusicService, music_qa_requirement,
    )
    executable = Path.home() / ".local/bin/suno"
    if not executable.is_file():
        pytest.skip("suno CLI is not installed")
    direction = direct_music(brief(design()))
    result = SunoMusicService(
        ledger_dir=tmp_path, transport=CliTransport(executable),
    ).dry_run(direction)
    assert result.submitted is False and result.charged is False
    assert result.model_verified_live is False
    assert result.external_model_key == "chirp-hawk"
    assert music_qa_requirement(direction).verdict == "NOT_EVALUATED"
