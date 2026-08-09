# AI-VIDEO Agentic Production Harness P2 Production Project Core Implementation Plan

> **For agentic workers:** 实施本 plan 时，REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans。按 Task 顺序执行，并使用 checkbox (`- [ ]`) 跟踪进度。

**Goal:** 在不改变 Legacy CLI、Manifest v1、`runs/<run_id>/` layout 或引入 renderer/provider 的前提下，实现可加载、可哈希、可静态校验的 v2 `ProductionProject`、creative artifacts、Shot visual strategy 和 immutable Asset Registry core。

**Architecture:** 新能力隔离在 `src/ai_video/production/`；Pydantic models 拥有 schema，pure validators 拥有 cross-reference 和 visual-strategy rules，`registry.py` 拥有 immutable registry snapshot 校验，`project.py` 是完整 bundle 的唯一 loader。P2 只读取一个最小 `ProductionManifest` 作为 active project/registry revision pointer，不实现 P5 的 dependency graph、fresh/stale lifecycle、desired/applied state 或 selective rebuild。

**Tech Stack:** Python 3.11+、Pydantic v2、PyYAML、pytest、现有 `AiVideoError`/`ErrorCode`、`hashlib` 和本地 filesystem；不新增 runtime dependency，不调用 ComfyUI、ffmpeg、HyperFrames、Remotion、ElevenLabs、Captions 或任何 network Provider。

---

Status: Approved for implementation by the user's explicit execution request and blocker-resolution choice on 2026-08-09.

## Scope and Authorization

P2 只实现：

- strict v2 `ProductionProject` 和 creative artifact schema；
- `ProductionBrief`、`Story`、`Character`、`Scene`、`Storyboard`、`Shot`；
- 六种 `visual_strategy` 及 strategy-specific static validation；
- deterministic semantic content hash；
- frozen `AssetRecord` / `AssetRegistrySnapshot` 的 read-only content-addressed verification；
- 最小只读 `ProductionManifest` active revision pointer；
- Manifest-owned active project content hash/revision、project-relative containment、artifact hash/file hash 和 concrete Shot-to-Asset cross-reference validation；
- importable Python loading API 和 no-network tests。

P2 明确不实现：

- 新 CLI command、flag 或 exit code；
- 修改 Legacy `ProjectConfig`、`ShotSpec`、`RunManifest`、pipeline 或 resume；
- 修改 `runs/<run_id>/` layout；
- artifact generation、renderer、timeline、Audio、Caption、QA/repair；
- dependency graph、fresh/stale、desired/applied state、selective rebuild；
- registry activation/write transaction、append-only cross-revision enforcement、GC 或 migration tool；首个写入/激活 v2 snapshot 的后续 slice 必须实现 atomic commit protocol 和 crash-injection tests；
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
| envelope hash | `src/ai_video/production/hashing.py` | Reuse `config.sha256_file()` for file bytes; P5 owns desired fingerprint projection |
| safe input path | `src/ai_video/production/paths.py` | No permissive reuse of Legacy absolute-path resolution |
| strategy/reference rules | `src/ai_video/production/validation.py` | Do not reuse ordered-shot or QA heuristics |
| registry validation | `src/ai_video/production/registry.py` | No discovery, lifecycle or provider calls |
| bundle loader | `src/ai_video/production/project.py` | Do not branch Legacy `load_project()` |
| active revision | minimal v2 `ProductionManifest` with project revision/hash and registry revision | Do not modify Manifest v1; P5 extends v2 lifecycle state |
| public API | `src/ai_video/production/__init__.py` | No P2 public CLI |

P2 不定义 `Shot.desired_fingerprint`。`content_hash` 封印完整 immutable artifact envelope，包括 revision、receipt 和 provenance；P5 另行定义排除 envelope/lifecycle metadata 的 desired fingerprint projection，并只在 Production Manifest 中持久化 desired/applied state。

## File Map

Create:

- `src/ai_video/production/{__init__,models,hashing,paths,validation,registry,project}.py`
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

- [x] **Step 1: Write failing schema and hash tests**

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

- [x] **Step 2: Run RED**

~~~bash
python -m pytest tests/test_production_models.py -q
~~~

Expected: collection fails because `ai_video.production` does not exist.

- [x] **Step 3: Add typed error codes**

Add to `ErrorCode`:

~~~python
    PRODUCTION_PROJECT_INVALID = "production_project_invalid"
    ASSET_REGISTRY_INVALID = "asset_registry_invalid"
~~~

- [x] **Step 4: Implement semantic hashing**

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

- [x] **Step 5: Implement the model contract**

Create `src/ai_video/production/models.py` with:

~~~python
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


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
    source_provenance: tuple[SourceReference, ...] = Field(min_length=1)


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
    beats: tuple[StoryBeat, ...] = Field(min_length=1)
    source_references: tuple[str, ...] = ()


class Character(VersionedArtifact):
    character_id: str
    name: str
    identity: str
    appearance_bible: str
    wardrobe: tuple[str, ...] = ()
    voice_profile: VoiceProfile | None = None
    reference_asset_ids: tuple[str, ...] = ()
    allowed_variations: tuple[str, ...] = ()


class Scene(VersionedArtifact):
    scene_id: str
    location: str
    time: str
    mood: str
    participant_ids: tuple[str, ...] = ()
    continuity_constraints: tuple[str, ...] = ()
    visual_reference_asset_ids: tuple[str, ...] = ()


class Storyboard(VersionedArtifact):
    beats: tuple[StoryboardBeat, ...] = Field(min_length=1)


class Shot(VersionedArtifact):
    shot_id: str
    scene_id: str
    storyboard_beat_id: str
    intent: str
    dialogue: str = ""
    narration: str = ""
    duration_policy: DurationPolicy
    character_ids: tuple[str, ...] = ()
    continuity_constraints: tuple[str, ...] = ()
    visual_strategy: VisualStrategy
    required_asset_roles: tuple[AssetRoleRequirement, ...] = ()
    motion_directives: tuple[MotionDirective, ...] = ()
    generated_video_rationale: str | None = None
    hybrid_layers: tuple[HybridLayer, ...] = ()
    composition_directives: tuple[CompositionDirective, ...] = ()
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
    allowed: tuple[Literal["hyperframes", "remotion"], ...] = Field(
        default_factory=lambda: ["hyperframes"]
    )
    default_preference: Literal["hyperframes", "remotion"] = "hyperframes"

    @model_validator(mode="after")
    def _default_is_allowed(self) -> "RendererPolicy":
        if self.default_preference not in self.allowed:
            raise ValueError("renderer default_preference must be present in allowed")
        return self


class ArtifactReference(StrictModel):
    artifact_id: str = Field(min_length=1)
    revision: int = Field(ge=1)
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    path: Path


class ProjectArtifactRefs(StrictModel):
    brief: ArtifactReference
    story: ArtifactReference
    characters: tuple[ArtifactReference, ...]
    scenes: tuple[ArtifactReference, ...]
    storyboard: ArtifactReference
    shots: tuple[ArtifactReference, ...]


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
    shot_ids: tuple[str, ...] = Field(min_length=1)
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
    asset_ids: tuple[str, ...] = Field(min_length=1)
    allowed_asset_types: tuple[AssetType, ...] = Field(min_length=1)


class MotionDirective(StrictModel):
    kind: Literal[
        "pan", "zoom", "parallax", "reveal", "layered", "animate", "particles", "transition"
    ]
    parameters: dict[str, float | int | str] = Field(min_length=1)


class HybridLayer(StrictModel):
    role: str
    asset_role: str
    asset_id: str
    z_index: int


class ReviewPolicy(StrictModel):
    required_checks: tuple[str, ...] = ()


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
    input_artifact_ids: tuple[str, ...] = ()
    input_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    creation_receipt_id: str
    usage_license: str
    egress: EgressMetadata = Field(default_factory=EgressMetadata)
    cost_receipt_id: str | None = None


class AssetRegistrySnapshot(StrictModel):
    schema_version: Literal["2.0"] = "2.0"
    revision_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    assets: tuple[AssetRecord, ...]


class ProductionManifest(StrictModel):
    schema_version: Literal["2.0"] = "2.0"
    project_id: str
    active_project_revision: int = Field(ge=1)
    active_project_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    active_registry_revision: str = Field(pattern=r"^[0-9a-f]{64}$")


class LoadedProductionProject(StrictModel):
    root: Path
    project: ProductionProject
    manifest: ProductionManifest
    brief: ProductionBrief
    story: Story
    characters: tuple[Character, ...]
    scenes: tuple[Scene, ...]
    storyboard: Storyboard
    shots: tuple[Shot, ...]
    registry: AssetRegistrySnapshot
    asset_paths: dict[str, Path]
~~~

Every field listed above must be concrete; no provider request, timeline, lifecycle or renderer execution model belongs in this file. Keep the file under 800 lines.

- [x] **Step 6: Export model entry points**

Create `src/ai_video/production/__init__.py`:

~~~python
from ai_video.production.models import (
    ArtifactReference,
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
    "ArtifactReference",
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

- [x] **Step 7: Verify and commit**

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

- [x] **Step 1: Write RED tests**

Cover one positive case for each strategy and negative cases for:

~~~python
def test_image_motion_requires_deterministic_motion(make_shot):
    shot = make_shot(
        VisualStrategy.IMAGE_MOTION,
        required_asset_roles=[
            AssetRoleRequirement(
                role="hero",
                asset_ids=["image-hero-1"],
                allowed_asset_types=[AssetType.IMAGE],
            )
        ],
    )
    with pytest.raises(AiVideoError) as exc:
        validate_shot_strategy(shot, asset_records())
    assert exc.value.code is ErrorCode.PRODUCTION_PROJECT_INVALID
    assert "motion_directives" in exc.value.user_message


def test_hybrid_requires_declared_layers(make_shot):
    shot = make_shot(
        VisualStrategy.HYBRID,
        required_asset_roles=[
            AssetRoleRequirement(
                role="background",
                asset_ids=["image-background-1"],
                allowed_asset_types=[AssetType.IMAGE],
            )
        ],
        hybrid_layers=[
            HybridLayer(
                role="hero",
                asset_role="missing",
                asset_id="image-hero-1",
                z_index=1,
            ),
            HybridLayer(
                role="background",
                asset_role="background",
                asset_id="image-background-1",
                z_index=0,
            ),
        ],
    )
    with pytest.raises(AiVideoError) as exc:
        validate_shot_strategy(shot, asset_records())
    assert "missing" in exc.value.user_message
~~~

Also test one positive case for every strategy plus unknown/duplicate Character, Scene,
Storyboard beat, Shot and artifact IDs; unknown Character/Scene asset references; unbound or
unknown Shot asset IDs; wrong bound asset type/source kind; `motion_graphics` without an
animation directive; `hybrid` missing a concrete source; and Storyboard beat/Shot scene mismatch.

- [x] **Step 2: Run RED**

~~~bash
python -m pytest tests/test_production_validation.py -q
~~~

Expected: collection fails because `validation.py` does not exist.

- [x] **Step 3: Implement the single validator**

Create `validation.py` with:

~~~python
def _invalid(message: str) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.PRODUCTION_PROJECT_INVALID,
        user_message=message,
        retryable=False,
    )


def _role_bindings(shot: Shot) -> dict[str, AssetRoleRequirement]:
    roles = [item.role for item in shot.required_asset_roles]
    if len(roles) != len(set(roles)):
        raise _invalid(f"Shot {shot.shot_id} has duplicate required asset roles.")
    for item in shot.required_asset_roles:
        if len(item.asset_ids) != len(set(item.asset_ids)):
            raise _invalid(f"Shot {shot.shot_id} role {item.role} has duplicate asset IDs.")
    return {item.role: item for item in shot.required_asset_roles}


def _bound_assets(
    shot: Shot,
    assets_by_id: dict[str, AssetRecord],
) -> tuple[dict[str, AssetRoleRequirement], dict[str, AssetRecord]]:
    roles = _role_bindings(shot)
    bound: dict[str, AssetRecord] = {}
    for role in roles.values():
        for asset_id in role.asset_ids:
            asset = assets_by_id.get(asset_id)
            if asset is None:
                raise _invalid(
                    f"Shot {shot.shot_id} role {role.role} references unknown asset {asset_id}."
                )
            if asset.asset_type not in role.allowed_asset_types:
                raise _invalid(
                    f"Shot {shot.shot_id} role {role.role} rejects asset type "
                    f"{asset.asset_type.value}."
                )
            bound[asset_id] = asset
    return roles, bound


def _has_type(bound: dict[str, AssetRecord], asset_type: AssetType) -> bool:
    return any(asset.asset_type is asset_type for asset in bound.values())


def validate_shot_strategy(
    shot: Shot,
    assets_by_id: dict[str, AssetRecord],
) -> None:
    roles, bound = _bound_assets(shot, assets_by_id)
    if shot.visual_strategy is VisualStrategy.STATIC_IMAGE and not _has_type(
        bound, AssetType.IMAGE
    ):
        raise _invalid(f"Shot {shot.shot_id} static_image requires an image role.")
    if shot.visual_strategy is VisualStrategy.IMAGE_MOTION:
        if not _has_type(bound, AssetType.IMAGE):
            raise _invalid(f"Shot {shot.shot_id} image_motion requires an image role.")
        if not shot.motion_directives:
            raise _invalid(f"Shot {shot.shot_id} image_motion requires motion_directives.")
    if shot.visual_strategy is VisualStrategy.MOTION_GRAPHICS:
        if not any(
            _has_type(bound, item)
            for item in (AssetType.IMAGE, AssetType.COMPOSITION_SOURCE)
        ):
            raise _invalid(
                f"Shot {shot.shot_id} motion_graphics requires an image or "
                "composition_source role."
            )
        if not shot.motion_directives:
            raise _invalid(
                f"Shot {shot.shot_id} motion_graphics requires motion_directives."
            )
    if shot.visual_strategy is VisualStrategy.GENERATED_VIDEO:
        generated_videos = [
            asset
            for asset in bound.values()
            if asset.asset_type is AssetType.VIDEO
            and asset.source_kind is AssetSourceKind.GENERATED
        ]
        if not generated_videos:
            raise _invalid(f"Shot {shot.shot_id} generated_video requires a video role.")
        if not shot.generated_video_rationale or not shot.generated_video_rationale.strip():
            raise _invalid(f"Shot {shot.shot_id} generated_video requires a rationale.")
    if shot.visual_strategy is VisualStrategy.EXISTING_VIDEO:
        imported_videos = [
            asset
            for asset in bound.values()
            if asset.asset_type is AssetType.VIDEO
            and asset.source_kind is AssetSourceKind.IMPORTED
        ]
        if not imported_videos:
            raise _invalid(f"Shot {shot.shot_id} existing_video requires an imported video role.")
    if shot.visual_strategy is VisualStrategy.HYBRID:
        if len(shot.hybrid_layers) < 2:
            raise _invalid(f"Shot {shot.shot_id} hybrid requires at least two layers.")
        layer_roles = [layer.role for layer in shot.hybrid_layers]
        if len(layer_roles) != len(set(layer_roles)):
            raise _invalid(f"Shot {shot.shot_id} hybrid layer roles must be unique.")
        if len({layer.asset_id for layer in shot.hybrid_layers}) < 2:
            raise _invalid(f"Shot {shot.shot_id} hybrid requires two source assets.")
        for layer in shot.hybrid_layers:
            role = roles.get(layer.asset_role)
            if role is None:
                raise _invalid(
                    f"Shot {shot.shot_id} hybrid references undeclared role {layer.asset_role}."
                )
            if layer.asset_id not in role.asset_ids:
                raise _invalid(
                    f"Shot {shot.shot_id} hybrid source {layer.asset_id} is not bound "
                    f"to role {layer.asset_role}."
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
    artifact_ids = _unique([
        bundle.brief.artifact_id,
        bundle.story.artifact_id,
        bundle.storyboard.artifact_id,
        *(item.artifact_id for item in bundle.characters),
        *(item.artifact_id for item in bundle.scenes),
        *(item.artifact_id for item in bundle.shots),
    ], "artifact_id")
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
            shot = next(item for item in bundle.shots if item.shot_id == shot_id)
            if shot.scene_id != beat.scene_id:
                raise _invalid(
                    f"Storyboard beat {beat.beat_id} scene does not match Shot {shot_id}."
                )
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
        validate_shot_strategy(
            shot,
            {item.asset_id: item for item in bundle.registry.assets},
        )
~~~

Import `Counter` and the referenced models. Do not mutate models, calculate dependency edges or
define a desired fingerprint; P5 owns that projection.

- [x] **Step 4: Verify and commit**

~~~bash
python -m pytest tests/test_production_models.py tests/test_production_validation.py -q
git add src/ai_video/production/validation.py tests/test_production_validation.py
git commit -m "feat: validate production shot strategies"
~~~

### Task 3: Add Immutable Asset Registry Validation

**Files:**
- Create: `src/ai_video/production/paths.py`
- Create: `src/ai_video/production/registry.py`
- Test: `tests/test_production_registry.py`

- [x] **Step 1: Write registry RED tests**

Use one local `assets/files/hero.png` and assert:

~~~python
def test_registry_loads_verified_local_asset(tmp_path):
    path = write_registry(tmp_path)
    snapshot, asset_paths = load_asset_registry(
        path.relative_to(tmp_path),
        tmp_path,
        tmp_path / "assets/files",
    )
    assert snapshot.assets[0].asset_id == "image-hero-1"
    assert not snapshot.assets[0].artifact_path.is_absolute()
    assert asset_paths["image-hero-1"].is_absolute()


@pytest.mark.parametrize("stored", ["/tmp/outside.png", "../outside.png"])
def test_registry_rejects_unsafe_paths(tmp_path, stored):
    path = write_registry(tmp_path, artifact_path=stored)
    with pytest.raises(AiVideoError) as exc:
        load_asset_registry(
            path.relative_to(tmp_path),
            tmp_path,
            tmp_path / "assets/files",
        )
    assert exc.value.code is ErrorCode.ASSET_REGISTRY_INVALID
~~~

Also cover duplicate `asset_id`, registry filename/revision mismatch, semantic hash mismatch,
missing file, wrong size, wrong file SHA-256, registry-file symlink escape, asset-file
symlink escape, an internal symlink that remains inside `asset_root`, and unsafe `asset_root`.

- [x] **Step 2: Run RED**

~~~bash
python -m pytest tests/test_production_registry.py -q
~~~

- [x] **Step 3: Implement registry verification**

Create `paths.py` with the single project-containment owner:

~~~python
from __future__ import annotations

from pathlib import Path


def resolve_contained_path(
    project_root: Path,
    stored: Path,
    *,
    allowed_root: Path | None = None,
) -> Path:
    if stored.is_absolute() or ".." in stored.parts:
        raise ValueError(f"Path must be clean and project-relative: {stored}")
    root = project_root.resolve()
    boundary = (allowed_root or root).resolve()
    try:
        boundary.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Allowed root escapes project root: {boundary}") from exc
    resolved = (root / stored).resolve()
    try:
        resolved.relative_to(boundary)
    except ValueError as exc:
        raise ValueError(f"Path escapes allowed root: {stored}") from exc
    return resolved
~~~

Internal symlinks are allowed only when their resolved target remains inside `allowed_root`.
Create `registry.py` with:

~~~python
def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.ASSET_REGISTRY_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def registry_semantic_sha256(registry: AssetRegistrySnapshot) -> str:
    payload = registry.model_dump(
        mode="json",
        exclude={"content_hash", "revision_id"},
    )
    return canonical_sha256(payload)


def _verify_asset(record: AssetRecord, root: Path, asset_root: Path) -> Path:
    try:
        resolved = resolve_contained_path(
            root,
            record.artifact_path,
            allowed_root=asset_root,
        )
    except ValueError as exc:
        raise _invalid(f"Asset path is unsafe: {record.asset_id}", str(exc)) from exc
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
    asset_root: str | Path,
) -> tuple[AssetRegistrySnapshot, dict[str, Path]]:
    root = Path(project_root).resolve()
    try:
        registry_path = resolve_contained_path(
            root,
            Path(path),
            allowed_root=root / "assets",
        )
        resolved_asset_root = Path(asset_root).resolve()
        resolved_asset_root.relative_to(root)
    except ValueError as exc:
        raise _invalid("Asset registry path configuration is unsafe.", str(exc)) from exc
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
        item.asset_id: _verify_asset(item, root, resolved_asset_root)
        for item in registry.assets
    }
    return registry, asset_paths
~~~

Import `sha256_file` from `ai_video.config`, `ValidationError` from Pydantic,
`resolve_contained_path` from `paths.py` and the named production models/helpers. Never
mutate the frozen snapshot, scan, write or activate registry state. This verifies one
content-addressed snapshot; it does not prove append-only history or cross-file crash safety.

- [x] **Step 4: Verify and commit**

~~~bash
python -m pytest tests/test_production_registry.py -q
git add src/ai_video/production/paths.py \
  src/ai_video/production/registry.py tests/test_production_registry.py
git commit -m "feat: add immutable asset registry validation"
~~~

### Task 4: Load and Validate a Complete Production Project

**Files:**
- Create: `src/ai_video/production/project.py`
- Create: `tests/production_project_factory.py`
- Create: `tests/test_production_project.py`
- Modify: `src/ai_video/production/__init__.py`

- [x] **Step 1: Create the production-path fixture factory**

Create `tests/production_project_factory.py` with `write_production_project(root: Path) -> Path`. It must:

1. instantiate every artifact through the Task 1 Pydantic models;
2. call `seal_artifact()` before YAML serialization;
3. create an `ArtifactReference` from each sealed creative artifact's exact ID, revision,
   content hash and path before sealing `ProductionProject`;
4. create `project.yaml`, `creative/*.yaml`, `state/manifest.json`, `assets/files/hero.png` and one `assets/registry.<revision>.json`;
5. set `ProductionManifest.active_project_content_hash` to the sealed project's exact hash;
6. serialize YAML with `yaml.safe_dump(model.model_dump(mode="json"), sort_keys=False, allow_unicode=True)`;
7. return only the `project.yaml` path so all tests use the production loader.

The exact minimal graph is:

~~~text
project_id: comic-demo
Character: hero
Scene: room (participant hero)
Storyboard beat: beat-1
Shot: shot-1, static_image, role hero_still
Asset: image-hero-1
ProductionManifest: active project revision 1 + exact project content hash + exact registry revision
~~~

The registry factory must call `registry_semantic_sha256()`, which excludes both self-referential `content_hash` and `revision_id` fields, set `revision_id == content_hash` and use the same value in its filename and Production Manifest.

- [x] **Step 2: Write end-to-end RED tests**

Create `tests/test_production_project.py`:

~~~python
import json

import pytest
import yaml

from ai_video.config import load_project
from ai_video.errors import AiVideoError, ErrorCode
from ai_video.production import load_production_project
from ai_video.production.hashing import seal_artifact
from ai_video.production.models import ProductionProject
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


def test_load_rejects_same_revision_with_unselected_content_hash(tmp_path):
    project_path = write_production_project(tmp_path)
    data = yaml.safe_load(project_path.read_text(encoding="utf-8"))
    data["title"] = "A different sealed project"
    replacement = seal_artifact(ProductionProject.model_validate(data))
    project_path.write_text(
        yaml.safe_dump(replacement.model_dump(mode="json"), allow_unicode=True),
        encoding="utf-8",
    )
    with pytest.raises(AiVideoError) as exc:
        load_production_project(project_path)
    assert "active project content hash" in exc.value.user_message


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
- same integer project revision with a different valid sealed content hash;
- creative artifact ID/revision/content-hash mismatch against its `ArtifactReference`;
- only `assets/registry.<active_registry_revision>.json` is loaded;
- typed registry errors are not flattened into project errors;
- unknown creative cross-reference fails;
- the loader creates no directories and does not change input mtimes.

- [x] **Step 3: Run RED**

~~~bash
python -m pytest tests/test_production_project.py -q
~~~

Expected: collection fails because `load_production_project` is not exported.

- [x] **Step 4: Implement clean input loading**

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
    ArtifactReference,
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
from ai_video.production.paths import resolve_contained_path
from ai_video.production.validation import validate_project_references

ModelT = TypeVar("ModelT", bound=BaseModel)


def _invalid(message: str, detail: str | None = None) -> AiVideoError:
    return AiVideoError(
        code=ErrorCode.PRODUCTION_PROJECT_INVALID,
        user_message=message,
        technical_detail=detail,
        retryable=False,
    )


def _resolve_input(
    root: Path,
    stored: Path,
    *,
    allowed_root: Path | None = None,
) -> Path:
    try:
        return resolve_contained_path(root, stored, allowed_root=allowed_root)
    except ValueError as exc:
        raise _invalid(
            f"Production artifact path must be clean and contained: {stored}",
            str(exc),
        ) from exc


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


def _load_referenced_artifact(
    root: Path,
    reference: ArtifactReference,
    model_type: type[ModelT],
) -> ModelT:
    model = _load_yaml_model(_resolve_input(root, reference.path), model_type)
    actual = (model.artifact_id, model.revision, model.content_hash)
    expected = (reference.artifact_id, reference.revision, reference.content_hash)
    if actual != expected:
        raise _invalid(
            f"Production artifact does not match its project reference: {reference.path}"
        )
    return model
~~~

Implement the loader:

~~~python
def load_production_project(path: str | Path) -> LoadedProductionProject:
    supplied_path = Path(path)
    if supplied_path.name != "project.yaml":
        raise _invalid("Production project entry point must be named project.yaml.")
    root = supplied_path.parent.resolve()
    project_path = _resolve_input(root, Path("project.yaml"))
    manifest = _load_json_model(
        _resolve_input(root, Path("state/manifest.json")),
        ProductionManifest,
    )
    project = _load_yaml_model(project_path, ProductionProject)
    if manifest.project_id != project.project_id:
        raise _invalid("Production manifest project_id does not match project.")
    if manifest.active_project_revision != project.revision:
        raise _invalid("Production manifest active project revision does not match project.")
    if manifest.active_project_content_hash != project.content_hash:
        raise _invalid("Production manifest active project content hash does not match project.")

    registry_path = Path(f"assets/registry.{manifest.active_registry_revision}.json")
    asset_root = _resolve_input(root, project.asset_root)
    registry, asset_paths = load_asset_registry(registry_path, root, asset_root)
    refs = project.artifacts
    bundle = LoadedProductionProject(
        root=root,
        project=project,
        manifest=manifest,
        brief=_load_referenced_artifact(root, refs.brief, ProductionBrief),
        story=_load_referenced_artifact(root, refs.story, Story),
        characters=[
            _load_referenced_artifact(root, item, Character)
            for item in refs.characters
        ],
        scenes=[
            _load_referenced_artifact(root, item, Scene)
            for item in refs.scenes
        ],
        storyboard=_load_referenced_artifact(root, refs.storyboard, Storyboard),
        shots=[
            _load_referenced_artifact(root, item, Shot)
            for item in refs.shots
        ],
        registry=registry,
        asset_paths=asset_paths,
    )
    validate_project_references(bundle)
    return bundle
~~~

Do not catch and reclassify `ASSET_REGISTRY_INVALID`; callers must see which contract failed.

- [x] **Step 5: Export the loader**

Add to `src/ai_video/production/__init__.py`:

~~~python
from ai_video.production.project import load_production_project

__all__.append("load_production_project")
~~~

- [x] **Step 6: Verify P2 and Legacy isolation**

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

- [x] **Step 7: Commit**

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

- [x] **Step 1: Document only the narrow public API**

After Task 1-4 tests pass, add a README subsection with:

~~~python
from ai_video.production import load_production_project

project = load_production_project("projects/example/project.yaml")
~~~

State explicitly that P2 provides importable schemas/static validation and read-only
content-addressed local registry verification, but no writer/activation transaction, append-only
history proof, cross-file crash safety, public command, renderer, Audio/Caption, dependency graph
or Provider. Do not claim a bundled example exists.

- [x] **Step 2: Update baseline and roadmap from evidence**

In `docs/v0.2-runtime-baseline.md`:

- move only verified P2 models, loader, strategy validation and registry verification to implemented;
- retain P2A-P9 and all Legacy resume/final/audio/QA debt as planned/debt;
- record focused and full test commands.

In `docs/v0.2-agentic-production-roadmap.md`:

- mark P2 implemented only after every exit gate passes;
- mark P2A as the mandatory write/activation gate and P3/P4/P7 eligible for separate planning but
  not runtime implementation before P2A;
- retain renderer, paid-provider and Base AI Comic gates.

- [x] **Step 3: Add focused contract checks**

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

- [x] **Step 4: Scan claims and commit**

~~~bash
rg -n "P2|ProductionProject|Asset Registry|HyperFrames|Remotion|Audio|dependency graph|Provider" \
  README.md docs/v0.2-runtime-baseline.md docs/v0.2-agentic-production-roadmap.md \
  docs/agent-primary-contract-matrix.md
git add README.md docs/v0.2-runtime-baseline.md \
  docs/v0.2-agentic-production-roadmap.md docs/agent-primary-contract-matrix.md
git commit -m "docs: document production project core"
~~~

Expected: P2A and every P3+ capability remain explicitly planned/not implemented.

### Task 6: Run Exit Gates and Independent Review

**Files:**
- Verify: every P2-owned file
- Verify unchanged: Legacy runtime, CLI, dependencies and generated paths

- [x] **Step 1: Run P2 tests**

~~~bash
python -m pytest \
  tests/test_production_models.py \
  tests/test_production_validation.py \
  tests/test_production_registry.py \
  tests/test_production_project.py -q
~~~

Expected: exit `0` with no skipped P2 test.

- [x] **Step 2: Run Legacy contract regressions**

~~~bash
python -m pytest \
  tests/test_config.py tests/test_cli.py tests/test_manifest.py \
  tests/test_pipeline.py tests/test_resume_e2e.py \
  tests/test_workflow_loader.py tests/test_workflow_renderer.py -q
~~~

Expected: exit `0`; public commands, Manifest v1, current config/workflow loading, resume and flat layout remain unchanged.

- [x] **Step 3: Run the full no-network suite**

~~~bash
python -m pytest -q
~~~

Expected: exit `0`. The existing optional Whisper skip may remain; no new P2 skip is allowed.

- [x] **Step 4: Verify scope**

~~~bash
git diff --check
git status --short
p2_base_commit=$(git merge-base HEAD main)
git diff --name-only "$p2_base_commit"..HEAD
rg -n "hyperframes|remotion|elevenlabs|captions|httpx|requests" \
  src/ai_video/production tests/test_production_*.py tests/production_project_factory.py
~~~

Expected: only the file map changed; no `pyproject.toml`, Legacy manifest/pipeline/CLI or `runs/**` change; no external integration import/network call. If `main` advanced after the feature branch was created, use the exact base commit recorded at the Integration Base Gate instead of the current merge-base.

- [x] **Step 5: Obtain independent review**

Review brief:

~~~text
Verify P2 against active spec sections 9-11, 15-16 and 20-23.
Check ProductionManifest is the only active revision pointer.
Check it binds the exact project revision and content hash before creative inputs load.
Check Asset Registry is frozen/read-only and owns no lifecycle or activation writer.
Check Shot roles bind concrete registry assets and P2 defines no desired fingerprint.
Check all six strategies, traversal, tampering and cross-reference tests.
Check registry/project/creative/asset symlink containment and fixed-root policy.
Reject activation/crash-safety claims, renderer/provider/dependency graph/Legacy runtime scope leak.
~~~

Required verdict: `accept` or `accept with concerns` with no blocking issue. The parent verifies every blocking claim directly.

- [x] **Step 6: Record branch truth**

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
6. Registry rejects duplicate IDs, traversal/symlink escape, wrong revision filename/hash, missing file, wrong size and wrong file hash.
7. Runtime-resolved asset paths are clean absolute paths inside project root.
8. Minimal `ProductionManifest` is the only active project revision/content-hash and registry revision pointer.
9. P2 persists no mutable freshness, lifecycle or desired/applied fingerprint and defines no Shot desired-fingerprint projection.
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

After P2 acceptance, P2A must be planned and implemented before any write-capable v2 slice.
P3/P4/P7 design plans may proceed independently, but their runtime implementation must retain the
P2A gate:

- `P2A Production State Commit Protocol Implementation Plan`;
- `P3 Deterministic Composition and HyperFrames Adapter Implementation Plan`;
- `P4 Voice and Captions Implementation Plan`;
- `P7 Image Asset Generation Implementation Plan`.

P3 owns `CompositionSpec`, `ResolvedTimeline` and one renderer adapter. P4 owns Audio/Caption data and paid-provider safety. P7 owns image generation/provenance. None may redefine P2 schema, registry, active pointers or strategy semantics without a versioned migration plan.
