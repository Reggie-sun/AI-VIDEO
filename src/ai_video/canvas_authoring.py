"""Pure canvas authoring adapter; existing Production artifacts remain authoritative.

Director data is ordinary input, not a lifecycle store. A reopened workflow must
present the same data bound by the Project's provenance. Approval and bootstrap
are explicit operations on the sole canonical committer.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import difflib
import hashlib
import json
from pathlib import Path
import re

from ai_video.production.hashing import seal_artifact
from ai_video.production.models import (
    ArtifactReference, AssetRegistrySnapshot, Character, DeliveryProfile,
    ProductionBrief, ProductionProject, ProjectArtifactRefs, RendererPolicy,
    Scene, Shot, SourceReference, Story, Storyboard,
)
from ai_video.production.registry import registry_semantic_sha256
from ai_video.production.state_commit import PreparedArtifact, _canonical_yaml_bytes


def input_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _safe_id(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9._-]{1,128}", value):
        raise ValueError("authoring IDs must be safe filename components")
    return value


def direction_reference(packet, direction):
    return SourceReference(kind="user_input", reference="canvas-director-data",
        content_hash=input_hash({"packet": packet, "direction": direction}))


def _delivery_profile(packet, direction):
    if "delivery_profile" in direction:
        return DeliveryProfile.model_validate(direction["delivery_profile"])
    ratios = {u.get("observed_parameters", {}).get("aspectRatio") for u in packet["units"]}
    ratios.discard(None)
    if len(ratios) > 1:
        raise ValueError("mixed source aspect ratios require an explicit delivery_profile")
    if not ratios:
        return DeliveryProfile(width=640, height=480, fps=24)
    ratio = ratios.pop()
    if not isinstance(ratio, str) or not re.fullmatch(r"[1-9][0-9]?:[1-9][0-9]?", ratio):
        raise ValueError("unsupported source aspect ratio requires an explicit delivery_profile")
    width, height = map(int, ratio.split(":"))
    scale = 480 / min(width, height)
    # Keep the observed framing at a 480-pixel short edge, with even codec
    # dimensions. The selected Provider still decides exact capability.
    return DeliveryProfile(width=2 * round(width * scale / 2),
        height=2 * round(height * scale / 2), fps=24)


@dataclass(frozen=True)
class CanvasAuthoringBundle:
    project: ProductionProject
    registry: AssetRegistrySnapshot
    creative_artifacts: tuple
    artifacts: tuple[PreparedArtifact, ...]
    adaptations: tuple[dict, ...]

    def bootstrap(self, *, committer, attempt_id):
        """Caller approves the reviewable bundle; no Provider/media side effects."""
        return committer.bootstrap_initial_state(attempt_id=attempt_id,
            project=self.project, registry=self.registry, artifacts=self.artifacts)


def author_canvas_project(*, packet, direction, registry=None, asset_artifacts=(), previous=None):
    """Map explicit director decisions into existing types and compute identities.

    Asset admission stays with the existing Registry/import owner. This adapter
    does not turn remote URLs or a canvas resourceId into verified local bytes.
    """
    packet, direction = deepcopy(packet), deepcopy(direction)
    allowed = {"project_id", "title", "language", "brief", "story", "characters", "scenes",
               "storyboard", "shots", "delivery_profile"}
    if set(direction) - allowed:
        raise ValueError("unknown director input fields")
    if packet.get("authority") != "development_preparation_only_not_production_state":
        raise ValueError("authoring requires an inspected canvas sequence packet")
    units = packet["units"]
    rows = direction["shots"]
    occurrences = [u["occurrence_id"] for u in units]
    if not units or len(set(occurrences)) != len(occurrences) or (
            [r["occurrence_id"] for r in rows] != occurrences):
        raise ValueError("director Shots must bind every occurrence once, in selected order")
    pid = _safe_id(direction["project_id"])
    if previous is not None and previous.project.project_id != pid:
        raise ValueError("authoring revision cannot cross Project identity")
    source = direction_reference(packet, direction)
    provenance = (SourceReference(kind="imported", reference="canvas-source-snapshot",
        content_hash=packet["source_snapshot_sha256"]), source)
    artifacts, models, adaptations = [], [], []
    previous_models = {} if previous is None else {m.artifact_id: m for m in (
        previous.brief, previous.story, *previous.characters, *previous.scenes,
        previous.storyboard, *previous.shots)}
    previous_refs = {} if previous is None else {r.artifact_id: r for r in (
        previous.project.artifacts.brief, previous.project.artifacts.story,
        *previous.project.artifacts.characters, *previous.project.artifacts.scenes,
        previous.project.artifacts.storyboard, *previous.project.artifacts.shots)}

    def creative(model, data, name, source_unit=None):
        if set(data) & {"artifact_id", "revision", "content_hash", "creation_receipt_id",
                        "source_provenance", "schema_version"}:
            raise ValueError("internal artifact identities are computed by the authoring owner")
        # Project binds all director inputs; each creative artifact binds its
        # own input, so an unrelated edit does not invalidate every Shot.
        local_hash = input_hash({"type": model.__name__, "data": data, "source": source_unit})
        local_provenance = (SourceReference(kind="user_input", reference=f"canvas-authoring:{name}",
            content_hash=local_hash),)
        prior = previous_models.get(f"{pid}-{name}")
        if prior is not None and local_provenance[0] in prior.source_provenance:
            # Canonical adoption may add roles/provenance after authoring. An
            # unrelated director edit must not erase those accepted outputs.
            models.append(prior)
            return prior, previous_refs[prior.artifact_id]
        value = seal_artifact(model(artifact_id=f"{pid}-{name}", revision=prior.revision if prior else 1,
            content_hash="0" * 64, creation_receipt_id=f"canvas-author-{local_hash}",
            source_provenance=local_provenance, **data))
        if prior is not None and value == prior:
            models.append(prior)
            return prior, previous_refs[prior.artifact_id]
        if prior is not None:
            value = seal_artifact(value.model_copy(update={"revision": prior.revision + 1}))
        path = Path(f"creative/{name}/{value.content_hash}.yaml")
        payload = _canonical_yaml_bytes(value)
        artifacts.append(PreparedArtifact(path, payload, hashlib.sha256(payload).hexdigest()))
        models.append(value)
        return value, ArtifactReference(artifact_id=value.artifact_id, revision=value.revision,
            content_hash=value.content_hash, path=path)

    _, brief = creative(ProductionBrief, {"title": direction["title"],
        "language": direction["language"], **direction["brief"]}, "brief")
    _, story = creative(Story, {"language": direction["language"], **direction["story"]}, "story")
    characters = tuple(creative(Character, c, f"characters/{_safe_id(c['character_id'])}")[1]
                       for c in direction["characters"])
    scenes = tuple(creative(Scene, s, f"scenes/{_safe_id(s['scene_id'])}")[1]
                   for s in direction["scenes"])
    _, storyboard = creative(Storyboard, direction["storyboard"], "storyboard")
    shot_ids = [r["shot"]["shot_id"] for r in rows]
    order = [s for b in direction["storyboard"]["beats"] for s in b["shot_ids"]]
    if len(set(shot_ids)) != len(shot_ids) or order != shot_ids:
        raise ValueError("Storyboard must retain exact selected occurrence order and distinct Shot IDs")
    shots = []
    for index, (unit, row) in enumerate(zip(units, rows, strict=True)):
        if set(row) - {"occurrence_id", "shot", "adaptation_reason", "source_dialogue",
                       "generation", "composition", "boundary"}:
            raise ValueError("unknown Shot director fields")
        edge = row.get("boundary")
        if index == 0 and edge is not None:
            raise ValueError("first occurrence cannot have a predecessor boundary")
        if index:
            source_edge = packet["boundaries"][index - 1]
            if source_edge["status"] in {"BLOCKED_SOURCE_CONFLICT", "BLOCKED_SOURCE_GAPS"}:
                raise ValueError("selected source boundary has unresolved conflicts or gaps")
            if not isinstance(edge, dict):
                raise ValueError("each later occurrence needs an explicit boundary decision")
            if edge.get("independent") is True:
                if set(edge) != {"independent", "reason"} or not str(edge["reason"]).strip():
                    raise ValueError("independent Shot requires an explicit director reason")
                if "planning_arguments" in source_edge:
                    raise ValueError("declared continuity cannot be downgraded to independent")
            elif "planning_arguments" in source_edge:
                if {k: edge.get(k) for k in source_edge["planning_arguments"]} != source_edge["planning_arguments"]:
                    raise ValueError("director boundary differs from the source authoring")
        original = unit["source_text"]
        adapted = row["shot"]["intent"]
        reason = row.get("adaptation_reason", "")
        if original != adapted and (not isinstance(reason, str) or not reason.strip()):
            raise ValueError("changed source prose requires an explicit adaptation reason")
        if "source_dialogue" in row and row["source_dialogue"] != row["shot"].get("dialogue", ""):
            raise ValueError("source dialogue changed; return to explicit director authoring")
        adaptations.append({"occurrence_id": unit["occurrence_id"], "original": original,
            "adapted": adapted, "reason": reason,
            "diff": "\n".join(difflib.unified_diff(original.splitlines(), adapted.splitlines(),
                        fromfile="source", tofile="authored", lineterm=""))})
        _, reference = creative(Shot, row["shot"], f"shots/{_safe_id(row['shot']['shot_id'])}",
            {"unit": unit, "decisions": {k: v for k, v in row.items() if k != "shot"}})
        shots.append(reference)
    profile = _delivery_profile(packet, direction)
    project = seal_artifact(ProductionProject(artifact_id=f"{pid}-project",
        revision=previous.project.revision + 1 if previous else 1,
        content_hash="0" * 64, creation_receipt_id=f"canvas-author-{source.content_hash}",
        source_provenance=provenance, project_id=pid, title=direction["title"],
        default_language=direction["language"], delivery_profile=profile,
        renderer_policy=RendererPolicy(), artifacts=ProjectArtifactRefs(brief=brief, story=story,
            characters=characters, scenes=scenes, storyboard=storyboard, shots=tuple(shots))))
    if registry is None:
        registry = previous.registry if previous is not None else None
    if registry is None:
        registry = AssetRegistrySnapshot(revision_id="0" * 64, content_hash="0" * 64, assets=())
        identity = registry_semantic_sha256(registry)
        registry = registry.model_copy(update={"revision_id": identity, "content_hash": identity})
    return CanvasAuthoringBundle(project, registry, tuple(models),
        tuple(sorted((*artifacts, *asset_artifacts), key=lambda a: a.relative_path.as_posix())),
        tuple(adaptations))
