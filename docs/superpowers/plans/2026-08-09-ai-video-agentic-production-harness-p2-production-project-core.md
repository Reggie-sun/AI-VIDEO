# AI-VIDEO Agentic Production Harness P2 Production Project Core Implementation Plan

> **For agentic workers:** 实施本 plan 时，REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans。按 Task 顺序执行，并使用 checkbox (`- [ ]`) 跟踪进度。

**Goal:** 在不改变 Legacy CLI、Manifest v1、`runs/<run_id>/` layout 或引入 renderer/provider 的前提下，实现可加载、可哈希、可静态校验的 v2 `ProductionProject`、creative artifacts、Shot visual strategy 和 immutable Asset Registry core。

**Architecture:** 新能力隔离在 `src/ai_video/production/`；Pydantic models 拥有 schema，pure validators 拥有 cross-reference 和 visual-strategy rules，`registry.py` 拥有 immutable registry snapshot 校验，`project.py` 是完整 bundle 的唯一 loader。P2 只读取一个最小 `ProductionManifest` 作为 active project/registry revision pointer，不实现 P5 的 dependency graph、fresh/stale lifecycle、desired/applied state 或 selective rebuild。

**Tech Stack:** Python 3.11+、Pydantic v2、PyYAML、pytest、现有 `AiVideoError`/`ErrorCode`、`hashlib` 和本地 filesystem；不新增 runtime dependency，不调用 ComfyUI、ffmpeg、HyperFrames、Remotion、ElevenLabs、Captions 或任何 network Provider。

---

Status: Proposed implementation plan. Writing or approving this document does not authorize P2 runtime implementation.

## Scope and Authorization

P2 只实现：

- strict v2 `ProductionProject` 和 creative artifact schema；
- `ProductionBrief`、`Story`、`Character`、`Scene`、`Storyboard`、`Shot`；
- 六种 `visual_strategy` 及 strategy-specific static validation；
- deterministic semantic content hash；
- immutable `AssetRecord` / `AssetRegistrySnapshot`；
- 最小只读 `ProductionManifest` active revision pointer；
- project-relative clean path resolution、artifact hash/file hash 和 cross-reference validation；
- importable Python loading API 和 no-network tests。

P2 明确不实现：

- 新 CLI command、flag 或 exit code；
- 修改 Legacy `ProjectConfig`、`ShotSpec`、`RunManifest`、pipeline 或 resume；
- 修改 `runs/<run_id>/` layout；
- artifact generation、renderer、timeline、Audio、Caption、QA/repair；
- dependency graph、fresh/stale、desired/applied state、selective rebuild；
- registry activation/write transaction、GC 或 migration tool；
- plugin、SDK、新 dependency、paid/remote Provider 或 network call。

P2 runtime work requires separate explicit user authorization after this plan is accepted.

## Integration Base Gate

Plan drafting evidence on 2026-08-09:

~~~text
local main: 261fc36
origin/main: dfab235
origin/main...main: 0 5
working tree before plan edit: clean
~~~

Before implementation:

~~~bash
git status --short --branch
git log --oneline --decorate -10
git rev-list --left-right --count origin/main...main
~~~

The executor must record one base decision:

1. create `feat/p2-production-project-core` from current local `main`, preserving P1/P0; or
2. first publish/integrate the five local commits, then branch from the shared base.

Do not branch from current `origin/main` without explicitly carrying `abe029c`, `aad2687`, `ed938f2`, `6eb895a` and `261fc36`. If another writer is active or unrelated changes exist, use a dedicated worktree.

## Ownership and Old Paths

| Contract | P2 Owner | Old Path Decision |
| --- | --- | --- |
| v2 schema | `src/ai_video/production/models.py` | Do not add v2 fields to Legacy `models.py` |
| semantic hash | `src/ai_video/production/hashing.py` | Reuse `config.sha256_file()` for file bytes |
| strategy/reference rules | `src/ai_video/production/validation.py` | Do not reuse ordered-shot or QA heuristics |
| registry validation | `src/ai_video/production/registry.py` | No discovery, lifecycle or provider calls |
| bundle loader | `src/ai_video/production/project.py` | Do not branch Legacy `load_project()` |
| active revision | minimal v2 `ProductionManifest` | Do not modify Manifest v1; P5 extends v2 state |
| public API | `src/ai_video/production/__init__.py` | No P2 public CLI |

`Shot.desired_fingerprint` is derived, not persisted inside immutable Shot content. P2 uses `content_hash` as revision identity; P5 may persist a desired fingerprint in Production Manifest. This avoids a second lifecycle owner.

## File Map

Create:

- `src/ai_video/production/{__init__,models,hashing,validation,registry,project}.py`
- `tests/production_project_factory.py`
- `tests/test_production_models.py`
- `tests/test_production_validation.py`
- `tests/test_production_registry.py`
- `tests/test_production_project.py`

Modify:

- `src/ai_video/errors.py`
- `README.md`
- `docs/v0.2-runtime-baseline.md`
- `docs/v0.2-agentic-production-roadmap.md`
- `docs/agent-primary-contract-matrix.md`

Do not modify `src/ai_video/{cli,config,models,manifest,pipeline,workflow_loader,workflow_renderer,ffmpeg_tools}.py`, `src/ai_video_mcp/**`, `pyproject.toml`, `configs/**`, `workflows/**` or `runs/**`.

## Test and Commit Map

| Task | RED Focus | Owner | Commit |
| --- | --- | --- | --- |
| 1 | strict schema and semantic hash | models + hashing | `feat: add production project core schemas` |
| 2 | six strategies and references | validation | `feat: validate production shot strategies` |
| 3 | registry/path/file evidence | registry | `feat: add immutable asset registry validation` |
| 4 | complete bundle loading | project + fixture | `feat: load validated production projects` |
| 5 | public truth/docs | API + docs | `docs: document production project core` |
| 6 | regression/review | verification | no commit unless correction required |

### Task 1: Add Strict Domain Models and Semantic Hashing

**Files:**
- Create: `src/ai_video/production/__init__.py`
- Create: `src/ai_video/production/models.py`
- Create: `src/ai_video/production/hashing.py`
- Modify: `src/ai_video/errors.py`
- Test: `tests/test_production_models.py`

- [ ] **Step 1: Write failing schema and hash tests**

Create `tests/test_production_models.py`:

~~~python
import pytest
from pydantic import ValidationError

from ai_video.production.hashing import canonical_sha256, seal_artifact, verify_artifact_hash
from ai_video.production.models import SourceReference, Story, StoryBeat


def make_story() -> Story:
    return Story(
        artifact_id="story-main",
        revision=1,
        content_hash="0" * 64,
        creation_receipt_id="receipt-story-1",
        source_provenance=[SourceReference(kind="user_input", reference="brief-1")],
        language="zh-CN",
        logline="一位侦探追查失踪的记忆。",
        synopsis="侦探在三幕故事中找到真相。",
        beats=[StoryBeat(beat_id="beat-1", summary="案件出现")],
        source_references=["source-novel-1"],
    )


def test_semantic_hash_ignores_mapping_order_and_content_hash():
    assert canonical_sha256({"b": 2, "a": 1, "content_hash": "x"}) == canonical_sha256(
        {"content_hash": "y", "a": 1, "b": 2}
    )


def test_sealed_artifact_detects_content_change():
    sealed = seal_artifact(make_story())
    assert verify_artifact_hash(sealed)
    assert not verify_artifact_hash(sealed.model_copy(update={"logline": "不同内容"}))


def test_domain_models_reject_unknown_fields():
    data = make_story().model_dump()
    data["unexpected"] = True
    with pytest.raises(ValidationError):
        Story.model_validate(data)
~~~

- [ ] **Step 2: Run RED**

~~~bash
python -m pytest tests/test_production_models.py -q
~~~

Expected: collection fails because `ai_video.production` does not exist.

- [ ] **Step 3: Add typed error codes**

Add to `ErrorCode`:

~~~python
    PRODUCTION_PROJECT_INVALID = "production_project_invalid"
    ASSET_REGISTRY_INVALID = "asset_registry_invalid"
~~~

- [ ] **Step 4: Implement semantic hashing**

Create `src/ai_video/production/hashing.py`:

~~~python
from __future__ import annotations

import hashlib
import json
from typing import Any, TypeVar

from pydantic import BaseModel

ArtifactT = TypeVar("ArtifactT", bound=BaseModel)


def _semantic_data(value: BaseModel | dict[str, Any]) -> dict[str, Any]:
    data = value.model_dump(mode="json") if isinstance(value, BaseModel) else dict(value)
    data.pop("content_hash", None)
    return data


def canonical_sha256(value: BaseModel | dict[str, Any]) -> str:
    payload = json.dumps(
        _semantic_data(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def seal_artifact(artifact: ArtifactT) -> ArtifactT:
    return artifact.model_copy(update={"content_hash": canonical_sha256(artifact)})


def verify_artifact_hash(artifact: BaseModel) -> bool:
    expected = getattr(artifact, "content_hash", None)
    return isinstance(expected, str) and len(expected) == 64 and expected == canonical_sha256(artifact)
~~~

- [ ] **Step 5: Implement the model contract**

Create `src/ai_video/production/models.py` with:

~~~python
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceReference(StrictModel):
    kind: Literal["user_input", "imported", "derived"]
    reference: str
    content_hash: str | None = None


class VersionedArtifact(StrictModel):
    artifact_id: str = Field(min_length=1)
    schema_version: Literal["2.0"] = "2.0"
    revision: int = Field(ge=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    creation_receipt_id: str = Field(min_length=1)
    source_provenance: list[SourceReference] = Field(min_length=1)


class ProductionProject(VersionedArtifact):
    project_id: str
    title: str
    default_language: str
    delivery_profile: DeliveryProfile
    renderer_policy: RendererPolicy
    artifacts: ProjectArtifactRefs
    asset_root: Path = Path("assets/files")


class Story(VersionedArtifact):
    language: str
    logline: str
    synopsis: str
    beats: list[StoryBeat] = Field(min_length=1)
    source_references: list[str] = Field(default_factory=list)


class Character(VersionedArtifact):
    character_id: str
    name: str
    identity: str
    appearance_bible: str
    wardrobe: list[str] = Field(default_factory=list)
    voice_profile: VoiceProfile | None = None
    reference_asset_ids: list[str] = Field(default_factory=list)
    allowed_variations: list[str] = Field(default_factory=list)


class Scene(VersionedArtifact):
    scene_id: str
    location: str
    time: str
    mood: str
    participant_ids: list[str] = Field(default_factory=list)
    continuity_constraints: list[str] = Field(default_factory=list)
    visual_reference_asset_ids: list[str] = Field(default_factory=list)


class Storyboard(VersionedArtifact):
    beats: list[StoryboardBeat] = Field(min_length=1)


class Shot(VersionedArtifact):
    shot_id: str
    scene_id: str
    storyboard_beat_id: str
    intent: str
    dialogue: str = ""
    narration: str = ""
    duration_policy: DurationPolicy
    character_ids: list[str] = Field(default_factory=list)
    continuity_constraints: list[str] = Field(default_factory=list)
    visual_strategy: VisualStrategy
    required_asset_roles: list[AssetRoleRequirement] = Field(default_factory=list)
    motion_directives: list[MotionDirective] = Field(default_factory=list)
    generated_video_rationale: str | None = None
    hybrid_layers: list[HybridLayer] = Field(default_factory=list)
    composition_directives: list[CompositionDirective] = Field(default_factory=list)
    review_policy: ReviewPolicy = Field(default_factory=ReviewPolicy)
~~~

Use these exact supporting definitions:

~~~python
class DeliveryProfile(StrictModel):
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    fps: int = Field(gt=0)
    codec_profile: str = "h264"


class VoiceProfile(StrictModel):
    language: str
    voice_hint: str
    notes: str = ""


class DurationPolicy(StrictModel):
    mode: Literal["fixed", "voice_driven", "content_driven"]
    seconds: float | None = Field(default=None, gt=0)
    minimum_seconds: float | None = Field(default=None, gt=0)
    maximum_seconds: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _validate_bounds(self) -> "DurationPolicy":
        if self.mode == "fixed" and self.seconds is None:
            raise ValueError("fixed duration policy requires seconds")
        if (
            self.minimum_seconds is not None
            and self.maximum_seconds is not None
            and self.minimum_seconds > self.maximum_seconds
        ):
            raise ValueError("minimum_seconds cannot exceed maximum_seconds")
        return self


class CompositionDirective(StrictModel):
    kind: Literal["fit", "position", "crop", "text", "transition_hint"]
    parameters: dict[str, float | int | str | bool] = Field(default_factory=dict)


class RendererPolicy(StrictModel):
    allowed: list[Literal["hyperframes", "remotion"]] = Field(
        default_factory=lambda: ["hyperframes"]
    )
    default_preference: Literal["hyperframes", "remotion"] = "hyperframes"

    @model_validator(mode="after")
    def _default_is_allowed(self) -> "RendererPolicy":
        if self.default_preference not in self.allowed:
            raise ValueError("renderer default_preference must be present in allowed")
        return self


class ProjectArtifactRefs(StrictModel):
    brief: Path
    story: Path
    characters: list[Path]
    scenes: list[Path]
    storyboard: Path
    shots: list[Path]
    state_manifest: Path = Path("state/manifest.json")


class ProductionBrief(VersionedArtifact):
    title: str
    objective: str
    audience: str
    format: str
    language: str
    constraints: list[str] = Field(default_factory=list)


class StoryBeat(StrictModel):
    beat_id: str
    summary: str


class StoryboardBeat(StrictModel):
    beat_id: str
    scene_id: str
    shot_ids: list[str] = Field(min_length=1)
    narrative_intent: str


class VisualStrategy(str, Enum):
    STATIC_IMAGE = "static_image"
    IMAGE_MOTION = "image_motion"
    MOTION_GRAPHICS = "motion_graphics"
    GENERATED_VIDEO = "generated_video"
    EXISTING_VIDEO = "existing_video"
    HYBRID = "hybrid"


class AssetType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    VOICE = "voice"
    MUSIC = "music"
    SFX = "sfx"
    CAPTION = "caption"
    COMPOSITION_SOURCE = "composition_source"
    RENDER = "render"
    REVIEW_EVIDENCE = "review_evidence"


class AssetRoleRequirement(StrictModel):
    role: str
    allowed_asset_types: list[AssetType] = Field(min_length=1)


class MotionDirective(StrictModel):
    kind: Literal["pan", "zoom", "parallax", "reveal", "layered"]
    parameters: dict[str, float | int | str] = Field(min_length=1)


class HybridLayer(StrictModel):
    role: str
    asset_role: str
    z_index: int


class ReviewPolicy(StrictModel):
    required_checks: list[str] = Field(default_factory=list)


class AssetSourceKind(str, Enum):
    IMPORTED = "imported"
    GENERATED = "generated"
    DERIVED = "derived"


class ToolIdentity(StrictModel):
    name: str
    version: str


class EgressMetadata(StrictModel):
    remote: Literal[False] = False
    destination: None = None
    authorization_receipt_id: None = None


class AssetRecord(StrictModel):
    asset_id: str
    asset_type: AssetType
    artifact_path: Path
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    size_bytes: int = Field(ge=0)
    mime_type: str
    duration_seconds: float | None = Field(default=None, ge=0)
    width: int | None = Field(default=None, gt=0)
    height: int | None = Field(default=None, gt=0)
    source_kind: AssetSourceKind
    tool: ToolIdentity
    input_artifact_ids: list[str] = Field(default_factory=list)
    input_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    creation_receipt_id: str
    usage_license: str
    egress: EgressMetadata = Field(default_factory=EgressMetadata)
    cost_receipt_id: str | None = None


class AssetRegistrySnapshot(StrictModel):
    schema_version: Literal["2.0"] = "2.0"
    revision_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    assets: list[AssetRecord]


class ProductionManifest(StrictModel):
    schema_version: Literal["2.0"] = "2.0"
    project_id: str
    active_project_revision: int = Field(ge=1)
    active_registry_revision: str = Field(pattern=r"^[0-9a-f]{64}$")


class LoadedProductionProject(StrictModel):
    root: Path
    project: ProductionProject
    manifest: ProductionManifest
    brief: ProductionBrief
    story: Story
    characters: list[Character]
    scenes: list[Scene]
    storyboard: Storyboard
    shots: list[Shot]
    registry: AssetRegistrySnapshot
    asset_paths: dict[str, Path]
~~~

Every field listed above must be concrete; no provider request, timeline, lifecycle or renderer execution model belongs in this file. Keep the file under 800 lines.

- [ ] **Step 6: Export model entry points**

Create `src/ai_video/production/__init__.py`:

~~~python
from ai_video.production.models import (
    AssetRecord,
    AssetRegistrySnapshot,
    Character,
    LoadedProductionProject,
    ProductionBrief,
    ProductionManifest,
    ProductionProject,
    Scene,
    Shot,
    Story,
    Storyboard,
    VisualStrategy,
)

__all__ = [
    "AssetRecord",
    "AssetRegistrySnapshot",
    "Character",
    "LoadedProductionProject",
    "ProductionBrief",
    "ProductionManifest",
    "ProductionProject",
    "Scene",
    "Shot",
    "Story",
    "Storyboard",
    "VisualStrategy",
]
~~~

Do not export a loader before Task 4.

- [ ] **Step 7: Verify and commit**

~~~bash
python -m pytest tests/test_production_models.py tests/test_errors.py -q
git add src/ai_video/production/__init__.py \
  src/ai_video/production/models.py \
  src/ai_video/production/hashing.py \
  src/ai_video/errors.py \
  tests/test_production_models.py
git commit -m "feat: add production project core schemas"
~~~

Expected: tests exit `0` and commit contains only listed files.

### Task 2: Validate Visual Strategies and Creative References

**Files:**
- Create: `src/ai_video/production/validation.py`
- Test: `tests/test_production_validation.py`

- [ ] **Step 1: Write RED tests**

Cover one positive case for each strategy and negative cases for:

~~~python
def test_image_motion_requires_deterministic_motion(make_shot):
    shot = make_shot(
        VisualStrategy.IMAGE_MOTION,
        required_asset_roles=[
            AssetRoleRequirement(role="hero", allowed_asset_types=[AssetType.IMAGE])
        ],
    )
    with pytest.raises(AiVideoError) as exc:
        validate_shot_strategy(shot)
    assert exc.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID
    assert "motion_directives" in exc.value.user_message


def test_hybrid_requires_declared_layers(make_shot):
    shot = make_shot(
        VisualStrategy.HYBRID,
        required_asset_roles=[
            AssetRoleRequirement(role="background", allowed_asset_types=[AssetType.IMAGE])
        ],
        hybrid_layers=[
            HybridLayer(role="hero", asset_role="missing", z_index=1),
            HybridLayer(role="background", asset_role="background", z_index=0),
        ],
    )
    with pytest.raises(AiVideoError) as exc:
        validate_shot_strategy(shot)
    assert "missing" in exc.value.user_message
~~~

Also test unknown/duplicate Character, Scene, Storyboard beat and Shot IDs, and unknown Character/Scene asset references.

- [ ] **Step 2: Run RED**

~~~bash
python -m pytest tests/test_production_validation.py -q
~~~

Expected: collection fails because `validation.py` does not exist.

- [ ] **Step 3: Implement the single validator**

Create `validation.py` with:

~~~python
def _invalid(message: str) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.PRODUCTION_PROJECT_INVALID,
        user_message=message,
        retryable=False,
    )


def _has_type(shot: Shot, asset_type: AssetType) -> bool:
    return any(asset_type in role.allowed_asset_types for role in shot.required_asset_roles)


def validate_shot_strategy(shot: Shot) -> None:
    roles = {item.role for item in shot.required_asset_roles}
    if len(roles) != len(shot.required_asset_roles):
        raise _invalid(f"Shot {shot.shot_id} has duplicate required asset roles.")
    if shot.visual_strategy is VisualStrategy.STATIC_IMAGE and not _has_type(
        shot, AssetType.IMAGE
    ):
        raise _invalid(f"Shot {shot.shot_id} static_image requires an image role.")
    if shot.visual_strategy is VisualStrategy.IMAGE_MOTION:
        if not _has_type(shot, AssetType.IMAGE):
            raise _invalid(f"Shot {shot.shot_id} image_motion requires an image role.")
        if not shot.motion_directives:
            raise _invalid(f"Shot {shot.shot_id} image_motion requires motion_directives.")
    if shot.visual_strategy is VisualStrategy.MOTION_GRAPHICS and not any(
        _has_type(shot, item)
        for item in (AssetType.IMAGE, AssetType.COMPOSITION_SOURCE)
    ):
        raise _invalid(
            f"Shot {shot.shot_id} motion_graphics requires an image or composition_source role."
        )
    if shot.visual_strategy is VisualStrategy.GENERATED_VIDEO:
        if not _has_type(shot, AssetType.VIDEO):
            raise _invalid(f"Shot {shot.shot_id} generated_video requires a video role.")
        if not shot.generated_video_rationale or not shot.generated_video_rationale.strip():
            raise _invalid(f"Shot {shot.shot_id} generated_video requires a rationale.")
    if shot.visual_strategy is VisualStrategy.EXISTING_VIDEO and not _has_type(
        shot, AssetType.VIDEO
    ):
        raise _invalid(f"Shot {shot.shot_id} existing_video requires a video role.")
    if shot.visual_strategy is VisualStrategy.HYBRID:
        if len(shot.hybrid_layers) < 2:
            raise _invalid(f"Shot {shot.shot_id} hybrid requires at least two layers.")
        layer_roles = [layer.role for layer in shot.hybrid_layers]
        if len(layer_roles) != len(set(layer_roles)):
            raise _invalid(f"Shot {shot.shot_id} hybrid layer roles must be unique.")
        if len({layer.asset_role for layer in shot.hybrid_layers}) < 2:
            raise _invalid(f"Shot {shot.shot_id} hybrid requires two asset roles.")
        missing = sorted({layer.asset_role for layer in shot.hybrid_layers} - roles)
        if missing:
            raise _invalid(
                f"Shot {shot.shot_id} hybrid references undeclared role(s): {', '.join(missing)}"
            )


def _unique(values: list[str], label: str) -> set[str]:
    duplicates = sorted(value for value, count in Counter(values).items() if count > 1)
    if duplicates:
        raise _invalid(f"duplicate {label}: {', '.join(duplicates)}")
    return set(values)


def validate_project_references(bundle: LoadedProductionProject) -> None:
    character_ids = _unique(
        [item.character_id for item in bundle.characters], "character_id"
    )
    scene_ids = _unique([item.scene_id for item in bundle.scenes], "scene_id")
    shot_ids = _unique([item.shot_id for item in bundle.shots], "shot_id")
    beat_ids = _unique([item.beat_id for item in bundle.storyboard.beats], "beat_id")
    asset_ids = _unique([item.asset_id for item in bundle.registry.assets], "asset_id")
    artifact_ids = {
        bundle.brief.artifact_id,
        bundle.story.artifact_id,
        bundle.storyboard.artifact_id,
        *(item.artifact_id for item in bundle.characters),
        *(item.artifact_id for item in bundle.scenes),
        *(item.artifact_id for item in bundle.shots),
    }
    known_inputs = artifact_ids | asset_ids
    for asset in bundle.registry.assets:
        missing_inputs = sorted(set(asset.input_artifact_ids) - known_inputs)
        if missing_inputs:
            raise _invalid(
                f"Asset {asset.asset_id} references unknown input(s): "
                f"{', '.join(missing_inputs)}"
            )

    for scene in bundle.scenes:
        missing_characters = sorted(set(scene.participant_ids) - character_ids)
        missing_assets = sorted(set(scene.visual_reference_asset_ids) - asset_ids)
        if missing_characters or missing_assets:
            raise _invalid(
                f"Scene {scene.scene_id} has unknown references: "
                f"{', '.join(missing_characters + missing_assets)}"
            )
    for character in bundle.characters:
        missing_assets = sorted(set(character.reference_asset_ids) - asset_ids)
        if missing_assets:
            raise _invalid(
                f"Character {character.character_id} references unknown asset(s): "
                f"{', '.join(missing_assets)}"
            )
    storyboard_membership: dict[str, str] = {}
    for beat in bundle.storyboard.beats:
        if beat.scene_id not in scene_ids:
            raise _invalid(f"Storyboard beat {beat.beat_id} references unknown scene.")
        for shot_id in beat.shot_ids:
            if shot_id not in shot_ids:
                raise _invalid(f"Storyboard beat {beat.beat_id} references unknown shot {shot_id}.")
            if shot_id in storyboard_membership:
                raise _invalid(f"Shot {shot_id} appears in multiple storyboard beats.")
            storyboard_membership[shot_id] = beat.beat_id
    for shot in bundle.shots:
        if shot.scene_id not in scene_ids:
            raise _invalid(f"Shot {shot.shot_id} references unknown scene {shot.scene_id}.")
        if shot.storyboard_beat_id not in beat_ids:
            raise _invalid(
                f"Shot {shot.shot_id} references unknown beat {shot.storyboard_beat_id}."
            )
        if storyboard_membership.get(shot.shot_id) != shot.storyboard_beat_id:
            raise _invalid(f"Shot {shot.shot_id} storyboard membership does not match.")
        missing_characters = sorted(set(shot.character_ids) - character_ids)
        if missing_characters:
            raise _invalid(
                f"Shot {shot.shot_id} references unknown character(s): "
                f"{', '.join(missing_characters)}"
            )
        validate_shot_strategy(shot)


def shot_desired_fingerprint(shot: Shot) -> str:
    return canonical_sha256(shot)
~~~

Import `Counter` and the referenced models/helpers. Do not mutate models or calculate dependency edges.

- [ ] **Step 4: Verify and commit**

~~~bash
python -m pytest tests/test_production_models.py tests/test_production_validation.py -q
git add src/ai_video/production/validation.py tests/test_production_validation.py
git commit -m "feat: validate production shot strategies"
~~~

### Task 3: Add Immutable Asset Registry Validation

**Files:**
- Create: `src/ai_video/production/registry.py`
- Test: `tests/test_production_registry.py`

- [ ] **Step 1: Write registry RED tests**

Use one local `assets/files/hero.png` and assert:

~~~python
def test_registry_loads_verified_local_asset(tmp_path):
    path = write_registry(tmp_path)
    snapshot, asset_paths = load_asset_registry(path, tmp_path)
    assert snapshot.assets[0].asset_id == "image-hero-1"
    assert not snapshot.assets[0].artifact_path.is_absolute()
    assert asset_paths["image-hero-1"].is_absolute()


@pytest.mark.parametrize("stored", ["/tmp/outside.png", "../outside.png"])
def test_registry_rejects_unsafe_paths(tmp_path, stored):
    path = write_registry(tmp_path, artifact_path=stored)
    with pytest.raises(AiVideoError) as exc:
        load_asset_registry(path, tmp_path)
    assert exc.value.code is ErrorCode.ASSET_REGISTRY_INVALID
~~~

Also cover duplicate `asset_id`, registry filename/revision mismatch, semantic hash mismatch, missing file, wrong size and wrong file SHA-256.

- [ ] **Step 2: Run RED**

~~~bash
python -m pytest tests/test_production_registry.py -q
~~~

- [ ] **Step 3: Implement registry verification**

Create `registry.py` with:

~~~python
def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.ASSET_REGISTRY_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _resolve_asset_path(root: Path, stored: Path) -> Path:
    if stored.is_absolute() or ".." in stored.parts:
        raise _invalid(f"Asset path must be clean and project-relative: {stored}")
    resolved = (root / stored).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise _invalid(f"Asset path escapes project root: {stored}") from exc
    return resolved


def registry_semantic_sha256(registry: AssetRegistrySnapshot) -> str:
    payload = registry.model_dump(
        mode="json",
        exclude={"content_hash", "revision_id"},
    )
    return canonical_sha256(payload)


def _verify_asset(record: AssetRecord, root: Path) -> Path:
    resolved = _resolve_asset_path(root, record.artifact_path)
    if not resolved.is_file():
        raise _invalid(f"Asset file does not exist: {record.asset_id}", str(resolved))
    if resolved.stat().st_size != record.size_bytes:
        raise _invalid(f"Asset size mismatch: {record.asset_id}", str(resolved))
    if sha256_file(resolved) != record.sha256:
        raise _invalid(f"Asset hash mismatch: {record.asset_id}", str(resolved))
    return resolved


def load_asset_registry(
    path: str | Path,
    project_root: str | Path,
) -> tuple[AssetRegistrySnapshot, dict[str, Path]]:
    registry_path = Path(path)
    try:
        registry = AssetRegistrySnapshot.model_validate_json(
            registry_path.read_text(encoding="utf-8")
        )
    except (OSError, ValidationError, ValueError) as exc:
        raise _invalid(f"Could not load asset registry: {registry_path}", str(exc)) from exc
    ids = [asset.asset_id for asset in registry.assets]
    if len(ids) != len(set(ids)):
        raise _invalid("Asset registry contains duplicate asset_id values.")
    if registry_semantic_sha256(registry) != registry.content_hash:
        raise _invalid("Asset registry content hash does not match.")
    if registry.revision_id != registry.content_hash:
        raise _invalid("Asset registry revision_id must equal content_hash.")
    if registry_path.name != f"registry.{registry.revision_id}.json":
        raise _invalid("Asset registry filename does not match revision_id.")
    asset_paths = {
        item.asset_id: _verify_asset(item, Path(project_root))
        for item in registry.assets
    }
    return registry, asset_paths
~~~

Import `sha256_file` from `ai_video.config`, `ValidationError` from Pydantic and the named production models/helpers. Never mutate the immutable snapshot, scan, write or activate registry state.

- [ ] **Step 4: Verify and commit**

~~~bash
python -m pytest tests/test_production_registry.py -q
git add src/ai_video/production/registry.py tests/test_production_registry.py
git commit -m "feat: add immutable asset registry validation"
~~~

### Task 4: Load and Validate a Complete Production Project

**Files:**
- Create: `src/ai_video/production/project.py`
- Create: `tests/production_project_factory.py`
- Create: `tests/test_production_project.py`
- Modify: `src/ai_video/production/__init__.py`

- [ ] **Step 1: Create the production-path fixture factory**

Create `tests/production_project_factory.py` with `write_production_project(root: Path) -> Path`. It must:

1. instantiate every artifact through the Task 1 Pydantic models;
2. call `seal_artifact()` before YAML serialization;
3. create `project.yaml`, `creative/*.yaml`, `state/manifest.json`, `assets/files/hero.png` and one `assets/registry.<revision>.json`;
4. serialize YAML with `yaml.safe_dump(model.model_dump(mode="json"), sort_keys=False, allow_unicode=True)`;
5. return only the `project.yaml` path so all tests use the production loader.

The exact minimal graph is:

~~~text
project_id: comic-demo
Character: hero
Scene: room (participant hero)
Storyboard beat: beat-1
Shot: shot-1, static_image, role hero_still
Asset: image-hero-1
ProductionManifest: active project revision 1 + exact registry revision
~~~

The registry factory must call `registry_semantic_sha256()`, which excludes both self-referential `content_hash` and `revision_id` fields, set `revision_id == content_hash` and use the same value in its filename and Production Manifest.

- [ ] **Step 2: Write end-to-end RED tests**

Create `tests/test_production_project.py`:

~~~python
import json

import pytest
import yaml

from ai_video.config import load_project
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production import load_production_project
from production_project_factory import write_production_project


def test_load_production_project_returns_verified_bundle(tmp_path):
    loaded = load_production_project(write_production_project(tmp_path))
    assert loaded.project.project_id == "comic-demo"
    assert loaded.shots[0].visual_strategy.value == "static_image"
    path = loaded.asset_paths["image-hero-1"]
    assert path.is_absolute()
    assert ".." not in str(path)


def test_load_rejects_manifest_project_mismatch(tmp_path):
    project_path = write_production_project(tmp_path)
    manifest_path = tmp_path / "state/manifest.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["project_id"] = "other-project"
    manifest_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(AiVideoError) as exc:
        load_production_project(project_path)
    assert exc.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID


def test_load_rejects_tampered_creative_hash(tmp_path):
    project_path = write_production_project(tmp_path)
    story_path = tmp_path / "creative/story.yaml"
    data = yaml.safe_load(story_path.read_text(encoding="utf-8"))
    data["logline"] = "tampered"
    story_path.write_text(yaml.safe_dump(data), encoding="utf-8")
    with pytest.raises(AiVideoError) as exc:
        load_production_project(project_path)
    assert "content hash" in exc.value.user_message


def test_legacy_project_loader_remains_unchanged():
    project = load_project("configs/wan22_fast.project.yaml")
    assert project.project_name == "wan22-fast-demo"
~~~

Also test:

- creative path with `..` and absolute paths are rejected before read;
- active project revision mismatch;
- only `assets/registry.<active_registry_revision>.json` is loaded;
- typed registry errors are not flattened into project errors;
- unknown creative cross-reference fails;
- the loader creates no directories and does not change input mtimes.

- [ ] **Step 3: Run RED**

~~~bash
python -m pytest tests/test_production_project.py -q
~~~

Expected: collection fails because `load_production_project` is not exported.

- [ ] **Step 4: Implement clean input loading**

Create `src/ai_video/production/project.py`:

~~~python
from __future__ import annotations

from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from ai_video.config import load_yaml
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production.hashing import verify_artifact_hash
from ai_video.production.models import (
    Character,
    LoadedProductionProject,
    ProductionBrief,
    ProductionManifest,
    ProductionProject,
    Scene,
    Shot,
    Story,
    Storyboard,
)
from ai_video.production.registry import load_asset_registry
from ai_video.production.validation import validate_project_references

ModelT = TypeVar("ModelT", bound=BaseModel)


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.PRODUCTION_PROJECT_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _resolve_input(root: Path, stored: Path) -> Path:
    if stored.is_absolute() or ".." in stored.parts:
        raise _invalid(f"Production artifact path must be clean and project-relative: {stored}")
    resolved = (root / stored).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise _invalid(f"Production artifact path escapes project root: {stored}") from exc
    return resolved


def _load_yaml_model(path: Path, model_type: type[ModelT]) -> ModelT:
    try:
        model = model_type.model_validate(load_yaml(path))
    except (ValidationError, AiVideoError) as exc:
        raise _invalid(f"Could not load production artifact: {path}", str(exc)) from exc
    if hasattr(model, "content_hash") and not verify_artifact_hash(model):
        raise _invalid(f"Production artifact content hash mismatch: {path}")
    return model


def _load_json_model(path: Path, model_type: type[ModelT]) -> ModelT:
    try:
        return model_type.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError, ValueError) as exc:
        raise _invalid(f"Could not load production state: {path}", str(exc)) from exc
~~~

Implement the loader:

~~~python
def load_production_project(path: str | Path) -> LoadedProductionProject:
    project_path = Path(path).resolve()
    root = project_path.parent
    project = _load_yaml_model(project_path, ProductionProject)
    manifest = _load_json_model(
        _resolve_input(root, project.artifacts.state_manifest),
        ProductionManifest,
    )
    if manifest.project_id != project.project_id:
        raise _invalid("Production manifest project_id does not match project.")
    if manifest.active_project_revision != project.revision:
        raise _invalid("Production manifest active project revision does not match project.")

    registry_path = root / f"assets/registry.{manifest.active_registry_revision}.json"
    registry, asset_paths = load_asset_registry(registry_path, root)
    refs = project.artifacts
    bundle = LoadedProductionProject(
        root=root,
        project=project,
        manifest=manifest,
        brief=_load_yaml_model(_resolve_input(root, refs.brief), ProductionBrief),
        story=_load_yaml_model(_resolve_input(root, refs.story), Story),
        characters=[
            _load_yaml_model(_resolve_input(root, item), Character)
            for item in refs.characters
        ],
        scenes=[
            _load_yaml_model(_resolve_input(root, item), Scene)
            for item in refs.scenes
        ],
        storyboard=_load_yaml_model(
            _resolve_input(root, refs.storyboard),
            Storyboard,
        ),
        shots=[
            _load_yaml_model(_resolve_input(root, item), Shot)
            for item in refs.shots
        ],
        registry=registry,
        asset_paths=asset_paths,
    )
    validate_project_references(bundle)
    return bundle
~~~

Do not catch and reclassify `ASSET_REGISTRY_INVALID`; callers must see which contract failed.

- [ ] **Step 5: Export the loader**

Add to `src/ai_video/production/__init__.py`:

~~~python
from ai_video.production.project import load_production_project

__all__.append("load_production_project")
~~~

- [ ] **Step 6: Verify P2 and Legacy isolation**

~~~bash
python -m pytest \
  tests/test_production_models.py \
  tests/test_production_validation.py \
  tests/test_production_registry.py \
  tests/test_production_project.py \
  tests/test_config.py \
  tests/test_cli.py -q
~~~

Expected: exit `0`; v2 loads only through the new API and Legacy CLI remains exactly `validate`/`run`/`resume`.

- [ ] **Step 7: Commit**

~~~bash
git add src/ai_video/production/__init__.py \
  src/ai_video/production/project.py \
  tests/production_project_factory.py \
  tests/test_production_project.py
git commit -m "feat: load validated production projects"
~~~

### Task 5: Synchronize Verified Product Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/v0.2-runtime-baseline.md`
- Modify: `docs/v0.2-agentic-production-roadmap.md`
- Modify: `docs/agent-primary-contract-matrix.md`

- [ ] **Step 1: Document only the narrow public API**

After Task 1-4 tests pass, add a README subsection with:

~~~python
from ai_video.production import load_production_project

project = load_production_project("projects/example/project.yaml")
~~~

State explicitly that P2 provides importable schemas/static validation and immutable local registry verification, but no public command, renderer, Audio/Caption, dependency graph or Provider. Do not claim a bundled example exists.

- [ ] **Step 2: Update baseline and roadmap from evidence**

In `docs/v0.2-runtime-baseline.md`:

- move only verified P2 models, loader, strategy validation and registry verification to implemented;
- retain P3-P9 and all Legacy resume/final/audio/QA debt as planned/debt;
- record focused and full test commands.

In `docs/v0.2-agentic-production-roadmap.md`:

- mark P2 implemented only after every exit gate passes;
- mark P3/P4/P7 eligible for separate planning, not implemented;
- retain renderer, paid-provider and Base AI Comic gates.

- [ ] **Step 3: Add focused contract checks**

Add to `docs/agent-primary-contract-matrix.md`:

~~~bash
python -m pytest \
  tests/test_production_models.py \
  tests/test_production_validation.py \
  tests/test_production_registry.py \
  tests/test_production_project.py \
  tests/test_config.py \
  tests/test_cli.py -q
~~~

- [ ] **Step 4: Scan claims and commit**

~~~bash
rg -n "P2|ProductionProject|Asset Registry|HyperFrames|Remotion|Audio|dependency graph|Provider" \
  README.md docs/v0.2-runtime-baseline.md docs/v0.2-agentic-production-roadmap.md \
  docs/agent-primary-contract-matrix.md
git add README.md docs/v0.2-runtime-baseline.md \
  docs/v0.2-agentic-production-roadmap.md docs/agent-primary-contract-matrix.md
git commit -m "docs: document production project core"
~~~

Expected: every P3+ capability remains explicitly planned/not implemented.

### Task 6: Run Exit Gates and Independent Review

**Files:**
- Verify: every P2-owned file
- Verify unchanged: Legacy runtime, CLI, dependencies and generated paths

- [ ] **Step 1: Run P2 tests**

~~~bash
python -m pytest \
  tests/test_production_models.py \
  tests/test_production_validation.py \
  tests/test_production_registry.py \
  tests/test_production_project.py -q
~~~

Expected: exit `0` with no skipped P2 test.

- [ ] **Step 2: Run Legacy contract regressions**

~~~bash
python -m pytest \
  tests/test_config.py tests/test_cli.py tests/test_manifest.py \
  tests/test_pipeline.py tests/test_resume_e2e.py \
  tests/test_workflow_loader.py tests/test_workflow_renderer.py -q
~~~

Expected: exit `0`; public commands, Manifest v1, current config/workflow loading, resume and flat layout remain unchanged.

- [ ] **Step 3: Run the full no-network suite**

~~~bash
python -m pytest -q
~~~

Expected: exit `0`. The existing optional Whisper skip may remain; no new P2 skip is allowed.

- [ ] **Step 4: Verify scope**

~~~bash
git diff --check
git status --short
p2_base_commit=$(git merge-base HEAD main)
git diff --name-only "$p2_base_commit"..HEAD
rg -n "hyperframes|remotion|elevenlabs|captions|httpx|requests" \
  src/ai_video/production tests/test_production_*.py tests/production_project_factory.py
~~~

Expected: only the file map changed; no `pyproject.toml`, Legacy manifest/pipeline/CLI or `runs/**` change; no external integration import/network call. If `main` advanced after the feature branch was created, use the exact base commit recorded at the Integration Base Gate instead of the current merge-base.

- [ ] **Step 5: Obtain independent review**

Review brief:

~~~text
Verify P2 against active spec sections 9-11, 15-16 and 20-23.
Check ProductionManifest is the only active revision pointer.
Check Asset Registry is immutable and owns no lifecycle.
Check Shot desired fingerprint is derived rather than mutable state.
Check all six strategies, traversal, tampering and cross-reference tests.
Reject renderer/provider/dependency graph/Legacy runtime scope leak.
~~~

Required verdict: `accept` or `accept with concerns` with no blocking issue. The parent verifies every blocking claim directly.

- [ ] **Step 6: Record branch truth**

~~~bash
git status --short --branch
git log --oneline --decorate -12
git rev-list --left-right --count origin/main...HEAD
~~~

Expected: clean working tree and explicit local-vs-origin state; do not imply push, merge or release without evidence.

## Acceptance Criteria

P2 is complete only when:

1. `ai_video.production` loads an explicit v2 project without changing Legacy loading.
2. Creative models reject unknown fields and carry stable ID, schema version, revision, semantic hash, receipt and provenance.
3. Semantic hash is deterministic and detects content mutation.
4. All six visual strategies have positive and negative tests.
5. Character, Scene, Storyboard and Shot cross-references are verified.
6. Registry rejects duplicate IDs, traversal, wrong revision filename/hash, missing file, wrong size and wrong file hash.
7. Runtime-resolved asset paths are clean absolute paths inside project root.
8. Minimal `ProductionManifest` is the only active project/registry revision pointer.
9. P2 persists no mutable freshness, lifecycle or desired/applied fingerprint.
10. No renderer, Audio/Caption, dependency graph, Provider or network behavior exists.
11. Public CLI remains `validate`, `run` and `resume`.
12. Manifest v1 and `runs/<run_id>/` layout are unchanged.
13. Focused P2, Legacy regression and full no-network suites pass.
14. README, baseline, roadmap and matrix describe only verified behavior.
15. Independent review has no blocking finding.

## Rollback

P2 creates no database migration, cloud resource or provider-side state. Before real user v2 projects are accepted, revert commits in reverse order:

~~~bash
git revert "$(git log -1 --format=%H --grep='^docs: document production project core$')"
git revert "$(git log -1 --format=%H --grep='^feat: load validated production projects$')"
git revert "$(git log -1 --format=%H --grep='^feat: add immutable asset registry validation$')"
git revert "$(git log -1 --format=%H --grep='^feat: validate production shot strategies$')"
git revert "$(git log -1 --format=%H --grep='^feat: add production project core schemas$')"
~~~

Do not delete user-created `projects/**`; after rollback they are unsupported inputs and must be preserved. Legacy configs, Manifest v1 and runs remain usable.

## Next Plan Boundary

After P2 acceptance, these may be planned independently:

- `P3 Deterministic Composition and HyperFrames Adapter Implementation Plan`;
- `P4 Voice and Captions Implementation Plan`;
- `P7 Image Asset Generation Implementation Plan`.

P3 owns `CompositionSpec`, `ResolvedTimeline` and one renderer adapter. P4 owns Audio/Caption data and paid-provider safety. P7 owns image generation/provenance. None may redefine P2 schema, registry, active pointers or strategy semantics without a versioned migration plan.
