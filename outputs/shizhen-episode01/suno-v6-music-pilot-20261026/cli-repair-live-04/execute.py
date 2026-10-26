"""One newly authorized CLI request; old receipts and limits remain immutable."""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

from ai_video.errors import AiVideoError
from ai_video.production.music_direction import MusicalDesign, MusicEditNeed, MusicRole, SceneMusicBrief
from ai_video.production.suno_music import (
    SunoMusicService, _envelope, build_generation_argv, direct_music,
    generation_identity, request_id_for,
)

UNIT = Path(__file__).resolve().parent
ROOT = UNIT.parent
HISTORY = (ROOT / "request-01/consume.json", ROOT / "request-02/consume.json", ROOT / "manual-request-03/consume.json")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())


def direction():
    return direct_music(SceneMusicBrief(
        cue_id="evidence-turn-cli-repair-04", scene_id="Scene04 修复台：两个源文件的缺口",
        script_excerpt="不同设备、不同日期，还是同一个时刻。林序坐直，摸到咖啡拉环，却没有拉开。拨出前停住，改成文字：你明早帮我看两个源文件。别转码。",
        emotion="技术确信转向自我怀疑；保持求证，不下超自然结论",
        scene_facts="只根据批准剧本设计，本cue没有已审听对应成片；键鼠、咖啡拉环和手机操作应保持前景。",
        edit_need=MusicEditNeed.UNDERSCORE, dialogue_present=True,
        musical_design=MusicalDesign(
            role=MusicRole.INSTRUMENTAL_BED,
            narrative_function="在证据无法解释缺口之后，让观众感到林序第一次怀疑自己的判断，不预告妹妹或怪物。",
            style="克制的当代室内乐与极简电子质感，理性表面下逐渐失去稳定感",
            instrumentation="弱音中提琴的薄层泛音缓慢分离，低音单簧管偶尔用相邻两音作不完整回答；轻微暗色电子底层只衔接呼吸，不以低频重击制造恐怖",
            pulse="没有稳定鼓点，自由呼吸和不等长空隙，音符之间容许环境声独立存在",
            development="近乎空白的起始，先出现孤立而清楚的音；温和的声部逐渐失去同一重心，压力来自缓慢偏离而非越来越响；随后减少声音，让未解决的尾音变薄并自行消失",
            mix_intent="干而近的细节，有限室内残响，稀疏中频与动态余量，避免盖住人物呼吸和设备操作",
            continuity="保留空位与未完成回答的系列写作意图；不声称与未审听的既有A/B拥有同一旋律",
            exclusions="vocals, humming, spoken word, choir, drums, jump-scare stingers, trailer hits, heroic brass, sentimental climax, pop chorus",
            listening_checks=("压力是否来自理性松动而非预告怪物", "是否有实际可退让的空隙", "尾音是否不迫使剪辑追随歌曲收束"),
        ),
    ))


class Transport:
    def run(self, argv, *, timeout_seconds):
        live = "generate" in argv and "--dry-run" not in argv
        if live:
            intent = json.loads((UNIT / "intent.json").read_text())
            expected = ["--json", "--no-browser", *build_generation_argv(direction(), dry_run=False)]
            if list(argv) != expected or intent["historical_hashes"] != {str(p.relative_to(ROOT)): sha(p) for p in HISTORY}:
                raise RuntimeError("Input/history mismatch; no submission")
            with (ROOT / ".execution.lock").open("a") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                write(UNIT / "consume.json", {
                    "consumed_at": datetime.now(timezone.utc).isoformat(), "logical_request_number": 4,
                    "previous_maximum": 3, "new_maximum": 4, "intent_sha256": sha(UNIT / "intent.json"),
                    "argv_sha256": hashlib.sha256(json.dumps(list(argv), ensure_ascii=False).encode()).hexdigest(),
                    "no_further_submissions": True,
                })
                result = subprocess.run(["suno", *argv], capture_output=True, text=True, timeout=timeout_seconds)
            raw = _envelope(result)
            data = raw.get("data") or []
            clips = data if isinstance(data, list) else data.get("clips", [])
            write(UNIT / "submit-transport.json", {
                "exit_code": result.returncode, "status": raw.get("status"),
                "error_code": (raw.get("error") or {}).get("code"),
                "clips": [{k: clip.get(k) for k in ("id", "title", "status", "model_name")} for clip in clips if isinstance(clip, dict)],
            })
            return result
        if list(argv) != ["--json", "--no-browser", "doctor"] and "--dry-run" not in argv:
            raise RuntimeError("Unsupported command")
        return subprocess.run(["suno", *argv], capture_output=True, text=True, timeout=timeout_seconds)


def main(action):
    d = direction()
    service = SunoMusicService(ledger_dir=ROOT / "service-ledger", transport=Transport())
    if action == "prepare":
        write(UNIT / "intent.json", {
            "authorization": "用户新增授权：授权我给你,可以继续生成测试。Parent限定新增1次CLI请求，累计3→4；不自动重试或追加。",
            "previous_maximum": 3, "new_maximum": 4, "logical_request_number": 4,
            "historical_hashes": {str(p.relative_to(ROOT)): sha(p) for p in HISTORY},
            "historical_unknowns_preserved": True, "old_stop_files_unchanged": True,
            "direction": d.model_dump(mode="json"), "request_id": request_id_for(d),
            "generation_identity": generation_identity(d), "argv": list(build_generation_argv(d, dry_run=False)),
            "budget_gate": "USER_DISABLED", "model": "v6", "no_video_or_audio_upload": True,
            "source_type": "approved_script_only", "quality": "NOT_EVALUATED",
            "concept_review": "Existing native reviewer: no findings; no hearing or film acceptance",
        })
        result = service.dry_run(d)
        write(UNIT / "dry-run.json", result.model_dump(mode="json"))
    elif action == "submit":
        if (UNIT / "consume.json").exists():
            raise RuntimeError("Request already consumed; never resubmit")
        try:
            result = service.submit(d, paid_generation_authorized=True)
            write(UNIT / "submit-result.json", result.model_dump(mode="json"))
        except (AiVideoError, OSError, RuntimeError, subprocess.TimeoutExpired) as error:
            write(UNIT / "STOP.json", {"type": type(error).__name__, "new_submissions_allowed": False})
            print(json.dumps({"status": "STOP", "type": type(error).__name__, "code": str(getattr(error, "code", "UNKNOWN"))}))
            raise SystemExit(2) from None
    else:
        raise ValueError("prepare or submit required")
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1])
