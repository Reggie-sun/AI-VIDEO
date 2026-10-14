"""Attempt extensions and serialization shared by the canonical Manifest model."""

from pydantic import SerializerFunctionWrapHandler, model_serializer, model_validator

from ai_video.production.artifact_contracts import StrictModel
from ai_video.production.image_materialization_failure import ImageMaterializationFailurePointer


class StateCommitAttemptContracts(StrictModel):
    image_materialization_failure: ImageMaterializationFailurePointer | None = None

    @model_validator(mode="after")
    def _validate_image_materialization_failure(self):
        if self.image_materialization_failure is not None and (
            self.operation != "image_generation"
            or self.status.value != "failed"
            or self.image_phase != "materialize"
            or self.image_request is None
            or self.paid_provider_state is None
            or self.paid_provider_state.phase.value not in {"accepted", "settled"}
            or any(value is not None for value in (self.candidate_project,
                self.candidate_registry, self.candidate_dependency_graph,
                self.candidate_dependency_states_hash))
            or self.candidate_image_asset_ids
        ):
            raise ValueError("image materialization closure requires a failed retained remote result")
        return self

    @model_serializer(mode="wrap")
    def _serialize_without_unused_render_fields(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        from ai_video.production._lifecycle_schema import prune_attempt_fields

        data = handler(self)
        if self.operation != "render_state":
            for field in (
                "base_render_state",
                "candidate_render_state",
                "renderer_selection",
                "render_phase",
            ):
                data.pop(field, None)
        prune_attempt_fields(data, self.operation)
        for field in (
            "base_dependency_graph",
            "candidate_dependency_graph",
            "candidate_dependency_states_hash",
        ):
            if data.get(field) is None:
                data.pop(field, None)
        if self.operation != "repair":
            data.pop("approved_repair_receipt", None)
        if self.operation != "review":
            data.pop("review_request", None)
            data.pop("review_phase", None)
        if self.paid_provider_state is None:
            data.pop("paid_provider_state", None)
        if self.video_generation_state is None:
            data.pop("video_generation_state", None)
        if self.ad_generation_state is None:
            data.pop("ad_generation_state", None)
        if self.image_materialization_failure is None:
            data.pop("image_materialization_failure", None)
        return data
