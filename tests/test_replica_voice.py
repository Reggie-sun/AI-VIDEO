from copy import deepcopy
from datetime import timedelta
import json
import os
from pathlib import Path
import subprocess
import sys
import wave

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.audio import VoicePricingSnapshot
from ai_video.production.hashing import canonical_sha256
from ai_video.production.minimax_speech import MiniMaxSpeechProviderPolicy
from ai_video.production.models import StateCommitStatus
from scripts.replica import normalize_vo, tts_run
from tests.paid_provider_support import NOW, paid_authorization
from tests.test_production_minimax_speech import _DummySecret, _FakeTransport, _response
from tests.test_production_voice_candidate import _toolchain


CFG = {
    "episode_id": "tutorial",
    "voice": {"region": "cn", "voice_id": "example"},
    "groups": [
        {"id": "g01", "lines": ["第1节。"], "say": "第一节。", "gap": 4},
        {"id": "g02", "lines": ["第2节。"], "say": "第二节。", "gap": 4},
    ],
}


def _authorize(preview, digest):
    assert len(digest) == 64
    return type(paid_authorization(preview)).create(
        **{
            **paid_authorization(preview).model_dump(exclude={"authorization_fingerprint"}),
            "budget_currency": "CNY",
            "expires_at": NOW + timedelta(minutes=5),
            "egress_policy_receipt_id": "test-egress",
        }
    )


def _operator(authorize):
    return tts_run.VoiceOperator(
        policy=MiniMaxSpeechProviderPolicy(
            provider_enabled=True, credential_reference_kind="secret_store",
            credential_reference_id="MINIMAX_SPEECH_CN_API_KEY", retention_mode="provider_standard",
            license_policy_decision="offline-fixture-use", license_allowed=True,
            use_policy_allowed=True, voice_authorization_verified=True,
            policy_receipt_id="fixture-policy", origin="https://api.minimaxi.com",
        ),
        pricing=VoicePricingSnapshot(snapshot_id="fixture-pricing", effective_date=NOW.date(), currency="CNY",
                                     pricing_unit="character", unit_price_microunits=1, minimum_billable_units=1),
        egress_receipt_id="test-egress", authorize=authorize,
    )


def _deny_cli_operator(*, episode_id, voice_root):
    return _operator(lambda *_: None)


def _run(root, transport, *, cfg=CFG, only=(), authorize=_authorize, digest=None):
    return tts_run.run_takes(
        cfg, root, approved_digest=digest or canonical_sha256(cfg), operator=_operator(authorize),
        transport=transport, credential=_DummySecret(), toolchain=_toolchain(), only=only, clock=lambda: NOW,
    )


def test_module_cli_accepts_imported_operator_and_applies_its_denial(tmp_path):
    root = Path(__file__).resolve().parents[1]
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps(CFG, ensure_ascii=False), encoding="utf-8")
    source_paths = os.pathsep.join(str(root / directory) for directory in ("src", "tests"))
    result = subprocess.run([
        sys.executable, "-m", "scripts.replica.tts_run", str(plan), str(tmp_path / "voice"), "g01",
        "--execute", "--approved-plan-sha256", canonical_sha256(CFG),
        "--runtime", "tests.test_replica_voice:_deny_cli_operator",
    ], cwd=root, env={**os.environ, "PYTHONPATH": source_paths}, capture_output=True, text=True, timeout=30)

    assert result.returncode == 1, result
    error = json.loads(result.stderr)
    assert error["code"] == ErrorCode.PAID_PROVIDER_AUTHORIZATION_REQUIRED
    assert "denied authority" in error["message"]


def _transport():
    class Transport(_FakeTransport):
        def request(self, request):
            def bind(data):
                data["trace_id"] = f"replica-test-{self.invocations}"
                data["extra_info"].update(usage_characters=4)

            self.response = _response(mutate=bind)
            return super().request(request)

    return Transport()


def test_exact_replay_and_only_changed_spoken_group(tmp_path):
    transport = _transport()
    first = _run(tmp_path, transport)
    assert transport.invocations == 2
    assert normalize_vo.current_takes(CFG, tmp_path) == first
    assert all(path.is_file() for path in first.values())
    procedural = normalize_vo.normalize(CFG, tmp_path, only=["g01"], ffmpeg=_toolchain().ffmpeg_path)
    assert procedural["g01"] == normalize_vo.processed_path(CFG["groups"][0], CFG, tmp_path)
    with wave.open(str(procedural["g01"])) as generated:
        assert (generated.getframerate(), generated.getnchannels(), generated.getsampwidth()) == (48_000, 2, 2)
    manifest = tts_run.voice_root(tmp_path) / "state" / "manifest.json"
    before = manifest.read_bytes()
    captions = deepcopy(CFG)
    captions["groups"][0]["lines"] = ["字幕修改。"]
    assert _run(tmp_path, transport, cfg=captions, authorize=lambda *_: pytest.fail("replay attempted authorization")) == first
    assert (transport.invocations, manifest.read_bytes()) == (2, before)

    changed = deepcopy(captions)
    changed["groups"][1]["say"] = "第二段。"
    assert normalize_vo.processed_path(changed["groups"][1], changed, tmp_path) != normalize_vo.processed_path(
        CFG["groups"][1], CFG, tmp_path,
    )
    result = _run(tmp_path, transport, cfg=changed, only=["g02"])
    assert set(result) == {"g02"} and transport.invocations == 3
    assert normalize_vo.current_takes(changed, tmp_path)["g01"] == first["g01"]


def test_timeout_and_edited_take_fail_closed(tmp_path):
    transport = _FakeTransport(error=TimeoutError("test"))
    with pytest.raises(AiVideoError) as unknown:
        _run(tmp_path, transport)
    assert unknown.value.code == ErrorCode.VOICE_PROVIDER_OUTCOME_UNKNOWN
    with pytest.raises(AiVideoError, match="unknown"):
        _run(tmp_path, transport)
    changed = deepcopy(CFG)
    changed["groups"][0]["say"] = "第一段。"
    with pytest.raises(AiVideoError, match="unresolved"):
        _run(tmp_path, transport, cfg=changed)
    assert transport.invocations == 1


def test_interrupted_transport_keeps_pending_attempt_and_intent(tmp_path):
    class Interrupted(BaseException):
        pass

    class Transport:
        calls = 0

        def request(self, request):
            self.calls += 1
            attempt = tts_run.load_voice_project(tmp_path, CFG).manifest.attempts[-1]
            assert attempt.status is StateCommitStatus.RUNNING
            assert attempt.paid_provider_state is not None
            raise Interrupted

    transport = Transport()
    with pytest.raises(Interrupted):
        _run(tmp_path, transport)
    with pytest.raises(AiVideoError, match="pending"):
        _run(tmp_path, transport)
    assert transport.calls == 1


def test_successful_wav_missing_is_not_rebilled(tmp_path):
    transport = _transport()
    wav = _run(tmp_path, transport, only=["g01"])["g01"]
    wav.unlink()
    with pytest.raises(AiVideoError):
        _run(tmp_path, transport, only=["g01"])
    assert transport.invocations == 1


def test_missing_approval_or_paid_authorization_before_running(tmp_path):
    transport = _transport()
    with pytest.raises(AiVideoError, match="approval evidence"):
        _run(tmp_path, transport, digest="0" * 64)
    assert not (tts_run.voice_root(tmp_path) / "project.yaml").exists()
    with pytest.raises(AiVideoError, match="denied authority"):
        _run(tmp_path, transport, authorize=lambda *_: None)
    attempts = tts_run.load_voice_project(tmp_path, CFG).manifest.attempts
    assert all(attempt.operation != "voice_generation" for attempt in attempts)
    assert transport.invocations == 0
