"""Pure reference-replica regressions from AI_daily 80abf28."""

import hashlib
import json
from types import SimpleNamespace

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.models import StateCommitStatus
from scripts.replica import align_lines, deliver, layers_kit, make_timeline, normalize_vo, redact, swap_layers, tts_run


def group(gid, start, duration, lines):
    return {"id": gid, "from": start, "dur": duration,
            "lines": [{"text": text, "from": a, "to": b} for text, a, b in lines]}


@pytest.fixture
def old_timeline():
    return [group("g01", 6, 100, [("a", 6, 50), ("b", 50, 106)]),
            group("g02", 116, 100, [("c", 116, 216)])]


def test_mapper_identity_when_nothing_changed(old_timeline):
    mapper, end = layers_kit.make_mapper(old_timeline, old_timeline, 230)
    assert end == 230
    for frame in (0, 6, 30, 50, 106, 116, 150, 216, 230):
        assert mapper(frame) == frame


def test_mapper_longer_group_shifts_later_shots_and_stretches_its_own(old_timeline):
    new = [group("g01", 6, 130, [("a", 6, 60), ("b", 60, 136)]),
           group("g02", 146, 100, [("c", 146, 246)])]
    mapper, end = layers_kit.make_mapper(old_timeline, new, 230)
    assert [mapper(frame) for frame in (50, 78, 116, 216)] == [60, 98, 146, 246]
    assert end == 260


def test_mapper_rewritten_group_only_anchors_its_block(old_timeline):
    new = [old_timeline[0], group("g02", 116, 160, [("c1", 116, 180), ("c2", 180, 276)])]
    mapper, end = layers_kit.make_mapper(old_timeline, new, 230, rewritten={"g02": (116, 216, 116, 276)})
    assert mapper(216) == 276
    assert end == 290


def test_mapper_shared_edge_follows_the_next_line_start_regardless_of_order():
    old = [group("g01", 0, 100, [("b", 50, 100), ("a", 0, 50)])]
    new = [group("g01", 0, 120, [("b", 60, 120), ("a", 0, 45)])]
    mapper, _ = layers_kit.make_mapper(old, new, 100)
    assert mapper(50) == 60


def test_mapper_rejects_missing_group_and_zero_length_shot(old_timeline):
    with pytest.raises(ValueError):
        layers_kit.make_mapper(old_timeline, old_timeline[:1], 230)
    with pytest.raises(ValueError):
        layers_kit.remap_phone([(50, 51, "A", 0, 1, [])], lambda frame: 60)


def test_remap_phone_keeps_source_span(old_timeline):
    new = [group("g01", 6, 200, [("a", 6, 100), ("b", 100, 206)]),
           group("g02", 216, 100, [("c", 216, 316)])]
    mapper, _ = layers_kit.make_mapper(old_timeline, new, 230)
    (start, end, _, _, rate, _), = layers_kit.remap_phone([(50, 106, "A", 10.0, 1.0, [])], mapper)
    assert (start, end) == (100, 206)
    assert (end - start) / layers_kit.FPS * rate == pytest.approx((106 - 50) / layers_kit.FPS)


SRC = {"A": ("assets/a.mp4", 448, 960, 20.0)}


def test_tile_check_rejects_gap():
    phone = [(0, 10, "A", 0, 1, [])]
    with pytest.raises(ValueError):
        layers_kit.tile_check(phone, [(12, 20, "X", {})], 20)
    layers_kit.tile_check(phone, [(10, 20, "X", {})], 20)


def test_box_times_become_clip_frames():
    video, overlay = layers_kit.phone_clips([(30, 90, "A", 2.0, 2.0, [(1, 2, 11, 22, 3.0, 4.0)])], SRC, 0, 100)
    assert video[0]["trimStart"] == 60
    box = overlay[0]["props"]["boxes"][0]
    assert (box["from"], box["to"]) == (15, 30)
    assert (box["w"], box["h"]) == (10, 20)


def test_shot_reading_past_source_end_fails():
    with pytest.raises(ValueError):
        layers_kit.phone_clips([(0, 300, "A", 15.0, 1.0, [])], SRC, 0, 300)


def test_clip_crossing_a_part_edge_is_an_error():
    with pytest.raises(ValueError):
        layers_kit.phone_clips([(0, 40, "A", 0, 1, [])], SRC, 30, 60)
    with pytest.raises(ValueError):
        layers_kit.range_check([(30, 50, "A", 0, 1, [])], [], 30, 60)
    layers_kit.range_check([(30, 50, "A", 0, 1, []), (0, 30, "A", 0, 1, [])], [(50, 60, "X", {})], 30, 60)


def test_subtitle_hold_stops_at_next_group():
    first = dict(group("g01", 0, 100, [("一", 0, 90)]), src="x.wav")
    second = dict(group("g02", 102, 50, [("二", 102, 150)]), src="x.wav")
    subs, _ = layers_kit.voice_sub_clips({"g01": first, "g02": second}, ["g01", "g02"], str)
    assert [clip["duration"] for clip in subs] == [102, 54]


def test_range_filter_and_shift():
    shots = [(0, 30, "A", 0, 1, []), (30, 60, "A", 1, 1, [])]
    video, _ = layers_kit.phone_clips(shots, SRC, 30, 60)
    assert [clip["from"] for clip in layers_kit.shift(video, -30)] == [0]


def test_timeline_gaps_and_line_frames():
    groups = [{"id": "g01", "gap": 0}, {"id": "g02"}]
    timings = {"g01": {"lines": [{"text": "一", "start": 0.0, "end": 1.0}]},
               "g02": {"lines": [{"text": "二", "start": 0.5, "end": 2.0}]}}
    timeline = make_timeline.build(groups, timings, {"g01": 1.01, "g02": 2.0}, "assets/voice/v1/")
    assert (timeline[0]["from"], timeline[0]["dur"]) == (6, 31)
    assert timeline[1]["from"] == 6 + 31 + 10
    assert timeline[1]["lines"][0]["from"] == 47 + 15
    assert timeline[1]["src"] == "assets/voice/v1/g02.wav"


def characters(text):
    return [(char, index * 0.1, (index + 1) * 0.1) for index, char in enumerate(text)]


def test_spoken_text_wins_when_asr_writes_number_words():
    ratio, lines = align_lines.match_lines(["我选1000日元的，", "折合人民币46元。"],
                                           characters("我选一千日元的折合人民币四十六元"),
                                           "我选一千日元的，折合人民币四十六元。")
    assert ratio == 1.0
    assert lines[0]["end"] == pytest.approx(0.7)
    assert lines[1]["start"] == pytest.approx(0.7)
    assert lines[1]["chars"] == 9


def test_subtitle_text_kept_when_asr_writes_digits():
    ratio, lines = align_lines.match_lines(["我选1000日元的"], characters("我选1000日元的"), "我选一千日元的")
    assert (ratio, lines[0]["chars"]) == (1.0, 9)


def test_line_missing_from_say_is_reported():
    _, lines = align_lines.match_lines(["我选", "1000日元"], characters("我选"), "我选")
    assert [line["text"] for line in align_lines.weak_lines(lines)] == ["1000日元"]


def test_punctuation_only_line_takes_nothing():
    _, lines = align_lines.match_lines(["我选1000日元", "……"], characters("我选一千日元吧"), "我选一千日元吧")
    assert lines[1]["chars"] == 0
    assert align_lines.weak_lines(lines) == []
    assert lines[0]["end"] == pytest.approx(0.7)


def test_extra_word_at_edge_follows_the_clause_mark():
    say = "价格一千日元呢，很便宜"
    _, lines = align_lines.match_lines(["价格1000日元", "很便宜"], characters(align_lines.norm(say)), say)
    assert lines[0]["end"] == pytest.approx(0.7)


def test_ratio_tie_keeps_subtitle_alignment():
    _, lines = align_lines.match_lines(["甲乙"], characters("甲乙"), "甲乙")
    assert lines[0]["chars"] == 2


def test_unaligned_line_stops_the_build():
    timings = {"g01": {"lines": [{"text": "漏读的一句", "start": None, "end": None}]}}
    with pytest.raises(ValueError):
        make_timeline.build([{"id": "g01"}], timings, {"g01": 1.0}, "v/")


def test_weak_line_is_reported_even_when_group_ratio_is_high():
    lines = [{"text": "长句", "start": 0, "end": 1, "matched": 40, "chars": 40},
             {"text": "漏", "start": 1, "end": 2, "matched": 2, "chars": 8}]
    assert [line["text"] for line in align_lines.weak_lines(lines)] == ["漏"]


def test_redact_graph_resamples_and_covers_odd_sizes_and_edge_frames():
    graph, last = redact.filter_graph([[10, 20, 41, 51, 1.5, 2.5, "手机号"], [0, 0, 101, 10, 0.0, 4]])
    assert last == "v2"
    assert graph.startswith("[0:v]fps=30[v0]")
    assert "crop=32:32:9:19" in graph
    assert "crop=102:10:0:0" in graph
    assert "enable='between(t,1.467,2.533)'" in graph
    assert "enable='between(t,0.0,4.033)'" in graph
    assert "scale=7:2:flags=area" in graph
    assert "boxblur" not in graph


@pytest.fixture
def voice_plan():
    return {"episode_id": "replica", "voice": {"region": "cn", "voice_id": "test-voice", "speed_milli": 1000},
            "groups": [{"id": "g01", "lines": ["你好"], "say": "你好", "direction": "平实"}]}


def test_fingerprint_ignores_int_float_rate(voice_plan):
    group = voice_plan["groups"][0]
    other = dict(voice_plan, voice=dict(voice_plan["voice"], speed_milli=1000.0))
    assert tts_run.fingerprint(group, voice_plan) == tts_run.fingerprint(group, other)


def test_current_take_must_match_text(tmp_path, monkeypatch, voice_plan):
    group = voice_plan["groups"][0]
    stale_name = tts_run.take_name(dict(group, say="旧稿"), voice_plan)
    attempts = [SimpleNamespace(attempt_id=stale_name)]
    stale = tmp_path / f"{stale_name}.wav"
    stale.write_bytes(b"old take")
    project = SimpleNamespace(manifest=SimpleNamespace(attempts=attempts), asset_paths={f"voice-{stale_name}": stale})
    monkeypatch.setattr(normalize_vo, "load_voice_project", lambda *_: project)
    with pytest.raises(AiVideoError) as failure:
        normalize_vo.current_takes(voice_plan, tmp_path)
    assert failure.value.code is ErrorCode.AUDIO_ASSET_INVALID

    name = tts_run.take_name(group, voice_plan)
    receipt = SimpleNamespace(script_hash=hashlib.sha256(group["say"].encode()).hexdigest(),
                              model_id="speech-2.8-hd", voice_id="test-voice", language="Chinese",
                              destination="https://api.minimaxi.com")
    attempts.append(SimpleNamespace(attempt_id=name, status=StateCommitStatus.SUCCEEDED, voice_request=receipt))
    wanted = tmp_path / f"{name}.wav"
    wanted.write_bytes(b"exact take")
    project.asset_paths[f"voice-{name}"] = wanted
    assert normalize_vo.current_takes(voice_plan, tmp_path) == {"g01": wanted}


def test_swap_then_restore_removes_backup(tmp_path):
    main, part = tmp_path / "main", tmp_path / "part"
    for project, frames in ((main, 100), (part, 40)):
        project.mkdir()
        (project / "layers.json").write_text(json.dumps({"who": project.name}), encoding="utf-8")
        (project / "project.json").write_text(json.dumps({"durationInFrames": frames}), encoding="utf-8")
    swap_layers.main([str(main), str(part)])
    assert json.loads((main / "project.json").read_text())["durationInFrames"] == 40
    swap_layers.main([str(main), "--restore"])
    assert json.loads((main / "layers.json").read_text())["who"] == "main"
    assert not (main / ".full-backup").exists()


def test_srt_items_follow_subs_clips():
    layers = {"tracks": [{"id": "subs", "clips": [
        {"from": 100, "duration": 60, "props": {"lines": [{"text": "乙", "from": 0, "to": 20},
                                                       {"text": "丙", "from": 30, "to": 50}]}},
        {"from": 0, "duration": 40, "props": {"lines": [{"text": "甲", "from": 0, "to": 30}]}}]}]}
    assert deliver.srt_items(layers) == [(0, 40, "甲"), (100, 130, "乙"), (130, 160, "丙")]
    assert deliver.ts(3725) == "00:02:04,167"


def test_lines_get_times_from_matching_characters():
    ratio, lines = align_lines.match_lines(["今天天气好。", "我们出去玩！"], characters("今天天气好我们出去玩"))
    assert ratio == 1.0
    assert lines[0]["end"] == pytest.approx(0.5)
    assert lines[1]["start"] == pytest.approx(0.5)
    assert lines[1]["matched"] == 5
