from __future__ import annotations

from enum import Enum
import hashlib
import json
from typing import Literal

from pydantic import ConfigDict, Field, JsonValue, model_validator

from ai_video.production.hashing import canonical_sha256
from ai_video.production.models import (
    ProjectSnapshotPointer,
    RegistrySnapshotPointer,
    StrictModel,
)


class _TransitionModel(StrictModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class BoundaryKind(str, Enum):
    WITHIN_CONTINUOUS_TAKE = "within_continuous_take"
    HARD_CUT = "hard_cut"
    SCENE_BOUNDARY = "scene_boundary"


class ContinuityObligation(str, Enum):
    FULL_CONTINUITY = "full_continuity"
    IDENTITY_STYLE_CARRYOVER = "identity_style_carryover"
    SUBSTANTIAL_RESET = "substantial_reset"


class ContinuityAnchorRole(str, Enum):
    FIRST_FRAME = "first_frame"
    LAST_FRAME = "last_frame"
    REFERENCE = "reference"
    REFERENCE_VIDEO = "reference_video"


class MotionCoverage(str, Enum):
    SUBJECT_MOTION = "subject_motion"
    CAMERA_MOTION = "camera_motion"


class CreativeArtifactIdentity(_TransitionModel):
    artifact_id: str = Field(min_length=1)
    revision: int = Field(strict=True, ge=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class ContinuityAnchorBinding(_TransitionModel):
    role: ContinuityAnchorRole
    source_kind: Literal["registered_asset", "planned_derivation"]
    source_identity: str = Field(min_length=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    evidence_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    materialization_receipt_id: str | None = None

    @model_validator(mode="after")
    def _validate_source_evidence(self) -> "ContinuityAnchorBinding":
        if self.source_kind == "registered_asset":
            if not self.materialization_receipt_id:
                raise ValueError("registered anchor requires a materialization receipt")
        elif self.materialization_receipt_id is not None:
            raise ValueError("planned derivation cannot claim materialization receipt")
        return self


class ContinuityTransitionPolicy(_TransitionModel):
    schema_version: Literal["1"] = "1"
    policy_id: str = Field(min_length=1)
    project: ProjectSnapshotPointer
    registry: RegistrySnapshotPointer
    source_shot: CreativeArtifactIdentity
    target_shot: CreativeArtifactIdentity
    boundary_kind: BoundaryKind
    continuity_obligation: ContinuityObligation
    take_id: str | None = None
    source_execution_stack_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    destination_execution_stack_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    continuity_grade: Literal["c4_native_boundary_motion"]
    required_carryover_dimensions: tuple[str, ...]
    anchors: tuple[ContinuityAnchorBinding, ...]
    qa_policy_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    authoring_evidence_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    policy_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_policy(self) -> "ContinuityTransitionPolicy":
        if self.source_shot.artifact_id == self.target_shot.artifact_id:
            raise ValueError("transition policy requires distinct source and target Shots")
        allowed = {
            BoundaryKind.WITHIN_CONTINUOUS_TAKE: {
                ContinuityObligation.FULL_CONTINUITY
            },
            BoundaryKind.HARD_CUT: {
                ContinuityObligation.FULL_CONTINUITY,
                ContinuityObligation.IDENTITY_STYLE_CARRYOVER,
            },
            BoundaryKind.SCENE_BOUNDARY: {
                ContinuityObligation.IDENTITY_STYLE_CARRYOVER,
                ContinuityObligation.SUBSTANTIAL_RESET,
            },
        }
        if self.continuity_obligation not in allowed[self.boundary_kind]:
            raise ValueError("boundary and continuity obligation are incompatible")
        if self.boundary_kind is BoundaryKind.WITHIN_CONTINUOUS_TAKE:
            if not self.take_id:
                raise ValueError("continuous take policy requires take_id")
            if self.source_execution_stack_hash != self.destination_execution_stack_hash:
                raise ValueError("continuous take cannot cross execution stacks")
        elif self.take_id is not None:
            raise ValueError("take_id is reserved for continuous take policies")
        dimensions = self.required_carryover_dimensions
        if dimensions != tuple(sorted(set(dimensions))):
            raise ValueError("carryover dimensions must be unique and canonically ordered")
        roles = tuple(item.role for item in self.anchors)
        if roles != tuple(sorted(set(roles), key=lambda item: item.value)):
            raise ValueError("continuity anchors must be unique and canonically ordered")
        if self.continuity_obligation is ContinuityObligation.SUBSTANTIAL_RESET:
            if dimensions or self.anchors:
                raise ValueError("substantial reset cannot retain carryover inputs")
        else:
            if not dimensions:
                raise ValueError("continuity carryover requires explicit dimensions")
            if self.continuity_obligation is ContinuityObligation.FULL_CONTINUITY:
                required_roles = {
                    ContinuityAnchorRole.FIRST_FRAME,
                    ContinuityAnchorRole.LAST_FRAME,
                    ContinuityAnchorRole.REFERENCE,
                    ContinuityAnchorRole.REFERENCE_VIDEO,
                }
                if set(roles) != required_roles:
                    raise ValueError("full continuity requires all four anchor roles")
            elif ContinuityAnchorRole.REFERENCE not in roles:
                raise ValueError("identity/style carryover requires a reference anchor")
        expected = canonical_sha256(
            self.model_dump(mode="json", exclude={"policy_hash"})
        )
        if self.policy_hash != expected:
            raise ValueError("policy_hash does not match transition policy")
        return self

    @classmethod
    def create(cls, **values: object) -> "ContinuityTransitionPolicy":
        data = dict(values)
        data.setdefault("schema_version", "1")
        data.pop("policy_hash", None)
        provisional = cls.model_construct(**data, policy_hash="0" * 64)
        data["policy_hash"] = canonical_sha256(
            provisional.model_dump(mode="json", exclude={"policy_hash"})
        )
        return cls.model_validate(data)


class ValidationEdgeBinding(_TransitionModel):
    source_shot_id: str = Field(min_length=1)
    target_shot_id: str = Field(min_length=1)
    policy_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    motion_coverage: tuple[MotionCoverage, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _canonical_coverage(self) -> "ValidationEdgeBinding":
        if self.motion_coverage != tuple(
            sorted(set(self.motion_coverage), key=lambda item: item.value)
        ):
            raise ValueError("motion coverage must be unique and canonically ordered")
        return self


class RealShotValidationSet(_TransitionModel):
    schema_version: Literal["1"] = "1"
    validation_set_id: str = Field(min_length=1)
    project: ProjectSnapshotPointer
    registry: RegistrySnapshotPointer
    character: CreativeArtifactIdentity
    scene: CreativeArtifactIdentity
    shots: tuple[CreativeArtifactIdentity, ...] = Field(min_length=3, max_length=4)
    edges: tuple[ValidationEdgeBinding, ...] = Field(min_length=2)
    human_freeze_evidence_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    rubric_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_set(self) -> "RealShotValidationSet":
        shot_ids = tuple(item.artifact_id for item in self.shots)
        if len(shot_ids) != len(set(shot_ids)):
            raise ValueError("validation-set Shots must be unique")
        expected_edges = tuple(zip(shot_ids, shot_ids[1:]))
        actual_edges = tuple(
            (item.source_shot_id, item.target_shot_id) for item in self.edges
        )
        if actual_edges != expected_edges:
            raise ValueError("validation-set edges must cover every adjacent Shot")
        policy_hashes = tuple(item.policy_hash for item in self.edges)
        if len(policy_hashes) != len(set(policy_hashes)):
            raise ValueError("validation-set edge policies must be unique")
        coverage = {
            item for edge in self.edges for item in edge.motion_coverage
        }
        if coverage != {MotionCoverage.SUBJECT_MOTION, MotionCoverage.CAMERA_MOTION}:
            raise ValueError("validation set must cover subject and camera motion")
        expected = canonical_sha256(
            self.model_dump(mode="json", exclude={"content_hash"})
        )
        if self.content_hash != expected:
            raise ValueError("content_hash does not match real-Shot validation set")
        return self

    @classmethod
    def create(cls, **values: object) -> "RealShotValidationSet":
        data = dict(values)
        data.setdefault("schema_version", "1")
        data.pop("content_hash", None)
        provisional = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(
            provisional.model_dump(mode="json", exclude={"content_hash"})
        )
        return cls.model_validate(data)


class CandidateStackBinding(_TransitionModel):
    label: Literal["m0", "m1"]
    execution_stack_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class P0QualificationInput(_TransitionModel):
    schema_version: Literal["1"] = "1"
    input_kind: Literal[
        "inventory",
        "calibration_fixture",
        "rubric",
        "effect_budget",
        "human_freeze",
    ]
    input_id: str = Field(min_length=1)
    payload: dict[str, JsonValue] = Field(min_length=1)
    execution_stack_hashes: tuple[str, ...] = ()
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    def _content_hash_payload(self) -> dict[str, object]:
        payload = self.model_dump(mode="json", exclude={"content_hash"})
        if not self.execution_stack_hashes:
            payload.pop("execution_stack_hashes", None)
        return payload

    @model_validator(mode="after")
    def _validate_input(self) -> "P0QualificationInput":
        if self.execution_stack_hashes != tuple(sorted(set(self.execution_stack_hashes))):
            raise ValueError("P0 qualification stack hashes must be unique and ordered")
        if any(len(item) != 64 or any(char not in "0123456789abcdef" for char in item) for item in self.execution_stack_hashes):
            raise ValueError("P0 qualification stack hash is invalid")
        serialized = json.dumps(
            self.payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).lower()
        if any(
            token in serialized
            for token in ("api_key", "secret=", "sourceurl", "/home/", "file://")
        ):
            raise ValueError("P0 qualification input cannot contain secret or local-path material")
        self._validate_kind_payload()
        expected = canonical_sha256(self._content_hash_payload())
        if self.content_hash != expected:
            raise ValueError("content_hash does not match P0 qualification input")
        return self

    def _validate_kind_payload(self) -> None:
        payload = self.payload
        if self.input_kind == "inventory":
            components = payload.get("components")
            if (
                not isinstance(components, list)
                or not components
                or payload.get("remote_provider_enabled") is not False
                or payload.get("cloud_fallback_enabled") is not False
                or not isinstance(payload.get("hybrid_artifact_present"), bool)
            ):
                raise ValueError("P0 inventory must seal components and disabled remote paths")
            component_ids: list[str] = []
            for component in components:
                if not isinstance(component, dict):
                    raise ValueError("P0 inventory component must be a sealed object")
                component_id = component.get("id")
                presence = component.get("presence")
                content_hash = component.get("sha256")
                if (
                    not isinstance(component_id, str)
                    or not component_id
                    or presence not in {"present", "absent"}
                    or (
                        presence == "present"
                        and (
                            not isinstance(content_hash, str)
                            or len(content_hash) != 64
                            or any(char not in "0123456789abcdef" for char in content_hash)
                        )
                    )
                    or (presence == "absent" and content_hash != "none")
                ):
                    raise ValueError("P0 inventory component identity is invalid")
                component_ids.append(component_id)
            if len(component_ids) != len(set(component_ids)):
                raise ValueError("P0 inventory component IDs must be unique")
            return
        if self.input_kind == "calibration_fixture":
            source = payload.get("source_dimensions")
            target = payload.get("target_canvas")
            tensor = payload.get("target_tensor_shape")
            prompt = payload.get("prompt")
            preprocessing = payload.get("preprocessing")
            role_mapping = payload.get("role_mapping")
            if (
                not isinstance(source, list)
                or len(source) != 2
                or not all(isinstance(item, int) and item > 0 for item in source)
                or source != [1659, 948]
                or target != [1344, 768]
                or source[0] * 768 != source[1] * 1344
                or payload.get("source_aspect_ratio") != "7:4"
                or payload.get("target_tensor_layout") != "BHWC"
                or tensor != [1, 768, 1344, 3]
                or payload.get("target_tensor_dtype")
                != "float32_normalized_0_to_1"
                or payload.get("dimension_multiple") != 32
                or payload.get("exact_scale_ratio") != "64/79"
                or not isinstance(prompt, str)
                or not self._is_h3_prompt(prompt)
                or payload.get("prompt_sha256")
                != hashlib.sha256(prompt.encode("utf-8")).hexdigest()
                or not isinstance(preprocessing, dict)
                or preprocessing.get("first_frame")
                != "lanczos_crop_disabled_isotropic"
                or preprocessing.get("last_frame")
                != "lanczos_center_crop_no_crop_at_exact_7_to_4"
                or preprocessing.get("reference")
                != "match_area_round32_resolves_1344x768"
                or role_mapping
                != {
                    "first_frame": "conditioning.first_frame",
                    "last_frame": "conditioning.last_frame",
                    "reference": "ref_images.ref_image_0",
                    "reference_video": "ref_videos.ref_video_0",
                }
                or payload.get("ref_video_audios") != []
                or payload.get("ref_audios") != []
                or payload.get("task_type") != "Hybrid"
                or payload.get("frame_count") != 124
                or payload.get("fps") != 24
                or payload.get("steps") != 20
                or payload.get("sampler") != "dual_clock_euler"
                or payload.get("scheduler") != "native_flow"
                or payload.get("turbo_lora") is not False
                or payload.get("output_container") != "mp4"
                or payload.get("output_crf") != 17
                or payload.get("native_audio") is not True
            ):
                raise ValueError("P0 calibration fixture does not match the sealed T8 tensor contract")
            return
        if self.input_kind == "rubric":
            boundary = payload.get("boundary")
            sequence = payload.get("sequence")
            if (
                payload.get("verdict_owner") != "P6"
                or payload.get("human_evidence_required") is not True
                or not isinstance(boundary, dict)
                or boundary.get("decoded_first_and_last_required") is not True
                or boundary.get("perceptual_backend_missing")
                != "NOT_EVALUATED_requires_exact_human_review"
                or not isinstance(sequence, dict)
                or sequence.get("raw_full_speed_review_required") is not True
                or sequence.get(
                    "crossfade_optical_flow_interpolation_retime_forbidden"
                )
                is not True
            ):
                raise ValueError("P0 rubric must preserve P6 and exact human-review ownership")
            return
        if self.input_kind == "effect_budget":
            if any(
                payload.get(key) != value
                for key, value in {
                    "provider": "loopback_local_comfyui",
                    "submits_per_generation": 1,
                    "retry": False,
                    "fallback": False,
                    "remote": False,
                    "paid": False,
                    "automatic_activation": False,
                    "unknown_outcome": "explicit_recovery_only",
                }.items()
            ):
                raise ValueError("P0 effect budget must be local, one-submit, and no-fallback")
            return
        not_claimed = payload.get("not_claimed")
        if (
            payload.get("approval_scope") != "freeze_source_candidates_for_P0_only"
            or payload.get("approved_candidate_order") != ["A1", "A2", "A3", "A4"]
            or not isinstance(not_claimed, list)
            or set(not_claimed)
            != {"creative_PASS", "P6_PASS", "Final_Acceptance"}
        ):
            raise ValueError("P0 human freeze cannot claim quality or final acceptance")

    @staticmethod
    def _is_h3_prompt(prompt: str) -> bool:
        markers = (
            "integrated_multimodal_description:",
            "overall_soundscape:",
            "non_diegetic_music:",
        )
        if not prompt.startswith("For the target video,") or "\n\n" not in prompt:
            return False
        conditioning = prompt.split("\n\n", 1)[0]
        if not all(
            token in conditioning
            for token in ("<Picture 1>", "<Picture 2>", "<Picture 3>", "<Video 1>")
        ):
            return False
        if any(prompt.count(marker) != 1 for marker in markers):
            return False
        positions = tuple(prompt.index(marker) for marker in markers)
        visual = prompt[positions[0] : positions[1]].lower()
        return positions == tuple(sorted(positions)) and all(
            token in visual for token in ("live-action", "camera", "amplitude", "speed")
        )

    @classmethod
    def create(cls, **values: object) -> "P0QualificationInput":
        data = dict(values)
        data.setdefault("schema_version", "1")
        data.pop("content_hash", None)
        provisional = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(provisional._content_hash_payload())
        return cls.model_validate(data)


class P0QualificationPreparedReceipt(_TransitionModel):
    schema_version: Literal["1"] = "1"
    status: Literal["qualification_prepared"] = "qualification_prepared"
    receipt_id: str = Field(min_length=1)
    project: ProjectSnapshotPointer
    registry: RegistrySnapshotPointer
    inventory_receipt_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    calibration_fixture_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    rubric_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    effect_budget_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    human_freeze_evidence_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    validation_set_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    policy_hashes: tuple[str, ...] = Field(min_length=2)
    candidate_stacks: tuple[CandidateStackBinding, CandidateStackBinding]
    limitations: tuple[str, ...] = Field(min_length=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def _validate_receipt(self) -> "P0QualificationPreparedReceipt":
        if tuple(item.label for item in self.candidate_stacks) != ("m0", "m1"):
            raise ValueError("P0 receipt requires ordered m0 and m1 candidate stacks")
        stack_hashes = tuple(
            item.execution_stack_hash for item in self.candidate_stacks
        )
        if len(set(stack_hashes)) != 2:
            raise ValueError("P0 candidate execution stacks must be distinct")
        if self.policy_hashes != tuple(sorted(set(self.policy_hashes))):
            raise ValueError("P0 policy hashes must be unique and canonically ordered")
        if not all(item.strip() for item in self.limitations):
            raise ValueError("P0 limitations cannot be blank")
        expected = canonical_sha256(
            self.model_dump(mode="json", exclude={"content_hash"})
        )
        if self.content_hash != expected:
            raise ValueError("content_hash does not match P0 prepared receipt")
        return self

    @classmethod
    def create(cls, **values: object) -> "P0QualificationPreparedReceipt":
        data = dict(values)
        data.setdefault("schema_version", "1")
        data.setdefault("status", "qualification_prepared")
        data.pop("content_hash", None)
        provisional = cls.model_construct(**data, content_hash="0" * 64)
        data["content_hash"] = canonical_sha256(
            provisional.model_dump(mode="json", exclude={"content_hash"})
        )
        return cls.model_validate(data)
