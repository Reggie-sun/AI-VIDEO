# AI-VIDEO Agentic Production Harness P6 Codex Review and Repair Harness Implementation Plan

**Goal:** 在已验收并推送的 P2/P2A/P3/P4/P5 contract 之上，引入 strategy-aware、durable、fail-closed 的 Review / Repair / Final Acceptance Harness，使 Codex 只能依据绑定 exact render、timeline、dependency graph 与 QA policy 的 immutable evidence 提出 repair，并且只有经授权的 Repair Receipt 才能触发 P5 precise selective rebuild。

**Architecture:** Project-local `video-analysis` MCP 继续只收集 technical evidence，不拥有 Production Manifest、review/repair lifecycle 或 final acceptance。新的 `src/ai_video/production/review.py` 只负责 immutable receipt identity、五层 QA adjudication、review freshness、repair scope validation 与 final acceptance 的纯计算；`ProductionManifest 2.4` 独占 mutable review/repair/acceptance lifecycle；`ProductionStateCommitter` 继续是 Review Evidence、Review Receipt、Repair Receipt、Final Acceptance Receipt promotion、Manifest activation、unknown-outcome mapping 与 explicit recovery 的唯一 writer。P5 graph shape 不增加 QA/review/repair nodes；QA policy-only change只使 Manifest-owned review state stale。只有 approved repair 产生 exact before/after production graph 后，既有 P5 resolver 才计算并验证 precise invalidation。

**Tech Stack:** Python 3.11+、Pydantic v2 strict/frozen models、stdlib canonical JSON/SHA-256、既有 P2A no-follow/fsync/promote-without-overwrite/atomic Manifest replace primitives、既有 P5 pure resolver、project-local `video-analysis` MCP、pytest deterministic media fixtures/fakes。无新 runtime dependency、无 network、无 Provider、无 ComfyUI、无 HyperFrames executable、无 paid/free quota、无 secret。

---

Status: 本文件仅是 P6 implementation plan。它不授权 P6 runtime implementation、merge、push、release、P7/P8/P9、真实 renderer execution、Provider call、dependency installation 或任何 external write。Planning base 是 local `main` commit `efb2c46b20db7c2380b06d1a0ead3e34d66967f9`；`origin/main` 是 `52eca580dc93ad756f5c5e266e730b4017d48ce1`，已包含 accepted P5。Local `main` 只比 `origin/main` ahead 1 个独立 research commit：`docs/research/2026-08-17-minimax-h3-rtx5090-provider-assessment.md`。该 commit 不得被修改、重写、revert、amend 或混入 P6 runtime commits。P5 已 push、尚未 release；baseline、roadmap、contract matrix 与 `AGENTS.md` 中仍称 P5 “尚未 push”的文字是 stale docs，不覆盖 Git/code truth。

## Problem Boundary

P6 要建立的 bounded path 是：

```text
Manifest-selected ProductionProject 2.x
+ current DependencyGraphSnapshot 2.0 and dependency states
+ current RenderStateSnapshot / ResolvedTimeline / exact output hash
+ immutable QA Policy and Shot visual_strategy context
        |
        v
ProductionStateCommitter::run_review()
R+1 durable ReviewRequest + one-use analysis permit
        |
        v
video-analysis MCP
technical evidence collection only; no receipt/state/acceptance ownership
        |
        v
review.py::evaluate_review_layers()
technical | layout | strategy | semantic
        |
        v
ProductionStateCommitter-owned immutable ReviewEvidence/ReviewReceipt promotion
+ Manifest 2.4 review lifecycle activation
        |
        +--> review fail / evidence absent -> no final acceptance
        |
        v
Codex proposes bounded RepairRequest
+ exact issue/evidence IDs, targets, expected P5 invalidation, authorization
        |
        v
ProductionStateCommitter::execute_approved_repair()
R+1 durable RepairRequest + Manifest-selected ApprovedRepairReceipt, then one-use permit
R+2 exact candidate production artifacts + graph transition
R+3 existing atomic render activation
R+4 fresh re-review + immutable RepairOutcomeReceipt
        |
        v
review.py::evaluate_final_acceptance()
current graph + current timeline + current render hash + fresh required receipts
        |
        v
ProductionStateCommitter::activate_final_acceptance()
one Manifest atomic replace; no second writer or acceptance owner
```

Problem boundary记录：

- Single durable state owner 是 `src/ai_video/production/state_commit.py::ProductionStateCommitter`。它独占 Manifest、receipt snapshot promotion、selection、attempt lifecycle、commit-point mapping 与 explicit recovery。
- Pure review/repair contract owner 是 `src/ai_video/production/review.py`。它不写文件、不调用 MCP/renderer/provider、不修改 creative intent、不持有 active state。
- Technical evidence collection owner 是 `src/ai_video_mcp/tools/review.py::video_review()`。它只报告 measured evidence，不宣告 Production review pass、semantic pass 或 final acceptance。
- P5 invalidation owner 仍是 `src/ai_video/production/dependency.py::{resolve_dependency_state,select_rebuild_nodes}`。Receipt 自报的 expected invalidation 只是 authorization claim，必须用 exact before/after graph 重算验证。
- Temporal owner 仍是 `ResolvedTimeline`。P6 只能消费 exact `composition_fingerprint`、frame/sample spans 与 receipt pointer，不计算或修正 canonical order/frame/sample/timing。
- Old paths to extend/contain 是 `review.py::_review_issues()`、`optimize_plan.py::video_optimize_plan()` 与 `apply_optimization.py::apply_video_optimization()`；不得另建第二套 MCP repair control plane。
- P6 不执行 P7 image generation、P8 generated-video/cloud Provider 或 P9 retention/hardening。

## Planning Truth and Preflight

| Surface | Current Runtime Truth | P6 Consequence |
| --- | --- | --- |
| Git | `HEAD=efb2c46`；`origin/main=52eca58`；`origin/main...main = 0 1` | 直接在 single-writer clean `main` planning；implementation 日重新核验，绝不从旧 P5 worktree 或 research parent 之外错误起步 |
| P2 | `Shot.visual_strategy` 已有六种 enum；`Shot.review_policy` 仅有 `required_checks` | Strategy context可直接消费；QA policy/version另建 immutable contract，不能把 heuristic 塞回 Shot lifecycle |
| P3/P4 | `ResolvedTimeline`、render output hash、audio spans、caption cues均已有 exact durable evidence | Review必须绑定这些 current identities，不允许从文件名、mtime、console推断 |
| P5 | Graph 2.0 immutable；Manifest 2.3独占 graph lifecycle；selective resolver pure | P6 review lifecycle不得进入 Graph；approved repair只把 exact before/after graph交给既有 resolver |
| P5 boundary test | `test_scope_boundaries_remain_absent_and_generated_image_uses_asset_seam` 明确排除 `qa/review/repair` node IDs | P6保持 graph shape；不得为方便而增加 QA node、repair node或mutable review status |
| MCP review | `_review_issues()` 按整段视频 frame diversity/scene count直接产生 `static_visuals` | Production mode必须接收 Shot/timeline strategy windows；合法低运动策略不得失败 |
| MCP optimize | `video_optimize_plan()` 把 issues 映射为 Legacy config/shot/workflow edit建议 | Legacy mode保留；Production mode只能形成 typed repair proposal，不得生成未授权直接 edit path |
| MCP apply | `_write_yaml()`、`_apply_project_defaults()`、`_apply_shot_prompts()` 直接改文件 | 仅保留 Legacy compatibility；Production mode必须在任何写入前 fail closed，真实 repair只走 committer-issued permit |
| Persistence | Manifest最高为2.3；无 Review/Repair/Acceptance schemas | 首次P6 mutation显式迁移到2.4；read不升级，rollback不降级 |

Planning/implementation preflight：

```bash
git status --short --branch
git rev-parse HEAD
git rev-parse origin/main
git rev-list --left-right --count origin/main...main
git log --oneline --decorate -12
git worktree list --porcelain
rg -n "static_visuals|def video_review|def video_optimize_plan|def apply_video_optimization|_write_yaml" \
  src/ai_video_mcp/tools tests/test_mcp_*.py
rg -n "VisualStrategy|ReviewPolicy|ToolIdentity|ProductionManifest|DependencyGraphSnapshot|resolve_dependency_state|select_rebuild_nodes|activate_render_state|def recover" \
  src/ai_video/production tests
```

Expected planning truth：当前 tree clean；本 P6 plan是唯一新增文件；旧 worktree `/home/reggie/vscode_folder/AI-VIDEO-p5-plan` 不是 base且不得清理。Implementation Task 0开始时必须记录而不是事后重算：

```bash
P6_IMPLEMENTATION_BASE="$(git rev-parse HEAD)"
test -n "$P6_IMPLEMENTATION_BASE"
git show -s --format='%H %s' "$P6_IMPLEMENTATION_BASE"
```

该exact local base必须包含并保留受保护research commit；最终P6-only diff始终使用`$P6_IMPLEMENTATION_BASE...HEAD`。`origin/main...HEAD`只报告publication truth，不作为P6-only diff base。Implementation 日若出现 unrelated dirty work或并发writer，按当时 `AGENTS.md` 隔离；不得覆盖用户改动。

## Canonical Ownership

| Contract | Single Owner | Non-Owner Rule |
| --- | --- | --- |
| immutable P6 schemas | `production/models.py` | MCP dict、Agent memory、console output不得发明未校验字段 |
| review/repair fingerprints and pure adjudication | `production/review.py` | committer、MCP、renderer不得复制判定公式 |
| measured technical evidence | `ai_video_mcp/tools/review.py` | 只报告metrics/evidence；不写Manifest、不声明semantic/final pass |
| mutable review/repair/final lifecycle | `ProductionManifest 2.4` | Graph、Receipt、Asset Registry、console、Agent memory均不得保存active mutable truth |
| receipt write/selection/recovery | `ProductionStateCommitter` | 不新增ReceiptWriter、RepairRegistry、sidecar journal、startup repair或automatic recovery |
| production dependency/invalidation | P5 `dependency.py` | Repair Receipt不得直接把自报set写成stale；必须重算before/after graph |
| project/registry/render exact evidence | existing P2/P3/P4 pointers and readers | P6不复制asset provenance、timeline或render verification |
| final acceptance decision | `review.py::evaluate_final_acceptance()` + committer activation | MCP、heuristic、review text或Agent memory不能单独accept |
| creative repair choice | Codex + durable explicit authorization | heuristic、`video_optimize_plan`、`video_apply_optimization`不得自行改creative intent |

## QA Layer Contract

| Layer | Owner | Required Inputs | Evidence Strength | Fail-Closed Rule |
| --- | --- | --- | --- | --- |
| `technical` | `video-analysis`收集；`review.py`校验/adjudicate | exact output hash、probe、frame/audio sample metrics、timeline audio/motion expectations、tool identity | deterministic measured evidence；每个metric有content-addressed evidence ID | evidence缺失/哈希不匹配/tool identity不符为`not_evaluated`，不能pass；black、required-motion frozen、expected-audio silent、clipping等命中为fail |
| `layout` | selected renderer产生可测布局；`review.py`校验 | current timeline cue/layer IDs、delivery safe area、caption boxes、layer boxes、transition boundary samples | renderer-bound geometry/pixel evidence或human attestation；必须绑定exact frames | 只有console/CSS source/heuristic无frame evidence不能pass；overflow、unsafe area、text clipping、layer collision、transition boundary defect为fail |
| `strategy` | `review.py` | exact Shot `visual_strategy`、Shot/span mapping、motion directives、technical/layout evidence | typed strategy contract + bounded measured span evidence | `static_image`/合法低运动不得因video-like diversity不足失败；`image_motion`/`motion_graphics`/dynamic video必须按各自contract判断；无strategy mapping不pass |
| `semantic` | explicit evaluator adapter或human reviewer | story/Shot intent、character/continuity expectations、exact render evidence、evaluator/human identity | signed/identified human evidence或explicit evaluator receipt；不得是generic heuristic | evidence absent=`not_evaluated`；heuristic、console text、Agent memory、未落盘judgment永不等于pass |
| `final_acceptance` | `review.py::evaluate_final_acceptance()`；`ProductionStateCommitter`持久化 | current desired graph pointer/states、current ResolvedTimeline fingerprint、current render output hash、current QA policy、fresh required Review Receipts | exact reopened immutable pointers + all required pass verdicts | 任一identity drift、required layer stale/fail/not_evaluated、rerender后未重review、semantic required但无explicit evidence均拒绝accept |

`QaVerdict` 固定为 `pass | fail | not_evaluated`。不得用“warning”“unknown but okay”绕过 required layer。`final_acceptance` 不是第五个 heuristic；它是对前四层与 current production identities 的 fail-closed aggregation。

## Old Path to Replace or Extend

必须精确替换/扩展以下旧路径：

- 扩展 `src/ai_video_mcp/tools/review.py::_review_issues()`：Legacy无context行为保持；Production context必须按 `ResolvedTimeline.visual_spans` 的 exact Shot window + `Shot.visual_strategy` 解释 frame diversity。原 `static_visuals` 不再是production acceptance verdict，只能成为 raw low-diversity evidence。
- 扩展 `video_review()`：Production mode返回 strict `TechnicalEvidenceBundle` payload，包含 evidence IDs、input output hash、tool identity、per-window frame/audio measurements。它仍不写 Review Receipt/Manifest。
- 扩展technical measurements覆盖 genuine frozen、black、silent、clipped；所有阈值来自 immutable `QaPolicy`，不得散落在 optimize/apply tools。
- 扩展 `video_optimize_plan()`：Legacy返回现有 file-target plan；Production mode只能消费 durable Review Receipt identity并输出 `RepairProposal`，不得把 `static_visuals` 默认翻译为“加motion prompt”。
- 限制 `apply_video_optimization()`：Legacy path保持；一旦收到Production project/review context，在调用 `_write_yaml()`、`_apply_project_defaults()` 或 `_apply_shot_prompts()` 前必须返回 typed authorization-required/no-op。它不能接收一个bool绕过，也不能成为committer的替代入口。
- P6实际repair只通过 `ProductionStateCommitter::execute_approved_repair()` 使用 committer-issued one-use permit。Executor只能返回 exact candidate artifacts；不能直接选择Manifest、graph lifecycle或final acceptance。
- `state_commit.py::activate_render_state()` 在Manifest 2.4上必须同一个final replace中保持 Composition/Timeline/Source/Render atomic fresh，同时把所有绑定旧render/timeline/output/graph的affected review states精确标stale；不得拆开推进四个render nodes。
- `project.py::load_production_project()` 只读reopen Manifest-selected Review/Repair/Acceptance receipts；不扫描latest、不自动recover、不清理orphans、不重新判定semantic。

## Unchanged Contracts

- Legacy public CLI仍只有`ai-video validate`、`ai-video run`、`ai-video resume`；不加command、flag或exit-code语义。
- Legacy Manifest v1、flat `runs/<run_id>/` layout、resume、local-first ComfyUI、Wan workflow、Legacy MCP optimize/apply compatibility不变。
- P2 reader继续strict/read-only/no-network；load不创建目录、不upgrade schema、不recover、不写review状态。
- P2A `ProductionStateCommitter`继续唯一Manifest/snapshot activation/recovery owner；final Manifest replace继续是logical commit point。
- P5 `DependencyGraphSnapshot`继续只保存immutable typed nodes/edges/reasons/contributions；不保存review status、repair status、acceptance或mutable lifecycle。
- P5 desired/applied/fresh/stale/failed/blocked/superseded继续由Manifest dependency states独占；same-desired failure不auto-retry，exact replay不advance state。
- `ResolvedTimeline`继续唯一order/frame/sample/timing owner；P6只消费opaque fingerprint和resolved spans。
- Composition、ResolvedTimeline、renderer source、render继续由同一次final render activation原子fresh；Review不得分别推进其中任何node。
- HyperFrames仍唯一已实现renderer；无Remotion、Captions.ai final-render path、第二renderer、ffmpeg alternate final renderer或cloud fallback。
- P6不实现P7 image Provider、P8 video Provider、P9 retention、frontend、API server、队列或通用Agent runtime。
- 默认acceptance只使用deterministic fixtures/fakes/no-network；不调用ComfyUI、HyperFrames executable、ElevenLabs/remote API，不读取secret，不使用quota。

## Immutable Receipt Schema

在`models.py`新增strict/frozen、content-addressed/versioned contract。最终命名若需匹配本地style可局部调整，但owner与字段语义不得漂移。

```python
class QaLayer(str, Enum):
    TECHNICAL = "technical"
    LAYOUT = "layout"
    STRATEGY = "strategy"
    SEMANTIC = "semantic"
    FINAL_ACCEPTANCE = "final_acceptance"

class QaVerdict(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    NOT_EVALUATED = "not_evaluated"

class EvidenceStrength(str, Enum):
    MEASURED = "measured"
    RENDERER_BOUND = "renderer_bound"
    EXPLICIT_EVALUATOR = "explicit_evaluator"
    HUMAN = "human"

class QaPolicy(VersionedArtifact):
    schema_version: Literal["2.0"] = "2.0"
    policy_id: str
    policy_version: str
    required_layers: tuple[QaLayer, ...]
    technical_thresholds: QaTechnicalThresholds
    layout_rules: QaLayoutRules
    strategy_rules_version: str
    semantic_requirement: Literal["optional", "required"]

class QaPolicyPointer(StrictModel):
    path: Path
    policy_id: str
    policy_version: str
    content_hash: str
    file_sha256: str

class ReviewRequest(VersionedArtifact):
    schema_version: Literal["2.0"] = "2.0"
    request_id: str
    base_manifest_revision: int
    dependency_graph: DependencyGraphSnapshotPointer
    dependency_states_hash: str
    render_state: RenderStateSnapshotPointer
    render_output_sha256: str
    timeline_fingerprint: str
    qa_policy: QaPolicyPointer
    requested_layers: tuple[QaLayer, ...]
    evidence_tool_identities: tuple[ToolIdentity, ...]

class ReviewRequestPointer(StrictModel):
    path: Path
    request_id: str
    content_hash: str
    file_sha256: str

class ReviewEvidence(VersionedArtifact):
    schema_version: Literal["2.0"] = "2.0"
    evidence_id: str
    layer: QaLayer
    strength: EvidenceStrength
    render_output_sha256: str
    timeline_fingerprint: str
    dependency_graph_revision_id: str
    tool_identity: ToolIdentity
    measurement_contract_version: str
    subject_ids: tuple[str, ...]
    measured_payload: dict[str, JsonValue]

class ReviewReceipt(VersionedArtifact):
    schema_version: Literal["2.0"] = "2.0"
    review_id: str
    layer: Literal[QaLayer.TECHNICAL, QaLayer.LAYOUT, QaLayer.STRATEGY, QaLayer.SEMANTIC]
    render_state: RenderStateSnapshotPointer
    render_output_sha256: str
    timeline_fingerprint: str
    dependency_graph_revision_id: str
    qa_policy: QaPolicyPointer
    evidence_ids: tuple[str, ...]
    tool_identities: tuple[ToolIdentity, ...]
    issue_ids: tuple[str, ...]
    verdict: QaVerdict

class RepairRequest(VersionedArtifact):
    schema_version: Literal["2.0"] = "2.0"
    repair_id: str
    base_manifest_revision: int
    dependency_graph: DependencyGraphSnapshotPointer
    dependency_states_hash: str
    render_state: RenderStateSnapshotPointer
    render_output_sha256: str
    timeline_fingerprint: str
    qa_policy: QaPolicyPointer
    review_receipt_ids: tuple[str, ...]
    issue_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    root_cause_hypothesis: str
    selected_repair_action: RepairAction
    exact_target_artifact_ids: tuple[str, ...]
    exact_target_node_ids: tuple[str, ...]
    expected_invalidation_node_ids: tuple[str, ...]
    actor: ActorIdentity
    authorization: RepairAuthorization
    before_fingerprints: tuple[NamedFingerprint, ...]

class ApprovedRepairReceipt(VersionedArtifact):
    schema_version: Literal["2.0"] = "2.0"
    repair_id: str
    request_content_hash: str
    base_manifest_revision: int
    dependency_graph: DependencyGraphSnapshotPointer
    dependency_states_hash: str
    render_state: RenderStateSnapshotPointer
    render_output_sha256: str
    timeline_fingerprint: str
    qa_policy: QaPolicyPointer
    review_receipt_ids: tuple[str, ...]
    issue_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    root_cause_hypothesis: str
    selected_repair_action: RepairAction
    exact_target_artifact_ids: tuple[str, ...]
    expected_invalidation_node_ids: tuple[str, ...]
    actor: ActorIdentity
    authorization: RepairAuthorization
    before_fingerprints: tuple[NamedFingerprint, ...]

class RepairOutcomeReceipt(VersionedArtifact):
    schema_version: Literal["2.0"] = "2.0"
    repair_id: str
    approved_receipt: ApprovedRepairReceiptPointer
    review_receipt_ids: tuple[str, ...]
    issue_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    root_cause_hypothesis: str
    selected_repair_action: RepairAction
    exact_target_artifact_ids: tuple[str, ...]
    exact_target_node_ids: tuple[str, ...]
    expected_invalidation_node_ids: tuple[str, ...]
    actor: ActorIdentity
    authorization: RepairAuthorization
    before_fingerprints: tuple[NamedFingerprint, ...]
    after_fingerprints: tuple[NamedFingerprint, ...]
    actual_invalidation_node_ids: tuple[str, ...]
    rerender_state: RenderStateSnapshotPointer
    rerender_output_sha256: str
    rerender_timeline_fingerprint: str
    fresh_review_receipts: tuple[ReviewReceiptPointer, ...]

class FinalAcceptanceReceipt(VersionedArtifact):
    schema_version: Literal["2.0"] = "2.0"
    acceptance_id: str
    dependency_graph: DependencyGraphSnapshotPointer
    dependency_states_hash: str
    render_state: RenderStateSnapshotPointer
    render_output_sha256: str
    timeline_fingerprint: str
    qa_policy: QaPolicyPointer
    required_review_receipts: tuple[ReviewReceiptPointer, ...]
    verdict: Literal[QaVerdict.PASS]
```

每个`VersionedArtifact`继续使用既有 semantic sealing；`evidence_id`、`review_id`、`repair_id`与`acceptance_id`必须由canonical payload deterministically验证，不能使用random UUID作为content identity。Canonical paths固定为：

```text
state/reviews/evidence.<content_hash>.json
state/reviews/policy.<content_hash>.json
state/reviews/request.<content_hash>.json
state/reviews/review.<content_hash>.json
state/repairs/request.<content_hash>.json
state/repairs/approved.<content_hash>.json
state/repairs/outcome.<content_hash>.json
state/acceptance/final.<content_hash>.json
```

Paths由`production/paths.py`提供exact helper并接受no-follow/project-root containment。`QaPolicyPointer`、`ReviewRequestPointer`、`RepairRequestPointer`、`ApprovedRepairReceiptPointer`与`RepairOutcomeReceiptPointer`必须验证semantic identity、file SHA-256与canonical path。Review/Final Receipt保存exact `QaPolicyPointer`而非仅保存hash claim，使historical receipt在active policy变化后仍能exact reopen。`measured_payload`必须canonicalize为immutable mapping；raw ReviewEvidence只绑定measurement contract，不绑定QA thresholds，policy-specific pass/fail只在`review.py` adjudicate并进入Review Receipt。Receipt不是Asset Registry，也不得创建独立review/repair registry。

## Manifest 2.4 Review Lifecycle

`ProductionManifest 2.4`新增Manifest-owned fields：

```python
class ReviewLifecycle(str, Enum):
    FRESH = "fresh"
    STALE = "stale"
    FAILED = "failed"
    NOT_EVALUATED = "not_evaluated"

class ReviewLayerState(StrictModel):
    layer: QaLayer
    desired_fingerprint: str
    applied_fingerprint: str | None
    lifecycle: ReviewLifecycle
    active_receipt: ReviewReceiptPointer | None

class FinalAcceptanceState(StrictModel):
    desired_fingerprint: str
    applied_fingerprint: str | None
    lifecycle: ReviewLifecycle
    active_receipt: FinalAcceptanceReceiptPointer | None

class ProductionManifest(StrictModel):
    schema_version: Literal["2.0", "2.1", "2.2", "2.3", "2.4"]
    active_qa_policy: QaPolicyPointer | None = None
    active_review_receipts: tuple[ReviewReceiptPointer, ...] = ()
    review_states: tuple[ReviewLayerState, ...] = ()
    active_approved_repair: ApprovedRepairReceiptPointer | None = None
    repair_outcome_receipts: tuple[RepairOutcomeReceiptPointer, ...] = ()
    final_acceptance_state: FinalAcceptanceState | None = None

class StateCommitAttempt(StrictModel):
    # existing P2A/P3/P4/P5 fields remain unchanged
    review_phase: ReviewAttemptPhase | None = None
    repair_phase: RepairAttemptPhase | None = None
    base_qa_policy: QaPolicyPointer | None = None
    review_request: ReviewRequestPointer | None = None
    repair_request: RepairRequestPointer | None = None
    approved_repair_receipt: ApprovedRepairReceiptPointer | None = None
    base_dependency_graph: DependencyGraphSnapshotPointer | None = None
    base_dependency_states_hash: str | None = None
    base_render_state: RenderStateSnapshotPointer | None = None
    base_render_output_sha256: str | None = None
    base_timeline_fingerprint: str | None = None
    candidate_receipts_hash: str | None = None
```

规则：

1. Manifest 2.0-2.3 read/serialization/recovery保持原bytes contract，不注入P6 defaults，不自动upgrade。P6 fields在model上必须optional/defaulted并由serializer从2.0-2.3 bytes省略；before-validator拒绝old versions显式携带任何P6 field。
2. Manifest 2.4 validator必须要求non-null `active_qa_policy`、canonical unique review states/receipt layers，并验证approval/outcome/final state组合；不能因为model defaults而允许无policy的2.4 Manifest。
3. 首次`bootstrap_review_policy()`显式写入、fsync、reopen并选择exact `QaPolicyPointer`，同时迁移2.3 -> 2.4；后续policy replacement只走`ProductionStateCommitter.activate_qa_policy()`，同一Manifest replace选择new policy并precisely stale affected reviews/final。P6要求active P5 graph，因此不从2.0-2.2直接猜测bootstrap，也不接受caller-only policy hash。
4. Review desired fingerprint唯一公式绑定`layer + exact graph revision + exact render output hash + timeline fingerprint + QA policy ID/version/hash + relevant Shot visual_strategy/review_policy + evidence contract/tool version`。
5. QA policy/version-only change不得改P5 graph；只重新计算affected `ReviewLayerState`为stale/not_evaluated，并使final acceptance stale。
6. Graph revision、current render pointer/output hash或timeline fingerprint变化时，所有绑定旧identity的required review state stale；保留old immutable receipt作为history evidence，但不能current-pass。
7. Rerender activation后 final acceptance必须stale，required review必须重新运行；不能复用旧pixels上的receipt。
8. Semantic receipt只有`EvidenceStrength.EXPLICIT_EVALUATOR`或`HUMAN`且identity可reopen时可pass；heuristic/measured technical evidence不能升级为semantic pass。
9. Final acceptance只有所有required review states fresh且receipt verdict pass、current P5 render node fresh、current timeline/render/output/graph exact match时可activate。
10. Review/repair/acceptance lifecycle不进入DependencyGraphSnapshot或`dependency_states`。
11. P6-aware `StateCommitAttempt` 必须把R+1 ReviewRequest/RepairRequest中的exact typed base identities复制并做cross-field equality validation；old operation禁止P6 fields。Running/succeeded/failed/outcome-unknown phases各自要求完整pointer/hash组合，不能用free-form metadata或console text替代。

## Strategy-Aware Evidence Contract

Production technical context必须由already-loaded verified bundle构造，不能由MCP自己扫描project：

```python
class TechnicalReviewWindow(StrictModel):
    shot_id: str
    visual_strategy: VisualStrategy
    start_frame: int
    end_frame_exclusive: int
    expects_audio: bool
    visual_span_ids: tuple[str, ...]
    motion_expectation: MotionExpectation | None

class MotionExpectation(StrictModel):
    directive_kind: str
    directive_parameters_fingerprint: str
    measurement_kind: Literal["transform_delta", "layer_state_delta", "decoded_frame_delta"]
    minimum_measured_delta_milli: int
    tolerance_milli: int

class TechnicalReviewContext(StrictModel):
    render_output_sha256: str
    timeline_fingerprint: str
    windows: tuple[TechnicalReviewWindow, ...]
    measurement_contract_version: str
```

- `static_image` 的`motion_expectation=None`；低 diversity是合法，不生成`static_visuals` failure。
- `image_motion` 与`motion_graphics` 必须把exact directive kind、canonical parameters fingerprint、measurement kind、minimum delta与tolerance写入window。Raw low-diversity永远不能单独fail；只有directive-specific measured expectation明确未满足才可判frozen/strategy mismatch。
- `generated_video`/`existing_video` 对应video span若连续帧无变化，可产生`frozen_frames` technical issue；不得把“scene count少”单独当fail。
- `hybrid`只对明确dynamic layer/window要求motion；静态layer不被全局diversity误伤。
- 当前P3 `CompositionSpec -> ResolvedTimeline` runtime只接受`static_image` raster path；P6不得借review扩展renderer。若`image_motion`/`motion_graphics`没有current exact P3 render state，runtime verdict必须是`not_evaluated`。Pure adjudication tests可使用strict synthetic measured evidence证明合法低运动不失败，但不得伪造current timeline/render acceptance。
- Black、silence、clipping raw evidence只报告policy-neutral measured luminance/audio peak/silence ranges、sample counts与measurement contract identity；不得在MCP层应用QaPolicy threshold或输出Production pass/fail。`review.py`用Manifest-selected policy完成唯一adjudication。
- Expected-audio为false时silence不是failure；expected-audio为true且证据证明全段/越界静音才fail。
- Layout evidence必须报告caption cue/layer/transition IDs与exact frames；只看HTML/CSS字符串不能pass。

## Repair Authorization and Selective Invalidation

Production repair固定四阶段：

1. `prepare_repair_request()`纯函数从fresh/failing Review Receipts创建immutable request。Request model自身必须绑定current Manifest revision、graph pointer/states hash、render pointer/output、timeline、selected QA policy、exact issues/evidence、targets、expected invalidation、actor和explicit authorization。
2. `ProductionStateCommitter.approve_repair()`在`state/commit.lock`下reopen所有binding，先durable promotion并Manifest-select immutable `ApprovedRepairReceipt`。该pre-action Repair Receipt绑定exact base/action/targets/expected closure/actor/auth/before fingerprints，不会事后修改。
3. 只有Manifest exact-selected approved receipt才能让`begin_repair_execution()`签发不可序列化、one-use、exact-receipt `RepairExecutionPermit`。Authorization missing/expired/wrong actor/wrong target时executor submit count必须为0。
4. `execute_approved_repair()`调用一个bounded injected executor。Executor只返回candidate artifacts/typed result；不得写Manifest、graph state、receipt或final acceptance。Process crash/unknown outcome后permit不可重mint，explicit recovery不得blind reapply。
5. `validate_repair_scope()`用candidate inputs重建P5 graph并调用`resolve_dependency_state()`；`actual affected_node_ids`必须等于允许的exact closure、覆盖approved receipt expected set且无额外unrelated nodes。Mismatch在activation前fail closed。Candidate project/registry/graph仍通过existing committer final replace；后续render用existingatomic unit，re-review后写新的immutable `RepairOutcomeReceipt`，它引用approved receipt并绑定actual invalidation、after fingerprints、exact rerender pointer/output/timeline与fresh review receipt pointers。

禁止：

- `video_optimize_plan`自报target set直接写Manifest；
- `video_apply_optimization`用bool/CLI flag绕过permit；
- blanket stale、按Shot顺序向后invalidate、整个project repair；
- repair graph里增加`repair:*`node或mutablestatus；
- 未经authorization改变Shot intent、visual strategy、prompt、caption text/style、voice、asset或composition；
- unknown outcome后“因为是local edit”就重复apply。

## Crash, Recovery, and Exact Replay

Review attempt windows：

| Window | Durable Truth | Replay/Recovery Rule |
| --- | --- | --- |
| before R+1 | old review states/receipts | no analysis permit, submit count 0 |
| R+1 review intent | exact request + base graph/render/timeline/policy + one-use permit identity | same request active时不得发第二permit |
| evidence collection returns, before promotion | outcome可能unknown | 不自动重复analysis；explicit recovery只认exact durable evidence |
| evidence/receipt promoted, before Manifest replace | complete orphan evidence | preserve/report，不scan latest、不autoactivate |
| final Manifest replace | exact receipts + review states selected together | single logical commit point |
| replace outcome unknown | authoritative Manifest old or new | reopen exact Manifest；new exact identity则replay no-op，否则typed unknown |

Repair attempt windows：

| Phase | Durable Truth | Replay/Recovery Rule |
| --- | --- | --- |
| R+1 `approved` | RepairRequest + Manifest-selected immutable ApprovedRepairReceipt、actor/auth、base identities、expected invalidation | only selected approved receipt can mint one-use permit |
| action started/unknown | request submitted; outcome not authoritative | no blind reapply/remint；explicit operator resolution |
| R+2 `repair_applied` | candidate artifact/graph exact old or new active tuple | existing P2A recovery only accepts exact tuple |
| R+3 `rerendered` | existing RenderState activation atomic | Composition/Timeline/Source/Render一起fresh；review/final stale |
| R+4 `reviewed` | fresh required Review Receipts bound to new output | immutable RepairOutcomeReceipt can be materialized |
| succeeded | immutable RepairOutcomeReceipt selected in Manifest and linked to approval | exact replay calls analysis/repair/render 0 times |

Complete orphan Review/Repair/Acceptance snapshots preserve/report；partial owned temps仅在bounded non-succeeded attempt中清理。Reader/startup不得automatic recovery。Rollback不删除immutable receipts或downgrade2.4。

## Exact Implementation File Map

### Create

- `src/ai_video/production/review.py`
  - `review_evidence_semantic_sha256()`、`review_receipt_semantic_sha256()`、`repair_request_fingerprint()`、`approved_repair_receipt_semantic_sha256()`、`repair_outcome_receipt_semantic_sha256()`、`desired_review_states()`、`evaluate_review_layers()`、`validate_repair_scope()`、`evaluate_final_acceptance()`；pure/no-write/no-network。
- `tests/test_production_review.py`
  - receipt hash/schema bindings、五层QA、strategy-aware判定、policy/render/timeline/graph freshness、semantic fail-closed、final acceptance。
- `tests/test_production_repair.py`
  - authorization、one-use permit、exact invalidation、unapproved zero submit、unknown outcome、exact replay、unrelated freshness。
- `tests/test_production_review_repair_e2e.py`
  - deterministic review -> approved bounded repair -> selective rebuild -> rerender fake evidence -> mandatory re-review -> final acceptance。

### Modify

- `src/ai_video_mcp/tools/review.py`
  - strategy-window-aware technical evidence；frozen/black/silent/clipped measurements；Legacy default preserved。
- `src/ai_video_mcp/tools/optimize_plan.py`
  - explicit Legacy/Production separation；Production只输出typed proposal。
- `src/ai_video_mcp/tools/apply_optimization.py`
  - Production fail-closed/no direct write；Legacy behavior unchanged。
- `src/ai_video/production/models.py`
  - P6 immutable schemas/pointers（含QaPolicy、ReviewRequest、approved/outcome repair chain）、Manifest 2.4 review/repair/acceptance lifecycle、attempt phases/exact base fields。
- `src/ai_video/production/paths.py`
  - canonical evidence/review/repair/acceptance paths and containment。
- `src/ai_video/production/dependency.py`
  - 只新增before/after repair validation helper input seam（若pure `review.py`直接复用public resolver则无需修改）；不得添加QA/review/repair nodes或status。
- `src/ai_video/production/project.py`
  - read-only exact selected receipt/final acceptance reopen verification；2.4 current-vs-historical binding。
- `src/ai_video/production/state_commit.py`
  - sole P6 write/orchestration owner、Manifest 2.4 migration、review/repair/final activation、one-use permits、crash/recovery/exact replay。
- `src/ai_video/production/__init__.py`
  - 只导出reviewed models、pure decision与safe committer surfaces；不导出raw writer/permit constructor。
- `src/ai_video/errors.py`
  - typed `REVIEW_EVIDENCE_INVALID`、`REVIEW_NOT_CURRENT`、`REPAIR_AUTHORIZATION_REQUIRED`、`REPAIR_SCOPE_INVALID`、`FINAL_ACCEPTANCE_INVALID`。
- `tests/test_mcp_review.py`
- `tests/test_mcp_optimize_plan.py`
- `tests/test_mcp_apply_optimization.py`
- `tests/test_production_models.py`
- `tests/test_production_dependency.py`
- `tests/test_production_selective_rebuild.py`
- `tests/test_production_project.py`
- `tests/test_production_state_commit.py`
- `tests/test_production_state_recovery.py`
- `tests/test_production_hyperframes.py`
- `tests/production_project_factory.py`
- `tests/helpers/p2a_crash_worker.py`
  - compatibility、fixtures、P6 phases、current graph invariants、crash/unknown/recovery。
- `docs/agent-primary-contract-matrix.md`
- `docs/v0.2-runtime-baseline.md`
- `docs/v0.2-agentic-production-roadmap.md`
- `AGENTS.md`
- `README.md`
  - only after runtime acceptance；先同步Git truth（P5已push、P6 implementation branch truth），再记录实际通过的P6 behavior。

### Do Not Modify

- Legacy `src/ai_video/{cli.py,config.py,manifest.py,pipeline.py}` 与 workflow/ComfyUI/ffmpeg owners，除非implementation evidence证明technical probe缺口且先修订plan；默认不触碰。
- `src/ai_video/production/{audio.py,captions.py,elevenlabs.py,composition.py}` owner logic。
- package/dependency files。
- existing P5 plan/spec/research document。
- P7/P8/P9 modules、Provider、second renderer、frontend、API server或general Agent runtime。

## Required Acceptance Matrix

| Case | Must Prove | Must Not Happen | Primary Test |
| --- | --- | --- | --- |
| valid `static_image` | low frame diversity is recorded but strategy/technical pass when other checks pass | no `static_visuals` fail, no motion prompt repair | `test_mcp_review.py::test_production_static_image_is_not_misclassified_as_static_visuals` |
| legal low-motion `image_motion` | directive-specific small delta within tolerance passes pure strategy adjudication | no raw diversity failure；unsupported current P3 render remains not_evaluated | `test_production_review.py::test_legal_low_motion_image_motion_uses_directive_tolerance` |
| legal low-motion `motion_graphics` | sparse keyed/layer delta satisfying directive passes pure adjudication | no video-like scene diversity requirement；no renderer expansion | `test_production_review.py::test_legal_low_motion_graphics_uses_layer_expectation` |
| genuine frozen | motion-required exact span emits `frozen_frames` with frame range/evidence ID | no whole-video scene-count guess | `test_mcp_review.py::test_production_required_motion_span_reports_genuine_freeze` |
| black | policy-threshold black range fails technical | no console-only verdict | `test_production_review.py::test_black_frame_evidence_fails_technical_layer` |
| silent | expected-audio span silent fails；no-audio strategy may pass | no unconditional “has_audio=false” fail | `test_production_review.py::test_silence_is_relative_to_timeline_audio_expectation` |
| clipped | measured clipped samples fail technical | no guessed waveform result | `test_production_review.py::test_measured_audio_clipping_fails_technical_layer` |
| caption overflow | exact cue/frame box outside canvas fails layout | no style-source-only pass | `test_production_review.py::test_caption_overflow_fails_layout` |
| safe area | box outside policy safe area fails layout | no pixel-free pass | `test_production_review.py::test_safe_area_violation_fails_layout` |
| layer collision | overlapping forbidden layer boxes fail layout | no blanket collision across allowed overlays | `test_production_review.py::test_layer_collision_uses_exact_policy_and_frame` |
| transition boundary | wrong boundary frame/opacity evidence fails layout | no timeline recomputation | `test_production_review.py::test_transition_boundary_evidence_binds_resolved_frames` |
| strategy mismatch | dynamic strategy without required behavior fails strategy | legal low-motion strategy stays valid | `test_production_review.py::test_strategy_mismatch_is_distinct_from_legal_low_motion` |
| semantic evidence absent | semantic=`not_evaluated`; required semantic blocks acceptance | heuristic/console/memory cannot pass | `test_production_review.py::test_semantic_absence_never_becomes_pass` |
| QA policy-only change | affected review state + final acceptance stale | graph/assets/render remain byte/state fresh | `test_production_review.py::test_policy_only_change_stales_review_not_p5_graph` |
| render/timeline/output drift | old review stale on any exact identity change | old receipt not rebound | `test_production_review.py::test_render_timeline_or_output_change_stales_old_review` |
| unapproved repair | executor submit count 0 and no write | no creative/config/Manifest mutation | `test_production_repair.py::test_unapproved_repair_submit_count_is_zero` |
| approved exact repair | actual P5 affected set equals authorized closure | no blanket stale | `test_production_repair.py::test_approved_repair_invalidates_only_exact_target_graph` |
| rerender | render-domain four nodes atomic fresh；old review/final stale | no final acceptance before re-review | `test_production_review_repair_e2e.py::test_rerender_requires_new_review_before_acceptance` |
| exact replay | analysis/repair/render call counts all 0 | no revision/evidence rewrite | `test_production_review_repair_e2e.py::test_exact_replay_repeats_no_material_action` |
| crash/unknown repair | permit not reminted；explicit recovery reports unknown | no blind repair reapply | `test_production_state_recovery.py::test_repair_unknown_outcome_never_blind_reapplies` |
| unrelated domains | unrelated Shot/voice/caption/visual/audio remain fresh | no Shot-order propagation | `test_production_repair.py::test_repair_preserves_unrelated_domain_freshness` |

## Task 0: Revalidate Runtime Truth and Lock the Boundary

**Files:** read only all files listed by this plan; test existing P5/MCP baseline.

- [ ] **Step 1: Verify exact base and writer ownership**

运行`Planning Truth and Preflight`命令。Expected：implementation base是包含`52eca58`与independent research commit的accepted descendant；research file无diff；无overlapping writer。

- [ ] **Step 2: Record exact old-path proof**

```bash
rg -n "def _review_issues|static_visuals|def video_review" src/ai_video_mcp/tools/review.py
rg -n "def video_optimize_plan|static_visuals" src/ai_video_mcp/tools/optimize_plan.py
rg -n "def _write_yaml|def _apply_project_defaults|def _apply_shot_prompts|def apply_video_optimization" \
  src/ai_video_mcp/tools/apply_optimization.py
rg -n "test_scope_boundaries_remain_absent|resolve_dependency_state|select_rebuild_nodes" \
  src/ai_video/production/dependency.py tests/test_production_selective_rebuild.py
```

- [ ] **Step 3: Run pre-change focused baseline**

```bash
python -m pytest \
  tests/test_mcp_review.py \
  tests/test_mcp_optimize_plan.py \
  tests/test_mcp_apply_optimization.py \
  tests/test_production_dependency.py \
  tests/test_production_selective_rebuild.py \
  tests/test_production_models.py \
  tests/test_production_project.py \
  tests/test_production_state_commit.py \
  tests/test_production_state_recovery.py -q
```

Expected：green。Pre-existing failure先隔离，不扩大P6修复面。

## Task 1: Define Strict P6 Receipt and Manifest 2.4 Schemas

**Files:** `models.py`、`paths.py`、`errors.py`、`test_production_models.py`。

- [ ] **Step 1: Write RED schema tests**

覆盖exact enums、strict/frozen/no-extra、semantic IDs/content hash、QaPolicy/ReviewRequest/approved/outcome canonical pointers、required receipt fields、evidence strength、semantic pass restriction、approved pre-action Receipt与outcome before/after/rerender/review chain、Final Acceptance bindings、Manifest 2.0-2.3 serialization unchanged、2.4-only fields、attempt exact base/phase invariants。

- [ ] **Step 2: Run RED**

```bash
python -m pytest tests/test_production_models.py -q
```

Expected：new symbols/schema missing。

- [ ] **Step 3: Implement minimum models/paths/errors**

不得在models validator中实现MCP metrics、graph resolution、filesystem write或final acceptance orchestration。

- [ ] **Step 4: Run GREEN**

```bash
python -m pytest tests/test_production_models.py -q
```

- [ ] **Step 5: Commit exact files**

```bash
git add src/ai_video/production/models.py src/ai_video/production/paths.py src/ai_video/errors.py tests/test_production_models.py
git commit -m "feat: define p6 review and repair contracts"
```

## Task 2: Implement Pure Review, Repair Scope, and Acceptance Decisions

**Files:** create `production/review.py`、`test_production_review.py`、`test_production_repair.py`；verify only existing P5 resolver.

- [ ] **Step 1: Write RED receipt identity and freshness tests**

证明canonical order/mtime independence、policy-only staleness、graph/render/timeline/output drift、old receipt retained but ineligible、no writes/network。

- [ ] **Step 2: Write RED five-layer tests**

覆盖QA matrix全部technical/layout/strategy/semantic/final rules；`not_evaluated`不可被aggregation当pass。

- [ ] **Step 3: Write RED repair scope tests**

用P5 before/after graphs断言Receipt expected set不受信任；exact equality/allowed closure才通过；unrelated nodes必须fresh；blanket set拒绝。

- [ ] **Step 4: Run RED**

```bash
python -m pytest tests/test_production_review.py tests/test_production_repair.py -q
```

- [ ] **Step 5: Implement pure public surface**

所有函数输入/输出immutable；只调用existing canonical hash与P5 public resolver；不open文件、不调用MCP、renderer/provider、clock或random。

- [ ] **Step 6: Run GREEN and P5 purity regressions**

```bash
python -m pytest \
  tests/test_production_review.py \
  tests/test_production_repair.py \
  tests/test_production_dependency.py \
  tests/test_production_selective_rebuild.py -q
```

- [ ] **Step 7: Commit**

```bash
git add src/ai_video/production/review.py tests/test_production_review.py tests/test_production_repair.py
git commit -m "feat: adjudicate p6 review and repair evidence"
```

## Task 3: Make Video Analysis Evidence Strategy-Aware

**Files:** MCP review tool/test；fixture additions only where needed。

- [ ] **Step 1: Write RED raw measurement tests**

覆盖valid static image、directive-specific `image_motion`/`motion_graphics` low-motion evidence、motion-required freeze、black frames、expected silence、clipping、per-window IDs、output hash/tool identity；Production context absent仍走Legacy behavior。Current P3 unsupported strategy无exact render时必须not_evaluated。

- [ ] **Step 2: Run RED**

```bash
python -m pytest tests/test_mcp_review.py -q
```

- [ ] **Step 3: Implement bounded evidence collection**

使用ffmpeg/ffprobe deterministic local subprocess；不写Manifest/Receipt，不加载Production project，不推导timeline，不声明任何Production layer pass/fail。Raw cache key只包含output hash、exact window contract、measurement contract version与tool version；不得包含QaPolicy hash或在MCP层应用policy thresholds。

- [ ] **Step 4: Run GREEN**

```bash
python -m pytest tests/test_mcp_review.py -q
```

- [ ] **Step 5: Commit**

```bash
git add src/ai_video_mcp/tools/review.py tests/test_mcp_review.py
git commit -m "feat: collect strategy-aware technical evidence"
```

## Task 4: Isolate Legacy Optimize/Apply from Production Repair

**Files:** MCP optimize/apply tools and corresponding tests.

- [ ] **Step 1: Write RED mode-separation tests**

Legacy outputs/edits保持；Production optimize只产proposal；Production apply在所有write helper前拒绝。Monkeypatch `_write_yaml`、executor和filesystem write计数，unapproved case全部为0。

- [ ] **Step 2: Run RED**

```bash
python -m pytest tests/test_mcp_optimize_plan.py tests/test_mcp_apply_optimization.py -q
```

- [ ] **Step 3: Implement fail-closed separation**

不得为MCP apply增加可伪造的`authorized=True`；Production response只给committer-controlled next action identity。

- [ ] **Step 4: Run GREEN and Legacy MCP regression**

```bash
python -m pytest tests/test_mcp_review.py tests/test_mcp_optimize_plan.py tests/test_mcp_apply_optimization.py -q
```

- [ ] **Step 5: Commit**

```bash
git add \
  src/ai_video_mcp/tools/optimize_plan.py \
  src/ai_video_mcp/tools/apply_optimization.py \
  tests/test_mcp_optimize_plan.py \
  tests/test_mcp_apply_optimization.py
git commit -m "fix: gate production optimization behind repair receipts"
```

## Task 5: Add Read-Only Receipt and Acceptance Verification

**Files:** `project.py`、`models.py`、`test_production_project.py`、factory.

- [ ] **Step 1: Write RED exact selection tests**

Manifest 2.4 exact QaPolicy/ReviewRequest/Review/approved repair/outcome/final pointer、path/file hash/semantic hash；missing/tampered/symlink/decoy/latest拒绝；no scan/write/network/recovery；old 2.0-2.3 read unchanged。

- [ ] **Step 2: Write RED cross-binding tests**

Receipt render/timeline/output/graph/policy/evidence/tool mismatch拒绝；historical stale receipt可reopen审计但不得current-pass；semantic invalid strength拒绝；final acceptance逐pointerreopen。

- [ ] **Step 3: Run RED**

```bash
python -m pytest tests/test_production_project.py tests/test_production_models.py -q
```

- [ ] **Step 4: Implement private readers/verifiers**

新增private `_load_active_review_receipts()`、`_verify_review_states()`、`_load_active_repair_receipts()`、`_verify_final_acceptance_state()`；不得调用committer/recover。

- [ ] **Step 5: Run GREEN**

```bash
python -m pytest tests/test_production_project.py tests/test_production_review.py -q
```

- [ ] **Step 6: Commit**

```bash
git add src/ai_video/production/project.py src/ai_video/production/models.py tests/test_production_project.py tests/production_project_factory.py
git commit -m "feat: verify manifest-selected p6 receipts"
```

## Task 6: Persist Reviews through the Sole Committer

**Files:** `state_commit.py`、`__init__.py`、commit/review tests、factory.

- [ ] **Step 1: Write RED ownership and permit tests**

只导出`ProductionStateCommitter.bootstrap_review_policy()`、`activate_qa_policy()`、`run_review()`与safe request types；no ReceiptWriter/raw permit constructor。QaPolicy先exact promotion/selection；replacement policy同一replace只stale review/final；ReviewRequest exact base fields在analysis前durable；attempt复制其typed pointers/hashes；exact replay analysis count 0；wrong base/policy/render/timeline拒绝。

- [ ] **Step 2: Write RED activation ordering tests**

Evidence/receipt temp -> file fsync -> promote -> parent fsync -> reopen verify -> final Manifest replace；replace前active receipts old；all layer receipts同一次replace选择。

- [ ] **Step 3: Run RED**

```bash
python -m pytest tests/test_production_state_commit.py tests/test_production_review.py -q
```

- [ ] **Step 4: Implement review lifecycle inside existing owner**

复用existing `PreparedArtifact`、`_write_immutable_artifact()`、`_write_manifest_atomic()`、lock/error mapping。Analysis callable只能用one-use permit调用一次；tool result canonicalize后由committer写。

- [ ] **Step 5: Run GREEN**

```bash
python -m pytest \
  tests/test_production_state_commit.py \
  tests/test_production_project.py \
  tests/test_production_review.py -q
```

- [ ] **Step 6: Commit**

```bash
git add \
  src/ai_video/production/state_commit.py \
  src/ai_video/production/__init__.py \
  tests/test_production_state_commit.py \
  tests/test_production_review.py \
  tests/production_project_factory.py
git commit -m "feat: persist p6 reviews through production state"
```

## Task 7: Execute Only Approved Repairs and Reuse P5 Selective Rebuild

**Files:** committer/review module、repair tests、P5 regression tests、factory.

- [ ] **Step 1: Write RED zero-submit authorization tests**

Missing/false/wrong actor/wrong graph/wrong target/stale review/expired authorization或approved receipt未被Manifest exact-select，全部在executor前拒绝；submit/write counts 0，除明确approval transaction外不推进repair execution Manifest phase。

- [ ] **Step 2: Write RED exact invalidation tests**

Required matrix至少含caption layout repair、one visual target、one voice/audio target与composition-only target；expected/actual set exact；unrelated Shot/voice/caption/visual/audio fresh；no blanket stale。

- [ ] **Step 3: Write RED phase/replay tests**

R+1 request + immutable approved Repair Receipt selection后permit one-use；R+2 candidate graph coactivation；R+3 existing atomic render；R+4 re-review + immutable outcome Repair Receipt；exact replay executor/renderer/analysis counts 0。

- [ ] **Step 4: Run RED**

```bash
python -m pytest \
  tests/test_production_repair.py \
  tests/test_production_dependency.py \
  tests/test_production_selective_rebuild.py \
  tests/test_production_state_commit.py -q
```

- [ ] **Step 5: Implement minimum committer path**

不得新增repair registry/worker/queue。Receipt expected set必须用P5 resolver重算；actual result extra/missing node均fail。Render仍调用existing P3 path和activation contract。

- [ ] **Step 6: Run GREEN**

```bash
python -m pytest \
  tests/test_production_repair.py \
  tests/test_production_dependency.py \
  tests/test_production_selective_rebuild.py \
  tests/test_production_state_commit.py \
  tests/test_production_hyperframes.py -q
```

- [ ] **Step 7: Commit**

```bash
git add \
  src/ai_video/production/review.py \
  src/ai_video/production/state_commit.py \
  tests/test_production_repair.py \
  tests/test_production_dependency.py \
  tests/test_production_selective_rebuild.py \
  tests/test_production_state_commit.py \
  tests/production_project_factory.py
git commit -m "feat: execute authorized p6 selective repairs"
```

## Task 8: Bind Rerender, Re-review, and Final Acceptance

**Files:** `state_commit.py`、review/e2e tests、factory；verify-only existing HyperFrames path。

- [ ] **Step 1: Write RED rerender staleness tests**

2.4 render activation atomicallyfresh四个render nodes并stale bound review/final states；unaffected source assets仍fresh；old receipt retained historical。

- [ ] **Step 2: Write RED final acceptance tests**

current graph/states、timeline、output、policy、fresh required receipts全部exact才pass；semantic required absent、any stale/fail/not_evaluated、old render hash、old timeline、old graph、post-rerender prereview全部拒绝。

- [ ] **Step 3: Write deterministic E2E RED**

在fake/no-network fixture中证明review fail -> approved one-target repair -> precise graph -> fake rerender -> mandatory new review -> final acceptance；不执行renderer binary。

- [ ] **Step 4: Run RED**

```bash
python -m pytest \
  tests/test_production_review.py \
  tests/test_production_review_repair_e2e.py \
  tests/test_production_hyperframes.py -q
```

- [ ] **Step 5: Implement final acceptance activation**

`activate_final_acceptance()`必须在lock内重新打开所有exact evidence；caller不能只传hash claim。Final receipt promotion与Manifest state同一commit sequence。

- [ ] **Step 6: Run GREEN**

```bash
python -m pytest \
  tests/test_production_review.py \
  tests/test_production_repair.py \
  tests/test_production_review_repair_e2e.py \
  tests/test_production_hyperframes.py \
  tests/test_production_state_commit.py -q
```

- [ ] **Step 7: Commit**

```bash
git add \
  src/ai_video/production/review.py \
  src/ai_video/production/state_commit.py \
  tests/test_production_review.py \
  tests/test_production_review_repair_e2e.py \
  tests/test_production_hyperframes.py \
  tests/test_production_state_commit.py \
  tests/production_project_factory.py
git commit -m "feat: bind p6 rereview and final acceptance"
```

## Task 9: Add Crash Windows, Explicit Recovery, and Exact Replay

**Files:** `state_commit.py`、crash worker、recovery/repair/e2e tests、factory.

- [ ] **Step 1: Extend crash phases/modes**

增加review intent/evidence/receipt/final replace、repair authorized/action unknown/candidate graph/rerender/review/final receipt、acceptance replace checkpoints。Crash worker只用fake actions/no network/no renderer executable。

- [ ] **Step 2: Write RED temp/orphan/tamper tests**

partial owned temp bounded cleanup；complete orphan preserve/report；symlink/escape/tamper/decoy latest拒绝；no auto activation。

- [ ] **Step 3: Write RED old/new/unknown tests**

每个final replace只允许exact old/new state tuple；unknown action不remint permit，不重复analysis/repair/render；exact selected receipt replay zero writes。

- [ ] **Step 4: Write RED forward compatibility/rollback tests**

2.0-2.3 recovery unchanged；2.4 read/recovery works with execution disabled；no downgrade、no evidence deletion、no automatic recovery。

- [ ] **Step 5: Run RED**

```bash
python -m pytest tests/test_production_state_recovery.py tests/test_production_review_repair_e2e.py -q
```

- [ ] **Step 6: Implement within existing recovery owner**

扩展existing `_active_recovery_items()`、`_recover_attempts()`、`_preserved_orphan_items()`与owned temp cleanup；不得新增startup hook/GC service。

- [ ] **Step 7: Run GREEN**

```bash
python -m pytest \
  tests/test_production_state_recovery.py \
  tests/test_production_state_commit.py \
  tests/test_production_project.py \
  tests/test_production_review_repair_e2e.py -q
```

- [ ] **Step 8: Commit**

```bash
git add \
  src/ai_video/production/state_commit.py \
  tests/test_production_state_recovery.py \
  tests/helpers/p2a_crash_worker.py \
  tests/test_production_review_repair_e2e.py \
  tests/production_project_factory.py
git commit -m "feat: recover p6 review and repair state explicitly"
```

## Task 10: Synchronize Runtime and Branch Truth Documentation

**Files:** matrix、baseline、roadmap、`AGENTS.md`、`README.md` only after runtime acceptance.

- [ ] **Step 1: Correct branch truth first**

基于live Git写清P5已push到`origin/main`、尚未release；local research commit与P6 implementation branch/worktree truth分开。不得复制本plan中的预期test count当runtime evidence。

- [ ] **Step 2: Document only verified P6 behavior**

写清technical evidence owner、Manifest 2.4 review lifecycle、immutable receipts、strategy-aware static behavior、approved repair/P5 exact invalidation、semantic/final fail-closed、single committer/recovery、fake/no-network acceptance和P7-P9 deferred。

- [ ] **Step 3: Verify consistency**

```bash
rg -n "P5|P6|push|release|Review Receipt|Repair Receipt|Final Acceptance|Manifest 2.4|static_visuals" \
  README.md AGENTS.md docs/agent-primary-contract-matrix.md \
  docs/v0.2-runtime-baseline.md docs/v0.2-agentic-production-roadmap.md
git diff --check
```

- [ ] **Step 4: Commit exact docs**

```bash
git add README.md AGENTS.md docs/agent-primary-contract-matrix.md docs/v0.2-runtime-baseline.md docs/v0.2-agentic-production-roadmap.md
git commit -m "docs: record accepted p6 review repair runtime"
```

## Task 11: Independent Review, Verification, and Branch Truth

- [ ] **Step 1: Run canonical focused verification**

```bash
python -m pytest \
  tests/test_mcp_review.py \
  tests/test_mcp_optimize_plan.py \
  tests/test_mcp_apply_optimization.py \
  tests/test_production_review.py \
  tests/test_production_repair.py \
  tests/test_production_review_repair_e2e.py \
  tests/test_production_dependency.py \
  tests/test_production_selective_rebuild.py \
  tests/test_production_models.py \
  tests/test_production_validation.py \
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
  tests/test_workflow_renderer.py \
  tests/test_mcp_review.py \
  tests/test_mcp_optimize_plan.py \
  tests/test_mcp_apply_optimization.py -q
```

- [ ] **Step 3: Run full default suite**

```bash
python -m pytest -q
```

Expected：default suite不调用ComfyUI、HyperFrames executable、Provider、remote/paid API、secret或quota。

- [ ] **Step 4: Run independent reviewer**

Reviewer必须read-only、不得派生subagent，并输出`accept | accept with concerns | reject`、blocking issues、non-blocking concerns、exact file/symbol/test evidence与minimal follow-up。重点回答本plan末尾Review Questions。

- [ ] **Step 5: Parent verifies review claims and final diff**

```bash
test -n "$P6_IMPLEMENTATION_BASE"
git show -s --format='%H %s' "$P6_IMPLEMENTATION_BASE"
git status --short --branch
git diff --check "$P6_IMPLEMENTATION_BASE"...HEAD
git diff --name-status "$P6_IMPLEMENTATION_BASE"...HEAD
git log --oneline --decorate "$P6_IMPLEMENTATION_BASE"..HEAD
git rev-list --left-right --count origin/main...HEAD
```

`P6_IMPLEMENTATION_BASE`必须是Task 0记录的exact local pre-P6 HEAD，不得用`merge-base origin/main HEAD`重算。确认research commit位于base中且仍原样；P6-only diff每一行映射P6；`origin/main...HEAD`只作publication report；无package/Legacy/P7+/secret/generated artifact/unrelated dirty file。

- [ ] **Step 6: Stop without merge/push/release**

报告branch、HEAD、test counts、review verdict、remaining risk与local-vs-origin truth。P6 implementation完成不等于publication、release或P7-P9授权。

## Focused Verification Command

P6 runtime implementation的canonical focused command是：

```bash
python -m pytest \
  tests/test_mcp_review.py \
  tests/test_mcp_optimize_plan.py \
  tests/test_mcp_apply_optimization.py \
  tests/test_production_review.py \
  tests/test_production_repair.py \
  tests/test_production_review_repair_e2e.py \
  tests/test_production_dependency.py \
  tests/test_production_selective_rebuild.py \
  tests/test_production_models.py \
  tests/test_production_validation.py \
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

该命令必须使用deterministic local fixtures/fakes/no-network；不得安装SDK、调用ComfyUI/HyperFrames executable/ElevenLabs/remote API、读取secret或使用quota。

## Schema Migration

- Manifest 2.0-2.3保持read/recovery/serialization compatibility；P6 reader不注入新fields。
- P6只接受已bootstrap P5的Manifest 2.3，并在首次explicit `bootstrap_review_policy()`中durable写入/select exact QaPolicyPointer并迁移2.4。
- Immutable QaPolicy/ReviewRequest/ReviewEvidence/ReviewReceipt/RepairRequest/ApprovedRepairReceipt/RepairOutcomeReceipt/FinalAcceptanceReceipt schema首版均为2.0；identity为semantic content hash。
- Migration必须从exact current graph/render/timeline/output/policy构造review desired states；没有receipt时为`not_evaluated`，不得伪造pass。
- Existing active render/graph/dependency states保持；migration不重建asset/render，不运行analysis，不执行repair。
- 2.4禁止downgrade2.3。Disable P6 execution时仍必须read/audit/recover 2.4。

## Rollback

P6 operational rollback固定为：

1. 禁用新的review/repair/final acceptance execution entrypoints，不删除state。
2. 保留Manifest 2.4 reader、Review/Repair/Acceptance Receipt readers与explicit recovery。
3. 保留active/historical/orphan immutable receipts、evidence、attempts和P5 graph/render state。
4. 禁止schema downgrade到2.3，禁止重写receipts、清空review lifecycle或用旧Review Receipt重新accept。
5. Manifest 2.0-2.3 projects继续按P2-P5 behavior运行；2.4 project可read/audit/recover，但P6 disabled时新review/repair/acceptance typed-fail。
6. Legacy MCP optimize/apply继续legacy-only；不得把它作为rollback后的Production repair fallback。
7. 不删除或autoactivate partial/complete orphan；长期GC/retention属于P9或独立授权。

## Independent Review Questions

Reviewer必须用plan、code与tests回答：

1. `video-analysis`是否只收集technical evidence，没有Manifest、review/repair lifecycle或final acceptance ownership？
2. Production `static_visuals`是否真正按Shot `visual_strategy`与timeline window解释，合法`static_image`/低运动是否不被误判？
3. Technical/layout/strategy/semantic/final_acceptance五层owner、inputs、evidence strength与fail-closed rules是否明确且可测试？
4. Semantic pass是否只能来自explicit evaluator/human durable evidence，而不是heuristic、console或Agent memory？
5. QaPolicy与ReviewRequest是否有canonical pointer、Manifest selection与exact reopen；Review Receipt是否immutable/content-addressed/versioned并绑定exact render/output hash、timeline、graph、policy、evidence IDs与tool identity？
6. Creative action前是否已有Manifest-selected immutable ApprovedRepairReceipt；outcome receipt是否引用它并共同覆盖issues/evidence/root cause/action/targets/expected+actual invalidation/actor/auth/before-after/exact rerender/fresh review receipts？
7. `video_optimize_plan`/`video_apply_optimization`是否在Production mode无法形成第二条repair control path，unapproved submit/write是否为0？
8. Review lifecycle是否只在Manifest 2.4，P5 graph是否继续不含QA/review/repair/status？
9. QA policy-only change是否只stale affected reviews/final acceptance，不改graph/assets/render？
10. Approved repair是否用before/after P5 resolver验证exact affected set，且unrelated Shot/voice/caption/visual/audio保持fresh？
11. `ProductionStateCommitter`是否仍唯一receipt/Manifest/activation/recovery writer，无RepairRegistry/auto recovery？
12. `ResolvedTimeline`与render-domain atomic activation contract是否完整保留？
13. Rerender后是否强制new review，旧receipt是否不能final acceptance？
14. Exact replay是否analysis/repair/render全0次，unknown outcome是否不blind reapply？
15. Legacy、P7/P8/P9、second renderer、Provider/cloud/frontend/general Agent runtime是否未扩scope？

## Definition of Done

P6 runtime只有在未来另获授权并满足以下全部条件时可称为implemented：

- MCP technical evidence strategy-aware，并通过valid static + frozen/black/silent/clipped fixtures。
- 五层QA owner/evidence/fail-closed contract均由strict tests证明；semantic absence不能pass。
- Review/Repair/Final Acceptance receipts immutable、content-addressed、versioned且exact绑定current production identities。
- Manifest 2.4独占review/repair/final lifecycle；P5 graph无QA/repair status或nodes。
- Production optimize/apply无法绕过durable Repair Receipt/authorization；unapproved submit/write为0。
- Approved repair only触发P5 exact before/after selective invalidation；无blanket stale，unrelated domains fresh。
- `ProductionStateCommitter`独占receipt write、Manifest activation、unknown mapping与explicit recovery。
- Composition/Timeline/Source/Render保持同一次final activation atomic fresh；rerender后必须重review才可accept。
- Exact replay不重复analysis/repair/render；crash/unknown不blind reapply。
- Manifest 2.3 -> 2.4 migration、temp/partial/orphan、old/new/unknown、forward reader/recovery和rollback通过。
- focused、Legacy、full default no-network suites实际通过。
- independent reviewer无blocking issue，parent直接验证critical claims与final diff。
- docs先修正P5已push的stale truth，再只记录实际验收P6 runtime。
- implementation checkpoint已提交但不push/release；P7-P9仍需独立plan与授权。

本plan-only checkpoint的Definition of Done更窄：只创建并独立审查本文件、只提交本文件、不实施任何runtime、不修改其它docs、不push、不release，并报告exact plan path、commit、review verdict与remaining risks。
