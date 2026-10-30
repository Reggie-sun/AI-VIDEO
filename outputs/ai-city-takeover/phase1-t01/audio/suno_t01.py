"""T01 / 第二階段共用配樂：導演音樂設計 → 既有 SunoMusicService（CLI）。

用法（倉庫根目錄）：
  PYTHONPATH=src uv run python outputs/ai-city-takeover/phase1-t01/audio/suno_t01.py --check
  PYTHONPATH=src uv run python outputs/ai-city-takeover/phase1-t01/audio/suno_t01.py --submit
預算：使用者 2026-10-30 批准 Suno ≤2 次生成、≤20 credits（見 logs/decisions.md）。
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ai_video.production.music_direction import (
    MusicalDesign, MusicEditNeed, MusicRole, SceneMusicBrief, direct_music,
)
from ai_video.production.suno_music import CliTransport, SunoMusicService, build_generation_argv

HERE = Path(__file__).resolve().parent

DESIGN = MusicalDesign(
    role=MusicRole.INSTRUMENTAL_BED,
    narrative_function=(
        "Carry the cold, patient inevitability of a machine quietly taking over a sleeping city at 3:47 a.m.; "
        "give the edit a clear pulse to cut on, hold tension through the takeover request, and release it on the "
        "takeover without triumph."
    ),
    style=(
        "dark cinematic electronic, minimal techno meets film score, nocturnal and cold, precise, restrained, "
        "120 BPM, 4/4"
    ),
    instrumentation=(
        "deep sub-bass pulse on every beat, tight dry kick, crisp closed hi-hats in sixteenths, one hypnotic analog "
        "synth arpeggio in a minor key, distant metallic textures, low sustained pad, a filtered noise riser into "
        "each drop, the drop lands on a heavy kick with a wide low synth chord"
    ),
    pulse="steady 120 BPM four on the floor from the first bar, clear downbeats, no rubato, no tempo change",
    development=(
        "starts on the beat with no long intro, builds tension over eight bars with a riser, hard drop on a downbeat, "
        "keeps the groove with small variations, sparse breakdown, second build and a bigger drop, clean ending"
    ),
    mix_intent="punchy and clean low end, kick and sub clearly separated, spacious, no harsh highs",
    exclusions=(
        "trailer braams, dubstep wobble, festival EDM lead, lo-fi, piano ballad, guitar, orchestral hits"
    ),
    listening_checks=(
        "前段是否有清楚可剪的拍點、riser 與 drop",
        "全曲是否完全沒有人聲、哼唱或念白",
        "drop 是否冷而克制，而不是勝利感或廉價預告片衝擊",
    ),
)

BRIEF = SceneMusicBrief(
    cue_id="ai-city-takeover-score",
    scene_id="ai-city-takeover",
    script_excerpt=(
        "凌晨3:47，霧中高架上全城最後一位人類司機被系統鎖定、請求接管、接管完成；"
        "隨後全城系統一個個被無聲接管，直到清晨。"
    ),
    emotion="冷靜、精密、壓迫的必然感",
    scene_facts="T01 取 10 秒窗（拍點→riser→drop）；第二階段取 25–30 秒窗；畫面中無對白。",
    edit_need=MusicEditNeed.UNDERSCORE,
    dialogue_present=False,
    musical_design=DESIGN,
)


def service() -> SunoMusicService:
    ledger = HERE / "suno-ledger"
    ledger.mkdir(exist_ok=True)
    return SunoMusicService(ledger_dir=ledger, transport=CliTransport(Path.home() / ".local/bin/suno"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="preflight + offline dry-run only")
    ap.add_argument("--submit", action="store_true", help="one authorized generation")
    args = ap.parse_args()
    direction = direct_music(BRIEF)
    print(json.dumps({"title": direction.title, "tags": direction.tags, "exclude": direction.exclude,
                      "argv": build_generation_argv(direction, dry_run=False)}, ensure_ascii=False, indent=1))
    svc = service()
    readiness = svc.preflight()
    print("preflight:", readiness.model_dump())
    if args.check:
        print("dry_run:", svc.dry_run(direction).model_dump())
        return 0
    if args.submit:
        if not readiness.ready:
            print("not ready; no submission")
            return 2
        result = svc.submit(direction, paid_generation_authorized=True)
        print("submit:", result.model_dump())
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
