from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import pytest

from ai_video.errors import AiVideoError
from ai_video.production.dependency import (
    build_dependency_graph,
    desired_fingerprints,
    resolve_dependency_state,
)
from ai_video.production.hashing import canonical_sha256, seal_artifact
from ai_video.production.models import (
    ActorIdentity,
    ApprovedRepairReceipt,
    NamedFingerprint,
    ProductionManifest,
    QaLayer,
    RepairAction,
    RepairAuthorization,
    RepairRequest,
    SourceReference,
    StateCommitAttempt,
)
from ai_video.production.project import load_production_project
from ai_video.production.review import validate_repair_scope
from ai_video.production.state_commit import (
    PreparedArtifact,
    ProductionStateCommitter,
    StateCommitRequest,
    _canonical_json_bytes,
    prepare_dependency_graph_transition,
)
from test_production_hyperframes import make_manifest_25_render_fixture
from test_production_review import _Manifest25ReviewFixture, _qa_policy


ZERO_HASH = "0" * 64
REPAIR_CLOSURE = (
    "composition:main",
    "timeline:main",
    "renderer-source:main",
    "render:main",
)


def _p7_attempts(manifest: ProductionManifest) -> tuple[StateCommitAttempt, ...]:
    return tuple(
        item for item in manifest.attempts if item.operation == "image_generation"
    )


@dataclass(frozen=True)
class _Manifest25RepairFixture:
    root: Path
    committer: ProductionStateCommitter
    repair_request: RepairRequest
    approval: ApprovedRepairReceipt
    baseline_states: dict[str, tuple[object, ...]]

    def load_manifest(self) -> ProductionManifest:
        return load_production_project(self.root / "project.yaml").manifest

    def _candidate_graph(self, *, forge_image_node: bool = False):
        graph = load_production_project(self.root / "project.yaml").dependency_graph
        assert graph is not None
        target_ids = {"composition:main"}
        if forge_image_node:
            target_ids.add(
                next(
                    item.node_id
                    for item in graph.nodes
                    if item.node_id.startswith("asset:image-")
                )
            )
        nodes = []
        for node in graph.nodes:
            if node.node_id not in target_ids:
                nodes.append(node)
                continue
            first, *rest = node.contributions
            changed = first.model_copy(
                update={
                    "fingerprint": canonical_sha256(
                        {
                            "repair": "base-e2e-layout",
                            "node_id": node.node_id,
                            "before": first.fingerprint,
                        }
                    )
                }
            )
            nodes.append(node.model_copy(update={"contributions": (changed, *rest)}))
        return build_dependency_graph(nodes, graph.edges)

    def state_commit_request(
        self,
        approved_pointer,
        *,
        forge_image_node: bool = False,
    ) -> StateCommitRequest:
        manifest = self.load_manifest()
        graph = self._candidate_graph(forge_image_node=forge_image_node)
        states = resolve_dependency_state(graph, manifest.dependency_states).states
        transition = prepare_dependency_graph_transition(
            expected_manifest_revision=manifest.manifest_revision,
            base_dependency_graph=manifest.active_dependency_graph,
            candidate_graph=graph,
            candidate_dependency_states=states,
            expected_desired_fingerprints=desired_fingerprints(graph),
        )
        artifacts = []
        for pointer in (
            manifest.active_project,
            manifest.active_registry,
            transition.candidate_dependency_graph,
        ):
            if pointer == transition.candidate_dependency_graph:
                payload = _canonical_json_bytes(graph)
            else:
                payload = (self.root / pointer.path).read_bytes()
            artifacts.append(
                PreparedArtifact(
                    pointer.path,
                    payload,
                    hashlib.sha256(payload).hexdigest(),
                )
            )
        return StateCommitRequest(
            attempt_id=(
                "base-e2e-forged-repair"
                if forge_image_node
                else "base-e2e-layout-repair"
            ),
            operation="repair",
            expected_manifest_revision=manifest.manifest_revision,
            artifacts=tuple(sorted(artifacts, key=lambda item: item.relative_path.as_posix())),
            next_project=manifest.active_project,
            next_registry=manifest.active_registry,
            approved_repair_receipt=approved_pointer,
            dependency_graph_transition=transition,
        )

    def actual_invalidated_nodes(self, manifest: ProductionManifest) -> tuple[str, ...]:
        return tuple(
            sorted(
                item.node_id
                for item in manifest.dependency_states
                if self.baseline_states[item.node_id][0] != item.desired_fingerprint
            )
        )

    def unchanged_media_nodes(
        self, manifest: ProductionManifest
    ) -> dict[str, tuple[object, ...]]:
        return {
            item.node_id: (
                item.desired_fingerprint,
                item.applied_fingerprint,
                item.lifecycle,
                item.applied_evidence,
            )
            for item in manifest.dependency_states
            if item.node_id not in REPAIR_CLOSURE
        }


def make_manifest_25_failed_layout_review_fixture(
    tmp_path: Path,
) -> _Manifest25RepairFixture:
    render_fixture = make_manifest_25_render_fixture(tmp_path)
    render_fixture.render()
    trusted = ActorIdentity(actor_id="base-e2e-reviewer", actor_kind="human")
    review_fixture = _Manifest25ReviewFixture(
        root=tmp_path,
        committer=ProductionStateCommitter(tmp_path),
        timeline=render_fixture.timeline,
        policy=_qa_policy(
            required_layers=(QaLayer.LAYOUT,),
            repair_authorities=(trusted,),
        ),
        review_layer=QaLayer.LAYOUT,
        review_fails=True,
    )
    before_policy = review_fixture.load_manifest()
    review_fixture.committer.activate_qa_policy(
        review_fixture.policy,
        expected_manifest_revision=before_policy.manifest_revision,
        attempt_id="base-e2e-failed-layout-policy",
    )
    review_pointer = review_fixture.run_required_review()
    manifest = review_fixture.load_manifest()
    assert manifest.active_dependency_graph is not None
    assert manifest.active_render_state is not None
    assert manifest.active_qa_policy is not None
    bundle = load_production_project(tmp_path / "project.yaml")
    assert bundle.render_state is not None
    actor = ActorIdentity(actor_id="codex", actor_kind="codex")
    action = RepairAction(
        kind="composition_layout",
        parameters_fingerprint=canonical_sha256({"layout": "safe-area-repair"}),
    )
    scope = canonical_sha256(
        {
            "repair_id": "base-e2e-layout-repair",
            "actor": actor.model_dump(mode="json"),
            "action": action.model_dump(mode="json"),
            "target_artifact_ids": ["composition-main"],
            "target_node_ids": ["composition:main"],
            "expected_invalidation_node_ids": list(REPAIR_CLOSURE),
        }
    )
    state_by_id = {item.node_id: item for item in manifest.dependency_states}
    request = seal_artifact(
        RepairRequest(
            artifact_id="repair-request-base-e2e-layout",
            revision=1,
            content_hash=ZERO_HASH,
            creation_receipt_id="repair-request-base-e2e-layout",
            source_provenance=(
                SourceReference(kind="derived", reference=review_pointer.review_id),
            ),
            repair_id="base-e2e-layout-repair",
            base_manifest_revision=manifest.manifest_revision,
            dependency_graph=manifest.active_dependency_graph,
            dependency_states_hash=canonical_sha256(
                {
                    "dependency_states": [
                        item.model_dump(mode="json")
                        for item in manifest.dependency_states
                    ]
                }
            ),
            render_state=manifest.active_render_state,
            render_output_sha256=bundle.render_state.output.file_sha256,
            timeline_fingerprint=bundle.render_state.timeline_fingerprint,
            qa_policy=manifest.active_qa_policy,
            review_receipt_ids=(review_pointer.review_id,),
            issue_ids=("caption-overflow",),
            evidence_ids=("review-evidence-manifest-25-layout",),
            root_cause_hypothesis="caption layout exceeds safe area",
            selected_repair_action=action,
            exact_target_artifact_ids=("composition-main",),
            exact_target_node_ids=("composition:main",),
            expected_invalidation_node_ids=REPAIR_CLOSURE,
            actor=actor,
            authorization=RepairAuthorization(
                authorization_id="base-e2e-layout-authorization",
                authorized=True,
                authorized_by=trusted,
                scope_fingerprint=scope,
            ),
            before_fingerprints=(
                NamedFingerprint(
                    name="composition:main",
                    fingerprint=state_by_id["composition:main"].desired_fingerprint,
                ),
            ),
        )
    )
    approval = seal_artifact(
        ApprovedRepairReceipt.model_validate(
            {
                **request.model_dump(mode="python"),
                "artifact_id": "approved-repair-base-e2e-layout",
                "content_hash": ZERO_HASH,
                "request_content_hash": request.content_hash,
            }
        )
    )
    baseline = {
        item.node_id: (
            item.desired_fingerprint,
            item.applied_fingerprint,
            item.lifecycle,
            item.applied_evidence,
        )
        for item in manifest.dependency_states
    }
    return _Manifest25RepairFixture(
        root=tmp_path,
        committer=ProductionStateCommitter(
            tmp_path, repair_authorizer=lambda _: trusted
        ),
        repair_request=request,
        approval=approval,
        baseline_states=baseline,
    )


def test_repair_scope_accepts_only_exact_affected_nodes():
    assert validate_repair_scope(
        expected_node_ids=("caption:a", "composition:a", "render:a"),
        actual_node_ids=("render:a", "caption:a", "composition:a"),
    ) == ("caption:a", "composition:a", "render:a")


def test_repair_scope_rejects_blanket_or_missing_invalidation():
    with pytest.raises(AiVideoError):
        validate_repair_scope(
            expected_node_ids=("caption:a", "render:a"),
            actual_node_ids=("caption:a", "render:a", "voice:unrelated"),
        )
    with pytest.raises(AiVideoError):
        validate_repair_scope(
            expected_node_ids=("caption:a", "render:a"),
            actual_node_ids=("render:a",),
        )


def test_manifest_25_generic_repair_uses_exact_p5_closure_and_preserves_assets(
    tmp_path: Path,
) -> None:
    fixture = make_manifest_25_failed_layout_review_fixture(tmp_path)
    before = fixture.load_manifest()
    approved_manifest = fixture.committer.record_approved_repair_receipt(
        fixture.repair_request,
        fixture.approval,
        expected_manifest_revision=before.manifest_revision,
        attempt_id="base-e2e-repair-approval",
    )

    forged = fixture.state_commit_request(
        approved_manifest.active_approved_repair,
        forge_image_node=True,
    )
    before_forged = fixture.load_manifest()
    with pytest.raises(AiVideoError):
        fixture.committer.commit(forged)
    assert fixture.load_manifest() == before_forged

    after = fixture.committer.commit(
        fixture.state_commit_request(approved_manifest.active_approved_repair)
    )

    assert after.schema_version == "2.5"
    assert _p7_attempts(after) == _p7_attempts(before)
    assert after.active_registry == before.active_registry
    assert set(fixture.actual_invalidated_nodes(after)) == set(REPAIR_CLOSURE)
    assert fixture.unchanged_media_nodes(after) == fixture.unchanged_media_nodes(before)
