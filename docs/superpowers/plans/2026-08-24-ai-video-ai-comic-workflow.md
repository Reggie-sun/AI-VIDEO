# AI-VIDEO AI Comic Workflow Skill Implementation Plan

## Status

Not started。本文是 implementation handoff，不授权当前窗口实现 Skill、修改 Runtime、运行 Provider、生成媒体、写 Production state、push 或 release。执行必须由后续明确 implementation request 启动。

## Goal

实现一个独立 repo-local `ai-comic-workflow`，把 AI 漫剧 brief 转换为 schema-valid `AiComicProductionPackage`，并在进入现有 AI-VIDEO authoring / Production Runtime 前完成 story、character、scene、Shot、continuity 与 audio-intent gates。

## Scope

包括 Skill discovery、progressive-disclosure references、strict input/output contracts、local validator、standalone / serial examples、pre-handoff AI comic QC、AI-VIDEO runtime handoff projection、tests 与 Harness routing。

## Contract Surfaces

- Governing spec：`docs/superpowers/specs/2026-08-24-ai-video-ai-comic-workflow.md`。
- Skill entry：`.agents/skills/ai-comic-workflow/SKILL.md`。
- Input schema：`ai-comic-workflow/input/1`。
- Output schema：`ai-comic-workflow/package/1`。
- Validator CLI：

```bash
python .agents/skills/ai-comic-workflow/scripts/validate_contract.py \
  --kind input --file PATH
python .agents/skills/ai-comic-workflow/scripts/validate_contract.py \
  --kind package --file PATH
```

- Validator exit semantics：`0` valid；`2` malformed/contract-invalid；`3` validator-internal failure。stdout 为 stable JSON diagnostics；stderr 不输出 input/package body。
- Runtime handoff target：existing `ProductionBrief`、`Story`、`Character`、`Scene`、`Storyboard`、`Shot` proposals only。
- Repository routing：`AGENTS.md`、`.agent/harness/policy.yaml` 与 corresponding Harness tests。

## Invariants

- `ai-comic-workflow` 不读取、调用、导入或依赖 `ecommerce-ad-workflow`。
- Input/output拒绝 product、advertising、CTA、campaign 与 creative-variant fields。
- Skill package不是 Runtime，不提交 Provider，不生成媒体，不写 Project/Registry/Manifest。
- `ProductionStateCommitter`仍是唯一 durable writer / activation / recovery owner。
- `ResolvedTimeline`仍是唯一 frame/sample/timing owner。
- HyperFrames仍是默认 Production renderer。
- `VideoPlanner`仍是 per-Shot generation/readiness owner；本 Skill不选择 Provider、mode 或 fallback。
- P4仍拥有 audio/caption materialization与timing；P6仍拥有 Review/Repair/Final Acceptance。
- External creative Skills只提供 advisory output，且必须回写为同一个 `AiComicProductionPackage`。
- Valid package只表示 authoring contract通过，不表示 media quality、lip sync、continuity quality、P6 PASS 或 release。

## Current / Target Behavior

### Current

AI-VIDEO 已有 creative artifacts、single-Shot planning与完整 Production Runtime，但没有一个确定的 AI 漫剧 authoring sequence。Agent可以直接写 `Story` / `Shot`，却没有 package-level gate验证 story arc、character state、beat-to-Shot traceability、continuity与audio coverage。

### Target

Codex discovery `ai-comic-workflow` 后，按阶段读取 references，产出 schema-valid package。Invalid advertising fields、dangling references、缺 state transition、缺 audio intent或 forbidden Runtime state全部 fail closed。通过后只生成 explicit runtime handoff proposal。

## Compatibility

- 不修改 public CLI、Production API、schema、Manifest、Registry 或 artifact layout；
- 不新增 dependency；使用 repository 已有 Python 3.11、Pydantic 与标准库；
- JSON schema为 checked-in contract view，validator的Pydantic definitions与 schema bytes必须由 tests证明一致；
- Skill删除后 Production Runtime保持可用；
- `skills-lock.json` 不记录该 repo-local custom Skill；
- existing `open-video` / `h3-video` 保持不变，但不得作为本 Workflow execution dependency。

## Out Of Scope

- ecommerce advertising；
- new Production authoring API or automatic materializer；
- Provider prompt compiler、selection、generation或media review；
- automatic repair / retry / fallback；
- live ComfyUI、T8、H3、Seedance或paid smoke；
- runtime typography、compositing、motion engine或second timeline；
- changing existing `Base AI Comic E2E` acceptance。

## Acceptance Criteria

1. Repo-local Skill可被 discovery，trigger只覆盖 AI 漫剧 / AI 剧情短片 / serial fiction。
2. Valid standalone与serial fixtures通过 input和package validation。
3. Forbidden ecommerce/ad fields产生 deterministic diagnostics与 exit `2`。
4. Character、Scene、beat、Storyboard、Shot reference integrity可执行验证。
5. 每个 Shot 有 beat、scene、narrative purpose、open/close state与continuity requirements。
6. 有 dialogue/narration 的 Shot 必须有对应 audio intent与 lip-sync requirement。
7. 非 intentional audio gap、孤立 Shot、无 payoff standalone arc、invalid serial prior state阻止 package ready。
8. Runtime handoff只包含 existing creative artifact proposals与 capability needs。
9. Forbidden Provider/Manifest/Registry/timeline/render/review/activation fields被拒绝。
10. Skill/reference/schema/template/validator不读取network、credential或Production state，也不写 repository/runtime state。
11. `AGENTS.md` routing明确其与 ecommerce Workflow独立，并保持现有 creative Skill precedence。
12. Exact staged delta通过 targeted tests、docs contract、policy audit与 Harness；receipt可验证且fresh。

## File Map

### Skill Package

- Create `.agents/skills/ai-comic-workflow/SKILL.md`：frontmatter trigger、stage routing、gates、reference loading、output / stop contract。
- Create `.agents/skills/ai-comic-workflow/references/story-core-and-arcs.md`：dramatic question、stakes、turn、payoff 与 arc selection。
- Create `.agents/skills/ai-comic-workflow/references/episodic-structure.md`：standalone / serial、prior state、retained threads、cliffhanger 与 closure。
- Create `.agents/skills/ai-comic-workflow/references/character-and-relationships.md`：identity anchors、motivation、relationships、state transitions、allowed variations。
- Create `.agents/skills/ai-comic-workflow/references/scene-and-state-continuity.md`：location、space、axis、props、light、environment 与 open/close state。
- Create `.agents/skills/ai-comic-workflow/references/dialogue-and-audio.md`：dialogue intent、subtext、voice、lip sync、music、ambience、SFX、silence coverage。
- Create `.agents/skills/ai-comic-workflow/references/storyboard-and-shot-intent.md`：beat-to-Shot projection、duration budget、camera intent 与 filler rejection。
- Create `.agents/skills/ai-comic-workflow/references/runtime-handoff.md`：现有 AI-VIDEO artifact proposal map与 forbidden Runtime fields。
- Create `.agents/skills/ai-comic-workflow/references/ai-comic-qc.md`：pre-handoff logic rubric，不冒充 P6。
- Create `.agents/skills/ai-comic-workflow/schemas/ai-comic-input.schema.json`：input contract view。
- Create `.agents/skills/ai-comic-workflow/schemas/ai-comic-production-package.schema.json`：package contract view。
- Create `.agents/skills/ai-comic-workflow/templates/standalone-vertical-short.input.example.json`：valid standalone input fixture。
- Create `.agents/skills/ai-comic-workflow/templates/standalone-vertical-short.package.example.json`：与 standalone input hash-bound 的 valid package fixture。
- Create `.agents/skills/ai-comic-workflow/templates/serial-vertical-short.input.example.json`：valid serial prior-state input fixture。
- Create `.agents/skills/ai-comic-workflow/templates/serial-vertical-short.package.example.json`：与 serial input hash-bound 的 valid package fixture。
- Create `.agents/skills/ai-comic-workflow/scripts/validate_contract.py`：Pydantic contract definitions、cross-reference/gate validation与no-write CLI。

### Tests And Routing

- Create `tests/test_ai_comic_workflow_skill.py`：Skill discovery、schema parity、fixtures、negative boundaries、validator CLI、no-I/O guard与 handoff tests。
- Modify `AGENTS.md`：增加独立 AI comic routing，明确不得路由 ecommerce ads，且 external Skills仍 advisory-only。
- Modify `.agent/harness/policy.yaml`：为 `.agents/skills/ai-comic-workflow/**` 与 `tests/test_ai_comic_workflow_skill.py` 增加 focused check ID，同时保留 generic control-plane checks。
- Modify `tests/test_agent_harness.py`：验证 exact path routing、mandatory focused check与 no unintended Runtime suite omission。

### Documentation Closure

- Modify `docs/v0.2-runtime-baseline.md` only after implementation and exact Harness PASS：记录 Skill 已实现为 Development / authoring workflow，明确不属于 Product Runtime capability或media acceptance。
- Modify `docs/v0.2-agentic-production-roadmap.md` only if current roadmap has a matching accepted planning lane；只记录 actual implemented status，不创建新的 Production phase。

### Must Not Modify

- `src/ai_video/production/**`；
- `src/ai_video/planning/**`；
- `src/ai_video/cli.py`、Legacy pipeline、workflow templates；
- `skills-lock.json`；
- `.agents/skills/ecommerce-ad-workflow/**`；
- `.workflow/**`、`runs/**`、generated media；
- unrelated dirty/staged files。

## Shared Control-Plane Ownership Note

该计划与 Ecommerce plan 的业务文件完全分离，但未来实现都可能需要修改 `AGENTS.md`、`.agent/harness/policy.yaml` 与 `tests/test_agent_harness.py`。这三个文件是 repository-wide routing surface，不是 shared Workflow domain。

若两个 implementation writer 并行执行，Skill package与各自 test文件可保持独立；任何 writer写上述同一 control-plane file前必须按 `AGENTS.md` 停止并由用户决定 ownership或顺序。推荐串行完成两个 routing milestone，不建立 shared orchestrator或 shared schema。

## Major Milestones

### Milestone 0: Freeze Current Truth And Negative Boundary

**Files:** read governing spec、current `AGENTS.md`、contract matrix、Harness policy、runtime baseline、Video Planner spec、current Skill inventory；不修改 Product Runtime。

**Contract:** 确认本 Workflow只做 AI comic authoring，列出 forbidden ecommerce fields、forbidden Runtime effects与 exact target files；确认没有 same-file writer conflict。

**Implementation Notes:**

- 记录 execution base、`git status --short` 与 live-agent ownership；
- 用 `python scripts/agent_harness.py inspect --path ...` 对 planned paths确认 mandatory checks；
- 重新核对 current `ProductionBrief` / `Story` / `Character` / `Scene` / `Storyboard` / `Shot` fields，不从旧 memory猜 schema；
- 不运行 Provider、ComfyUI或media commands。

**Acceptance:** boundary matrix与 file ownership无 unresolved item；任何 Product Runtime change都被排除或另行提请 scope expansion。

**Verification:**

```bash
git status --short
git rev-parse HEAD
python scripts/agent_harness.py inspect \
  --path .agents/skills/ai-comic-workflow/SKILL.md \
  --path tests/test_ai_comic_workflow_skill.py
```

### Milestone 1: Establish RED Contract Tests And Harness Route

**Files:** create `tests/test_ai_comic_workflow_skill.py`；modify `.agent/harness/policy.yaml`、`tests/test_agent_harness.py`。

**Contract:** Tests固定两个 schema versions、validator exit semantics、forbidden advertising fields、reference integrity、audio coverage、runtime-handoff forbidden fields、no-network/no-write与 progressive-disclosure file inventory。

**Implementation Notes:**

- 先提交会因 Skill/schema/validator缺失而失败的 focused contract tests；
- Harness category只匹配 AI comic Skill 与其 test，不把 ecommerce Skill或 Product Runtime归入本 check；
- generic `.agents/skills/**` control-plane checks继续运行；
- test不得动态安装 package或写 `.agents/skills`。

**Acceptance:** RED failure只来自 planned missing files/contract behavior；Harness policy audit可识别新的 test path且无 unreferenced test。

**Verification:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_ai_comic_workflow_skill.py \
  tests/test_agent_harness.py -q
python -m scripts.agent_harness policy-audit
```

### Milestone 2: Implement Input, Package And Validator Contracts

**Files:** create both schema files、both template fixtures与 `scripts/validate_contract.py`。

**Contract:** Canonical Pydantic models验证 input/package structure与 cross-field invariants；checked-in JSON Schema与 model-generated schema保持一致；CLI read-only并返回 stable JSON diagnostics。

**Implementation Notes:**

- IDs与hashes deterministic；same canonical JSON产生same package identity；
- standalone与serial使用明确 discriminated fields；
- dangling Character/Scene/beat/Shot references fail closed；
- `dialogue` / `narration` 与 audio/lip-sync requirements交叉验证；
- `intentional_silence=false` 的 uncovered interval fail closed；
- explicitly reject advertising/product/CTA/campaign fields and all Runtime execution fields；
- validator不得读取 env credential、network、Project、Registry、Manifest或 media bytes。

**Acceptance:** valid fixtures exit `0`；每类 negative fixture exit `2`且 diagnostic path稳定；internal exception才使用 exit `3`且不泄露 document body。

**Verification:**

```bash
python .agents/skills/ai-comic-workflow/scripts/validate_contract.py \
  --kind input \
  --file .agents/skills/ai-comic-workflow/templates/standalone-vertical-short.input.example.json
python .agents/skills/ai-comic-workflow/scripts/validate_contract.py \
  --kind package \
  --file .agents/skills/ai-comic-workflow/templates/standalone-vertical-short.package.example.json
python -m pytest -p no:cacheprovider tests/test_ai_comic_workflow_skill.py -q
```

### Milestone 3: Implement Workflow Guidance And Progressive Disclosure

**Files:** create `SKILL.md` 与八个 reference files。

**Contract:** Skill严格执行 G0-G7；每个 stage只加载对应 references；失败输出 exact diagnostic并停止，不生成占位 Shot或触发 execution。

**Implementation Notes:**

- frontmatter description包含 AI comic-specific trigger和 explicit ecommerce exclusion；
- `SKILL.md` 保持 router-size，长方法论放 references；
- stage output全部累积到一个 package，不创建多份 state owner；
- `hell-grind-aigc-skill`、`higgsfield`、`video-shotcraft`仅在 `AGENTS.md`允许范围内 advisory routing；
- 不调用 `open-video` 的 autonomous generation/stitch path；
- no subagent、worktree、commit、Provider或media authorization由 Skill自行推导。

**Acceptance:** 一个 unfamiliar Codex可以只按 `SKILL.md` 和按需 references完成 valid package；trigger、gate、stop与 handoff语义不依赖 ecommerce assets或 docs。

**Verification:**

```bash
python -m pytest -p no:cacheprovider tests/test_ai_comic_workflow_skill.py -q
rg -n "ecommerce-ad-workflow|product_truth|creative_variant_matrix|cta" \
  .agents/skills/ai-comic-workflow
```

Expected：只有 explicit forbidden-boundary说明或 negative fixtures命中，不存在依赖、调用或 output field。

### Milestone 4: Integrate Repository Routing Without Runtime Coupling

**Files:** modify `AGENTS.md`；complete Harness policy/tests；conditionally update runtime baseline/roadmap after GREEN。

**Contract:** AI comic request路由到新 Skill；ecommerce request不触发它；existing semantic continuity / Provider prompt / motion design precedence保持不变；Production canonical owners不变。

**Implementation Notes:**

- routing wording只描述 durable trigger和 boundary，不把 `AGENTS.md`变成操作手册；
- external Skills仍 advisory-only；
- runtime baseline只记录实际 implemented authoring capability与未验证边界；
- 不修改 docs-contract registry，除非该 Skill未来成为 registered implemented Runtime surface。V1不是。

**Acceptance:** routing tests对 AI comic positive cases、ecommerce negative cases与 generic video cases deterministic；Architecture / docs contract无新增 owner冲突。

**Verification:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_ai_comic_workflow_skill.py \
  tests/test_agent_harness.py \
  tests/test_docs_contract_gate.py -q
python -m scripts.docs_contract_gate check
python -m scripts.agent_harness policy-audit
python -m scripts.architecture_gate check
```

### Milestone 5: Exact-Snapshot Verification And Delivery

**Files:** only task-owned Skill、tests、routing与 truthful docs。

**Contract:** final staged snapshot包含本 plan授权的 files；unrelated dirty files不进入 stage/commit/receipt。

**Implementation Notes:**

- inspect `git diff -- <task-owned-files>` and `git diff --check`；
- stage with exact `git add <files>`，never `git add .`；
- run Harness against non-empty staged snapshot；
- verify receipt freshness and hashes；
- commit only task-owned files；push/release需要独立 authorization。

**Acceptance:** targeted checks、policy audit、docs contract、Architecture Gate与 exact staged Harness PASS；final receipt可验证；no Provider/media evidence被声称。

**Verification:**

```bash
git diff --check
git status --short
make harness-verify RUN_ID=ai-comic-workflow-v1
python scripts/agent_harness.py verify-receipt \
  .agent/harness/runs/ai-comic-workflow-v1/receipt.json
```

Receipt path必须以实际 Harness output为准，不得猜测；上例只规定 run ID 与 verification intent。

## Rollback

本计划不改变 Production schema或durable state。Rollback按 task-owned commit反向移除：

1. `ai-comic-workflow` Skill package；
2. focused tests与 Harness mapping；
3. `AGENTS.md` routing与 truthful runtime-baseline note。

不得删除或修改 existing ProductionProject、Registry、Manifest、media、`Base AI Comic E2E`、Provider profiles或其它 Skills。Rollback 后原有 AI-VIDEO Runtime与 manual authoring path必须继续工作。

## Completion Decision

达到 Milestone 5 后只能声明：`ai-comic-workflow/1 authoring contract implemented and offline-verified`。在没有真实媒体与 P6 / human evidence时，不得声明 AI 漫剧成片质量、角色一致性、lip sync、watchability、Final Acceptance、live-ready、published 或 released。
