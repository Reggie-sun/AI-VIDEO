"""Canvas image candidate setup through the existing image and P5 owners."""

from ai_video.canvas_dependencies import canvas_dependency_inputs
from ai_video.production.composition_contracts import CompositionLayerSpec, CompositionSpec
from ai_video.production.hashing import seal_artifact
from ai_video.production.image_candidate import make_image_candidate_preparer
from ai_video.production.models import SourceReference


def canvas_image_candidate_preparer(*, renderer_version="0.7.103"):
    """A candidate projection, never a second delivery timeline or state writer."""
    def prepare(loaded, request, *evidence):
        spec = seal_artifact(CompositionSpec(artifact_id="canvas-image-candidate", revision=1,
            content_hash="0" * 64, creation_receipt_id=request.request_fingerprint,
            source_provenance=(SourceReference(kind="derived", reference=request.request_id,
                content_hash=request.request_fingerprint),),
            composition_id="canvas-image-candidate", shot_ids=(request.target_shot_id,),
            layers=(CompositionLayerSpec(layer_id="candidate", shot_id=request.target_shot_id,
                asset_role=request.target_asset_role, asset_id=request.output_asset_id),),
            delivery_profile=loaded.project.delivery_profile))
        inputs = canvas_dependency_inputs(loaded, spec, renderer_version)
        return make_image_candidate_preparer(inputs)(loaded, request, *evidence)
    return prepare
