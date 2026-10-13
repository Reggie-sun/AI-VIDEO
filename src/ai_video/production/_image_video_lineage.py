"""Read-only provenance for a retained P7 image after canonical revisions."""

from ai_video.production.models import StateCommitStatus, VideoAttemptPhase


def has_exact_authoring_successor(bundle, shot, image_asset) -> bool:
    """Trace unchanged image placement through succeeded project commits.

    Each edge reopens its exact immutable base and candidate. A changed Shot
    receipt is insufficient; the chain must reach the original P7 placement
    or an independently verified video successor. The caller still verifies
    the complete original image attempt and its activation chronology.
    """
    from ai_video.production.paths import _read_regular_file_nofollow
    from ai_video.production.project import load_production_project_candidate

    def reopen(project, registry):
        for pointer in (project, registry):
            raw = _read_regular_file_nofollow(bundle.root / pointer.path, contained_by=bundle.root)
            if raw.file_sha256 != pointer.file_sha256:
                raise ValueError("image authoring successor snapshot bytes changed")
        candidate = load_production_project_candidate(bundle.root, bundle.manifest,
            project.path, registry.path)
        if (candidate.project.project_id != bundle.project.project_id
                or candidate.project.content_hash != project.content_hash
                or candidate.registry.content_hash != registry.content_hash):
            raise ValueError("image authoring successor snapshot identity changed")
        return candidate

    def placement(value):
        return tuple((r.role, r.asset_ids) for r in value.required_asset_roles
                     if image_asset.asset_id in r.asset_ids)

    current, before_revision = shot, bundle.manifest.manifest_revision
    for attempt in sorted(bundle.manifest.attempts,
                          key=lambda a: a.base_manifest_revision, reverse=True):
        if (attempt.operation != "commit_project_registry"
                or attempt.status is not StateCommitStatus.SUCCEEDED
                or attempt.base_manifest_revision >= before_revision
                or any(p is None for p in (attempt.base_project, attempt.base_registry,
                    attempt.candidate_project, attempt.candidate_registry))):
            continue
        candidate = reopen(attempt.candidate_project, attempt.candidate_registry)
        if (next((s for s in candidate.shots if s.shot_id == current.shot_id), None) != current
                or image_asset not in candidate.registry.assets):
            continue
        base = reopen(attempt.base_project, attempt.base_registry)
        prior = next((s for s in base.shots if s.shot_id == current.shot_id), None)
        if (prior is None or image_asset not in base.registry.assets
                or not placement(prior) or placement(prior) != placement(current)):
            return False
        if (prior.creation_receipt_id == image_asset.creation_receipt_id
                or has_exact_video_successor(bundle, prior, image_asset)):
            return True
        current, before_revision = prior, attempt.base_manifest_revision
    return False


def has_exact_video_successor(bundle, shot, image_asset) -> bool:
    """Require an activated, exact successor that consumed this image.

    A later Shot receipt alone is not evidence. Reopen both the video effect
    chain and its immutable candidate Shot, preserving the original P7 owner.
    """
    from ai_video.production._video_project_reader import (
        load_video_request_receipt, verify_video_evidence, _verify_generated_video_candidate,
    )
    from ai_video.production.paths import _read_regular_file_nofollow
    from ai_video.production.project import load_production_project_candidate

    assets = {asset.asset_id: asset for asset in bundle.registry.assets}
    for attempt in bundle.manifest.attempts:
        state = attempt.video_generation_state
        if (state is None or attempt.status is not StateCommitStatus.SUCCEEDED
                or state.phase is not VideoAttemptPhase.ACTIVATE):
            continue
        request = load_video_request_receipt(bundle.root, state.request)
        output = assets.get(request.output_asset_id)
        if output is None or output.creation_receipt_id != shot.creation_receipt_id:
            continue
        scope = request.activation_scope
        if (scope is None or scope.request.target_shot_id != shot.shot_id
                or not any(role.role == scope.request.target_asset_role
                           and role.asset_ids == (output.asset_id,)
                           for role in shot.required_asset_roles)
                or not any(ref.asset_id == image_asset.asset_id
                           and ref.asset_sha256 == image_asset.sha256
                           for ref in scope.request.image_bindings)
                or attempt.candidate_project is None or attempt.candidate_registry is None):
            continue
        for pointer in (attempt.candidate_project, attempt.candidate_registry):
            raw = _read_regular_file_nofollow(bundle.root / pointer.path, contained_by=bundle.root)
            if raw.file_sha256 != pointer.file_sha256:
                raise ValueError("image successor candidate snapshot bytes changed")
        candidate = load_production_project_candidate(bundle.root, bundle.manifest,
            attempt.candidate_project.path, attempt.candidate_registry.path)
        if (candidate.project.content_hash != attempt.candidate_project.content_hash
                or candidate.registry.content_hash != attempt.candidate_registry.content_hash
                or next((item for item in candidate.shots if item.shot_id == shot.shot_id), None) != shot
                or next((item for item in candidate.registry.assets
                         if item.asset_id == image_asset.asset_id), None) != image_asset
                or next((item for item in candidate.registry.assets
                         if item.asset_id == output.asset_id), None) != output):
            continue
        verify_video_evidence(bundle.root, (state,),
            schema_version=bundle.manifest.schema_version, bundle=bundle)
        _verify_generated_video_candidate(candidate, attempt, request)
        return True
    return False
