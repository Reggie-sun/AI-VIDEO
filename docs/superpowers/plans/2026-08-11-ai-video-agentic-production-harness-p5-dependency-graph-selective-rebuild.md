# AI-VIDEO Agentic Production Harness P5 Dependency Graph and Selective Rebuild Implementation Plan

> **For agentic workers:** 实施本 plan 时，REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans。按 Task 顺序执行，并使用 checkbox (`- [ ]`) 跟踪进度。

**Goal:** 在已验收并合入 local `main` 的 P2/P2A/P3/P4 contract 之上，引入 immutable、content-addressed 的 Dependency Graph resolver input，并由唯一 Production Manifest 持久化 desired/applied fingerprints 与 lifecycle，使 project、audio、caption、composition 和 render 变化只重建精确受影响的 transitive subgraph。

**Architecture:** 新的 `src/ai_video/production/dependency.py` 只负责构造、验证和解析 typed DAG，纯计算 deterministic desired fingerprints、blocked propagation 与 selective rebuild decisions，不写文件、不拥有状态，也不推导 timeline。`src/ai_video/production/models.py` 定义 strict graph/Manifest 2.3 schemas；`src/ai_video/production/state_commit.py::ProductionStateCommitter` 继续是 graph snapshot、Manifest lifecycle、activation、commit-point mapping 与 explicit recovery 的唯一 writer，最终一个 Manifest atomic replace 同时选择候选 project/registry/render/graph identity。`ResolvedTimeline` 继续独占 order/frame/sample/timing；Graph只组合execution前typed contracts，existing `composition_fingerprint`和P3/P4 receipts仅用于Manifest-owned applied evidence verification。

**Tech Stack:** Python 3.11+、Pydantic v2 frozen strict models、stdlib `hashlib`/canonical JSON、现有 `canonical_sha256()`/no-follow/path-containment/P2A fsync and atomic-replace primitives、pytest deterministic local fixtures、fake/no-network tests。无新 runtime dependency、无 Provider call、无 renderer installation、无 cloud fallback。

---

Status: 本文件仅是 P5 implementation plan。它不授权 P5 runtime implementation、merge、push、release、P6/P7/P8/P9、Provider call、dependency installation 或 live renderer execution。Planning base 是 local `main` commit `f9eedaeb5f6432d8ba0bf937c78111dbcfa3ce80`；P4 已 fast-forward 合入 local `main`，merged-main full verification 为 `1094 passed, 4 skipped`，但 local history 仍未 push/release。实施日必须从当时已接受的 P4 descendant 重新核验 Git/runtime truth。

## Problem Boundary

P5 要建立的 bounded path 是：

```text
verified P2/P4 creative artifacts + Asset Registry records
+ P3/P4 CompositionSpec / ResolvedTimeline / renderer receipts
        |
        v
dependency.py::build_production_dependency_graph()
        |
        v
immutable DependencyGraphSnapshot 2.0
typed nodes + typed edges + dependency reason + fingerprint contribution only
        |
        v
dependency.py::resolve_dependency_state()
deterministic desired fingerprints + precise transitive propagation
        |
        v
ProductionStateCommitter-owned candidate durability and activation
        |
        v
ProductionManifest 2.3
active graph pointer + desired/applied + fresh/stale/failed/blocked/superseded
        |
        v
dependency.py::select_rebuild_nodes()
ready frontier and exact affected set; no execution side effects
```

P5 的边界固定如下：

- Dependency Graph 是 immutable、content-addressed/versioned resolver input，只保存 typed nodes、typed edges、dependency reason 与 immutable fingerprint contributions。
- Graph 不保存 `desired_fingerprint`、`applied_fingerprint`、`fresh`、`stale`、`failed`、`blocked`、`superseded`、attempt state、timestamps、active selection 或 mutable status。
- Production Manifest 是 active graph revision、desired/applied fingerprints、lifecycle、blocked reason、failure evidence 和 active project/registry/render selection 的唯一 owner。
- `ProductionStateCommitter` 仍是唯一 v2 snapshot writer、graph activation、Manifest commit-point mapping 与 explicit recovery owner。不得创建 `DependencyGraphWriter`、graph sidecar journal、第二 Manifest、第二 registry writer、background auto-recovery 或 startup repair。
- `ResolvedTimeline` 仍是唯一 Shot order、frame/sample boundary、absolute timing 与 renderer identity owner。Graph 必须消费 `ResolvedTimeline.composition_fingerprint`；不得根据 Shot order、directory order、caption seconds 或 audio duration另算 canonical timeline。
- P5 只决定哪些 logical nodes `fresh | stale | failed | blocked | superseded` 以及哪些 node ready for rebuild；它不调用 voice provider、不 author creative intent、不渲染、不执行 QA/repair。
- 已有 P2/P2A/P3/P4 action owners继续执行各自 bounded action；P5 只要求它们的 final P2A Manifest replace 同时提交匹配的 graph revision/lifecycle transition，避免 registry/render 与 graph 分裂。

## Planning Truth and Preflight

| Surface | Current Runtime Truth | P5 Consequence |
| --- | --- | --- |
| P2 | strict/read-only creative/project/registry loader 已实现 | Graph builder可消费已验证 models；reader仍不得写、激活或 recover |
| P2A | `ProductionStateCommitter` 是唯一 project/registry/render/voice writer/recovery owner | graph snapshot 和 lifecycle只能加入该 owner，不建平行 control plane |
| P3 | `CompositionSpec`、`ResolvedTimeline`、single HyperFrames source/render receipts 已在 local `main` | Desired graph消费composition/renderer contracts；existing timeline/source/output fingerprints只作applied evidence；不新增 renderer/timeline |
| P4 | audio、voice request、alignment、CaptionTrack、caption style、audio mix fingerprints已合入 `f9eedaeb5f6432d8ba0bf937c78111dbcfa3ce80` | Graph按 typed contribution接入它们；不重算或合并语义不同的 hash |
| Current invalidation | `_commit_locked()` 在 project/registry pair change 时 blanket-clear render；voice R+4硬编码 `active_render_state=None` | P5 用 graph lifecycle 替代 blanket stale；旧 render pointer保留为 applied evidence并标为 stale/blocked |
| Manifest | 当前版本为 2.0/2.1/2.2，无 graph pointer 或 node lifecycle | 首次 P5 mutation显式迁移到2.3；只读打开旧版本不升级 |
| Docs | matrix、baseline、roadmap、`AGENTS.md` 中 P4 branch/merge truth已过时 | 只在未来 P5 runtime acceptance 后同步；本 plan-only窗口不改这些文件 |
| Legacy | CLI、Manifest v1、flat `runs/`、ComfyUI、Wan path不受P2-P4影响 | P5不得接入 Legacy pipeline/manifest或改变 public CLI |

实施前执行：

```bash
git status --short --branch
git rev-parse HEAD
git log --oneline --decorate -12
git rev-list --left-right --count origin/main...main
rg -n "active_render_state|composition_fingerprint|input_artifact_ids|input_fingerprint|timing_fingerprint|voice_request" \
  src/ai_video/production tests
python -m pytest \
  tests/test_production_models.py \
  tests/test_production_project.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py \
  tests/test_production_composition.py \
  tests/test_production_hyperframes.py \
  tests/test_production_audio.py \
  tests/test_production_captions.py \
  tests/test_production_voice_captions_e2e.py -q
```

Expected implementation base: `f9eedaeb5f6432d8ba0bf937c78111dbcfa3ce80` 或后来明确接受、包含相同 P2/P2A/P3/P4 contracts 的 descendant。若实现日 code/tests 推翻本 plan 的字段或 owner，只能收紧 P5 contract并修订 plan；不得扩大到 P6/P7/P8/P9。

## Canonical Ownership

| Contract | Single Owner | Non-Owner Rule |
| --- | --- | --- |
| strict graph/pointer/lifecycle schemas | `src/ai_video/production/models.py` | resolver、Manifest JSON、provider response不得发明松散字段 |
| graph semantic hash and canonical path | `dependency.py::dependency_graph_semantic_sha256()` + `paths.py::canonical_dependency_graph_snapshot_path()` | filename、mtime、directory scan不是revision owner |
| graph construction and pure resolution | `dependency.py::{build_production_dependency_graph,resolve_dependency_state,select_rebuild_nodes}` | committer、renderer、Agent memory不重复实现传播规则 |
| mutable desired/applied/lifecycle | `ProductionManifest 2.3` | Graph、Asset Registry、render receipt、console output不保存mutable freshness |
| durable graph write/activation/recovery | `state_commit.py::ProductionStateCommitter` | 不新增graph writer class/service/sidecar或auto-recovery |
| project/registry identity | existing Manifest pointers + selected immutable snapshots | graph不重写asset provenance或registry identity |
| order/frame/sample/timing | `composition.py::resolve_composition()` -> `ResolvedTimeline` | graph只把`composition_fingerprint`当opaque contribution |
| renderer source/render evidence | existing HyperFrames source/render receipts and `active_render_state` | graph不生成HTML、不验证codec、不增加renderer |
| rebuild execution | existing domain owner chosen by Codex from ready node kind | resolver只返回decision，不调用provider/renderer或自动修改creative state |

## Old Path to Replace or Extend

必须精确替换/扩展以下旧路径：

- 替换 `state_commit.py::_commit_locked()` 中“project或registry pointer变化即 `retained_render_state=None`”的 blanket invalidation。Manifest 2.3 下保留旧 `active_render_state` 作为 exact applied evidence，并由 render node lifecycle 标记 `stale` 或 `blocked`；它只有在 render node `fresh` 且 desired/applied相等时才是 execution/final-output eligible。
- 替换 `ProductionStateCommitter.activate_voice_assets()` R+4 的硬编码 `active_render_state=None`。候选 registry、candidate graph、node states 与旧 applied render pointer必须在同一个 final Manifest replace中提交。
- 扩展 project/registry generic commit、audio import、voice activation和render activation，使 Manifest 2.3 上的每个 active identity change都必须携带 exact `DependencyGraphTransition`；旧2.0-2.2路径在首次P5 migration前保持原行为。
- 扩展 `load_production_project()`：2.3 reader读取Manifest-selected graph并验证pointer/hash/DAG/state一致性。若`active_render_state`已stale，它按state自身embedded historical project/registry exact pair验证，不把stale evidence误报为fresh，也不自动清除。
- 保留 `composition.py::timeline_fingerprint()`、`audio.py::audio_content_fingerprint()`、`captions.py::{caption_timing_fingerprint,caption_style_fingerprint}` 和 render receipt fingerprints为各自owner；Graph只做typed namespacing和组合。

## Unchanged Contracts

- Legacy public CLI仍只有`ai-video validate`、`ai-video run`、`ai-video resume`；不加command、flag或exit-code语义。
- Legacy Manifest v1、flat `runs/<run_id>/` layout、resume、local-first ComfyUI、Wan workflow和last-frame chain不变。
- P2 reader继续strict/read-only/no-network；任何load不创建目录、不upgrade schema、不recover、不激活graph。
- P2A `ProductionStateCommitter`继续唯一writer/recovery owner；Manifest atomic replace继续是logical commit point。
- Asset Registry继续只拥有immutable identity/provenance，不保存freshness/status。
- `ResolvedTimeline`继续唯一order/frame/sample/timing owner；P5不修改rounding、duration或caption snapping。
- HyperFrames继续唯一renderer；无Remotion、Captions.ai final-render、second renderer、ffmpeg alternate final render或cloud fallback。
- P5不实现P6 review/repair/final acceptance、P7 image generation、P8 Provider、P9 retention/hardening。
- 默认acceptance只使用deterministic local fixtures、fake/no-network tests；不安装SDK、不读取secret、不调用ElevenLabs/ComfyUI/remote API。

## Graph Schema and Fingerprint Contract

### Immutable Graph Models

在`models.py`新增以下strict/frozen contract；命名若与现有style冲突可做局部一致化，但字段语义不得漂移：

```python
class DependencyNodeKind(str, Enum):
    CREATIVE_ARTIFACT = "creative_artifact"
    ASSET = "asset"
    COMPOSITION_SPEC = "composition_spec"
    RESOLVED_TIMELINE = "resolved_timeline"
    RENDERER_SOURCE = "renderer_source"
    RENDER = "render"

class DependencySemanticRole(str, Enum):
    NONE = "none"
    VOICE = "voice"
    VISUAL = "visual"
    AUDIO = "audio"
    CAPTION = "caption"
    COMPOSITION = "composition"
    TIMELINE = "timeline"
    RENDERER_SOURCE = "renderer_source"
    RENDER = "render"

class DependencyReason(str, Enum):
    AUTHORING_INPUT = "authoring_input"
    GENERATION_INPUT = "generation_input"
    ASSET_BINDING = "asset_binding"
    AUDIO_SOURCE = "audio_source"
    ALIGNMENT_TIMING = "alignment_timing"
    CAPTION_STYLE = "caption_style"
    COMPOSITION_RESOLUTION = "composition_resolution"
    TIMELINE_MATERIALIZATION = "timeline_materialization"
    RENDER_EXECUTION = "render_execution"

class FingerprintContribution(StrictModel):
    key: str
    fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

class DependencyNode(StrictModel):
    node_id: str
    kind: DependencyNodeKind
    semantic_role: DependencySemanticRole
    artifact_id: str
    artifact_revision: int | None = Field(default=None, ge=1)
    contributions: tuple[FingerprintContribution, ...] = Field(min_length=1)

class DependencyEdge(StrictModel):
    source_node_id: str
    target_node_id: str
    reason: DependencyReason
    contribution: FingerprintContribution

class DependencyGraphSnapshot(StrictModel):
    schema_version: Literal["2.0"] = "2.0"
    revision_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    nodes: tuple[DependencyNode, ...]
    edges: tuple[DependencyEdge, ...]
```

Graph structural validators必须要求：node IDs唯一且按`node_id`canonical order；node contributions按`key`排序且key唯一；edge按`(target, source, reason, contribution.key)`排序且identity唯一；`revision_id == content_hash`。`dependency.py`的semantic validator独占endpoint存在性、self-edge/cycle、topological order和semantic hash验证，并要求`revision_id == content_hash == dependency_graph_semantic_sha256(graph)`。`dependency_graph_semantic_sha256()`必须先从canonical model dump中排除`revision_id`与`content_hash`，避免self-referential hash。Graph不得出现任何lifecycle/status/timestamp/active/applied/desired字段。

一个versioned artifact可以映射为多个typed logical projection nodes。`Shot`必须至少拆成`creative:shot:<shot_id>:voice`、`creative:shot:<shot_id>:visual`和`creative:shot:<shot_id>:composition`；每个node都保存相同`artifact_id`/revision provenance和对应`DependencySemanticRole`，但contributions只覆盖自己的semantic projection。禁止把完整`Shot.content_hash`作为所有Shot outgoing edges的共同source fingerprint，否则dialogue变化会错误invalidates visual consumers。

Canonical node-ID grammar固定为：non-Shot creative `creative:<artifact-kind>:<artifact-id>`；Shot projection `creative:shot:<shot-id>:<semantic-role>`；asset `asset:<asset-id>`；composition `composition:<composition-id>`；timeline `timeline:<composition-id>`；source `renderer-source:<composition-id>`；render `render:<composition-id>`。Builder必须从typed IDs生成这些strings；resolver不得通过parse string决定semantics。

### Deterministic Desired Fingerprint

`dependency.py::desired_fingerprints()`使用唯一公式：

```python
desired[node_id] = canonical_sha256({
    "schema": "ai-video-dependency-desired/1",
    "node_id": node.node_id,
    "kind": node.kind.value,
    "semantic_role": node.semantic_role.value,
    "contributions": [
        {"key": item.key, "fingerprint": item.fingerprint}
        for item in node.contributions
    ],
    "incoming": [
        {
            "source_node_id": edge.source_node_id,
            "source_desired_fingerprint": desired[edge.source_node_id],
            "reason": edge.reason.value,
            "key": edge.contribution.key,
            "fingerprint": edge.contribution.fingerprint,
        }
        for edge in canonical_incoming_edges[node.node_id]
    ],
})
```

该公式在canonical topological order中计算；不读取mtime、filesystem order、Manifest revision、attempt ID、timestamp或status。由于source node已经是semantic projection，`source_desired_fingerprint`只传播该projection；上游projection desired没有变化时传播停止。Builder还必须按下表验证`(source kind, source semantic_role, reason, target kind, target semantic_role)`，不得parse node ID或猜contribution key：

| Source | Reason | Target |
| --- | --- | --- |
| creative `NONE` | `AUTHORING_INPUT` | creative `NONE`, `VOICE`, `VISUAL`, or `COMPOSITION` |
| creative `VOICE` | `GENERATION_INPUT` | asset `VOICE` |
| creative `VISUAL` | `GENERATION_INPUT` or `ASSET_BINDING` | asset `VISUAL` |
| creative `COMPOSITION` | `COMPOSITION_RESOLUTION` | composition `COMPOSITION` |
| asset `VOICE` or `AUDIO` | `AUDIO_SOURCE` | asset `CAPTION` or composition `COMPOSITION` |
| asset `CAPTION` | `ALIGNMENT_TIMING` or `CAPTION_STYLE` | composition `COMPOSITION` |
| asset `VISUAL` | `ASSET_BINDING` | composition `COMPOSITION` |
| composition `COMPOSITION` | `COMPOSITION_RESOLUTION` | timeline `TIMELINE` |
| timeline `TIMELINE` | `TIMELINE_MATERIALIZATION` | renderer source `RENDERER_SOURCE` |
| asset `VISUAL`, `VOICE`, or `AUDIO` | `ASSET_BINDING` | renderer source `RENDERER_SOURCE` |
| asset `CAPTION` | `ALIGNMENT_TIMING` or `CAPTION_STYLE` | renderer source `RENDERER_SOURCE` |
| renderer source `RENDERER_SOURCE` | `RENDER_EXECUTION` | render `RENDER` |
| timeline `TIMELINE` | `RENDER_EXECUTION` | render `RENDER` |

未列出的组合一律`DEPENDENCY_GRAPH_INVALID`。因此creative `VOICE`到asset `VISUAL`即使node ID/keys伪装正确也必须拒绝。

公式级必须测试：只改`Shot.dialogue`时`creative:shot:<shot-id>:voice`、voice/caption/timeline/source/render desired改变，而`creative:shot:<shot-id>:visual`、image asset和unrelated Shot nodes完全不变；只改visual role时反向成立。另将一个node只改`semantic_role`且保持ID/contributions相同时，desired fingerprint必须改变，旧applied state不得继续fresh。

### Manifest Lifecycle

Manifest 2.3新增：

```python
class DependencyLifecycle(str, Enum):
    FRESH = "fresh"
    STALE = "stale"
    FAILED = "failed"
    BLOCKED = "blocked"
    SUPERSEDED = "superseded"

class DependencyNodeState(StrictModel):
    node_id: str
    graph_revision_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    desired_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")
    applied_fingerprint: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    lifecycle: DependencyLifecycle
    applied_evidence: DependencyAppliedEvidence | None = None
    blocked_by: tuple[str, ...] = ()
    error_code: str | None = None
    error_message: str | None = None

class DependencyGraphSnapshotPointer(StrictModel):
    path: Path
    revision_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    file_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
```

`DependencyAppliedEvidence`是Manifest-owned exact binding，不进入Graph desired inputs：

```python
class ProjectDependencyEvidence(StrictModel):
    owner: Literal["project_snapshot"]
    pointer: ProjectSnapshotPointer
    artifact_id: str
    artifact_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

class RegistryDependencyEvidence(StrictModel):
    owner: Literal["registry_snapshot"]
    pointer: RegistrySnapshotPointer
    artifact_id: str
    artifact_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

class RenderDependencyEvidence(StrictModel):
    owner: Literal["render_state"]
    pointer: RenderStateSnapshotPointer
    artifact_id: str
    artifact_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

DependencyAppliedEvidence = Annotated[
    ProjectDependencyEvidence | RegistryDependencyEvidence | RenderDependencyEvidence,
    Field(discriminator="owner"),
]
```

Evidence不复制artifact bytes。Project variant保存revision/content hash/file hash/canonical path完整pointer，因而project切换后superseded creative evidence仍可exact reopen；registry/render variants同理。Reader/committer必须沿该pointer重新打开并验证，不能用current active pointer替代origin pointer，也不能扫描filename恢复identity。

Lifecycle rules：

- `fresh`: `applied_fingerprint == desired_fingerprint`，有与node kind匹配且可reopen验证的`applied_evidence`，`blocked_by=()`且无error。
- `stale`: desired/applied不同或applied缺失，所有required predecessors fresh，因而进入ready frontier。
- `failed`: 同一desired fingerprint的bounded rebuild已terminal failed；保存typed sanitized error，resolver不自动retry。
- `blocked`: 至少一个required predecessor不是fresh；`blocked_by`按node ID排序，不能有error。
- `superseded`: node不在active graph；保留last desired/applied/evidence及其原`graph_revision_id`，不进入rebuild decision。
- graph revision改变且failed node desired改变时，旧failure不继承，新state按predecessor情况成为stale或blocked。
- exact graph/state replay若计算结果与Manifest完全相同，返回当前Manifest，不增加revision，不写文件。

`select_rebuild_nodes()`返回两个canonical sets：`affected_node_ids`包含本次transitive stale/blocked nodes；`ready_node_ids`只包含当前stale frontier。它还返回typed `execution_units`，把logical nodes映射回existing action owner：creative/asset按各自owner单独推进；composition、resolved timeline、renderer source与render固定映射为一个`render_with_hyperframes` durable unit并atomic apply。它不自动包含same-desired failed nodes；显式retry必须由调用者另行授权并通过committer记录新attempt。

Manifest 2.3的`dependency_states`允许两类entry且`node_id`全局唯一：active graph中每个node恰好一个non-superseded state；不在active graph的retained state必须是`superseded`并保留其origin graph revision。若同一logical node ID后来重新进入active graph，committer用新的active state替换旧superseded entry；P5不保留同ID多代history，长期history/retention属于P9。

## P2/P3/P4 Contribution Mapping

| Current Source | Graph Node/Edge Contribution | Owner Preserved |
| --- | --- | --- |
| `ProductionBrief`/`Story`/`Character`/`Scene`/`Storyboard` | creative node的scoped semantic contribution；exact artifact references形成authoring edges | P2 models/hash |
| `Shot` | voice、visual、composition三个logical projection nodes，各自从strict Shot fields canonical hash；完整Shot hash只作为provenance/evidence，不向所有consumer传播 | P2 models/hash |
| `Shot.dialogue`/`Shot.narration` + immutable `VoiceGenerationRequest` | affected VOICE asset node的`script_hash`、typed input IDs和P5 `voice_semantic_projection` | P4 request fields + P5 scoped projection |
| succeeded `VoiceRequestReceipt.request_fingerprint` | voice asset的applied request evidence；不直接作为desired semantic fingerprint | P4 voice lifecycle evidence |
| `AssetRecord` | asset node的`sha256`、typed `input_artifact_ids`和`input_fingerprint` | Asset Registry |
| `AudioAssetMetadata` | audio node的`audio_content_fingerprint` evidence、script/voice/tool identity、measured sample contract | P4 audio |
| `CaptionTrack`/`CaptionAssetMetadata` | caption asset node的source audio hash、`timing_fingerprint`、alignment receipt/policy | P4 captions |
| `caption_style_fingerprint()` | caption asset/style input到timeline/source的`CAPTION_STYLE` contribution | P4 captions/renderer |
| `CompositionSpec` | composition node `content_hash`；layers/audio mix/caption bindings/delivery/renderer preference作为typed contributions | P3/P4 composition |
| desired timeline node | CompositionSpec projection、upstream asset desired fingerprints、resolver contract version和selected renderer identity；不要求timeline已存在 | `resolve_composition()` contract |
| `ResolvedTimeline.composition_fingerprint` | timeline node的applied evidence；reopen timeline pointer后证明exact resolved result | P3/P4 timeline artifact |
| desired renderer-source node | desired timeline、asset/caption style projections、source materializer contract/version | HyperFrames adapter contract |
| `RendererSourceReceipt` | renderer-source node的applied evidence；source/bundle/check hashes不得反向进入desired | HyperFrames source receipt |
| desired render node | desired source、timeline、renderer/tool/output contract fingerprints | P3/P4 render contract |
| `RenderReceipt`/`RenderStateSnapshot` | render node的applied evidence；output/decoded/measured hashes不得反向进入desired | P3/P4 render lifecycle |

P4中的`input_fingerprint`不保证都处于同一semantic layer。builder必须用`FingerprintContribution.key`做typed namespace，例如`voice.semantic`、`asset.bytes`、`caption.timing`、`caption.style`、`composition.mix`、`timeline.contract`、`renderer.source.contract`；禁止把裸hash tuple无tag拼接。Execution outputs只进入`DependencyAppliedEvidence`与existing immutable receipts，不得改变desired graph。

`dependency.py::voice_semantic_projection_fingerprint()`必须从immutable `VoiceGenerationRequest`只覆盖provider/model/voice/language/settings/output format/script hash/input artifact IDs/input fingerprint；明确排除request/attempt ID、base Manifest revision、pricing snapshot、budget reservation、egress authorization、timestamps和provider outcome。完整P4 `voice_request_fingerprint`仍作为durable submit/applied evidence，authorization receipt轮换不得单独invalidates voice/audio graph。Tests必须证明只换budget/egress receipt时P5 desired不变，而script/model/voice/settings变化时desired改变。

未来P7扩展只依赖现有generic输入：一个严格验证的generated IMAGE `AssetRecord`可通过`input_artifact_ids`/`input_fingerprint`形成asset node并连接Shot consumer。P5只增加synthetic local fixture证明该extension seam；不得增加image provider、request submit、P7 module、remote behavior或新asset lifecycle。

Applied evidence exact binding固定为：

| Node Kind | Manifest Evidence Owner | Exact Reopen Proof |
| --- | --- | --- |
| creative projection | active/candidate `ProjectSnapshotPointer` | reopen exact project snapshot及referenced creative artifact；projection从same sealed bytes重算 |
| asset | active/candidate `RegistrySnapshotPointer` | reopen exact registry record和asset bytes；verify record SHA/input identity |
| composition | `RenderStateSnapshot.timeline` pointer when present | reopen timeline并验证`composition_spec_id/revision/hash`；未resolve时无applied evidence |
| resolved timeline | `RenderStateSnapshot.timeline` pointer | reopen sealed timeline并验证`composition_fingerprint`与desired-at-apply |
| renderer source | `RenderStateSnapshot.source_receipt` + source bundle pointers | reopen source receipt/bundle exact hashes/check evidence |
| render | `RenderStateSnapshot.render_receipt` + output pointer | reopen receipt/output并验证decoded/measured evidence |

`record_dependency_node_applied()`只允许project-owned creative与registry-owned asset node按固定owner在lock内reopen；caller不能自选arbitrary path或只提交hash。Current P3/P4没有独立active CompositionSpec、timeline或source pointer，所以P5不得用旧render pointer伪造其中任何一个node的fresh state：composition、resolved timeline、renderer source与render是一个existing `render_with_hyperframes()` durable execution unit，只有final `RenderStateSnapshot` activation后四者才在同一个Manifest replace中一起applied。该unit在任一内部node进入ready frontier且所有external predecessors fresh时可执行；任何asset/caption/creative predecessor blocked都必须拒绝。Bounded render action成功后committer批量apply四者，失败时source/timeline candidate仍是attempt evidence而非active/fresh state。

## Required Mutation Matrix

`tests/test_production_selective_rebuild.py`必须同时断言exact rebuild set与exact must-not-rebuild set：

| Mutation | Must Rebuild | Must Not Rebuild |
| --- | --- | --- |
| one Shot script / voice request | affected voice asset、alignment/caption asset、timeline、renderer source、render | unrelated images、other Shot voice、BGM/SFX |
| voice settings/model | affected voice asset及其timing/caption/timeline/source/render consumers | Story、unrelated visual/audio assets |
| alignment result/policy only | affected CaptionTrack、timeline、renderer source、render | voice bytes、visual assets、unrelated captions |
| caption text/timing with same voice | affected caption asset、timeline、renderer source、render | voice、visual generation、BGM/SFX |
| caption style | timeline、renderer source、render；timeline included because current P4 cue identity carries style hash | voice、alignment/timing fingerprint、visual/audio assets |
| BGM/SFX/ambience bytes | affected audio asset、timeline、renderer source、render | voice、captions、visual assets |
| gain/fade/ducking/mix only | CompositionSpec、timeline、renderer source、render | source audio bytes、voice/alignment、visual assets |
| one visual asset hash | that asset consumer、timeline、renderer source、render | unrelated visual assets、voice、captions、audio |
| transform/Shot order/delivery FPS or resolution | CompositionSpec、timeline、renderer source、render | source assets，除非其typed generation request显式包含delivery contribution |
| renderer source authored bytes/tool config | renderer source、render | timeline、creative state、assets |
| renderer version | timeline、renderer source、render，因为current `ResolvedTimeline.renderer`明确进入timeline identity | creative state、source assets |
| identical semantic input / mtime / tuple order only | none | every node |

测试必须逐层证明blocked propagation：上游voice stale时caption/composition/timeline/source/render blocked；voice applied后caption成为ready；caption applied后composition成为ready；此时只暴露一个包含composition/timeline/source/render的atomic execution unit，最终render activation后四者一起fresh。不得把仍有external blocked predecessor的unit标成可执行，也不得使用“从Shot N开始全stale”。

## Manifest Migration, Activation, and Recovery

### Version Rules

1. Manifest 2.0/2.1/2.2继续按原bytes/read/recovery contract读取，不注入graph defaults、不改file hash、不自动upgrade。
2. 首次`bootstrap_dependency_graph()`或任何P5-aware state mutation才迁移到Manifest 2.3。
3. DependencyGraphSnapshot首版为2.0；`revision_id == content_hash`，canonical path为`state/dependency_graph.<revision_id>.json`。
4. Bootstrap从当前verified active或candidate project/registry bundle构造desired graph，render receipts可以完全不存在。能沿fixed owner exact reopen的nodes初始化`desired == applied`和`fresh`；尚无applied artifact的composition/timeline/source/render nodes按predecessor成为`stale`或`blocked`。有evidence但无法验证时migration fail closed，不能降格为“尚未applied”。
5. Manifest 2.3上的project/registry/audio/voice/render mutation必须在同一个final Manifest replace中选择candidate graph与states；不能先切registry/render后留下旧active graph。
6. rollback禁止2.3降级到2.2；保留2.3 reader/recovery和immutable graphs，只能禁用P5 mutation/rebuild entrypoints。

### Commit Sequence

以base Manifest revision `R`为例：

| Revision / Window | Durable State | Recovery / Replay Rule |
| --- | --- | --- |
| before `R+1` | old active project/registry/render/graph | pure graph可重新计算；无state mutation |
| `R+1` | running P2A attempt，绑定exact base identities、candidate graph pointer、candidate states hash | mismatch replay拒绝；reader不自动recover |
| graph temporary partial | attempt-owned temp only | explicit recovery只清理bounded non-succeeded owned temp |
| graph promoted/fsynced/verified | complete immutable candidate graph，active pointer仍old | preserve/report orphan；不得扫描latest或自动activate |
| candidate project/registry/render artifacts complete | exact candidate bundle durable，active state仍old | reverify exact-set；不猜测activation |
| final Manifest replace | project/registry/render/graph pointers与node states一起切换 | single logical commit point |
| replace后directory fsync/reopen不明确 | authoritative Manifest可能old或new | typed unknown outcome；reopen exact Manifest决定，不重复external action |
| exact new state already active | candidate graph/hash/states全匹配 | idempotent replay返回current Manifest，零artifact rewrite |

`StateCommitAttempt` 2.3新增`base_dependency_graph`、`candidate_dependency_graph`和`candidate_dependency_states_hash`，只在P5-aware operation出现。Graph-only bootstrap、project/registry commit、audio import、voice activation和render activation都必须绑定exact old/new graph identity。Recovery仍由`ProductionStateCommitter._recover_attempts()`统一dispatch；不得新增automatic GC。Complete orphan graph只preserve/report；实际删除属于未来显式GC/retention scope，不在P5。

### Historical Render Evidence

Manifest 2.3中`active_render_state`仍是唯一selected applied render evidence pointer。project/registry变化后不再blanket-null；reader使用RenderStateSnapshot内嵌的exact historical project/registry pair验证bytes，并通过render node lifecycle决定它是fresh、stale或blocked。只有`fresh`且desired/applied相等的render才能作为current final output。Manifest 2.0-2.2继续保留旧“active render必须匹配current pair”的语义。

## Exact Implementation File Map

### Create

- `src/ai_video/production/dependency.py`
  - graph semantic hash、canonical validation、P2/P3/P4 typed graph builder、desired resolver、blocked propagation、selective decision；pure/no-write。
- `tests/test_production_dependency.py`
  - graph schemas、DAG/canonical/hash、typed contribution mapping、desired/applied/lifecycle、determinism、cycles/errors。
- `tests/test_production_selective_rebuild.py`
  - required mutation matrix、blocked frontier、idempotent replay、offline P5 acceptance。

### Modify

- `src/ai_video/production/models.py`
  - graph/pointer/contribution/lifecycle/resolution schemas、Manifest 2.3、attempt graph fields、`LoadedProductionProject.dependency_graph`。
- `src/ai_video/production/paths.py`
  - canonical graph snapshot path和no-follow containment。
- `src/ai_video/production/project.py`
  - read-only active graph load/hash/DAG/state verification；2.3 historical render evidence verification。
- `src/ai_video/production/state_commit.py`
  - P2A-owned graph bootstrap/transition、node applied/failed lifecycle、atomic co-activation、exact replay/recovery；retire 2.3 blanket clear。
- `src/ai_video/production/hyperframes.py`
  - P5-aware render activation request携带candidate graph transition；renderer本身不解析graph。
- `src/ai_video/production/__init__.py`
  - 只导出reviewed graph models、pure resolver和safe committer surface；不导出low-level writer helpers。
- `src/ai_video/errors.py`
  - `DEPENDENCY_GRAPH_INVALID`、`DEPENDENCY_RESOLUTION_INVALID` typed codes。
- `tests/production_project_factory.py`
  - graph 2.0、Manifest 2.3、2.0/2.1/2.2 migration、P3/P4 mutation fixtures。
- `tests/helpers/p2a_crash_worker.py`
  - graph bootstrap/project/voice/render activation crash modes。
- `tests/test_production_models.py`
- `tests/test_production_project.py`
- `tests/test_production_state_commit.py`
- `tests/test_production_state_recovery.py`
- `tests/test_production_hyperframes.py`
- `tests/test_production_voice_captions_e2e.py`
  - compatibility、co-activation、historical render evidence、replay/recovery regression。
- `docs/agent-primary-contract-matrix.md`
- `docs/v0.2-runtime-baseline.md`
- `docs/v0.2-agentic-production-roadmap.md`
- `AGENTS.md`
- `README.md`
  - only after runtime acceptance；先修正P4已合入local main的stale branch truth，再记录已验证P5 behavior。

### Do Not Modify

- `src/ai_video/cli.py`、`config.py`、Legacy `manifest.py`、`pipeline.py`、workflow/ComfyUI/ffmpeg modules。
- `src/ai_video/production/audio.py`、`captions.py`、`elevenlabs.py`、`composition.py`的owner logic；P5消费现有fingerprints，不移动职责。只有实现证据证明缺失一个pure export时，先修订plan并保持行为不变。
- package/dependency files。
- P6 QA/repair、P7 image generation、P8 providers、P9 hardening files或新modules。
- existing P4 plan/spec；它们是historical accepted record。

### Task 0: Revalidate Runtime Truth and Lock the Boundary

**Files:**
- Read: `AGENTS.md`
- Read: `docs/agent-primary-contract-matrix.md`
- Read: `docs/v0.2-runtime-baseline.md`
- Read: `docs/v0.2-agentic-production-roadmap.md`
- Read: `docs/superpowers/specs/2026-08-09-ai-video-agentic-production-harness-v0.2.md`
- Read: `docs/superpowers/plans/2026-08-10-ai-video-agentic-production-harness-p4-voice-and-captions.md`
- Read: exact source/test files in `Exact Implementation File Map`
- Test: existing P2/P2A/P3/P4 focused suites

- [ ] **Step 1: Verify branch/worktree ownership and exact base**

运行Planning Truth命令，并记录exact HEAD、dirty files、live writer ownership、local-vs-origin counts。P5是cross-module/schema/crash-safety Heavy change；若当前树有unrelated dirty work或并发writer，按`AGENTS.md`使用独立branch/worktree。

```bash
P5_IMPLEMENTATION_BASE="$(git rev-parse HEAD)"
test -n "$P5_IMPLEMENTATION_BASE"
git status --short --branch
git rev-list --left-right --count origin/main...HEAD
```

Expected: base是`f9eedaeb5f6432d8ba0bf937c78111dbcfa3ce80`或明确接受的descendant，且P4代码存在；不得从`origin/main`遗漏local accepted slices。

- [ ] **Step 2: Record owner and old-path proof**

```bash
rg -n "retained_render_state = None|active_render_state.: None|def _commit_locked|def activate_voice_assets" \
  src/ai_video/production/state_commit.py
rg -n "def timeline_fingerprint|def caption_timing_fingerprint|def caption_style_fingerprint|def audio_content_fingerprint" \
  src/ai_video/production
```

Expected: exact blanket invalidation与existing fingerprint owners均定位；若符号变化，更新plan中的exact symbol，不能另造owner。

- [ ] **Step 3: Run focused pre-change baseline**

```bash
python -m pytest \
  tests/test_production_models.py \
  tests/test_production_project.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py \
  tests/test_production_composition.py \
  tests/test_production_hyperframes.py \
  tests/test_production_audio.py \
  tests/test_production_captions.py \
  tests/test_production_voice_captions_e2e.py -q
```

Expected: green。失败先判断pre-existing regression；不得把P5计划扩大为无关修复。

- [ ] **Step 4: Commit no files**

Task 0只形成session evidence，不创建runtime/doc commit。

### Task 1: Add Strict Graph and Manifest 2.3 Schemas

**Files:**
- Modify: `src/ai_video/production/models.py`
- Modify: `src/ai_video/errors.py`
- Modify: `tests/test_production_models.py`

- [ ] **Step 1: Write RED structural schema tests**

新增exact tests覆盖enum values、typed `DependencySemanticRole`、field strictness、canonical contribution/node/edge order、duplicate keys/IDs、graph fields forbid extra、graph不得含status、pointer path shape、`revision_id == content_hash`、discriminated project/registry/render evidence pointers、lifecycle/applied-evidence local invariants、Manifest 2.0/2.1/2.2 serialization不变、2.3 field/version constraints、attempt graph fields old-version rejection。Dangling endpoint、self-edge、cycle、topological order和semantic hash不属于本Task；它们在Task 2由`dependency.py`单一实现和GREEN。

```python
def test_dependency_graph_is_immutable_input_without_mutable_status():
    graph = make_dependency_graph_snapshot()
    dumped = graph.model_dump(mode="json")
    assert set(dumped) == {"schema_version", "revision_id", "content_hash", "nodes", "edges"}
    assert not ({"fresh", "stale", "desired_fingerprint", "applied_fingerprint"} & set(str(dumped).split()))

def test_manifest_23_is_the_only_graph_lifecycle_owner():
    manifest = make_manifest_23_with_dependency_graph()
    assert manifest.active_dependency_graph is not None
    assert {state.lifecycle for state in manifest.dependency_states} == {DependencyLifecycle.FRESH}
```

- [ ] **Step 2: Run RED**

```bash
python -m pytest tests/test_production_models.py -q
```

Expected: new symbols/validators缺失导致fail；existing P2-P4 tests仍green。

- [ ] **Step 3: Implement minimum strict models and errors**

按`Graph Schema and Fingerprint Contract`实现structural models/local cross-field validators。`models.py`不得实现DAG traversal或semantic graph hash。`ProductionManifest`只在schema 2.3允许graph fields；old serializer省略new fields，禁止schema downgrade。Error codes只增加：

```python
DEPENDENCY_GRAPH_INVALID = "dependency_graph_invalid"
DEPENDENCY_RESOLUTION_INVALID = "dependency_resolution_invalid"
```

- [ ] **Step 4: Run GREEN**

```bash
python -m pytest tests/test_production_models.py -q
```

- [ ] **Step 5: Commit**

```bash
git add src/ai_video/production/models.py src/ai_video/errors.py tests/test_production_models.py
git commit -m "feat: define p5 dependency graph contracts"
```

### Task 2: Implement the Pure Immutable Graph Resolver

**Files:**
- Create: `src/ai_video/production/dependency.py`
- Create: `tests/test_production_dependency.py`
- Modify: `src/ai_video/production/paths.py`

- [ ] **Step 1: Write RED canonical graph tests**

覆盖semantic hash明确排除`revision_id`/`content_hash`、canonical path、input tuple order/mtime independence、DAG topological order、cycle/dangling/self-edge rejection、canonical node-ID generation、typed contribution names和完整`(kind, semantic_role, reason, target)`compatibility matrix、no filesystem/network/write。正例必须含Story -> Storyboard、Scene -> Shot visual projection、Storyboard -> Shot composition projection的typed `AUTHORING_INPUT` edges；负例必须含wrong creative role和voice-role source -> visual-role asset，全部按typed fields判断而不是node ID string。

```python
def test_desired_fingerprint_propagates_edge_by_edge_and_stops_at_same_input():
    graph = make_linear_dependency_graph()
    first = desired_fingerprints(graph)
    same = desired_fingerprints(graph.model_copy(deep=True))
    assert same == first
    changed = desired_fingerprints(change_node_contribution(graph, "asset:voice-1", "voice.request"))
    assert changed["creative:shot:shot-1:visual"] == first["creative:shot:shot-1:visual"]
    assert changed["asset:voice-1"] != first["asset:voice-1"]
    assert changed["asset:caption-1"] != first["asset:caption-1"]
    assert changed["render:final"] != first["render:final"]

def test_shot_dialogue_projection_does_not_invalidate_visual_consumers():
    before, after = make_shot_projection_graphs(dialogue="changed")
    old = desired_fingerprints(before)
    new = desired_fingerprints(after)
    assert new["creative:shot:shot-1:voice"] != old["creative:shot:shot-1:voice"]
    assert new["creative:shot:shot-1:visual"] == old["creative:shot:shot-1:visual"]
    assert new["asset:image-1"] == old["asset:image-1"]

def test_semantic_role_is_part_of_desired_identity():
    graph = make_linear_dependency_graph()
    changed = change_node_semantic_role(graph, "asset:voice-1", DependencySemanticRole.AUDIO)
    assert desired_fingerprints(changed)["asset:voice-1"] != desired_fingerprints(graph)["asset:voice-1"]
```

- [ ] **Step 2: Write RED lifecycle/resolution tests**

覆盖fresh/stale/failed/blocked/superseded、failed same-desired保持failed、failed new-desired重置、blocked_by canonical、ready frontier、affected set、exact replay no-op。

```python
def test_blocked_nodes_become_ready_one_frontier_at_a_time():
    resolution = resolve_dependency_state(make_linear_dependency_graph(), make_old_applied_states())
    assert resolution.ready_node_ids == ("asset:voice-1",)
    assert resolution.by_id["asset:caption-1"].lifecycle is DependencyLifecycle.BLOCKED
    next_resolution = resolve_dependency_state(
        resolution.graph,
        mark_applied(resolution.states, "asset:voice-1"),
    )
    assert next_resolution.ready_node_ids == ("asset:caption-1",)
```

- [ ] **Step 3: Run RED**

```bash
python -m pytest tests/test_production_dependency.py -q
```

- [ ] **Step 4: Implement pure functions**

实现以下exact public surface；所有函数只接收validated models并返回immutable values：`dependency_graph_semantic_sha256(graph) -> str`、`build_dependency_graph(nodes, edges) -> DependencyGraphSnapshot`、`desired_fingerprints(graph) -> dict[str, str]`、`resolve_dependency_state(graph, previous) -> DependencyResolution`、`select_rebuild_nodes(resolution) -> SelectiveRebuildDecision`。其中`desired_fingerprints()`必须逐字实现本plan的`ai-video-dependency-desired/1`公式；`resolve_dependency_state()`必须逐字实现Manifest Lifecycle六条transition rules。

唯一canonical graph path为：

```python
def canonical_dependency_graph_snapshot_path(revision_id: str) -> Path:
    return Path(f"state/dependency_graph.{revision_id}.json")
```

- [ ] **Step 5: Run GREEN and prove purity**

```bash
python -m pytest tests/test_production_dependency.py tests/test_production_models.py -q
```

- [ ] **Step 6: Commit**

```bash
git add \
  src/ai_video/production/dependency.py \
  src/ai_video/production/paths.py \
  tests/test_production_dependency.py
git commit -m "feat: resolve immutable p5 dependency graphs"
```

### Task 3: Map Verified P2/P3/P4 Desired Inputs and Applied Evidence

**Files:**
- Modify: `src/ai_video/production/dependency.py`
- Modify: `tests/test_production_dependency.py`
- Modify: `tests/production_project_factory.py`
- Verify only: `src/ai_video/production/{audio.py,captions.py,composition.py,hyperframes.py}`

- [ ] **Step 1: Write RED typed mapping tests**

覆盖每个`P2/P3/P4 Contribution Mapping` row；assert exact node IDs/kinds、edge reasons/keys、hash origins。特别断言style不改变`caption.timing`，audio mix不改变audio bytes，Shot dialogue不改变visual projection。Desired timeline/source/render nodes不要求execution receipts；existing `composition_fingerprint`/source/render receipts只进入applied evidence。

```python
def test_production_graph_builds_pre_render_desired_nodes_without_retiming(tmp_path):
    inputs = make_p4_dependency_inputs(tmp_path)
    graph = build_production_dependency_graph(inputs)
    timeline = node_by_id(graph, f"timeline:{inputs.composition_spec.composition_id}")
    assert contribution(timeline, "timeline.contract") == inputs.resolver_contract_fingerprint
    assert inputs.applied_evidence is None
    assert not hasattr(graph, "total_frames")
    assert not hasattr(graph, "total_samples")
```

- [ ] **Step 2: Write RED desired/applied separation tests**

断言voice desired asset由exact request/input IDs连接；caption desired由source audio desired、alignment policy和style独立贡献；timeline/source/render desired由execution前contract连接。`RendererSourceReceipt`、`RenderReceipt`、decoded/output hashes和measured metadata只构成optional `AppliedProductionEvidence`，从applied evidence中删除所有receipts后Graph bytes/desired fingerprints保持不变。Mismatched candidate asset、unselected/tampered applied receipt在bootstrap/record-applied时typed-fail，但不改变desired builder。

```python
def test_execution_receipts_do_not_feed_back_into_desired_graph(tmp_path):
    inputs, no_evidence = make_p4_dependency_inputs(tmp_path, with_applied_render=False)
    same_inputs, rendered_evidence = make_p4_dependency_inputs(tmp_path, with_applied_render=True)
    assert build_production_dependency_graph(inputs) == build_production_dependency_graph(same_inputs)
    assert build_applied_dependency_evidence(inputs, no_evidence) == ()
    assert build_applied_dependency_evidence(same_inputs, rendered_evidence)
```

- [ ] **Step 3: Write future generated-image extension seam test**

用纯local synthetic generated IMAGE `AssetRecord` + existing Shot role，断言generic `input_artifact_ids`/`input_fingerprint`形成typed asset edge；同时断言没有P7 module/provider/submit symbol。

```python
def test_generated_image_record_is_a_verifiable_future_input_without_provider_runtime(tmp_path):
    inputs = make_dependency_inputs_with_generated_image_record(tmp_path)
    graph = build_production_dependency_graph(inputs)
    assert edge_reason(graph, "creative:shot:shot-1:visual", "asset:image-1") is DependencyReason.GENERATION_INPUT
    assert "image_provider" not in dependency_module_public_symbols()
```

- [ ] **Step 4: Run RED**

```bash
python -m pytest tests/test_production_dependency.py -q
```

- [ ] **Step 5: Implement the exact builder**

```python
@dataclass(frozen=True)
class ProductionDependencyInputs:
    project: LoadedProductionProject
    composition_spec: CompositionSpec
    renderer: RendererIdentity
    voice_requests: tuple[VoiceGenerationRequest, ...]
    resolver_contract_fingerprint: str
    source_materializer_contract_fingerprint: str
    render_contract_fingerprint: str

@dataclass(frozen=True)
class AppliedProductionEvidence:
    timeline: ResolvedTimeline | None = None
    source_receipt: RendererSourceReceipt | None = None
    render_receipt: RenderReceipt | None = None
    render_state: RenderStateSnapshot | None = None
```

实现`build_production_dependency_graph(inputs: ProductionDependencyInputs) -> DependencyGraphSnapshot`与`build_applied_dependency_evidence(inputs, applied: AppliedProductionEvidence | None) -> tuple[DependencyNodeState, ...]`。`project`可以是`load_production_project()`得到的active bundle，也可以是`load_production_project_candidate()`验证的candidate project/registry bundle；builder不得假设它已激活。Desired builder只使用execution前typed values，不scan filesystem、不选择latest artifact、不补default creative intent。Applied builder单独验证existing content hashes/pointer identities/receipt cross-links，receipts可全部缺失；缺失表示对应node尚未applied，而不是阻止graph bootstrap。

- [ ] **Step 6: Run GREEN and existing fingerprint regressions**

```bash
python -m pytest \
  tests/test_production_dependency.py \
  tests/test_production_audio.py \
  tests/test_production_captions.py \
  tests/test_production_composition.py \
  tests/test_production_hyperframes.py -q
```

- [ ] **Step 7: Commit**

```bash
git add \
  src/ai_video/production/dependency.py \
  tests/test_production_dependency.py \
  tests/production_project_factory.py
git commit -m "feat: map p4 production inputs into p5 graph"
```

### Task 4: Add Read-Only Active Graph Verification

**Files:**
- Modify: `src/ai_video/production/project.py`
- Modify: `src/ai_video/production/models.py`
- Modify: `tests/test_production_project.py`
- Modify: `tests/production_project_factory.py`

- [ ] **Step 1: Write RED reader tests**

覆盖Manifest 2.3 exact pointer/file hash/semantic hash、cycle/dangling/canonical order、blocked_by合法、fresh applied==desired且applied evidence可reopen、missing/tampered/symlink/decoy graph、no fallback/scan、no writes/network/recovery。State consistency规则必须是：每个active graph node恰有一个non-superseded state；额外state只能是absent-from-active-graph的superseded node并保留origin graph revision；node ID不得重复。

```python
def test_reader_selects_exact_manifest_graph_without_scan_repair_or_write(tmp_path):
    root = make_manifest_23_project(tmp_path)
    before = snapshot_tree(root)
    loaded = load_production_project(root / "project.yaml")
    assert loaded.dependency_graph is not None
    assert loaded.dependency_graph.content_hash == loaded.manifest.active_dependency_graph.content_hash
    assert snapshot_tree(root) == before
```

- [ ] **Step 2: Write RED historical render evidence tests**

2.3下registry改变、render node stale时，reader用RenderStateSnapshot embedded old pair验证旧render evidence并拒绝把它当fresh；tamper old project/registry/render bytes仍fail closed。2.0-2.2旧pair semantics保持。

- [ ] **Step 3: Write RED superseded retention tests**

Graph revision删除一个node且project revision已切换时，Manifest保留该node为superseded；reader必须用state中完整old `ProjectSnapshotPointer`而非current active project exact reopen origin artifact。相同node ID重新进入active graph时只有一个new non-superseded state，旧superseded entry被替换；duplicate active/history IDs拒绝。

- [ ] **Step 4: Run RED**

```bash
python -m pytest tests/test_production_project.py tests/test_production_models.py -q
```

- [ ] **Step 5: Implement read-only loading**

新增private `_load_active_dependency_graph()` / `_verify_manifest_dependency_states()`；`LoadedProductionProject.dependency_graph`仅由Manifest 2.3 pointer填充。reader不调用committer/recover、不清理orphans、不改变mtime。

- [ ] **Step 6: Run GREEN**

```bash
python -m pytest \
  tests/test_production_project.py \
  tests/test_production_dependency.py \
  tests/test_production_registry.py -q
```

- [ ] **Step 7: Commit**

```bash
git add \
  src/ai_video/production/project.py \
  src/ai_video/production/models.py \
  tests/test_production_project.py \
  tests/production_project_factory.py
git commit -m "feat: verify manifest-selected p5 graphs"
```

### Task 5: Bootstrap and Atomically Activate Graph State through P2A

**Files:**
- Modify: `src/ai_video/production/state_commit.py`
- Modify: `src/ai_video/production/__init__.py`
- Modify: `tests/test_production_state_commit.py`
- Modify: `tests/production_project_factory.py`

- [ ] **Step 1: Write RED ownership/bootstrap tests**

定义唯一safe surface：pure `prepare_dependency_graph_transition()`、`ProductionStateCommitter.bootstrap_dependency_graph()`、`ProductionStateCommitter.record_dependency_node_applied()`、`ProductionStateCommitter.record_dependency_node_failed()`。四个API都必须接收exact expected Manifest revision、active/candidate graph identity和desired fingerprint；两个result APIs还必须接收node ID与固定owner的typed evidence/failure，并由committer在lock内重新打开project/registry/render-state pointer验证，不能接受caller-controlled arbitrary evidence path。

tests断言pure builder不写；只有committer写graph/Manifest；package root不导出`GraphWriter`、raw atomic helper或recovery bypass。

- [ ] **Step 2: Write RED migration tests**

覆盖Manifest 2.0/2.1/2.2 -> 2.3首次bootstrap、verified existing nodes初始化fresh、合法pre-render project在无timeline/source/render receipts时bootstrap为precise stale/blocked frontier、unverified existing evidence阻断migration、candidate bundle尚未active也可构图、no schema rewrite on read、no downgrade、exact replay zero write/revision bump。

- [ ] **Step 3: Write RED durability/order tests**

断言顺序为graph temp write -> file fsync -> promote-without-overwrite -> parent fsync -> reopen/hash verify -> final Manifest temp/fsync/replace/directory fsync/reopen。final replace前active graph仍old/none。

- [ ] **Step 4: Run RED**

```bash
python -m pytest tests/test_production_state_commit.py tests/test_production_models.py -q
```

- [ ] **Step 5: Implement within the existing committer**

复用`PreparedArtifact`、`_write_immutable_artifact()`、`_write_manifest_atomic()`、`state/commit.lock`与现有error mapping。Graph transition value必须绑定base graph、candidate pointer、candidate states hash、expected Manifest revision；committer重新计算hash，不信任caller claim。

- [ ] **Step 6: Run GREEN**

```bash
python -m pytest \
  tests/test_production_state_commit.py \
  tests/test_production_dependency.py \
  tests/test_production_project.py -q
```

- [ ] **Step 7: Commit**

```bash
git add \
  src/ai_video/production/state_commit.py \
  src/ai_video/production/__init__.py \
  tests/test_production_state_commit.py \
  tests/production_project_factory.py
git commit -m "feat: commit p5 graph state through p2a"
```

### Task 6: Replace Blanket Invalidation with Atomic Selective Transitions

**Files:**
- Modify: `src/ai_video/production/state_commit.py`
- Modify: `src/ai_video/production/hyperframes.py`
- Modify: `tests/test_production_state_commit.py`
- Modify: `tests/test_production_hyperframes.py`
- Modify: `tests/test_production_voice_captions_e2e.py`
- Modify: `tests/production_project_factory.py`

- [ ] **Step 1: Write RED generic project/registry transition tests**

Manifest 2.3下，project/registry变更必须携带candidate graph/states；old applied render pointer保留但render node precise stale/blocked。无graph transition、wrong base、wrong desired、extra blanket stale均在写前拒绝。

- [ ] **Step 2: Write RED audio/voice transition tests**

voice R+4和audio import final replace必须同时选择candidate registry + graph + states；只影响voice/caption/timeline/source/render subgraph。断言unrelated image/BGM nodes仍fresh，old render pointer保留为applied evidence，unknown outcome不resubmit。

- [ ] **Step 3: Write RED render activation tests**

render success final replace同时切`active_render_state`、candidate graph，并批量更新composition/timeline/renderer-source/render applied fingerprints；exact replay零runner/零artifact write。因为current owner没有独立active composition/timeline/source pointer，单独把任一render-domain node标fresh必须拒绝；旧render pointer与caller-forged desired fingerprint也不得推进frontier。

- [ ] **Step 4: Run RED**

```bash
python -m pytest \
  tests/test_production_state_commit.py \
  tests/test_production_hyperframes.py \
  tests/test_production_voice_captions_e2e.py -q
```

- [ ] **Step 5: Implement co-activation and retire 2.3 blanket clear**

`StateCommitRequest`、voice activation request、`ActivateRenderStateRequest`在Manifest 2.3上require一个exact `DependencyGraphTransition`。2.0-2.2保持原coarse behavior；2.3禁止`active_render_state=None`作为stale表达。`hyperframes.py`只转交committer需要的transition，不读取或解析graph。

- [ ] **Step 6: Run GREEN and P3/P4 regressions**

```bash
python -m pytest \
  tests/test_production_state_commit.py \
  tests/test_production_hyperframes.py \
  tests/test_production_voice_captions_e2e.py \
  tests/test_production_composition.py \
  tests/test_production_audio.py \
  tests/test_production_captions.py -q
```

- [ ] **Step 7: Commit**

```bash
git add \
  src/ai_video/production/state_commit.py \
  src/ai_video/production/hyperframes.py \
  tests/test_production_state_commit.py \
  tests/test_production_hyperframes.py \
  tests/test_production_voice_captions_e2e.py \
  tests/production_project_factory.py
git commit -m "feat: apply precise p5 invalidation transitions"
```

### Task 7: Add Crash Windows, Explicit Recovery, and Idempotent Replay

**Files:**
- Modify: `src/ai_video/production/state_commit.py`
- Modify: `tests/test_production_state_recovery.py`
- Modify: `tests/helpers/p2a_crash_worker.py`
- Modify: `tests/production_project_factory.py`

- [ ] **Step 1: Extend crash phase fixtures**

在existing `CommitPhase`中增加graph candidate write/fsync/promotion/verification和final co-activation checkpoints；crash worker支持`graph_bootstrap`、`graph_project_commit`、`graph_voice_activate`、`graph_render_activate` modes，不调用network/provider/real renderer。

- [ ] **Step 2: Write RED partial/temp/orphan tests**

覆盖partial owned graph temp只在non-succeeded attempt下清理；symlink/escape/tamper拒绝；complete unselected graph preserve/report；decoy/latest filename不参与恢复。

- [ ] **Step 3: Write RED old/new/unknown tests**

每个crash点只允许exact old or exact new project/registry/render/graph tuple；final replace outcome不明返回typed unknown；reopen authoritative Manifest；不得重复voice/provider/render action。

```python
def test_graph_activation_crash_recovers_only_exact_old_or_new_quadruple(tmp_path):
    outcomes = run_graph_crash_matrix(tmp_path)
    assert outcomes <= {"exact_old", "exact_new"}
    assert "mixed_graph_state" not in outcomes
```

- [ ] **Step 4: Write RED forward-compatible recovery/rollback tests**

2.0/2.1/2.2 recovery保持；2.3 explicit recovery理解graph attempt；rollback-disabled resolver仍能read/recover 2.3，不删除immutable evidence、不schema downgrade、不auto-activate orphan。

- [ ] **Step 5: Run RED**

```bash
python -m pytest tests/test_production_state_recovery.py -q
```

- [ ] **Step 6: Implement recovery inside existing owner**

扩展`_active_recovery_items()`、`_recover_attempts()`、`_preserved_orphan_items()`、owned temp cleanup和pointer validation。任何reader/startup不得隐式调用这些逻辑。

- [ ] **Step 7: Run GREEN with commit regressions**

```bash
python -m pytest \
  tests/test_production_state_recovery.py \
  tests/test_production_state_commit.py \
  tests/test_production_project.py -q
```

- [ ] **Step 8: Commit**

```bash
git add \
  src/ai_video/production/state_commit.py \
  tests/test_production_state_recovery.py \
  tests/helpers/p2a_crash_worker.py \
  tests/production_project_factory.py
git commit -m "feat: recover p5 graph activation explicitly"
```

### Task 8: Prove the Required Mutation Matrix Offline

**Files:**
- Create: `tests/test_production_selective_rebuild.py`
- Modify: `tests/production_project_factory.py`
- Modify: `tests/test_production_dependency.py`

- [ ] **Step 1: Build one deterministic P4 graph fixture**

Fixture含two Shots、two visual assets、two voice assets、two CaptionTracks/styles、BGM/SFX、CompositionSpec、ResolvedTimeline、source/render receipts。所有bytes/hash固定，zero network/secret/tool call。

- [ ] **Step 2: Parameterize every mutation row**

每case显式提供`mutation`、`must_rebuild`、`must_not_rebuild`；断言exact affected set、first ready frontier和unrelated fresh set。

```python
@pytest.mark.parametrize(
    ("mutation", "must_rebuild", "must_not_rebuild"),
    MUTATION_MATRIX_CASES,
)
def test_required_mutation_matrix_is_precise(mutation, must_rebuild, must_not_rebuild):
    before, after = make_mutated_graph_pair(mutation)
    decision = resolve_changed_graph(before, after)
    assert set(decision.affected_node_ids) == set(must_rebuild)
    assert set(decision.affected_node_ids).isdisjoint(must_not_rebuild)
```

- [ ] **Step 3: Add blocked/failure/replay scenarios**

证明upstream failed -> downstream blocked；same desired failure不auto-retry；new desired clearsold failure；逐节点applied后frontier推进；exact replay不advance Manifest、不调用provider/renderer。

- [ ] **Step 4: Add boundary rejection assertions**

断言无P6 review/repair node execution、无P7 provider、无P8 video/cloud、无alternate renderer、无Legacy Manifest write。Generated-image extension只使用strict synthetic `AssetRecord`。

- [ ] **Step 5: Run focused P5 acceptance**

```bash
python -m pytest \
  tests/test_production_dependency.py \
  tests/test_production_selective_rebuild.py \
  tests/test_production_models.py \
  tests/test_production_project.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py -q
```

- [ ] **Step 6: Commit**

```bash
git add \
  tests/test_production_selective_rebuild.py \
  tests/test_production_dependency.py \
  tests/production_project_factory.py
git commit -m "test: prove p5 selective rebuild matrix"
```

### Task 9: Synchronize Runtime and Branch Truth Documentation

**Files:**
- Modify: `docs/agent-primary-contract-matrix.md`
- Modify: `docs/v0.2-runtime-baseline.md`
- Modify: `docs/v0.2-agentic-production-roadmap.md`
- Modify: `AGENTS.md`
- Modify: `README.md`

- [ ] **Step 1: Correct stale P4 branch status first**

明确写P4已在`f9eedaeb5f6432d8ba0bf937c78111dbcfa3ce80`或后续accepted lineage fast-forward合入local `main`，merged-main full verification为实际复核结果；仍未push/release。修正matrix、baseline、roadmap和`AGENTS.md`中“P4当前feature branch/尚未merge”等过时文字。

- [ ] **Step 2: Document P5 only after runtime acceptance**

写清Graph immutable/no-status、Manifest 2.3 sole lifecycle owner、P2A single writer/recovery、single timeline、selective matrix、migration/rollback、fake/no-network acceptance、P6-P9 deferred。若任何runtime gate未通过，文档继续写planned/not implemented，不制造runtime truth。

- [ ] **Step 3: Verify documentation consistency**

```bash
rg -n "P4|P5|Dependency Graph|Selective Rebuild|Manifest 2.3|ResolvedTimeline|feature branch|merge|push|release" \
  README.md AGENTS.md \
  docs/agent-primary-contract-matrix.md \
  docs/v0.2-runtime-baseline.md \
  docs/v0.2-agentic-production-roadmap.md
git diff --check
```

- [ ] **Step 4: Commit**

```bash
git add \
  README.md AGENTS.md \
  docs/agent-primary-contract-matrix.md \
  docs/v0.2-runtime-baseline.md \
  docs/v0.2-agentic-production-roadmap.md
git commit -m "docs: record accepted p5 dependency runtime"
```

该Task属于未来P5 runtime execution；本plan-only窗口不得修改这些文件。

### Task 10: Independent Review, Full Verification, and Branch Truth

**Files:**
- Review: every P5 changed file
- Review: `git diff "$P5_IMPLEMENTATION_BASE"...HEAD`

- [ ] **Step 1: Run canonical focused verification**

```bash
python -m pytest \
  tests/test_production_dependency.py \
  tests/test_production_selective_rebuild.py \
  tests/test_production_models.py \
  tests/test_production_registry.py \
  tests/test_production_project.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py \
  tests/test_production_composition.py \
  tests/test_production_hyperframes.py \
  tests/test_production_audio.py \
  tests/test_production_captions.py \
  tests/test_production_elevenlabs.py \
  tests/test_production_voice_captions_e2e.py \
  tests/test_config.py \
  tests/test_cli.py -q
```

- [ ] **Step 2: Run Legacy isolation regression**

```bash
python -m pytest \
  tests/test_config.py \
  tests/test_cli.py \
  tests/test_manifest.py \
  tests/test_pipeline.py \
  tests/test_resume_e2e.py \
  tests/test_workflow_loader.py \
  tests/test_workflow_renderer.py -q
```

- [ ] **Step 3: Run full default no-network suite**

```bash
python -m pytest -q
```

Expected: no Provider/live renderer/secret/network test runs by default；P5不要求external tool compatibility refresh，因为它不改变renderer/provider dependency。

- [ ] **Step 4: Run independent reviewer**

Reviewer必须read-only、不得派生subagent，并给出`accept | accept with concerns | reject`、blocking issues、non-blocking concerns、exact file/symbol/test evidence和minimal follow-up。重点检查：

- Graph完全无mutable freshness/status；Manifest是唯一desired/applied/lifecycle owner。
- `ProductionStateCommitter`仍是唯一graph/Manifest/registry/render activation和recovery writer。
- old blanket clear已仅在2.3被precise lifecycle替代；旧render evidence保留但不会被误当fresh。
- desired formula deterministic、typed、edge-by-edge；blocked/frontier正确，same input stop propagation。
- `ResolvedTimeline`仍唯一timing owner，Graph没有frame/sample/order算法。
- script/voice/alignment/caption style/audio mix/visual/CompositionSpec/renderer mutations exact matrix成立。
- Manifest 2.0/2.1/2.2兼容、2.3 crash/unknown/replay/recovery/rollback fail closed。
- Legacy、P6/P7/P8/P9、second renderer/provider/cloud均未扩scope。

Parent必须直接复核blocking claims和final diff，修复后重跑相关tests；不能用review summary替代judgment。

- [ ] **Step 5: Inspect final diff and branch truth**

```bash
P5_IMPLEMENTATION_BASE="$(git merge-base main HEAD)"
test -n "$P5_IMPLEMENTATION_BASE"
git show -s --format='%H %s' "$P5_IMPLEMENTATION_BASE"
git status --short --branch
git diff --check "$P5_IMPLEMENTATION_BASE"...HEAD
git diff --name-status "$P5_IMPLEMENTATION_BASE"...HEAD
git log --oneline --decorate "$P5_IMPLEMENTATION_BASE"..HEAD
git rev-list --left-right --count origin/main...HEAD
```

确认每一行映射到P5；无package/Legacy/P6+/secret/generated runtime artifact/unrelated dirty file。

- [ ] **Step 6: Stop on feature branch**

不merge、不push、不release。报告exact branch、HEAD、test counts、review verdict、remaining risk和local-vs-origin truth；再次说明P5 implementation completion也不等于publication或后续phase authorization。

## Focused Verification Command

P5 runtime implementation的canonical focused command是：

```bash
python -m pytest \
  tests/test_production_dependency.py \
  tests/test_production_selective_rebuild.py \
  tests/test_production_models.py \
  tests/test_production_registry.py \
  tests/test_production_project.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py \
  tests/test_production_composition.py \
  tests/test_production_hyperframes.py \
  tests/test_production_audio.py \
  tests/test_production_captions.py \
  tests/test_production_elevenlabs.py \
  tests/test_production_voice_captions_e2e.py \
  tests/test_config.py \
  tests/test_cli.py -q
```

该命令必须使用deterministic local fixtures、fake/no-network paths；不安装SDK、不调用ElevenLabs/ComfyUI、不读取secret、不执行paid/free quota。

## Independent Review Questions

Reviewer必须能用code/tests回答：

1. Graph是否只保存typed nodes/edges/reasons/contributions，完全没有mutable desired/applied/status？
2. Manifest 2.3是否是active graph、desired/applied和lifecycle唯一owner？
3. graph/project/registry/render final selection是否只有一个P2A Manifest commit point？
4. old applied render evidence在registry变化后是否保留、严格验证且不会被误当fresh？
5. desired fingerprint是否由canonical typed contributions + upstream desired递归计算，并在same input处停止？
6. failed/blocked/superseded与ready frontier是否deterministic、idempotent且无auto-retry？
7. `ResolvedTimeline.composition_fingerprint`是否被opaque消费，而不是graph重算timing/order？
8. required mutation matrix是否同时证明must rebuild与must not rebuild？
9. Manifest migration、partial/temp/orphan、unknown outcome、exact replay、forward reader/recovery和rollback是否完整？
10. P6/P7/P8/P9、Legacy、second renderer、Provider/cloud是否完全未实现？

## Rollback

P5 operational rollback固定为：

1. 禁用新的graph mutation/rebuild entrypoints，不删除state。
2. 保留Manifest 2.3、DependencyGraphSnapshot 2.0 reader与explicit recovery。
3. 保留active及orphan immutable graph snapshots、dependency states、historical render evidence和attempt receipts。
4. 禁止schema downgrade到2.2，禁止重写old graphs或用blanket clear伪装rollback。
5. Manifest 2.0-2.2 projects继续走原P2-P4 behavior；已迁移2.3 project可read/audit/recover，但在resolver disabled时对新mutation typed-fail。
6. 不删除或自动activate partial/complete orphan；future GC/retention属于P9或独立授权。

## Definition of Done

P5 runtime只有在未来另获授权并满足以下全部条件时才可称为implemented：

- immutable graph 2.0只含typed nodes/edges/reasons/contributions并通过canonical DAG/hash/path tests。
- Manifest 2.3独占active graph、desired/applied与fresh/stale/failed/blocked/superseded lifecycle。
- P2A committer独占graph write/co-activation/recovery，final Manifest replace是single commit point。
- P2/P3/P4 fingerprints均按typed contribution进入graph，`ResolvedTimeline`仍唯一timing owner。
- required mutation matrix对每个case证明exact rebuild与must-not-rebuild集合，无blanket stale。
- blocked frontier、failed behavior、idempotent replay和same-input stop propagation通过tests。
- 2.0/2.1/2.2 -> 2.3 migration、temp/partial/orphan、crash unknown、forward reader/recovery和rollback通过。
- focused、Legacy和full default no-network suites实际通过。
- independent reviewer无blocking issue，parent完成final diff/branch truth review。
- docs先修正P4已merge local main的stale状态，再只记录实际验收的P5 runtime。
- feature branch checkpoint已提交，但不merge、不push、不release；P6-P9仍需独立plan与授权。

本plan-only checkpoint的Definition of Done更窄：只创建并独立审查本文件、只提交本文件、不实施任何runtime、不修改其它docs、不merge、不push，并明确本plan不是P5 runtime authorization。
