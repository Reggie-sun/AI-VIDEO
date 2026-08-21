from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from ai_video.quality_intelligence.models import (
    BoundedFreeText,
    LogicalShotKey,
    PilotAttemptRosterPointer,
    PilotCaptureCohortPointer,
    PilotDatasetIndexEntry,
    PilotDatasetIndexV1,
    QualityRecordPointer,
)
from ai_video.quality_intelligence.store import _seal_content_model


def _projection_api():
    return importlib.import_module("ai_video.quality_intelligence.rag_projection")


def _index() -> PilotDatasetIndexV1:
    cohort = PilotCaptureCohortPointer(
        schema_version="1.0",
        pilot_id="pilot_a",
        relative_path="cohorts/pilot_a/cohort." + "a" * 64 + ".json",
        content_hash="b" * 64,
        file_sha256="a" * 64,
    )
    roster = PilotAttemptRosterPointer(
        schema_version="1.0",
        pilot_id="pilot_a",
        relative_path="rosters/pilot_a/roster." + "c" * 64 + ".json",
        content_hash="d" * 64,
        file_sha256="c" * 64,
    )
    shots = tuple(
        LogicalShotKey(
            project_id="project_001",
            scene_id="scene_001",
            shot_id=f"shot_{index:03d}",
        )
        for index in range(1, 5)
    )
    entries = tuple(
        PilotDatasetIndexEntry(
            record=QualityRecordPointer(
                record_kind="prospective_q0_attempt",
                schema_version="1.0",
                relative_path=(
                    f"records/sha256/{index:02x}/" + f"{index:064x}" + ".json"
                ),
                content_hash=f"{index + 10:064x}",
                file_sha256=f"{index:064x}",
                recorded_sequence=index,
                recorded_attempt_id=f"attempt_{index:03d}",
            ),
            experiment_id="exp_a",
            pilot_id="pilot_a",
            project_id="project_001",
            scene_id="scene_001",
            shot_id=f"shot_{index:03d}",
            attempt_id=f"attempt_{index:03d}",
            generation_id=f"generation_{index:03d}",
            attempt_sequence=index,
            provider_name="local_comfyui_video",
            provider_kind="local_video",
            profile_id="profile_v1",
            capability_id="local_i2v_720p",
            model_id="model_x_1",
            outcome="succeeded" if index != 2 else "known_failure",
            human_verdict="GO" if index != 2 else "NOT_REVIEWED",
            coverage_tags=("provider:local_video",),
        )
        for index in range(1, 5)
    )
    index = PilotDatasetIndexV1(
        pilot_id="pilot_a",
        dataset_purpose=BoundedFreeText(value="closed Q0 comparison"),
        rubric_id="visual_quality_v1",
        rubric_version="1.0.0",
        rubric_hash="f" * 64,
        capture_contract_version="qer_v1",
        created_at="2026-08-21T12:00:00Z",
        repository_commit="0" * 40,
        cohort=cohort,
        roster=roster,
        shot_keys=shots,
        entries=entries,
        coverage_tags=("baseline",),
        known_confounders=(),
    )
    return _seal_content_model(index)[0]


def test_projection_is_deterministic_sanitized_markdown_bytes() -> None:
    api = _projection_api()
    first = api.render_rag_projection(_index())
    second = api.render_rag_projection(_index())
    assert isinstance(first, bytes)
    assert first == second
    text = first.decode("utf-8")
    assert "authority = advisory_experience" in text
    assert "dataset_content_hash = " + _index().content_hash in text
    assert "record_file_sha256 = " + f"{1:064x}" in text
    assert "evidence_boundary = exact_typed_projection_only" in text


@pytest.mark.parametrize(
    "forbidden",
    [
        "prompt_text",
        "negative_prompt",
        "provider_response",
        "https://",
        "Authorization:",
        "/home/",
        "reviewer_id",
        "analyzer_payload",
    ],
)
def test_projection_excludes_forbidden_payload_classes(forbidden: str) -> None:
    rendered = _projection_api().render_rag_projection(_index()).decode("utf-8")
    assert forbidden not in rendered


def test_projection_has_no_filesystem_or_agent_memory_side_effect(tmp_path: Path) -> None:
    before = tuple(tmp_path.rglob("*"))
    rendered = _projection_api().render_rag_projection(_index())
    assert rendered
    assert tuple(tmp_path.rglob("*")) == before
    assert not (tmp_path / ".agent" / "memory" / "index").exists()


def test_projection_rejects_unsealed_dataset() -> None:
    index = _index().model_copy(update={"content_hash": None})
    with pytest.raises(Exception):
        _projection_api().render_rag_projection(index)


def test_projection_rejects_forged_dataset_content_hash() -> None:
    index = _index().model_copy(update={"content_hash": "e" * 64})
    with pytest.raises(Exception):
        _projection_api().render_rag_projection(index)


def test_projection_schema_rejects_sensitive_coverage_tag() -> None:
    payload = _index().model_dump(mode="json")
    payload["entries"][0]["coverage_tags"] = [
        "https://signed.example/?token=raw-secret"
    ]
    with pytest.raises(Exception) as exc_info:
        PilotDatasetIndexV1.model_validate(payload)
    assert "raw-secret" not in str(exc_info.value)
