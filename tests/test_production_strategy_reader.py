from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.artifact_contracts import ArtifactReference
from ai_video.production.hashing import seal_artifact
from ai_video.production.production_strategy_materialization import prepare_strategy_commit
from ai_video.production.production_strategy_reader import (
    production_family_shot_ids,
    selected_shot_generation_acceptance,
    validate_production_lineage,
)
from ai_video.production.project import load_production_project
from ai_video.production.state_commit import (
    PreparedArtifact,
    ProductionStateCommitter,
    prepare_project_registry_commit,
)
from ai_video.production._state_commit_common import _canonical_yaml_bytes
from production_project_factory import write_production_project
from test_production_strategy_materialization import (
    _loaded_with_intent,
    _materialized_loaded,
)


def _persist_parent_authoring(tmp_path, loaded):
    """Make the otherwise in-memory authoring fixture a retained snapshot."""
    parent = loaded.shots[0]
    parent_path = Path(f"creative/shots/{parent.content_hash}.yaml")
    parent_ref = ArtifactReference(
        artifact_id=parent.artifact_id,
        revision=parent.revision,
        content_hash=parent.content_hash,
        path=parent_path,
    )
    project = seal_artifact(loaded.project.model_copy(update={
        "content_hash": "0" * 64,
        "artifacts": loaded.project.artifacts.model_copy(update={"shots": (parent_ref,)}),
    }))
    base = prepare_project_registry_commit(
        manifest=loaded.manifest,
        project=project,
        registry=loaded.registry,
        attempt_id="strategy-reader-authoring",
    )
    parent_payload = _canonical_yaml_bytes(parent)
    request = replace(base, artifacts=tuple(sorted(
        (*base.artifacts, PreparedArtifact(
            parent_path,
            parent_payload,
            hashlib.sha256(parent_payload).hexdigest(),
        )),
        key=lambda item: item.relative_path.as_posix(),
    )))
    ProductionStateCommitter(tmp_path).commit(request)
    reopened = load_production_project(tmp_path / "project.yaml")
    return reopened.model_copy(update={"qa_policy": loaded.qa_policy})


def test_in_memory_qa_cannot_replace_a_durably_selected_policy(tmp_path):
    loaded, decision = _loaded_with_intent(tmp_path)
    loaded = _persist_parent_authoring(tmp_path, loaded)
    request = prepare_strategy_commit(
        loaded=loaded, decision=decision, attempt_id="strategy-reader-commit"
    )
    with pytest.raises(AiVideoError, match="durable QA policy"):
        ProductionStateCommitter(tmp_path).commit(request)


def test_rejects_child_authoring_drift_after_parent_reopen(tmp_path):
    loaded, decision = _loaded_with_intent(tmp_path)
    request = prepare_strategy_commit(
        loaded=loaded, decision=decision, attempt_id="strategy-reader-drift"
    )
    materialized = _materialized_loaded(loaded, request).model_copy(
        update={"production_parents": (loaded.shots[0],)}
    )
    child = materialized.shots[0]
    changed = seal_artifact(child.model_copy(update={
        "content_hash": "0" * 64,
        "dialogue": "A replacement line that was not allocated.",
    }))
    drifted = materialized.model_copy(update={"shots": (changed,)})

    with pytest.raises(AiVideoError) as error:
        validate_production_lineage(drifted)
    assert error.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def test_legacy_project_has_no_lineage_requirement(tmp_path):
    write_production_project(tmp_path)
    reopened = load_production_project(tmp_path / "project.yaml")

    assert reopened.production_parents == ()
    assert production_family_shot_ids(reopened, "shot-1") == ("shot-1",)


@pytest.mark.parametrize("bad_first", [True, False])
def test_same_policy_hash_cannot_hide_a_tampered_child_pointer(tmp_path, bad_first):
    from ai_video.production_planning import ProductionPlanningService
    from ai_video.production.production_strategy_reader import load_production_allocation_policies
    from production_strategy_factory import make_persisted_strategy_fixture

    fixture = make_persisted_strategy_fixture(tmp_path)
    service = ProductionPlanningService(committer=fixture.committer)
    decision = service.prepare(parent_shot_id=fixture.parent_shot_id)
    service.materialize(decision=decision, attempt_id="allocation-pointer")
    loaded = load_production_project(tmp_path / "project.yaml")
    child = loaded.shots[0]
    pointer = child.production_lineage.allocation_policy
    bad = child.model_copy(update={"production_lineage": child.production_lineage.model_copy(
        update={"allocation_policy": pointer.model_copy(update={"file_sha256": "0" * 64})})})
    siblings = (bad, child) if bad_first else (child, bad)
    with pytest.raises(AiVideoError):
        load_production_allocation_policies(tmp_path, siblings)
