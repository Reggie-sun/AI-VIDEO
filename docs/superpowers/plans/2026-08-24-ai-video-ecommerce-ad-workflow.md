# AI-VIDEO Ecommerce Advertising Workflow Skill Implementation Plan

## Status

Authoring V1 complete in current local implementation。Milestone 0–6 的 `ecommerce-ad-workflow/1` offline authoring package 已实现；本文新增的 `AdCreativePlan` Runtime bridge 为 **follow-up slice / not started**。该记录不授权当前窗口修改 Runtime、运行 Provider、生成媒体、读取 credential、付费、写 Production state、push 或 release。

## Goal

实现一个独立 repo-local `ecommerce-ad-workflow`，把商品资料、Product Truth、消费者与广告约束转换为 schema-valid `EcommerceAdProductionPackage`，并在进入现有 AI-VIDEO authoring / Production Runtime 前完成 claim、Hook、ad beat、product presentation、advertising copy graphics、audio coverage、CTA、variant 与 capability gates。

## Scope

包括 Skill discovery、progressive-disclosure references、strict input/output contracts、local validator、30 秒竖屏 example、Product Truth / claim ledger、ad strategy、Hook、product presentation、copy graphics、audio coverage、creative variants、runtime handoff、Ad QC、tests 与 Harness routing。

## Contract Surfaces

- Governing spec：`docs/superpowers/specs/2026-08-24-ai-video-ecommerce-ad-workflow.md`。
- Skill entry：`.agents/skills/ecommerce-ad-workflow/SKILL.md`。
- Input schema：`ecommerce-ad-workflow/input/1`。
- Output schema：`ecommerce-ad-workflow/package/1`。
- Validator CLI：

```bash
python .agents/skills/ecommerce-ad-workflow/scripts/validate_contract.py \
  --kind input --file PATH
python .agents/skills/ecommerce-ad-workflow/scripts/validate_contract.py \
  --kind package --file PATH
```

- Validator exit semantics：`0` valid；`2` malformed/contract-invalid；`3` validator-internal failure。stdout 为 stable JSON diagnostics；stderr 不输出商品页、claim 或 package body。
- Runtime handoff target：existing `ProductionBrief`、talent-as-`Character`、set-as-`Scene`、`Storyboard`、`Shot`、asset requirements、audio/caption authoring requests与 explicit capability gaps。
- Repository routing：`AGENTS.md`、`.agent/harness/policy.yaml` 与 corresponding Harness tests。

## Invariants

- `ecommerce-ad-workflow` 不读取、调用、导入或依赖 `ai-comic-workflow`。
- Input/output拒绝 episode、serial、cliffhanger、AI comic package与 character-bible fields。
- Product facts、claims、rights与disclaimers必须可追溯；未知事实不得被填充为广告文案。
- Workflow不把商品 asset简化为 arbitrary overlay，也不把 unsupported physical interaction声称为可执行。
- `DIALOGUE_SUBTITLE` 可以请求现有 `CaptionTrack`；`HEADLINE`、`BENEFIT_CALLOUT`、`PRODUCT_LABEL`、`PROOF_LABEL`、`CTA`、`BRAND_END_CARD` 必须保持独立 advertising graphics semantics。
- Audio intent必须覆盖完整 ad duration；非 intentional silent window阻止 package ready。
- Skill package不是 Runtime，不提交 Provider，不生成媒体，不写 Project/Registry/Manifest。
- `ProductionStateCommitter`、`ResolvedTimeline`、HyperFrames、P4与P6 canonical ownership不变。
- Creative variant一次只改变一个 declared variable；不得把 Provider retry/seed/repair冒充 variant。
- Valid package不表示实际 compositing、typography、audio、media quality、P6 PASS 或 advertising performance。

## Current / Target Behavior

### Current

AI-VIDEO 能承接通用 brief、assets、Shots、audio/captions、composition与 Review，但广告 Product Truth、Hook、product presentation、advertising typography、audio emphasis、CTA 与 variants只能散落在 prose。当前 Runtime还不能稳定表达全部 product interaction和 commercial graphics；Workflow也没有统一 gate要求诚实暴露这些 gaps。

### Target

Codex discovery `ecommerce-ad-workflow` 后，按 Product Truth -> Strategy -> Hook / Beats -> Product Presentation -> Copy / Audio -> Storyboard / Shots -> Runtime Handoff -> Ad QC 的顺序产出 package。Claim、rights、product name、placement、copy hierarchy、audio gap或 Runtime capability不满足时 fail closed。

## Compatibility

- 不修改 public CLI、Production API、schema、Manifest、Registry 或 artifact layout；
- 不新增 dependency；使用 repository 已有 Python 3.11、Pydantic 与标准库；
- JSON schema为 checked-in contract view，validator的Pydantic definitions与 schema bytes必须由 tests证明一致；
- Skill删除后 Production Runtime保持可用；
- 不修改 `skills-lock.json`，因为 V1 不安装任何 external Skill；
- existing `open-video` / `h3-video`、advisory Skills与 Provider adapters保持不变；
- external source若只被方法论重写参考，不复制 unlicensed bytes；复制 MIT bytes时保留 attribution与 notice。

## Out Of Scope

- AI comic / episodic fiction；
- new Product Runtime schema or automatic materializer；
- Provider prompt compiler、selection、generation或media review；
- automatic campaign publishing、budget、ROAS、A/B result ingestion或optimizer；
- live Product page crawling without explicit authorization；
- automatic claim/legal approval；
- runtime Product Integration、Advertising Typography 或 Motion Graphics implementation；
- live ComfyUI、T8、H3、Seedance或paid smoke；
- second timeline、renderer、writer、QC lifecycle或asset registry。

上述 V1 out-of-scope boundary 保持不变。`AdCreativePlan` 不回填为 V1 已完成项；只有用户另行批准 Runtime slice 后，才按下文 follow-up 执行。

## Acceptance Criteria

1. Repo-local Skill可被 discovery，trigger只覆盖 ecommerce / product advertising。
2. Valid 30 秒 `9:16` fixture通过 input和package validation。
3. Forbidden AI comic / episode / cliffhanger fields产生 deterministic diagnostics与 exit `2`。
4. Every used claim绑定 exact Product Truth fact/source且不在 prohibited claims中。
5. Product name至少一次 visible或audible；缺失时 G4 fail closed。
6. Hook在第一秒有至少一个可观察 component，promise可追溯到 claim ledger。
7. 每个 ad beat、Shot、product presentation、copy role与audio cue互相可追溯。
8. `PHYSICAL_INTERACTION_REQUIRED` 缺 source/runtime capability时返回 `BLOCKED_CAPABILITY_GAP`，不降级为 fake overlay。
9. Commercial copy roles与 dialogue captions严格分离。
10. Audio coverage完整；非 intentional silent window阻止 package ready。
11. On-camera dialogue绑定 speaker、verbatim line、Shot与 `lip_sync_required`；缺一项即 fail closed。
12. Native/generated source audio声明 keep/mute/replace/trim policy，Shot lead-in noise有 P6 measurement requirement。
13. CTA与 `BRAND_END_CARD` 存在并绑定 final beat / Shot。
14. Creative variant每项只有一个 `changed_variable`，并有 complete `held_constants`。
15. Runtime handoff只包含 proposals、requirements与 classified gaps，不含 Provider/Manifest/timeline/render/P6/activation fields。
16. 三个 external repos均未安装、fork、vendor、submodule或成为 dependency。
17. Skill/reference/schema/template/validator no-network、no-credential、no-Production-write。
18. Package delivery intent固定为 video；product/source still只作为 input/reference，不作为最终 deliverable。
19. Exact staged delta通过 targeted tests、docs contract、policy audit与 Harness；receipt可验证且fresh。

## File Map

### Skill Package

- Create `.agents/skills/ecommerce-ad-workflow/SKILL.md`：frontmatter trigger、decision sequence、G0-G7、reference routing、stop与 output contract。
- Create `.agents/skills/ecommerce-ad-workflow/references/product-truth-and-claims.md`：facts、sources、rights、allowed/prohibited claims、disclaimers与医疗效果边界。
- Create `.agents/skills/ecommerce-ad-workflow/references/audience-angle-and-proof.md`：audience、pain point、objective、angle、promise、proof与 objection。
- Create `.agents/skills/ecommerce-ad-workflow/references/hooks.md`：visual/dialogue/copy/audio Hook components与 first-second gate。
- Create `.agents/skills/ecommerce-ad-workflow/references/ad-beat-sequences.md`：format-specific beat roles、duration budgets、causality与 mechanical-cut rejection。
- Create `.agents/skills/ecommerce-ad-workflow/references/product-presentation.md`：intro/demo/proof/hero/CTA roles、modes、source framing、interaction/capability requirements。
- Create `.agents/skills/ecommerce-ad-workflow/references/advertising-copy-graphics.md`：commercial roles、hierarchy、safe area、subject/product avoidance、motion/cue intent；明确不等于 captions。
- Create `.agents/skills/ecommerce-ad-workflow/references/audio-pacing-and-coverage.md`：dialogue/VO/music/SFX、ducking、reveal hits、intentional silence与 full-duration coverage。
- Create `.agents/skills/ecommerce-ad-workflow/references/creative-variants.md`：master truth、one-variable changes、held constants、hypothesis与 asset delta。
- Create `.agents/skills/ecommerce-ad-workflow/references/runtime-handoff.md`：existing Runtime projection、capability classification与 forbidden execution fields。
- Create `.agents/skills/ecommerce-ad-workflow/references/ad-qc.md`：truth、Hook、placement、copy、audio、CTA、brand closure preflight。
- Create `.agents/skills/ecommerce-ad-workflow/references/external-method-sources.md`：source URLs、verified license posture、adopted ideas、excluded runtime与 attribution rule。
- Create `.agents/skills/ecommerce-ad-workflow/schemas/ecommerce-ad-input.schema.json`：input contract view。
- Create `.agents/skills/ecommerce-ad-workflow/schemas/ecommerce-ad-production-package.schema.json`：package contract view。
- Create `.agents/skills/ecommerce-ad-workflow/templates/30s-vertical-product-ad.input.example.json`：valid 30-second vertical product-ad input fixture。
- Create `.agents/skills/ecommerce-ad-workflow/templates/30s-vertical-product-ad.package.example.json`：与 input hash-bound 的 valid package fixture。
- Create `.agents/skills/ecommerce-ad-workflow/scripts/validate_contract.py`：Pydantic contract definitions、cross-field/gate validation与no-write CLI。

### Tests And Routing

- Create `tests/test_ecommerce_ad_workflow_skill.py`：Skill discovery、schema parity、fixture、claims、product presentation、copy/audio、variants、forbidden AI comic fields、validator CLI、no-I/O与 handoff tests。
- Modify `AGENTS.md`：增加独立 ecommerce routing，明确不路由 AI comic，不覆盖现有 creative / Production ownership。
- Modify `.agent/harness/policy.yaml`：为 `.agents/skills/ecommerce-ad-workflow/**` 与 `tests/test_ecommerce_ad_workflow_skill.py` 增加 focused check ID，同时保留 generic control-plane checks。
- Modify `tests/test_agent_harness.py`：验证 exact path routing、mandatory focused check与 no unintended Runtime suite omission。

### Documentation Closure

- Modify `docs/v0.2-runtime-baseline.md` only after implementation and exact Harness PASS：记录 Skill 已实现为 Development / authoring workflow；明确 product integration / ad typography runtime capability仍按真实代码标记 supported或missing。
- Modify `docs/v0.2-agentic-production-roadmap.md` only if current roadmap has a matching accepted authoring lane；不得借 Skill implementation宣称 Runtime graphics/compositing完成。

### Must Not Modify

- `src/ai_video/production/**`；
- `src/ai_video/planning/**`；
- `src/ai_video/cli.py`、Legacy pipeline、workflow templates；
- `skills-lock.json`；
- `.agents/skills/ai-comic-workflow/**`；
- external repo checkout、symlink、submodule或 vendored source；
- `.workflow/**`、`runs/**`、generated media；
- unrelated dirty/staged files。

## Shared Control-Plane Ownership Note

该计划与 AI Comic plan 的业务 files、schemas、fixtures与 tests 完全分离。未来两者都可能修改 `AGENTS.md`、`.agent/harness/policy.yaml` 与 `tests/test_agent_harness.py`，因为这些是 repository-wide routing files，不代表两个 Workflow存在业务依赖。

若并行 implementation，独立 package files可并行；任何 writer写上述同一 control-plane file前必须按 `AGENTS.md` 停止并由用户决定 ownership或执行顺序。推荐串行完成两个 routing milestone，不新增 shared workflow、shared schema或第三 orchestrator。

## Major Milestones

### Milestone 0: Freeze Product Boundary And Current Runtime Truth

**Files:** read governing spec、current `AGENTS.md`、contract matrix、Harness policy、runtime baseline、Video Planner spec、current Skill inventory与 current composition/audio/caption models；不修改 Product Runtime。

**Contract:** 固定 Product Truth / claim / rights / capability boundary，列出 forbidden AI comic fields、forbidden Runtime effects与 exact target files；确认没有 same-file writer conflict。

**Implementation Notes:**

- 记录 execution base、`git status --short` 与 live-agent ownership；
- 用 Harness inspect确认 planned paths的 mandatory checks；
- 重新核对 current `CompositionSpec`、`CaptionTrack`、`AudioTrackSpec`与 HyperFrames capability，不能从本 spec推导 implemented support；
- 对 external source重新验证 exact commit/license only if implementation引用其 text/structure；纯独立重写无需 vendor；
- 不运行 Provider、ComfyUI、media或 Product page fetch。

**Acceptance:** product/ad scope与 Runtime gap表无 unresolved owner；任何 Runtime extension、external install或 campaign system都被排除或另行提请 scope expansion。

**Verification:**

```bash
git status --short
git rev-parse HEAD
python scripts/agent_harness.py inspect \
  --path .agents/skills/ecommerce-ad-workflow/SKILL.md \
  --path tests/test_ecommerce_ad_workflow_skill.py
```

### Milestone 1: Establish RED Contract Tests And Harness Route

**Files:** create `tests/test_ecommerce_ad_workflow_skill.py`；modify `.agent/harness/policy.yaml`、`tests/test_agent_harness.py`。

**Contract:** Tests固定 schema versions、validator exit semantics、forbidden AI comic fields、claim lineage、product-name presence、product presentation feasibility、copy role separation、audio coverage、variant isolation、runtime-handoff forbidden fields与 no-I/O behavior。

**Implementation Notes:**

- 先提交会因 Skill/schema/validator缺失而失败的 focused contract tests；
- Harness category只匹配 Ecommerce Skill 与其 test，不把 AI Comic Skill或 Product Runtime归入本 check；
- generic `.agents/skills/**` control-plane checks继续运行；
- test不得安装 external Skill、clone repo、读取network或写 `.agents/skills`。

**Acceptance:** RED failure只来自 planned missing files/behavior；policy audit识别新的 test path且无 unreferenced test。

**Verification:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_ecommerce_ad_workflow_skill.py \
  tests/test_agent_harness.py -q
python -m scripts.agent_harness policy-audit
```

### Milestone 2: Implement Product Truth, Package And Validator Contracts

**Files:** create both schema files、example fixture与 `scripts/validate_contract.py`。

**Contract:** Canonical Pydantic models验证 input/package structure、claim lineage与 cross-field gates；checked-in JSON Schema与 model-generated schema一致；CLI read-only并输出 stable JSON diagnostics。

**Implementation Notes:**

- every used claim绑定 fact/source且不能出现在 prohibited set；
- medical / therapeutic claims在 V1 无条件禁止；即使输入声称已有 source或 disclaimer，也必须返回 contract-invalid，未来放宽需要独立 spec；
- product name must be referenced by at least one visible `PRODUCT_LABEL` / `BRAND_END_CARD` or audible dialogue/VO event；
- every ad beat has duration budget；sum equals target duration within exact schema-defined tolerance；
- product presentation的 role/mode/Shot/cue/source identity完整；
- `PHYSICAL_INTERACTION_REQUIRED` 必须有 source-generation或Runtime capability requirement，缺失时 blocker；
- commercial graphics不可序列化为 generic caption role；
- audio coverage interval完整，只有 explicit intentional silence可留白；on-camera dialogue必须绑定 lip-sync requirement；
- each Shot的native/generated source audio声明 keep/mute/replace/trim policy与 lead-in noise measurement requirement；
- variant changed-variable cardinality exact one；
- reject episode、serial、cliffhanger、AI comic package和所有 Runtime execution fields；
- validator不得读取 env credential、network、Product page、Project、Registry、Manifest或 media bytes。

**Acceptance:** valid fixture exit `0`；每类 negative fixture exit `2`且 diagnostic path稳定；internal exception才使用 exit `3`且不泄露 document body。

**Verification:**

```bash
python .agents/skills/ecommerce-ad-workflow/scripts/validate_contract.py \
  --kind input \
  --file .agents/skills/ecommerce-ad-workflow/templates/30s-vertical-product-ad.input.example.json
python .agents/skills/ecommerce-ad-workflow/scripts/validate_contract.py \
  --kind package \
  --file .agents/skills/ecommerce-ad-workflow/templates/30s-vertical-product-ad.package.example.json
python -m pytest -p no:cacheprovider tests/test_ecommerce_ad_workflow_skill.py -q
```

### Milestone 3: Implement Workflow Guidance And Progressive Disclosure

**Files:** create `SKILL.md` 与 eleven reference files。

**Contract:** Skill严格执行 G0-G7；每个 stage只加载对应 reference；blocking claim、rights、placement、copy、audio或 capability finding立即停止，不触发 external/runtime execution。

**Implementation Notes:**

- frontmatter description包含 ecommerce-specific trigger和 explicit AI comic exclusion；
- `SKILL.md` 保持 router-size，长方法论放 references；
- Product Truth冻结后，strategy/variants不得改写 facts或 claim status；
- `video-shotcraft` / `hell-grind-aigc-skill` / `higgsfield`只按 `AGENTS.md`做 advisory routing；
- 不调用 `open-video` autonomous director，不安装 `aiads-skills`或 HiAPI / claude-ads；
- external-method source文件区分 adopted idea、independent rewrite、copied MIT bytes与 rejected components；
- no subagent、worktree、commit、Provider、paid call或media authorization由 Skill自行推导。

**Acceptance:** unfamiliar Codex只按 `SKILL.md` 和按需 references可完成 valid package；trigger、gate、stop与 handoff不依赖 AI comic files或 outputs。

**Verification:**

```bash
python -m pytest -p no:cacheprovider tests/test_ecommerce_ad_workflow_skill.py -q
rg -n "ai-comic-workflow|episode_mode|cliffhanger|serial_arc|character_bible" \
  .agents/skills/ecommerce-ad-workflow
```

Expected：只有 explicit forbidden-boundary说明或 negative fixtures命中，不存在依赖、调用或 output field。

### Milestone 4: Prove Product, Typography And Audio Failure Gates

**Files:** refine validator、schemas、reference docs与 focused tests only。

**Contract:** 以当前青颜类失败症状建立 deterministic authoring-level regressions，不读取或生成真实媒体：

- product name absent；
- product first appears without typed role/mode；
- physical hand interaction requested but only flat overlay capability declared；
- all commercial copy mislabeled as `DIALOGUE_SUBTITLE`；
- same typography role mechanically repeated across all Shots；
- middle audio interval uncovered and not intentional；
- on-camera dialogue lacks exact speaker/Shot/verbatim line/lip-sync binding；
- generated Shot keeps noisy native lead-in without trim/mute/replace policy；
- CTA / brand end card absent；
- every Shot has equal fixed duration without ad-beat rationale。

**Implementation Notes:** Tests只证明 Workflow拒绝这些 package defects，不得声称当前 Runtime已经修复 product compositing、typography、transition或 audio stream bugs。

**Acceptance:** each defect produces a distinct stable diagnostic；valid graphic reveal与 dedicated hero shot可通过 authoring gate，但仍携带 Runtime capability classification。

**Verification:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_ecommerce_ad_workflow_skill.py \
  -k "product or claim or typography or audio or cta or pacing" -q
```

### Milestone 5: Integrate Repository Routing Without Runtime Coupling

**Files:** modify `AGENTS.md`；complete Harness policy/tests；conditionally update runtime baseline/roadmap after GREEN。

**Contract:** ecommerce request路由到新 Skill；AI comic request不触发它；existing creative Skill precedence和 Production owners保持不变。

**Implementation Notes:**

- routing wording只保存 durable trigger与 boundary；
- external Skills仍 advisory-only；
- runtime baseline明确区分 `workflow can request` 与 `runtime can execute`；
- Product Integration / Advertising Typography仍按 current code标记 missing/partial，除非独立 Runtime slice已经有 executable evidence；
- 不修改 docs-contract registry，V1不是 implemented Product Runtime surface。

**Acceptance:** routing tests覆盖 ecommerce positive cases、AI comic negative cases与 generic video cases；Architecture / docs contract无 owner冲突。

**Verification:**

```bash
python -m pytest -p no:cacheprovider \
  tests/test_ecommerce_ad_workflow_skill.py \
  tests/test_agent_harness.py \
  tests/test_docs_contract_gate.py -q
python -m scripts.docs_contract_gate check
python -m scripts.agent_harness policy-audit
python -m scripts.architecture_gate check
```

### Milestone 6: Exact-Snapshot Verification And Delivery

**Files:** only task-owned Skill、tests、routing与 truthful docs。

**Contract:** final staged snapshot不包含 external repo、media、Runtime code或 unrelated dirty work。

**Implementation Notes:**

- inspect task-owned diff与 `git diff --check`；
- stage with exact `git add <files>`，never `git add .`；
- run Harness against non-empty staged snapshot；
- verify receipt freshness and hashes；
- commit only task-owned files；push/release需要独立 authorization。

**Acceptance:** targeted checks、policy audit、docs contract、Architecture Gate与 exact staged Harness PASS；final receipt可验证；no external install、Provider/media或 advertising-performance claim。

**Verification:**

```bash
git diff --check
git status --short
make harness-verify RUN_ID=ecommerce-ad-workflow-v1
python scripts/agent_harness.py verify-receipt \
  .agent/harness/runs/ecommerce-ad-workflow-v1/receipt.json
```

Receipt path必须以实际 Harness output为准，不得猜测；上例只规定 run ID 与 verification intent。

## Rollback

本计划不改变 Production schema或durable state。Rollback按 task-owned commit反向移除：

1. `ecommerce-ad-workflow` Skill package；
2. focused tests与 Harness mapping；
3. `AGENTS.md` routing与 truthful runtime-baseline note。

不得删除或修改 existing Project、Registry、Manifest、media、AI comic Workflow、Provider profiles、external source checkout或其它 Skills。Rollback 后原有 AI-VIDEO Runtime与 manual advertising authoring path必须继续工作。

## Completion Decision

达到 Milestone 6 后只能声明：`ecommerce-ad-workflow/1 authoring contract implemented and offline-verified`。在没有真实媒体、P6 / human review与投放数据时，不得声明 product compositing、commercial typography、audio completeness、watchability、Final Acceptance、live-ready、published、released或 advertising performance。

## Follow-up Runtime Slice: Minimal `AdCreativePlan` Bridge

### Problem Boundary

- **Single owner:** versioned `AdCreativePlan` owns whole-ad creative semantics before per-Shot planning。
- **Old path to retire:** advertising copy、product cards与sound decisions不得继续仅存在于repo外 FFmpeg finalization script或每个Shot的自由文本；这种路径不能产生canonical Runtime evidence。
- **Unchanged contracts:** `ProductionStateCommitter`仍是唯一writer，`ResolvedTimeline`仍是唯一timing owner，HyperFrames仍是默认renderer，`CaptionTrack`仍只服务dialogue/accessibility subtitle，P4/P6 ownership不变。
- **Focused verification intent:** schema/compiler tests + composition resolver tests + HyperFrames source audit/render tests + Harness exact-snapshot receipt；不以历史成片、contact sheet或`video-analysis`代替Runtime evidence。

### Contract Surface

新增一个轻量、可编译的 `AdCreativePlan`，不新增独立 service。其最小字段为 `creative_concept`、`protagonist_continuity_policy`、typed `ad_arc`、typed `product_presentations`、typed `graphic_treatments`、typed `sound_cues`、`visual_motif`、`hero_shot`、`end_card` 与 `cta`。

`product_presentation.mode` 固定至少包含：

- `IN_SCENE_PROVIDER`；
- `GRAPHIC_REVEAL`；
- `HERO_ASSET`。

`graphic_treatment.role` 固定至少包含 `DIALOGUE_SUBTITLE`、`HEADLINE`、`BENEFIT_CALLOUT`、`PRODUCT_LABEL`、`PROOF_LABEL`、`CTA` 与 `BRAND_END_CARD`。只有 `DIALOGUE_SUBTITLE` 可以请求现有 `CaptionTrack`；其他 role 必须进入独立、受审计的 commercial graphic projection。

`sound_cue.role` 固定至少包含 `DIALOGUE`、`VOICE_OVER`、`MUSIC`、`SFX`、`REVEAL_HIT` 与 `INTENTIONAL_SILENCE`，并只表达广告事件与同步 intent。Exact sample timing、mix与loudness仍由P4、`ResolvedTimeline`、HyperFrames render与P6负责。

### Implementation Tasks

1. **Schema and validation:** 在现有 cohesive model boundary增加 versioned `AdCreativePlan` 与 nested typed treatments；验证 claim/source lineage、beat/Shot bindings、single protagonist/montage policy、CTA/end-card closure，以及 unsupported physical interaction classification。
2. **Compiler:** 新增 pure compiler，将 `EcommerceAdProductionPackage` / accepted authoring proposals编译为 `AdCreativePlan`，再投影为 existing Shot proposals与 composition requirements；compiler不读取credential、不选择Provider、不写Project/Registry/Manifest。
3. **Composition projection:** 最小扩展现有 `CompositionSpec` expression surface，使受支持的 `GRAPHIC_REVEAL`、`HERO_ASSET` 与 commercial text可以进入同一 composition；不建立第二timeline，generated-video上的image layer在明确更新canonical asset/type gate之前继续fail closed。
4. **HyperFrames adapter:** 只在受审计source generator内支持必要的2D entry/exit、position/scale/rotation/opacity、shadow/clip与text hierarchy；继续拒绝任意script、event handler、external CSS/font/import与network。
5. **Capability gates:** `IN_SCENE_PROVIDER` 必须绑定source-generation evidence；tracking、mask、occlusion、depth、perspective、lighting、camera matching与真实hand-held product继续返回typed gap，不允许flat PNG fallback冒充physical interaction。
6. **Review extension:** 为product integration credibility、commercial typography hierarchy、ad arc、sound synchronization、hero shot、CTA与brand closure增加pure review evidence/requirements；不得自动写P6 acceptance。
7. **Verification:** 添加schema/compiler/resolver/source-audit/render/failure-path tests，并按`.agent/harness/policy.yaml`对exact staged snapshot运行mandatory checks与fresh receipt verification。

### Acceptance Criteria

1. 一个schema-valid `AdCreativePlan`可以稳定表达统一主角/continuity policy、typed ad arc、三类product presentation、commercial graphic roles、sound cues、hero/end-card/CTA。
2. `AdCreativePlan`只投影到现有Shot/composition path；没有第二timeline、renderer、writer、Registry、Manifest或activation owner。
3. `HEADLINE`、`BENEFIT_CALLOUT`、`PRODUCT_LABEL`、`PROOF_LABEL`、`CTA`与`BRAND_END_CARD`不经过`CaptionTrack`。
4. `GRAPHIC_REVEAL`和`HERO_ASSET`在受支持的2D范围内由canonical HyperFrames path执行并产生durable receipts；unsupported layer/type、tracking或physical interaction fail closed。
5. `IN_SCENE_PROVIDER`没有source-generation evidence时不能materialize；flat overlay不能伪造手持、接触、遮挡或光照融合。
6. 所有frame/sample timing仍来自同一sealed `ResolvedTimeline`；audio cues只投影到P4 inputs，不创建advertising audio timeline。
7. Source audit继续拒绝arbitrary HTML/JavaScript/CSS/network capability。
8. Focused tests与policy-required exact-snapshot Harness receipt通过后，只能声明`AdCreativePlan bridge implemented`；不得由此声明P6、Final Acceptance、真实商品融合质量或广告效果。

### Explicit Non-Goals

不建设第二条timeline、第二renderer、第二durable writer、通用Motion Engine、复杂3D/AR商品追踪、新Asset Registry、campaign runtime或多个广告service/Agent；不删除`ResolvedTimeline`、`ProductionStateCommitter`或HyperFrames，也不把所有广告能力塞进Composition Playbook。
