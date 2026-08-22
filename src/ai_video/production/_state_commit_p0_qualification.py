from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import (
    P0QualificationPreparedReceiptPointer,
    ProductionManifest,
)
from ai_video.production.paths import (
    _read_regular_file_nofollow,
    canonical_continuity_transition_policy_path,
    canonical_execution_stack_identity_path,
    canonical_p0_qualification_receipt_path,
    canonical_p0_qualification_input_path,
    canonical_real_shot_validation_set_path,
)
from ai_video.production.project import load_production_project
from ai_video.production.video_execution_stack import (
    ExecutionStackMaterialization,
    GenerationExecutionStackIdentity,
)
from ai_video.production.video_transition import (
    CandidateStackBinding,
    ContinuityTransitionPolicy,
    P0QualificationInput,
    P0QualificationPreparedReceipt,
    RealShotValidationSet,
)

from ._state_commit_common import _canonical_json_bytes, _state_invalid
from ._state_commit_contracts import PreparedArtifact


_ModelT = TypeVar("_ModelT", bound=BaseModel)


def _prepared_artifact(path: Path, model: BaseModel) -> PreparedArtifact:
    payload = _canonical_json_bytes(model)
    return PreparedArtifact(path, payload, hashlib.sha256(payload).hexdigest())


def _reseal_model(
    model: _ModelT,
    model_type: type[_ModelT],
    *,
    hash_field: str,
    updates: dict[str, object],
    exclude_defaults: bool = False,
) -> _ModelT:
    provisional = model.model_copy(update=updates)
    values = provisional.model_dump(mode="python")
    values[hash_field] = canonical_sha256(
        provisional.model_dump(
            mode="json",
            exclude={hash_field},
            exclude_defaults=exclude_defaults,
        )
    )
    return model_type.model_validate(values)


class _StateCommitP0QualificationMixin:
    def record_p0_qualification_prepared(
        self,
        receipt: P0QualificationPreparedReceipt,
        *,
        candidate_stacks: tuple[
            GenerationExecutionStackIdentity, GenerationExecutionStackIdentity
        ],
        policies: tuple[ContinuityTransitionPolicy, ...],
        validation_set: RealShotValidationSet,
        qualification_inputs: tuple[P0QualificationInput, ...],
        expected_manifest_revision: int,
        attempt_id: str,
    ) -> ProductionManifest:
        """Select immutable P0 inputs without claiming a winner or P6 verdict."""

        if not attempt_id:
            raise _state_invalid("P0 qualification prepared attempt ID is required.")
        if any(stack.materialization_status == "materialized" for stack in candidate_stacks):
            raise _state_invalid(
                "Materialized P0 qualification can only be written by its materialization owner."
            )
        self._validate_p0_bundle(
            receipt,
            candidate_stacks=candidate_stacks,
            policies=policies,
            validation_set=validation_set,
            qualification_inputs=qualification_inputs,
        )
        receipt_artifact = _prepared_artifact(
            canonical_p0_qualification_receipt_path(receipt.content_hash), receipt
        )
        pointer = P0QualificationPreparedReceiptPointer(
            path=receipt_artifact.relative_path,
            content_hash=receipt.content_hash,
            file_sha256=receipt_artifact.file_sha256,
        )
        artifacts = tuple(
            sorted(
                (
                    *(
                        _prepared_artifact(
                            canonical_execution_stack_identity_path(
                                stack.execution_stack_hash
                            ),
                            stack,
                        )
                        for stack in candidate_stacks
                    ),
                    *(
                        _prepared_artifact(
                            canonical_continuity_transition_policy_path(
                                policy.policy_hash
                            ),
                            policy,
                        )
                        for policy in policies
                    ),
                    _prepared_artifact(
                        canonical_real_shot_validation_set_path(
                            validation_set.content_hash
                        ),
                        validation_set,
                    ),
                    *(
                        _prepared_artifact(
                            canonical_p0_qualification_input_path(
                                item.input_kind, item.content_hash
                            ),
                            item,
                        )
                        for item in qualification_inputs
                    ),
                    receipt_artifact,
                ),
                key=lambda item: item.relative_path.as_posix(),
            )
        )
        with self._exclusive_lock():
            manifest = self._read_manifest()
            if manifest.active_p0_qualification_prepared is not None:
                current = self._reopen_p0_pointer(
                    manifest.active_p0_qualification_prepared
                )
                if any(stack.materialization_status == "materialized" for stack in current[1]):
                    raise _state_invalid(
                        "Materialized P0 qualification can only be resealed by its materialization owner."
                    )
            if manifest.active_p0_qualification_prepared == pointer:
                reopened = self._reopen_p0_pointer(pointer)
                self._validate_p0_selection_current(
                    manifest,
                    reopened[0],
                    policies=reopened[2],
                    validation_set=reopened[3],
                )
                return manifest
            if manifest.manifest_revision != expected_manifest_revision:
                raise _state_invalid("P0 qualification base Manifest revision changed.")
            if manifest.schema_version != "2.11":
                raise _state_invalid("P0 qualification requires Production Manifest 2.11.")
            bundle = load_production_project(self._project_root / "project.yaml")
            if (
                bundle.manifest != manifest
                or receipt.project != manifest.active_project
                or receipt.registry != manifest.active_registry
            ):
                raise _state_invalid(
                    "P0 qualification receipt does not bind current Production state."
                )
            self._validate_p0_against_project(
                bundle,
                policies=policies,
                validation_set=validation_set,
            )
            for artifact in artifacts:
                self._write_immutable_artifact(artifact, attempt_id=attempt_id)
            updated = ProductionManifest.model_validate(
                manifest.model_copy(
                    update={
                        "manifest_revision": manifest.manifest_revision + 1,
                        "active_p0_qualification_prepared": pointer,
                    }
                ).model_dump(mode="python")
            )
            self._write_p6_manifest_atomic(updated)
            reopened = self._read_manifest()
            if reopened != updated:
                raise _state_invalid("P0 qualification Manifest did not reopen exactly.")
            self._reopen_p0_pointer(pointer)
            return reopened

    def reopen_p0_qualification_prepared(
        self,
        *,
        require_materialized: bool = False,
    ) -> tuple[
        P0QualificationPreparedReceipt,
        tuple[GenerationExecutionStackIdentity, GenerationExecutionStackIdentity],
        tuple[ContinuityTransitionPolicy, ...],
        RealShotValidationSet,
        tuple[P0QualificationInput, ...],
    ]:
        manifest = self._read_manifest()
        pointer = manifest.active_p0_qualification_prepared
        if manifest.schema_version != "2.11" or pointer is None:
            raise _state_invalid("No active P0 qualification prepared receipt exists.")
        reopened = self._reopen_p0_pointer(pointer)
        self._validate_p0_selection_current(
            manifest,
            reopened[0],
            policies=reopened[2],
            validation_set=reopened[3],
            require_materialized=require_materialized,
        )
        return reopened

    def materialize_p0_qualification(
        self,
        *,
        materializations: tuple[
            ExecutionStackMaterialization, ExecutionStackMaterialization
        ],
        expected_manifest_revision: int,
        attempt_id: str,
    ) -> ProductionManifest:
        """Materialize both P0 candidates and atomically reseal their evidence graph."""

        if not attempt_id:
            raise _state_invalid("P0 stack materialization attempt ID is required.")
        if tuple(item.candidate_label for item in materializations) != ("m0", "m1"):
            raise _state_invalid("P0 stack materialization requires ordered m0 and m1 inputs.")
        with self._exclusive_lock():
            manifest = self._read_manifest()
            pointer = manifest.active_p0_qualification_prepared
            if manifest.schema_version != "2.11" or pointer is None:
                raise _state_invalid("No active P0 qualification prepared receipt exists.")
            current = self._reopen_p0_pointer(pointer)
            receipt, stacks, policies, validation_set, inputs = current
            try:
                materialized_stacks = tuple(
                    stack.materialize(materialization)
                    for stack, materialization in zip(stacks, materializations, strict=True)
                )
            except ValueError as exc:
                raise _state_invalid(
                    f"P0 execution stack materialization is invalid: {exc}"
                ) from exc
            if any(
                stack.materialization_status != "materialized"
                for stack in materialized_stacks
            ):
                raise _state_invalid("P0 execution stack materialization is incomplete.")
            stack_hashes = tuple(sorted(stack.execution_stack_hash for stack in materialized_stacks))
            old_to_new = dict(
                zip(
                    (stack.execution_stack_hash for stack in stacks),
                    (stack.execution_stack_hash for stack in materialized_stacks),
                    strict=True,
                )
            )
            materialized_inputs = tuple(
                P0QualificationInput.create(
                    **{
                        **item.model_dump(mode="python"),
                        "execution_stack_hashes": stack_hashes,
                    }
                )
                for item in inputs
            )
            input_hashes = {
                item.input_kind: item.content_hash for item in materialized_inputs
            }
            materialized_policies = tuple(
                _reseal_model(
                    policy,
                    ContinuityTransitionPolicy,
                    hash_field="policy_hash",
                    updates={
                        "source_execution_stack_hash": old_to_new[
                            policy.source_execution_stack_hash
                        ],
                        "destination_execution_stack_hash": old_to_new[
                            policy.destination_execution_stack_hash
                        ],
                        "qa_policy_hash": input_hashes["rubric"],
                        "authoring_evidence_hash": input_hashes["human_freeze"],
                    },
                )
                for policy in policies
            )
            materialized_validation_set = _reseal_model(
                validation_set,
                RealShotValidationSet,
                hash_field="content_hash",
                updates={
                    "rubric_hash": input_hashes["rubric"],
                    "human_freeze_evidence_hash": input_hashes["human_freeze"],
                    "edges": tuple(
                        edge.model_copy(update={"policy_hash": policy.policy_hash})
                        for edge, policy in zip(
                            validation_set.edges, materialized_policies, strict=True
                        )
                    ),
                },
            )
            materialized_receipt = _reseal_model(
                receipt,
                P0QualificationPreparedReceipt,
                hash_field="content_hash",
                updates={
                    "inventory_receipt_hash": input_hashes["inventory"],
                    "calibration_fixture_hash": input_hashes["calibration_fixture"],
                    "rubric_hash": input_hashes["rubric"],
                    "effect_budget_hash": input_hashes["effect_budget"],
                    "human_freeze_evidence_hash": input_hashes["human_freeze"],
                    "validation_set_hash": materialized_validation_set.content_hash,
                    "policy_hashes": tuple(
                        sorted(policy.policy_hash for policy in materialized_policies)
                    ),
                    "candidate_stacks": tuple(
                        CandidateStackBinding(
                            label=label, execution_stack_hash=stack.execution_stack_hash
                        )
                        for label, stack in zip(
                            ("m0", "m1"), materialized_stacks, strict=True
                        )
                    ),
                },
            )
            self._validate_p0_bundle(
                materialized_receipt,
                candidate_stacks=(materialized_stacks[0], materialized_stacks[1]),
                policies=materialized_policies,
                validation_set=materialized_validation_set,
                qualification_inputs=materialized_inputs,
            )
            if (
                manifest.active_p0_qualification_prepared.content_hash
                == materialized_receipt.content_hash
            ):
                self._validate_p0_selection_current(
                    manifest,
                    materialized_receipt,
                    policies=materialized_policies,
                    validation_set=materialized_validation_set,
                    require_materialized=True,
                )
                return manifest
            if manifest.manifest_revision != expected_manifest_revision:
                raise _state_invalid("P0 materialization base Manifest revision changed.")
            if (
                receipt.project != manifest.active_project
                or receipt.registry != manifest.active_registry
            ):
                raise _state_invalid("P0 materialization evidence is stale for current Production state.")
            bundle = load_production_project(self._project_root / "project.yaml")
            self._validate_p0_against_project(
                bundle,
                policies=materialized_policies,
                validation_set=materialized_validation_set,
            )
            receipt_artifact = _prepared_artifact(
                canonical_p0_qualification_receipt_path(materialized_receipt.content_hash),
                materialized_receipt,
            )
            artifacts = tuple(
                sorted(
                    (
                        *(
                            _prepared_artifact(
                                canonical_execution_stack_identity_path(stack.execution_stack_hash),
                                stack,
                            )
                            for stack in materialized_stacks
                        ),
                        *(
                            _prepared_artifact(
                                canonical_continuity_transition_policy_path(policy.policy_hash),
                                policy,
                            )
                            for policy in materialized_policies
                        ),
                        _prepared_artifact(
                            canonical_real_shot_validation_set_path(
                                materialized_validation_set.content_hash
                            ),
                            materialized_validation_set,
                        ),
                        *(
                            _prepared_artifact(
                                canonical_p0_qualification_input_path(
                                    item.input_kind, item.content_hash
                                ),
                                item,
                            )
                            for item in materialized_inputs
                        ),
                        receipt_artifact,
                    ),
                    key=lambda item: item.relative_path.as_posix(),
                )
            )
            for artifact in artifacts:
                self._write_immutable_artifact(artifact, attempt_id=attempt_id)
            updated = ProductionManifest.model_validate(
                manifest.model_copy(
                    update={
                        "manifest_revision": manifest.manifest_revision + 1,
                        "active_p0_qualification_prepared": P0QualificationPreparedReceiptPointer(
                            path=receipt_artifact.relative_path,
                            content_hash=materialized_receipt.content_hash,
                            file_sha256=receipt_artifact.file_sha256,
                        ),
                    }
                ).model_dump(mode="python")
            )
            self._write_p6_manifest_atomic(updated)
            reopened = self._read_manifest()
            if reopened != updated:
                raise _state_invalid("P0 materialization Manifest did not reopen exactly.")
            self._reopen_p0_pointer(
                materialized_receipt_pointer := updated.active_p0_qualification_prepared
            )
            return reopened

    def _validate_p0_selection_current(
        self,
        manifest: ProductionManifest,
        receipt: P0QualificationPreparedReceipt,
        *,
        policies: tuple[ContinuityTransitionPolicy, ...],
        validation_set: RealShotValidationSet,
        require_materialized: bool = False,
    ) -> None:
        if (
            receipt.project != manifest.active_project
            or receipt.registry != manifest.active_registry
        ):
            raise _state_invalid(
                "P0 qualification receipt is stale for current Production state."
            )
        bundle = load_production_project(self._project_root / "project.yaml")
        if bundle.manifest != manifest:
            raise _state_invalid("P0 qualification Manifest did not reopen exactly.")
        self._validate_p0_against_project(
            bundle,
            policies=policies,
            validation_set=validation_set,
        )
        if require_materialized:
            reopened = self._reopen_p0_pointer(manifest.active_p0_qualification_prepared)
            if any(stack.materialization_status != "materialized" for stack in reopened[1]):
                raise _state_invalid("P0 execution stack is unmaterialized and cannot execute.")

    def _reopen_p0_pointer(
        self, pointer: P0QualificationPreparedReceiptPointer
    ) -> tuple[
        P0QualificationPreparedReceipt,
        tuple[GenerationExecutionStackIdentity, GenerationExecutionStackIdentity],
        tuple[ContinuityTransitionPolicy, ...],
        RealShotValidationSet,
        tuple[P0QualificationInput, ...],
    ]:
        receipt = self._read_p0_model(
            pointer.path,
            pointer.file_sha256,
            P0QualificationPreparedReceipt,
        )
        if receipt.content_hash != pointer.content_hash:
            raise _state_invalid("P0 qualification receipt pointer is inconsistent.")
        validation_set = self._read_p0_model(
            canonical_real_shot_validation_set_path(receipt.validation_set_hash),
            None,
            RealShotValidationSet,
        )
        policies = tuple(
            self._read_p0_model(
                canonical_continuity_transition_policy_path(edge.policy_hash),
                None,
                ContinuityTransitionPolicy,
            )
            for edge in validation_set.edges
        )
        stacks_by_label = tuple(
            self._read_p0_model(
                canonical_execution_stack_identity_path(binding.execution_stack_hash),
                None,
                GenerationExecutionStackIdentity,
            )
            for binding in receipt.candidate_stacks
        )
        candidate_stacks = (stacks_by_label[0], stacks_by_label[1])
        input_hashes = (
            receipt.inventory_receipt_hash,
            receipt.calibration_fixture_hash,
            receipt.rubric_hash,
            receipt.effect_budget_hash,
            receipt.human_freeze_evidence_hash,
        )
        input_kinds = (
            "inventory",
            "calibration_fixture",
            "rubric",
            "effect_budget",
            "human_freeze",
        )
        qualification_inputs = tuple(
            self._read_p0_model(
                canonical_p0_qualification_input_path(kind, content_hash),
                None,
                P0QualificationInput,
            )
            for kind, content_hash in zip(input_kinds, input_hashes, strict=True)
        )
        self._validate_p0_bundle(
            receipt,
            candidate_stacks=candidate_stacks,
            policies=policies,
            validation_set=validation_set,
            qualification_inputs=qualification_inputs,
        )
        return receipt, candidate_stacks, policies, validation_set, qualification_inputs

    def _read_p0_model(
        self,
        relative_path: Path,
        expected_file_sha256: str | None,
        model_type: type[_ModelT],
    ) -> _ModelT:
        try:
            snapshot = _read_regular_file_nofollow(
                self._project_root / relative_path,
                contained_by=self._project_root / "state",
            )
            if (
                expected_file_sha256 is not None
                and snapshot.file_sha256 != expected_file_sha256
            ):
                raise ValueError("file hash does not match selected pointer")
            return model_type.model_validate_json(snapshot.data)
        except (OSError, ValidationError, ValueError) as exc:
            raise _state_invalid(
                "P0 qualification evidence could not be reopened.", str(exc)
            ) from exc

    def _validate_p0_bundle(
        self,
        receipt: P0QualificationPreparedReceipt,
        *,
        candidate_stacks: tuple[
            GenerationExecutionStackIdentity, GenerationExecutionStackIdentity
        ],
        policies: tuple[ContinuityTransitionPolicy, ...],
        validation_set: RealShotValidationSet,
        qualification_inputs: tuple[P0QualificationInput, ...],
    ) -> None:
        if len(candidate_stacks) != 2:
            raise _state_invalid("P0 qualification requires exactly two candidate stacks.")
        if any(
            canonical_sha256(
                stack.model_dump(mode="json", exclude={"execution_stack_hash"})
            )
            != stack.execution_stack_hash
            for stack in candidate_stacks
        ):
            raise _state_invalid("P0 execution stack identity hash is invalid.")
        if any(
            canonical_sha256(policy.model_dump(mode="json", exclude={"policy_hash"}))
            != policy.policy_hash
            for policy in policies
        ):
            raise _state_invalid("P0 continuity transition policy hash is invalid.")
        if canonical_sha256(
            validation_set.model_dump(mode="json", exclude={"content_hash"})
        ) != validation_set.content_hash:
            raise _state_invalid("P0 real-Shot validation set hash is invalid.")
        if canonical_sha256(
            receipt.model_dump(mode="json", exclude={"content_hash"})
        ) != receipt.content_hash:
            raise _state_invalid("P0 qualification prepared receipt hash is invalid.")
        expected_input_kinds = (
            "inventory",
            "calibration_fixture",
            "rubric",
            "effect_budget",
            "human_freeze",
        )
        if tuple(item.input_kind for item in qualification_inputs) != expected_input_kinds:
            raise _state_invalid(
                "P0 qualification inputs must contain one canonical ordered set."
            )
        if any(
            canonical_sha256(item._content_hash_payload())
            != item.content_hash
            for item in qualification_inputs
        ):
            raise _state_invalid("P0 qualification input hash is invalid.")
        inputs_by_kind = {item.input_kind: item for item in qualification_inputs}
        inventory_payload = inputs_by_kind["inventory"].payload
        calibration_payload = inputs_by_kind["calibration_fixture"].payload
        inventory_components = {
            item["id"]: item for item in inventory_payload["components"]
        }
        expected_output_contract_hash = canonical_sha256(
            {
                "width": calibration_payload["target_canvas"][0],
                "height": calibration_payload["target_canvas"][1],
                "frames": calibration_payload["frame_count"],
                "fps": calibration_payload["fps"],
                "container": calibration_payload["output_container"],
                "crf": calibration_payload["output_crf"],
                "native_audio": calibration_payload["native_audio"],
            }
        )
        hybrid_component = inventory_components.get("hybrid-artifact-candidate-v1")
        if (
            hybrid_component is not None
            and (hybrid_component["presence"] == "present")
            != inventory_payload["hybrid_artifact_present"]
        ):
            raise _state_invalid(
                "P0 inventory Hybrid artifact presence is inconsistent."
            )
        statuses = {stack.materialization_status for stack in candidate_stacks}
        if len(statuses) != 1:
            raise _state_invalid("P0 candidate stacks must share one materialization state.")
        stack_hashes = tuple(sorted(stack.execution_stack_hash for stack in candidate_stacks))
        for stack in candidate_stacks:
            if (
                stack.materialization_status == "unmaterialized"
                and (
                    stack.profile_hash != "none"
                    or stack.compiler_hash != "none"
                    or stack.workflow_hash != "none"
                )
            ) or (
                stack.materialization_status == "materialized"
                and (
                    stack.profile_hash == "none"
                    or stack.compiler_hash == "none"
                    or stack.workflow_hash == "none"
                )
            ) or (
                stack.sampler_identity != calibration_payload["sampler"]
                or stack.scheduler_identity != calibration_payload["scheduler"]
                or stack.output_contract_hash != expected_output_contract_hash
            ):
                raise _state_invalid(
                    "P0 candidate stack is not bound to the frozen calibration contract."
                )
            for component in stack.components:
                inventory_component = inventory_components.get(component.component_id)
                if (
                    inventory_component is None
                    or inventory_component["presence"] != component.presence
                    or inventory_component["sha256"] != component.content_hash
                ):
                    raise _state_invalid(
                        "P0 candidate stack component is not bound to the frozen inventory."
                    )
        candidate_stack_hashes = {
            item.execution_stack_hash for item in candidate_stacks
        }
        if (
            receipt.inventory_receipt_hash
            != inputs_by_kind["inventory"].content_hash
            or receipt.calibration_fixture_hash
            != inputs_by_kind["calibration_fixture"].content_hash
            or receipt.rubric_hash != inputs_by_kind["rubric"].content_hash
            or receipt.effect_budget_hash
            != inputs_by_kind["effect_budget"].content_hash
            or receipt.human_freeze_evidence_hash
            != inputs_by_kind["human_freeze"].content_hash
            or validation_set.rubric_hash != inputs_by_kind["rubric"].content_hash
            or validation_set.human_freeze_evidence_hash
            != inputs_by_kind["human_freeze"].content_hash
            or receipt.validation_set_hash != validation_set.content_hash
            or receipt.rubric_hash != validation_set.rubric_hash
            or receipt.human_freeze_evidence_hash
            != validation_set.human_freeze_evidence_hash
            or tuple(binding.execution_stack_hash for binding in receipt.candidate_stacks)
            != tuple(stack.execution_stack_hash for stack in candidate_stacks)
            or receipt.policy_hashes
            != tuple(sorted(policy.policy_hash for policy in policies))
            or tuple(edge.policy_hash for edge in validation_set.edges)
            != tuple(policy.policy_hash for policy in policies)
            or validation_set.project != receipt.project
            or validation_set.registry != receipt.registry
            or any(
                policy.source_execution_stack_hash not in candidate_stack_hashes
                or policy.destination_execution_stack_hash
                not in candidate_stack_hashes
                or policy.qa_policy_hash != inputs_by_kind["rubric"].content_hash
                or policy.authoring_evidence_hash
                != inputs_by_kind["human_freeze"].content_hash
                for policy in policies
            )
        ):
            raise _state_invalid("P0 qualification evidence bindings are inconsistent.")
        if any(
            item.execution_stack_hashes
            != (stack_hashes if statuses == {"materialized"} else ())
            for item in qualification_inputs
        ):
            raise _state_invalid("P0 qualification inputs are stale for execution stacks.")

    def _validate_p0_against_project(
        self,
        bundle,
        *,
        policies: tuple[ContinuityTransitionPolicy, ...],
        validation_set: RealShotValidationSet,
    ) -> None:
        shots = {item.artifact_id: item for item in bundle.shots}
        validation_shots = {
            item.artifact_id: item for item in validation_set.shots
        }
        assets = {item.asset_id: item for item in bundle.registry.assets}
        characters = {item.artifact_id: item for item in bundle.characters}
        scenes = {item.artifact_id: item for item in bundle.scenes}
        if (
            validation_set.project != bundle.manifest.active_project
            or validation_set.registry != bundle.manifest.active_registry
            or validation_set.character.artifact_id not in characters
            or validation_set.scene.artifact_id not in scenes
        ):
            raise _state_invalid("P0 validation set does not select current artifacts.")
        selected_character = characters[validation_set.character.artifact_id]
        identities = (
            (validation_set.character, characters[validation_set.character.artifact_id]),
            (validation_set.scene, scenes[validation_set.scene.artifact_id]),
            *((identity, shots.get(identity.artifact_id)) for identity in validation_set.shots),
        )
        if any(
            artifact is None
            or identity.revision != artifact.revision
            or identity.content_hash != artifact.content_hash
            for identity, artifact in identities
        ):
            raise _state_invalid("P0 validation set artifact identity is stale.")
        for policy, edge in zip(policies, validation_set.edges, strict=True):
            if (
                policy.project != validation_set.project
                or policy.registry != validation_set.registry
                or policy.source_shot != validation_shots.get(edge.source_shot_id)
                or policy.target_shot != validation_shots.get(edge.target_shot_id)
            ):
                raise _state_invalid("P0 transition policy does not bind its validation edge.")
            for anchor in policy.anchors:
                if anchor.source_kind == "registered_asset":
                    asset = assets.get(anchor.source_identity)
                    if (
                        asset is None
                        or anchor.content_hash != asset.sha256
                        or anchor.evidence_fingerprint
                        != asset.creation_receipt_id
                        or anchor.materialization_receipt_id
                        != asset.creation_receipt_id
                    ):
                        raise _state_invalid(
                            "P0 registered continuity anchor is stale or unregistered."
                        )
                    if (
                        anchor.role.value == "reference"
                        and anchor.source_identity
                        not in selected_character.reference_asset_ids
                    ):
                        raise _state_invalid(
                            "P0 reference anchor is not selected by the canonical Character."
                        )
                    if anchor.role.value == "last_frame":
                        target = shots[policy.target_shot.artifact_id]
                        endpoint_roles = tuple(
                            role
                            for role in target.required_asset_roles
                            if role.role == "approved_endpoint"
                        )
                        if (
                            len(endpoint_roles) != 1
                            or anchor.source_identity
                            not in endpoint_roles[0].asset_ids
                        ):
                            raise _state_invalid(
                                "P0 last-frame anchor is not the target Shot approved endpoint."
                            )
                elif anchor.role.value in {"first_frame", "reference_video"}:
                    suffix = (
                        "terminal-frame"
                        if anchor.role.value == "first_frame"
                        else "motion-tail"
                    )
                    if anchor.source_identity != f"{policy.source_shot.artifact_id}:{suffix}":
                        raise _state_invalid(
                            "P0 planned continuity derivation does not bind its source Shot."
                        )
                    expected_content_hash = canonical_sha256(
                        {
                            "derivation": f"exact-{suffix}/1",
                            "source_shot": policy.source_shot.model_dump(mode="json"),
                        }
                    )
                    expected_fingerprint = canonical_sha256(
                        {
                            "kind": (
                                "terminal"
                                if anchor.role.value == "first_frame"
                                else "motion-tail"
                            ),
                            "source": policy.source_shot.content_hash,
                        }
                    )
                    if (
                        anchor.content_hash != expected_content_hash
                        or anchor.evidence_fingerprint != expected_fingerprint
                    ):
                        raise _state_invalid(
                            "P0 planned continuity derivation recipe is inconsistent."
                        )
