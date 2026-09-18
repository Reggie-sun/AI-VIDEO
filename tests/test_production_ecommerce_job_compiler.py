from __future__ import annotations

from pathlib import Path

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production import (
    EcommerceProductionCompileProfile,
    EcommerceProductionHandoff,
    EcommerceUnsupportedGap,
    load_production_project,
)
from ai_video.production.ecommerce_job_compiler import (
    bootstrap_ecommerce_production_project,
    compile_ecommerce_production_handoff,
)
from ecommerce_job_factory import make_ecommerce_handoff


def test_compiler_builds_exact_asset_free_canonical_bootstrap_bundle() -> None:
    handoff = make_ecommerce_handoff()

    compiled = compile_ecommerce_production_handoff(
        handoff,
        expected_project_id="project-product-one",
    )

    assert compiled.project.project_id == "project-product-one"
    assert compiled.project.delivery_profile.width == 1080
    assert tuple(item.shot_id for item in compiled.shots) == ("shot-hero",)
    assert compiled.registry.assets == ()
    assert {item.relative_path for item in compiled.artifacts} == {
        compiled.project.artifacts.brief.path,
        compiled.project.artifacts.story.path,
        compiled.project.artifacts.storyboard.path,
        *(item.path for item in compiled.project.artifacts.characters),
        *(item.path for item in compiled.project.artifacts.scenes),
        *(item.path for item in compiled.project.artifacts.shots),
    }


def test_compiler_rejects_visual_layout_drift() -> None:
    handoff = make_ecommerce_handoff()
    drifted = handoff.model_copy(
        update={
            "artifact_proposals": handoff.artifact_proposals.model_copy(
                update={"shots": ()}
            )
        }
    )

    with pytest.raises(AiVideoError) as raised:
        compile_ecommerce_production_handoff(
            drifted,
            expected_project_id="project-product-one",
        )

    assert raised.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID
    assert "layout" in raised.value.user_message.lower()


def test_compiler_rejects_unresolved_runtime_gap() -> None:
    handoff = make_ecommerce_handoff()
    unresolved_compile_profile = EcommerceProductionCompileProfile.create(
        delivery_profile_id=handoff.delivery_profile.profile_id,
        visual_system_profile_id=handoff.visual_system_profile.profile_id,
        layout_plan_id=handoff.layout_plan.layout_plan_id,
        requirement_resolutions=(),
    )
    unresolved = EcommerceUnsupportedGap(
        gap_id="gap-product-integration",
        classification="REQUIRES_RUNTIME_CAPABILITY",
        requirement_ids=("req-ad-graphics",),
        blocker_code="ECOMMERCE_PRODUCT_INTEGRATION_UNRESOLVED",
        rationale="The product integration has no accepted execution path.",
    )
    values = {
        name: getattr(handoff, name)
        for name in type(handoff).model_fields
        if name not in {"handoff_id", "compile_profile", "unsupported_gaps"}
    }
    unresolved_handoff = EcommerceProductionHandoff.create(
        **values,
        compile_profile=unresolved_compile_profile,
        unsupported_gaps=(unresolved,),
    )

    with pytest.raises(AiVideoError, match="unresolved") as raised:
        compile_ecommerce_production_handoff(
            unresolved_handoff,
            expected_project_id="project-product-one",
        )

    assert raised.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def test_bootstrap_uses_canonical_committer_and_exact_replay_is_zero_write(
    tmp_path: Path,
) -> None:
    handoff = make_ecommerce_handoff()
    compiled = compile_ecommerce_production_handoff(
        handoff,
        expected_project_id="project-product-one",
    )

    first = bootstrap_ecommerce_production_project(
        tmp_path,
        attempt_id="ecommerce-bootstrap-1",
        compiled=compiled,
    )
    before = {
        path.relative_to(tmp_path): path.stat().st_mtime_ns
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    replay = bootstrap_ecommerce_production_project(
        tmp_path,
        attempt_id="ecommerce-bootstrap-1",
        compiled=compiled,
    )
    after = {
        path.relative_to(tmp_path): path.stat().st_mtime_ns
        for path in tmp_path.rglob("*")
        if path.is_file()
    }

    assert replay == first
    assert after == before
    reopened = load_production_project(tmp_path / "project.yaml")
    assert reopened.project == compiled.project
    assert reopened.registry == compiled.registry


def test_bootstrap_rejects_divergent_existing_project_without_overwrite(
    tmp_path: Path,
) -> None:
    handoff = make_ecommerce_handoff()
    compiled = compile_ecommerce_production_handoff(
        handoff,
        expected_project_id="project-product-one",
    )
    bootstrap_ecommerce_production_project(
        tmp_path,
        attempt_id="ecommerce-bootstrap-1",
        compiled=compiled,
    )
    project_bytes = (tmp_path / "project.yaml").read_bytes()

    divergent = compile_ecommerce_production_handoff(
        handoff,
        expected_project_id="project-other",
    )
    with pytest.raises(AiVideoError):
        bootstrap_ecommerce_production_project(
            tmp_path,
            attempt_id="ecommerce-bootstrap-2",
            compiled=divergent,
        )

    assert (tmp_path / "project.yaml").read_bytes() == project_bytes
