from datetime import timedelta

import pytest

from ai_video.production.paid_provider import (
    PaidProviderAuthorizationDecision,
    PaidProviderCallPreview,
    reserve_paid_provider_budget,
)
from tests.paid_provider_support import NOW, paid_authorization, paid_preview


def batch_preview(attempt_id):
    values = paid_preview(attempt_id=attempt_id).model_dump(exclude={"preview_fingerprint"})
    values.update(provider_kind="minimax-speech", model_id="speech-2.8-hd",
                  destination="https://api.minimax.io", billing_mode="minimax_speech_batch",
                  estimated_cost_upper_bound_microunits=None)
    return PaidProviderCallPreview.create(**values)


def batch_authorization(preview, limit=2):
    values = paid_authorization(preview).model_dump(exclude={"authorization_fingerprint"})
    values.update(project_budget_ceiling_microunits=None, per_call_ceiling_microunits=None,
                  voice_batch_submit_limit=limit, expires_at=NOW + timedelta(hours=1))
    return PaidProviderAuthorizationDecision.create(**values)


def test_batch_reserves_finite_calls_without_monetary_budget():
    ledger = None
    for attempt in ("voice-1", "voice-2"):
        preview = batch_preview(attempt)
        ledger, reservation = reserve_paid_provider_budget(
            ledger, preview=preview, authorization=batch_authorization(preview),
            reservation_id=attempt)
        assert reservation.actual_cost_microunits is None
        assert reservation.upper_bound_microunits is None
    assert ledger.committed_microunits is None
    assert ledger.available_microunits is None
    preview = batch_preview("voice-3")
    with pytest.raises(Exception, match="batch.*exhausted"):
        reserve_paid_provider_budget(ledger, preview=preview,
                                     authorization=batch_authorization(preview),
                                     reservation_id="voice-3")


def test_batch_mode_cannot_be_used_by_video():
    values = paid_preview(attempt_id="video").model_dump(exclude={"preview_fingerprint"})
    values.update(operation="video_generation", provider_kind="minimax-speech",
                  billing_mode="minimax_speech_batch", estimated_cost_upper_bound_microunits=None)
    with pytest.raises(ValueError):
        PaidProviderCallPreview.create(**values)


def test_legacy_batch_policy_hash_remains_exact():
    from ai_video.production.minimax_speech_batch import MiniMaxSpeechTestBatch
    batch = MiniMaxSpeechTestBatch(batch_id="legacy", scripts=("test",), source_reference="source")
    assert batch.policy_id == "speech-batch-9437345bc1af2857af529d4a552a145a7d04988ce9bbb9096f3e327c3bcf6f49"
    assert "region" not in batch.model_dump()
    assert MiniMaxSpeechTestBatch.model_validate_json(batch.model_dump_json()) == batch


@pytest.mark.parametrize("region", ["cn", "international"])
def test_cli_uses_region_bound_secret_and_endpoint(tmp_path, monkeypatch, capsys, region):
    import json
    import subprocess
    import sys
    from scripts import minimax_speech_batch as cli
    from ai_video.production.minimax_speech_batch import MiniMaxSpeechTestBatch, prepare_minimax_speech_test_project
    from tests.test_production_minimax_speech import _FakeTransport, _response

    source = tmp_path / "source"
    prepare_minimax_speech_test_project(source, MiniMaxSpeechTestBatch(
        batch_id="source", scripts=("test",), source_reference="fixture"))
    target = tmp_path / "target"
    transport = _FakeTransport(_response(mutate=lambda data: data["extra_info"].update(usage_characters=2)))
    monkeypatch.setattr(cli, "_HttpTransport", lambda: transport)
    original_run = subprocess.run
    lookups = []

    def run(argv, **kwargs):
        if argv[0] == "secret-tool":
            lookups.append(argv)
            return subprocess.CompletedProcess(argv, 0, b"TEST-SECRET", b"")
        return original_run(argv, **kwargs)

    monkeypatch.setattr(subprocess, "run", run)
    args = ["speech-batch", "--root", str(target), "--source-project", str(source / "project.yaml"), "--text", "你好"]
    if region != "cn":
        args += ["--region", region]
    monkeypatch.setattr(sys, "argv", args)
    cli.main()
    result = json.loads(capsys.readouterr().out)
    assert len(result["wav_files"]) == 1
    expected_reference = "MINIMAX_SPEECH_CN_API_KEY" if region == "cn" else "MINIMAX_SPEECH_API_KEY"
    assert lookups == [["secret-tool", "lookup", "application", "ai-video", "provider", "minimax-speech", "credential", expected_reference]]
    assert transport.calls[0].url == ("https://api.minimaxi.com/v1/t2a_v2" if region == "cn" else "https://api.minimax.io/v1/t2a_v2")
    gate = json.loads(next((target / "state/paid-provider/gates").glob("*.json")).read_bytes())
    assert gate["preview"]["secret_reference"]["reference_id"] == expected_reference
    assert "TEST-SECRET" not in json.dumps(gate)
    before = (target / "state/manifest.json").read_bytes()
    cli.main()
    assert transport.invocations == 1 and len(lookups) == 1
    assert (target / "state/manifest.json").read_bytes() == before


@pytest.mark.parametrize("region", [None, "cn"])
@pytest.mark.parametrize("relative_new_root", [False, True])
def test_real_entry_repeats_and_reopens_without_authorization_or_budget(tmp_path, monkeypatch, relative_new_root, region):
    import json
    from ai_video.production.minimax_speech_batch import MiniMaxSpeechTestBatch, run_minimax_speech_batch
    from ai_video.production.project import load_production_project
    from ai_video.production._paid_provider_project_reader import load_paid_provider_budget
    from tests.test_production_minimax_speech import _FakeTransport, _DummySecret, _response
    from tests.test_production_voice_candidate import _toolchain
    if relative_new_root:
        from pathlib import Path
        monkeypatch.chdir(tmp_path)
        tmp_path = Path("runs/new-voice-test")

    class Transport(_FakeTransport):
        def request(self, request):
            text = json.loads(request.body)["text"]
            self.response = _response(mutate=lambda data: data.update(
                trace_id=f"trace-{self.invocations}",
                extra_info={**data["extra_info"], "usage_characters": len(text)}))
            return super().request(request)

    batch = MiniMaxSpeechTestBatch(batch_id="batch-test", scripts=("什么？没报站啊。", "再试一次。"),
                                  source_reference="test-source", **({"region": region} if region else {}))
    transport = Transport()
    kwargs = dict(transport=transport, credential=_DummySecret(), toolchain=_toolchain(), clock=lambda: NOW)
    outputs = run_minimax_speech_batch(tmp_path, batch, **kwargs)
    assert len(outputs) == 2 and all(path.is_file() for path in outputs)
    assert transport.invocations == 2
    origin = "https://api.minimaxi.com" if region == "cn" else "https://api.minimax.io"
    assert all(call.url == origin + "/v1/t2a_v2" for call in transport.calls)
    loaded = load_production_project(tmp_path / "project.yaml")
    ledger = load_paid_provider_budget(tmp_path, loaded.manifest.active_paid_provider_budget)
    assert ledger.voice_batch_submit_limit == 2
    assert all(r.actual_cost_microunits is None for r in ledger.reservations)
    assert ledger.currency == ("CNY" if region == "cn" else "USD")
    before = (tmp_path / "state/manifest.json").read_bytes()
    assert run_minimax_speech_batch(tmp_path, batch, **kwargs) == outputs
    assert transport.invocations == 2
    assert (tmp_path / "state/manifest.json").read_bytes() == before
    other = batch.model_copy(update={"region": None if region == "cn" else "cn"})
    with pytest.raises(Exception, match="exact batch"):
        run_minimax_speech_batch(tmp_path, other, **kwargs)
    assert transport.invocations == 2
    assert (tmp_path / "state/manifest.json").read_bytes() == before


@pytest.mark.parametrize("region", [None, "cn"])
@pytest.mark.parametrize("failure", ["credential", "timeout", "malformed"])
def test_batch_stops_and_never_retries_known_failure_or_unknown(tmp_path, failure, region):
    from ai_video.production.minimax_speech_batch import MiniMaxSpeechTestBatch, run_minimax_speech_batch
    from ai_video.production.project import load_production_project
    from tests.test_production_minimax_speech import _FakeTransport, _DummySecret, _response
    from tests.test_production_voice_candidate import _toolchain

    class Credential(_DummySecret):
        def bearer_header(self):
            if failure == "credential":
                raise RuntimeError("SECRET MUST NOT APPEAR")
            return super().bearer_header()

    transport = _FakeTransport(_response(), error=TimeoutError() if failure == "timeout" else None)
    if failure == "malformed":
        from ai_video.production.minimax_speech import MiniMaxSpeechTransportResponse
        transport.response = MiniMaxSpeechTransportResponse(200, {"content-type": "application/json"}, b"{}")
    batch = MiniMaxSpeechTestBatch(batch_id="failure-test", scripts=("测试。", "下一句。"),
                                  source_reference="test-source", region=region)
    kwargs = dict(transport=transport, credential=Credential(), toolchain=_toolchain(), clock=lambda: NOW)
    with pytest.raises(Exception):
        run_minimax_speech_batch(tmp_path, batch, **kwargs)
    loaded = load_production_project(tmp_path / "project.yaml")
    attempts = [a for a in loaded.manifest.attempts if a.operation == "voice_generation"]
    assert len(attempts) == 1
    expected = "failed" if failure == "credential" else "outcome_unknown"
    assert attempts[0].status.value == expected
    assert "SECRET MUST NOT APPEAR" not in loaded.manifest.model_dump_json()
    count = transport.invocations
    with pytest.raises(Exception, match="explicit recovery"):
        run_minimax_speech_batch(tmp_path, batch, **kwargs)
    assert transport.invocations == count


def test_unknown_count_reservation_blocks_further_submits():
    from ai_video.production.paid_provider import apply_paid_provider_submit_receipt, PaidProviderSubmitReceipt
    preview = batch_preview("first")
    ledger, reservation = reserve_paid_provider_budget(None, preview=preview,
        authorization=batch_authorization(preview), reservation_id="first")
    receipt = PaidProviderSubmitReceipt.create(attempt_id="first", request_fingerprint=preview.request_fingerprint,
        preview_fingerprint=preview.preview_fingerprint, gate_receipt_fingerprint="1" * 64,
        reservation_id="first", outcome="outcome_unknown", external_effect_id=None, recorded_at=NOW)
    ledger = apply_paid_provider_submit_receipt(ledger, receipt)
    preview = batch_preview("second")
    with pytest.raises(Exception, match="unknown submit outcome"):
        reserve_paid_provider_budget(ledger, preview=preview, authorization=batch_authorization(preview),
                                     reservation_id="second")
