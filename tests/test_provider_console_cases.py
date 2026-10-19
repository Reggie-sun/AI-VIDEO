from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from scripts import provider_console_cases


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _fixture_catalog(tmp_path: Path) -> tuple[dict[str, object], dict[str, bytes]]:
    media: dict[str, bytes] = {
        "raw": b"raw-video",
        "cleaned": b"cleaned-preview",
        "robot": b"robot-edited-preview",
        "seedance": b"seedance-output",
    }
    media_hash = {key: hashlib.sha256(value).hexdigest() for key, value in media.items()}
    outcomes = ["PASS"] * 5 + ["FAIL"] + ["NOT_EVALUATED"] * 9
    answers = {
        "interaction_ref": "raw-interaction",
        "observations": [
            {"requirement_id": f"raw-{index}", "verdict": verdict}
            for index, verdict in enumerate(outcomes)
        ],
    }
    raw_presentation = {
        "interaction_ref": "raw-interaction",
        "analysis": {"artifact_sha256": media_hash["raw"], "size_bytes": len(media["raw"])},
        "items": [
            {"requirement_id": f"raw-{index}", "artifact_sha256": media_hash["raw"]}
            for index in range(15)
        ],
    }
    raw_record = {
        "attempt_id": "raw-attempt",
        "artifact_sha256": media_hash["raw"],
        "request_fingerprint": "raw-request",
    }
    cleaned_render = {
        "file_sha256": media_hash["cleaned"],
        "size_bytes": len(media["cleaned"]),
        "scope": "development_preview",
        "production_acceptance": "NOT_EVALUATED",
        "human_full_1x": "NOT_EVALUATED",
    }
    cleaned_review = {
        "artifact_sha256": media_hash["cleaned"],
        "review_status": "COMPLETED_SCOPED_MEDIA_REVIEW",
        "human_full_1x": "PENDING",
    }
    robot_render = {
        "output_sha256": media_hash["robot"],
        "output_size_bytes": len(media["robot"]),
        "scope": "development_preview",
        "production_acceptance": "NOT_EVALUATED",
    }
    robot_human = {
        "artifact_path": "runs/robot.mp4",
        "artifact_sha256": media_hash["robot"],
        "playback_rate_requested": 1.0,
        "user_reported_complete_watch_and_listen": True,
        "reported_scope": ["action", "final_turn", "sound"],
        "reported_verdict": "ACCEPTABLE",
        "product_qa_or_activation_written": False,
    }
    gate = {
        "overall_verdict": "PASS",
        "candidate": {
            "path": "runs/seedance.mp4",
            "sha256": media_hash["seedance"],
            "size_bytes": len(media["seedance"]),
            "provider": "seedance",
        },
        "required_findings": [{"verdict": "PASS"} for _ in range(8)],
    }
    activation = {
        "output_sha256": media_hash["seedance"],
        "output_size_bytes": len(media["seedance"]),
        "gate_path": "runs/seedance-gate.json",
        "gate_sha256": hashlib.sha256(_json_bytes(gate)).hexdigest(),
        "status": "activated_after_post_media_gate",
        "video_phase": "activate",
    }
    docs = {
        "runs/raw-answers.json": _json_bytes(answers),
        "runs/raw-presentation.json": _json_bytes(raw_presentation),
        "runs/raw-record.json": _json_bytes(raw_record),
        "runs/cleaned-render.json": _json_bytes(cleaned_render),
        "runs/cleaned-review.json": _json_bytes(cleaned_review),
        "runs/robot-render.json": _json_bytes(robot_render),
        "runs/robot-human.json": _json_bytes(robot_human),
        "runs/seedance-gate.json": _json_bytes(gate),
        "runs/seedance-activation.json": _json_bytes(activation),
    }
    for path, content in {**media, **docs}.items():
        target = tmp_path / (f"runs/{path}.mp4" if path in media else path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)

    validators = {
        "raw": [
            ("runs/raw-answers.json", "qa", "raw_answers"),
            ("runs/raw-presentation.json", "qa", "raw_presentation"),
            ("runs/raw-record.json", "record", "raw_rejection"),
        ],
        "cleaned": [
            ("runs/cleaned-render.json", "artifact", "cleaned_render"),
            ("runs/cleaned-review.json", "qa", "cleaned_review"),
        ],
        "robot": [
            ("runs/robot-render.json", "artifact", "robot_render"),
            ("runs/robot-human.json", "human", "robot_human"),
        ],
        "seedance": [
            ("runs/seedance-gate.json", "qa", "seedance_gate"),
            ("runs/seedance-activation.json", "record", "seedance_activation"),
        ],
    }
    catalog: dict[str, object] = {}
    ids = {
        "raw": "jieshi_s01_raw",
        "cleaned": "jieshi_s01_cleaned_preview",
        "robot": "robot_edited_preview",
        "seedance": "seedance_white_model_example",
    }
    for key, title, category in [
        ("raw", "Raw", "raw_generation"),
        ("cleaned", "Cleaned", "edited_preview"),
        ("robot", "Robot", "edited_preview"),
        ("seedance", "Seedance", "production_example"),
    ]:
        artifact_path = f"runs/{key}.mp4"
        proof_specs = []
        for path, kind, validator in validators[key]:
            data = docs[path]
            proof_specs.append(
                {
                    "path": path,
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "bytes": len(data),
                    "kind": kind,
                    "validator": validator,
                }
            )
            if validator == "seedance_activation":
                proof_specs[-1]["gate_path"] = "runs/seedance-gate.json"
                proof_specs[-1]["gate_sha256"] = hashlib.sha256(docs["runs/seedance-gate.json"]).hexdigest()
        catalog[key] = {
            "id": ids[key],
            "title": title,
            "description": f"{title} bounded evidence fixture",
            "category": category,
            **({"attempt_id": "raw-attempt"} if key == "raw" else {}),
            "artifact": {
                "path": artifact_path,
                "sha256": media_hash[key],
                "bytes": len(media[key]),
            },
            "proof_specs": proof_specs,
        }
    return catalog, {**media, **docs}


def _project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    catalog, _ = _fixture_catalog(tmp_path)
    monkeypatch.setattr(provider_console_cases, "CASE_CATALOG", tuple(catalog.values()))
    return provider_console_cases.project_delivery_cases(tmp_path)


def test_projects_four_bounded_case_types_from_exact_fixture_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    catalog, _ = _fixture_catalog(tmp_path)
    monkeypatch.setattr(provider_console_cases, "CASE_CATALOG", tuple(catalog.values()))
    before = {
        path.relative_to(tmp_path).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }

    document = provider_console_cases.project_delivery_cases(tmp_path)

    cases = {case["id"]: case for case in document["cases"]}
    assert set(cases) == {
        "jieshi_s01_raw",
        "jieshi_s01_cleaned_preview",
        "robot_edited_preview",
        "seedance_white_model_example",
    }
    assert cases["jieshi_s01_raw"]["quality"] == {
        "state": "failed",
        "pass": 5,
        "fail": 1,
        "not_evaluated": 9,
    }
    assert cases["jieshi_s01_raw"]["human"]["state"] == "not_evaluated"
    assert cases["jieshi_s01_cleaned_preview"]["artifact"]["state"] == "verified"
    assert cases["jieshi_s01_cleaned_preview"]["human"]["state"] == "not_evaluated"
    assert cases["robot_edited_preview"]["human"]["state"] == "bounded_acceptance"
    assert cases["robot_edited_preview"]["human"]["scope"] == "动作、最后转向、声音；用户报告完整 1× 听看"
    assert cases["seedance_white_model_example"]["quality"] == {
        "state": "bounded",
        "pass": 8,
        "fail": 0,
        "not_evaluated": 0,
    }
    assert cases["seedance_white_model_example"]["activation"]["state"] == "recorded"
    assert cases["seedance_white_model_example"]["qualification"]["state"] == "not_established"
    assert document["delivery"] == {
        "state": "not_established_in_reviewed_cases",
        "scope": "selected_case_audit",
        "autonomy": "not_measured",
    }
    after = {
        path.relative_to(tmp_path).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    assert after == before


def test_wrong_artifact_binding_makes_the_whole_case_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    catalog, _ = _fixture_catalog(tmp_path)
    raw = catalog["raw"]
    presentation = next(
        proof for proof in raw["proof_specs"] if proof["validator"] == "raw_presentation"
    )
    path = tmp_path / presentation["path"]
    data = json.loads(path.read_text())
    data["items"][0]["artifact_sha256"] = "0" * 64
    changed = _json_bytes(data)
    path.write_bytes(changed)
    presentation["sha256"] = hashlib.sha256(changed).hexdigest()
    presentation["bytes"] = len(changed)
    monkeypatch.setattr(provider_console_cases, "CASE_CATALOG", tuple(catalog.values()))

    document = provider_console_cases.project_delivery_cases(tmp_path)

    raw_case = next(case for case in document["cases"] if case["id"] == "jieshi_s01_raw")
    assert raw_case["artifact"]["state"] == "verified"
    assert raw_case["quality"]["state"] == "unavailable"
    assert raw_case["proofs"][1]["state"] == "unavailable"
    assert document["delivery"]["state"] == "unavailable"


@pytest.mark.parametrize("mutation", ["tamper", "missing"])
def test_tampered_or_missing_proof_does_not_reuse_historical_verdict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    catalog, _ = _fixture_catalog(tmp_path)
    raw_proof = catalog["raw"]["proof_specs"][0]
    path = tmp_path / raw_proof["path"]
    if mutation == "tamper":
        path.write_bytes(path.read_bytes() + b" ")
    else:
        path.unlink()
    monkeypatch.setattr(provider_console_cases, "CASE_CATALOG", tuple(catalog.values()))

    document = provider_console_cases.project_delivery_cases(tmp_path)

    raw_case = next(case for case in document["cases"] if case["id"] == "jieshi_s01_raw")
    assert raw_case["quality"]["state"] == "unavailable"
    assert raw_case["qualification"]["state"] == "unavailable"


def test_symlink_and_parent_escape_are_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    catalog, _ = _fixture_catalog(tmp_path)
    outside = tmp_path.parent / "outside-proof.json"
    outside.write_text("{}", encoding="utf-8")
    raw = catalog["raw"]
    raw["artifact"]["path"] = "runs/raw-link.mp4"
    raw_link = tmp_path / raw["artifact"]["path"]
    raw_link.symlink_to(outside)
    raw["proof_specs"][0]["path"] = "../outside-proof.json"
    monkeypatch.setattr(provider_console_cases, "CASE_CATALOG", tuple(catalog.values()))

    document = provider_console_cases.project_delivery_cases(tmp_path)

    raw_case = next(case for case in document["cases"] if case["id"] == "jieshi_s01_raw")
    assert raw_case["artifact"]["state"] == "unavailable"
    assert raw_case["quality"]["state"] == "unavailable"
    assert raw_case["proofs"][0]["state"] == "unavailable"
