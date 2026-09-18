from __future__ import annotations

from pathlib import Path

from ai_video.production import (
    EcommerceJobNextAction,
    EcommerceProductionJobRequest,
)
from ai_video.production.ecommerce_job import EcommerceProductionJobService
from ai_video.production.ecommerce_job_compiler import (
    bootstrap_ecommerce_production_project,
    compile_ecommerce_production_handoff,
)
from ecommerce_job_factory import make_ecommerce_handoff


def _request(tmp_path: Path, *, handoff_id: str | None = None):
    handoff = make_ecommerce_handoff()
    request = EcommerceProductionJobRequest(
        schema_version="ecommerce-production-job-request/1",
        job_id="job-product-one",
        project_root=tmp_path.resolve(),
        handoff_id=handoff_id or handoff.handoff_id,
        expected_project_id="project-product-one",
        execution_policy_id=handoff.compile_profile.profile_id,
        delivery_profile_id=handoff.delivery_profile.profile_id,
        max_new_generation_attempts=2,
        max_repairs_per_shot=1,
    )
    return handoff, request


def test_inspect_empty_root_is_read_only_bootstrap_projection(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    handoff, request = _request(project_root)

    projection = EcommerceProductionJobService().inspect(request, handoff)

    assert projection.next_action is EcommerceJobNextAction.BOOTSTRAP_PROJECT
    assert projection.manifest_revision is None
    assert not project_root.exists()


def test_inspect_bootstrapped_state_requires_exact_reference_preparation(
    tmp_path: Path,
) -> None:
    handoff, request = _request(tmp_path)
    compiled = compile_ecommerce_production_handoff(
        handoff,
        expected_project_id=request.expected_project_id,
    )
    bootstrap_ecommerce_production_project(
        tmp_path,
        attempt_id="ecommerce-bootstrap-1",
        compiled=compiled,
    )
    before = {
        path.relative_to(tmp_path): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in tmp_path.rglob("*")
        if path.is_file()
    }

    first = EcommerceProductionJobService().inspect(request, handoff)
    second = EcommerceProductionJobService().inspect(request, handoff)
    after = {
        path.relative_to(tmp_path): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in tmp_path.rglob("*")
        if path.is_file()
    }

    assert first == second
    assert first.next_action is EcommerceJobNextAction.PREPARE_REFERENCES
    assert first.manifest_revision == 1
    assert first.next_shot_id is None
    assert after == before


def test_inspect_mismatched_request_identity_returns_typed_blocker(
    tmp_path: Path,
) -> None:
    handoff, request = _request(tmp_path, handoff_id="f" * 64)

    projection = EcommerceProductionJobService().inspect(request, handoff)

    assert projection.next_action is EcommerceJobNextAction.BLOCKED
    assert projection.blocker is not None
    assert projection.blocker.blocker_code == "ECOMMERCE_HANDOFF_IDENTITY_MISMATCH"
    assert projection.blocker.outcome_known is True


def test_inspect_partial_canonical_root_fails_closed(tmp_path: Path) -> None:
    handoff, request = _request(tmp_path)
    (tmp_path / "project.yaml").write_text("incomplete", encoding="utf-8")

    projection = EcommerceProductionJobService().inspect(request, handoff)

    assert projection.next_action is EcommerceJobNextAction.BLOCKED
    assert projection.blocker is not None
    assert projection.blocker.blocker_code == "ECOMMERCE_CANONICAL_STATE_INCOMPLETE"
