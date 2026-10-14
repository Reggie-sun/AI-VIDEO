"""Remote image failures keep returned evidence and paid state joinable."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

from ai_video.errors import AiVideoError
from ai_video.production.image import ImageProvenanceReceipt
from ai_video.production.project import load_production_project
from ai_video.production.paths import (
    canonical_image_asset_path,
    canonical_image_receipt_path,
    canonical_image_result_path,
)
from ai_video.production.seedream import SEEDREAM_MODEL
from test_seedream_remote_image import NOW, png, setup


def _known_materialization_failure(root: Path, *, tamper: str | None = None):
    calls: list[httpx.Request] = []
    wire = png()

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(
            200,
            json={
                "model": SEEDREAM_MODEL,
                "data": [{"b64_json": base64.b64encode(wire).decode(), "size": "2048x1152"}],
            },
        )

    writer, call_bundle, provider, client = setup(root, respond)

    def fail_candidate(*_args):
        raise RuntimeError("deterministic local materialization failure")

    writer._image_candidate_preparer = fail_candidate
    with client, pytest.raises(AiVideoError):
        writer.generate_remote_image_asset(*call_bundle, provider)

    loaded = load_production_project(root / "project.yaml")
    request = call_bundle[0]
    attempt = next(item for item in loaded.manifest.attempts if item.attempt_id == request.attempt_id)
    result_path = next((root / "state/images/results").glob("*.json"))
    result_value = json.loads(result_path.read_bytes())
    receipt_path = next(
        path for path in (root / "state/images/receipts").glob("*.json")
        if json.loads(path.read_bytes()).get("output_asset_id") == request.output_asset_id
    )
    receipt = ImageProvenanceReceipt.model_validate_json(receipt_path.read_bytes())
    assert result_path == root / canonical_image_result_path(result_value["result_fingerprint"])
    assert receipt_path == root / canonical_image_receipt_path(receipt.content_hash)
    paths = {
        "result": result_path,
        "receipt": receipt_path,
        "png": root / canonical_image_asset_path(receipt.output_sha256),
    }
    if tamper is not None:
        target = paths[tamper]
        target.write_bytes(target.read_bytes() + b" ")

    return {
        "root": root,
        "writer": writer,
        "call_bundle": call_bundle,
        "request": request,
        "loaded": loaded,
        "attempt": attempt,
        "calls": calls,
        "result_fingerprint": result_value["result_fingerprint"],
        "receipt": receipt,
        "receipt_path": receipt_path,
        "result_path": result_path,
        "paths": paths,
        "manifest_bytes": (root / "state/manifest.json").read_bytes(),
        "manifest_revision": loaded.manifest.manifest_revision,
    }


def _close(case, **overrides):
    values = {
        "attempt_id": case["request"].attempt_id,
        "expected_manifest_revision": case["manifest_revision"],
        "result_fingerprint": case["result_fingerprint"],
        "image_receipt_hash": case["receipt"].content_hash,
        "actor_id": "codex-parent",
        "reason": "Known returned image failed local materialization.",
    }
    values.update(overrides)
    return case["writer"].close_remote_image_materialization_failure(**values)


def test_failure_model_is_sealed_and_pointer_path_is_canonical():
    from ai_video.production.image_materialization_failure import (
        ImageMaterializationFailure,
        ImageMaterializationFailurePointer,
    )
    from ai_video.production.hashing import canonical_sha256

    hashes = {key: "a" * 64 for key in (
        "request_fingerprint", "result_fingerprint", "image_receipt_hash",
        "output_sha256", "paid_submit_fingerprint", "base_project_hash",
        "base_registry_hash", "base_graph_hash",
    )}
    receipt = ImageMaterializationFailure.create(
        project_id="project-test",
        attempt_id="attempt-test",
        expected_manifest_revision=12,
        **hashes,
        actor_id="operator-test",
        reason="Known returned image failed local materialization.",
        recorded_at=NOW,
    )
    assert receipt.schema_version == "image-materialization-failure/1"
    assert receipt.content_hash == canonical_sha256(receipt)
    with pytest.raises(ValueError):
        ImageMaterializationFailure.model_validate({
            **receipt.model_dump(mode="python"),
            "reason": "changed after sealing",
        })

    pointer = ImageMaterializationFailurePointer(
        path=Path(f"state/images/materialization-failures/{receipt.content_hash}.json"),
        content_hash=receipt.content_hash,
        file_sha256="b" * 64,
    )
    assert pointer.path.name == f"{receipt.content_hash}.json"
    with pytest.raises(ValueError):
        ImageMaterializationFailurePointer(
            path=Path(f"state/images/materialization-failures/{'c' * 64}.json"),
            content_hash=receipt.content_hash,
            file_sha256="b" * 64,
        )
    with pytest.raises(ValidationError):
        ImageMaterializationFailure.create(
            project_id="project-test",
            attempt_id="attempt-test",
            expected_manifest_revision=12,
            **hashes,
            actor_id=" \t",
            reason="Known returned image failed local materialization.",
            recorded_at=NOW,
        )
    with pytest.raises(ValidationError):
        ImageMaterializationFailure.create(
            project_id="project-test",
            attempt_id="attempt-test",
            expected_manifest_revision=12,
            **hashes,
            actor_id="operator-test",
            reason=" \t",
            recorded_at=NOW,
        )


def test_known_returned_materialization_failure_closes_reopens_and_replays(tmp_path):
    case = _known_materialization_failure(tmp_path)
    from ai_video.production.image_materialization_failure import (
        ImageMaterializationFailure,
        load_retained_remote_image_result,
        verify_image_materialization_failure,
    )

    attempt = case["attempt"]
    assert attempt.status.value == "outcome_unknown"
    assert attempt.image_phase == "materialize"
    assert attempt.paid_provider_state.phase.value == "accepted"
    assert "image_materialization_failure" not in attempt.model_dump(mode="json")
    retained = load_retained_remote_image_result(
        tmp_path, attempt, case["result_fingerprint"], case["receipt"].content_hash
    )
    assert retained[0].request_fingerprint == case["request"].request_fingerprint
    assert retained[3].result_fingerprint == case["result_fingerprint"]
    assert retained[4].sha256 == case["receipt"].output_sha256
    assert retained[5] == case["receipt"]
    assert len(case["calls"]) == 1
    before = case["loaded"].manifest
    before_budget_path = before.active_paid_provider_budget.path
    before_budget = (tmp_path / before_budget_path).read_bytes()
    before_png = case["paths"]["png"].read_bytes()
    expected_revision = case["manifest_revision"]

    with pytest.raises(AiVideoError):
        _close(case, expected_manifest_revision=expected_revision - 1)
    assert (tmp_path / "state/manifest.json").read_bytes() == case["manifest_bytes"]

    closed = _close(case)
    closed_attempt = next(item for item in closed.attempts if item.attempt_id == attempt.attempt_id)
    pointer = closed_attempt.image_materialization_failure
    failure = ImageMaterializationFailure.model_validate_json((tmp_path / pointer.path).read_bytes())
    assert closed_attempt.status.value == "failed"
    assert closed_attempt.image_phase == "materialize"
    assert closed_attempt.finished_at == failure.recorded_at.isoformat()
    assert closed_attempt.error_code == "image_request_invalid"
    assert closed_attempt.provider_request_id == case["receipt"].provider_request_id
    assert closed.active_project == before.active_project
    assert closed.active_registry == before.active_registry
    assert closed.active_dependency_graph == before.active_dependency_graph
    assert closed.active_paid_provider_budget == before.active_paid_provider_budget
    assert (tmp_path / before_budget_path).read_bytes() == before_budget
    assert case["paths"]["png"].read_bytes() == before_png
    assert len(case["calls"]) == 1

    reopened = load_production_project(tmp_path / "project.yaml")
    reopened_attempt = next(item for item in reopened.manifest.attempts if item.attempt_id == attempt.attempt_id)
    assert reopened.manifest == closed
    verify_image_materialization_failure(reopened, reopened_attempt)
    assert _close(case) == closed
    assert len(case["calls"]) == 1
    assert (tmp_path / before_budget_path).read_bytes() == before_budget
    assert case["paths"]["png"].read_bytes() == before_png
    closed_manifest_bytes = (tmp_path / "state/manifest.json").read_bytes()

    for changed in ({"actor_id": "different-actor"}, {"reason": "different reason"},
                    {"expected_manifest_revision": expected_revision + 1}):
        with pytest.raises(AiVideoError):
            _close(case, **changed)
    assert (tmp_path / "state/manifest.json").read_bytes() == closed_manifest_bytes


@pytest.mark.parametrize("tamper", ["png", "result", "receipt"])
def test_close_rejects_tampered_retained_result_without_manifest_mutation(tmp_path, tamper):
    case = _known_materialization_failure(tmp_path, tamper=tamper)
    from ai_video.production.image_materialization_failure import load_retained_remote_image_result

    with pytest.raises((AiVideoError, ValueError)):
        load_retained_remote_image_result(
            tmp_path,
            case["attempt"],
            case["result_fingerprint"],
            case["receipt"].content_hash,
        )
    with pytest.raises(AiVideoError):
        _close(case)
    assert (tmp_path / "state/manifest.json").read_bytes() == case["manifest_bytes"]
    assert len(case["calls"]) == 1


def test_strict_reopen_rejects_tampered_failure_pointer_and_mixed_candidate(tmp_path):
    case = _known_materialization_failure(tmp_path)
    from ai_video.production.image_materialization_failure import verify_image_materialization_failure

    closed = _close(case)
    reopened = load_production_project(tmp_path / "project.yaml")
    attempt = next(item for item in reopened.manifest.attempts if item.attempt_id == case["request"].attempt_id)
    for tampered_attempt in (
        attempt.model_copy(update={"candidate_project": attempt.base_project}),
        attempt.model_copy(update={
            "candidate_image_asset_ids": (case["request"].output_asset_id,),
        }),
    ):
        with pytest.raises((AiVideoError, ValueError)):
            verify_image_materialization_failure(reopened, tampered_attempt)
    pointer = attempt.image_materialization_failure
    receipt_path = tmp_path / pointer.path
    receipt_path.write_bytes(receipt_path.read_bytes() + b" ")
    with pytest.raises(AiVideoError):
        load_production_project(tmp_path / "project.yaml")
    assert closed.manifest_revision == case["manifest_revision"] + 1


def test_public_recovery_retains_closed_result_and_old_request_cannot_submit(tmp_path):
    from ai_video.production._remote_image_reader import remote_image_wire_path
    from ai_video.production.image_materialization_failure import load_retained_remote_image_result
    from ai_video.production.state_commit import recover_production_state

    case = _known_materialization_failure(tmp_path)
    closed = _close(case)
    attempt = next(item for item in closed.attempts if item.attempt_id == case["request"].attempt_id)
    pointer = attempt.image_materialization_failure
    assert pointer is not None
    retained = load_retained_remote_image_result(
        tmp_path, attempt, case["result_fingerprint"], case["receipt"].content_hash
    )
    result = retained[3]
    assert result.remote_evidence is not None
    wire_path = remote_image_wire_path(result.remote_evidence, case["request"].provider_kind)
    report = recover_production_state(tmp_path)
    recovery_hashes = {item.path: item.sha256 for item in report.items}
    expected = {
        pointer.path: pointer.file_sha256,
        case["result_path"].relative_to(tmp_path): hashlib.sha256(
            case["result_path"].read_bytes()
        ).hexdigest(),
        case["receipt_path"].relative_to(tmp_path): hashlib.sha256(
            case["receipt_path"].read_bytes()
        ).hexdigest(),
        case["paths"]["png"].relative_to(tmp_path): hashlib.sha256(
            case["paths"]["png"].read_bytes()
        ).hexdigest(),
        wire_path: result.remote_evidence.wire_sha256,
    }
    for path, digest in expected.items():
        assert recovery_hashes[path] == digest
    assert report.manifest_revision_before == closed.manifest_revision
    assert report.manifest_revision_after == closed.manifest_revision

    class UnexpectedProvider:
        def preflight(self, *_args, **_kwargs):
            raise AssertionError("closed request must not reach Provider preflight")

        def generate(self, *_args, **_kwargs):
            raise AssertionError("closed request must not reuse a paid permit")

    with pytest.raises(AiVideoError):
        case["writer"].generate_remote_image_asset(*case["call_bundle"], UnexpectedProvider())
    assert len(case["calls"]) == 1
    assert load_production_project(tmp_path / "project.yaml").manifest == closed


def test_paid_unknown_without_a_retained_result_cannot_be_closed(tmp_path):
    calls = []

    def timeout(request):
        calls.append(request)
        raise httpx.ReadTimeout("unknown remote outcome")

    writer, call_bundle, provider, client = setup(tmp_path, timeout)
    with client, pytest.raises(AiVideoError):
        writer.generate_remote_image_asset(*call_bundle, provider)
    loaded = load_production_project(tmp_path / "project.yaml")
    attempt = next(item for item in loaded.manifest.attempts if item.attempt_id == call_bundle[0].attempt_id)
    assert attempt.status.value == "outcome_unknown"
    assert attempt.paid_provider_state.phase.value == "outcome_unknown"
    before = (tmp_path / "state/manifest.json").read_bytes()
    with pytest.raises(AiVideoError):
        writer.close_remote_image_materialization_failure(
            attempt_id=attempt.attempt_id,
            expected_manifest_revision=loaded.manifest.manifest_revision,
            result_fingerprint="a" * 64,
            image_receipt_hash="b" * 64,
            actor_id="codex-parent",
            reason="Known returned image failed local materialization.",
        )
    assert (tmp_path / "state/manifest.json").read_bytes() == before
    assert len(calls) == 1
