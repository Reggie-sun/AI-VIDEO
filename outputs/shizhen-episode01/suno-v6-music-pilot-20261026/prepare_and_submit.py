"""Task-local experiment driver; not a Production provider or activation path."""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

from ai_video.errors import AiVideoError
from ai_video.production.music_direction import MusicalDesign, MusicEditNeed, MusicRole, SceneMusicBrief, direct_music
from ai_video.production.suno_music import CliTransport, SunoMusicService, build_generation_argv, generation_identity, request_id_for, _envelope

ROOT = Path(__file__).resolve().parent
CLI = Path.home() / ".local/bin/suno"
MAX_REQUESTS = 3


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def stamp():
    return datetime.now(timezone.utc).isoformat()


def direction(number):
    common = dict(dialogue_present=True, character_id="linxu")
    if number == 1:
        return direct_music(SceneMusicBrief(
            cue_id="shizhen-ep01-absence", scene_id="监控与修复台",
            script_excerpt="录像呈现另一种顺序。两个无关源文件都从03:16:59跳到03:17:11。林序先核对证据，没有立刻相信超自然解释。",
            emotion="镇定逐渐失效，求证带来孤立", scene_facts="目前只有文字和分镜，异常段落没有实际视频。",
            edit_need=MusicEditNeed.UNDERSCORE, **common,
            musical_design=MusicalDesign(
                role=MusicRole.SUSPENSE_ATMOSPHERE,
                narrative_function="陪观众认真求证，再慢慢感觉现实少了一块；不预告怪物或妹妹。",
                style="当代都市心理悬疑的室内乐与极简电子声景，克制、亲近、未解决",
                instrumentation="中低音单簧管用短小的两个相邻音构成犹疑动机，弱音中提琴维持薄层，柔暗模拟低音只在乐句间呼吸；乐器各留空间",
                pulse="自由呼吸式稀疏脉冲，反复之间留不等长空隙，避免稳定舞曲鼓点",
                development="开始几乎空白，两个音反复试探；中段增加轻微拍频与未解决的和声压力，随后抽去低音留下同一动机；几次乐句间明显退开；结尾自然衰减但不解决",
                mix_intent="轻而清晰的干声细节，有限室内残响，保持中频对白空间，动态有余量",
                continuity="同一两个音的轮廓贯穿整段，不每次起新旋律；为后续在同一录音中选取铺垫与不安段落保留可剪接的间隙",
                exclusions="vocals, humming, choir, lyrics, drums, trailer hits, jump-scare stingers, heroic brass, pop chorus, triumphant ending",
                listening_checks=("不能在证据出现前宣告超自然答案", "同一录音的前后段能否听出相同动机", "乐句间退让是否真实存在，而不是只有Prompt写了静默"),
            ),
        ))
    if number == 2:
        return direct_music(SceneMusicBrief(
            cue_id="shizhen-ep01-sister", scene_id="林晚录像与旧照片",
            script_excerpt="妹妹先听画外，再轻声叫哥。林序知道这不是通话，随后看四年前的合照，说四年了。最后身份揭示退回真实雨声。",
            emotion="认出亲人的希望被危险压住，迟来的悲伤", scene_facts="目前只有文字和分镜，妹妹录像和旧照片段落没有实际视频。",
            edit_need=MusicEditNeed.THEME_STATEMENT, **common,
            musical_design=MusicalDesign(
                role=MusicRole.CHARACTER_THEME,
                narrative_function="让林序短暂认出亲人，同时给妹妹的呼吸与未说完的话让路，不替他提前哭泣。",
                style="私密、含蓄的当代室内乐情感配乐，温度与不安同时存在",
                instrumentation="毡音钢琴以两个相邻音缓慢问答，中提琴温和延长尾音，低音单簧管偶尔留下阴影；极少配器",
                pulse="自由速度，长呼吸和自然停顿，不用节拍器式节奏",
                development="先听到孤立的两音轮廓，温度只在中段短暂打开，旋律试图继续却停住；随后减少音符，在结尾留下干净可退回环境声的尾音，不做煽情高潮",
                mix_intent="近距离、安静而有清楚音头，中频稀疏，给低声中文对白让位，避免长混响遮住呼吸",
                continuity="保留两个相邻音与不完整回答这一写作意图；这是独立生成的关联假设，不能保证与前一曲同一旋律",
                exclusions="vocals, humming, choir, lyrics, percussion, lush romantic strings, sentimental climax, horror impact, pop chorus, resolved happy ending",
                listening_checks=("妹妹台词与呼吸不能被音乐抢走", "温度不应抹去危险，也不能把亲人重逢写成怪物来临", "最终身份反转不强配高潮"),
            ),
        ))
    raise ValueError("Third request is reserved for evidence-led repair, not automatic batch generation")


class OneUseTransport:
    def __init__(self, request_root, allowed_argv):
        self.unit = request_root
        self.allowed = tuple(allowed_argv)
        self.base = CliTransport(CLI)

    def run(self, argv, *, timeout_seconds):
        live = "generate" in argv and "--dry-run" not in argv
        if live:
            if (ROOT / "STOP.json").exists():
                resume_path = ROOT / "auth-repair-01/resume-request-02.json"
                if not resume_path.is_file() or list(ROOT.glob("STOP-request-*.json")):
                    raise RuntimeError("Experiment is stopped; no new submit before explicit recovery")
                resume = json.loads(resume_path.read_text())
                actual_hash = hashlib.sha256(json.dumps(list(argv), ensure_ascii=False).encode()).hexdigest()
                if resume["allowed_argv_sha256"] != actual_hash or resume["stop_sha256"] != hashlib.sha256((ROOT / "STOP.json").read_bytes()).hexdigest():
                    raise RuntimeError("Recovery authority does not match the exact new request/old stop")
                for relative, expected in resume["evidence_sha256"].items():
                    if hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != expected:
                        raise RuntimeError("Recovery evidence changed")
            if tuple(argv) != self.allowed:
                raise RuntimeError("Exact request differs from the sealed permit")
            with (ROOT / ".request-count.lock").open("a+") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                used = list(ROOT.glob("request-*/consume.json"))
                if len(used) >= MAX_REQUESTS:
                    raise RuntimeError("User request-count ceiling reached")
                payload = {"consumed_at": stamp(), "argv_sha256": hashlib.sha256(json.dumps(list(argv), ensure_ascii=False).encode()).hexdigest(), "request_index": len(used)+1}
                with (self.unit / "consume.json").open("x") as f:
                    os.chmod(f.name, 0o600)
                    json.dump(payload, f); f.flush(); os.fsync(f.fileno())
        result = self.base.run(argv, timeout_seconds=timeout_seconds)
        if live:
            try:
                # Validate the entire response before persisting even allowlisted fields.
                raw = _envelope(result)
                data = raw.get("data")
                clips = data if isinstance(data, list) else (data or {}).get("clips", [])
                safe = {"recorded_at": stamp(), "exit_code": result.returncode, "status": raw.get("status"), "error_code": (raw.get("error") or {}).get("code"), "clips": [{k:c[k] for k in ("id", "status", "title") if k in c} for c in clips if isinstance(c, dict)]}
            except Exception:
                safe = {"recorded_at": stamp(), "exit_code": result.returncode, "outcome": "unparseable_unknown"}
            write(self.unit / "transport-summary.json", safe)
        return result


def main():
    number = int(sys.argv[1]); action = sys.argv[2]
    d = direction(number)
    unit = ROOT / f"request-{number:02d}"
    unit.mkdir(exist_ok=True)
    live_argv = ("--json", "--no-browser", *build_generation_argv(d, dry_run=False))
    packet = {"schema": "task-local-suno-pilot/1", "created_at": stamp(), "source_type": "script_and_coverage_only", "source_video_for_this_cue": None, "direction": d.model_dump(mode="json"), "request_id": request_id_for(d), "generation_identity": generation_identity(d), "model": "v6", "sliders": "unset", "max_mode": False, "maximum_generation_requests": MAX_REQUESTS, "budget_gate": "disabled_by_explicit_user_instruction", "credential_access": "existing_CLI_owned_session_only", "egress": {"purpose": "text_music_generation", "argv": list(live_argv)}, "activation": "not_committed", "quality": "NOT_EVALUATED"}
    if action == "prepare":
        if (unit / "request.json").exists(): raise RuntimeError("Prepared request already exists; do not overwrite identity")
        write(unit / "request.json", packet)
        (unit / "style.txt").write_text(d.tags + "\n")
        (unit / "exclude.txt").write_text(d.exclude + "\n")
    else:
        prior=json.loads((unit / "request.json").read_text())
        if prior["generation_identity"] != packet["generation_identity"] or prior["egress"] != packet["egress"]:
            raise RuntimeError("Prepared input changed")
    service = SunoMusicService(ledger_dir=ROOT / "service-ledger", transport=OneUseTransport(unit, live_argv))
    if action == "prepare":
        result=service.dry_run(d); write(unit / "dry-run.json", result.model_dump(mode="json"))
    elif action == "submit":
        try:
            result=service.submit(d, paid_generation_authorized=True)
            write(unit / "submit-result.json", result.model_dump(mode="json"))
        except AiVideoError as exc:
            write(unit / "submit-error.json", {"code": str(exc.code), "message": str(exc), "stop": True})
            stop = ROOT / "STOP.json"
            if stop.exists():
                stop = ROOT / f"STOP-request-{number:02d}.json"
            write(stop, {"request_id": request_id_for(d), "code": str(exc.code), "recorded_at": stamp(), "new_submissions_allowed": False})
            print(json.dumps({"state": "STOP", "code": str(exc.code)})); return 2
    else: raise ValueError("Unknown action")
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
