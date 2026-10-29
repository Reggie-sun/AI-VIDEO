# AI-VIDEO Agent Guide

本文件是 repository constitution，常驻 authority、安全、唯一 owner 与 completion；可执行约束归 Harness，细节按需加载。默认中文，path、command、API、schema、Skill 名保持原文。

## Runtime Truth Sources

| Concern | Canonical Source |
| --- | --- |
| Authority、授权、安全、ownership、completion | `AGENTS.md` |
| Surface owner、invariant、禁止旁路 | `docs/agent-primary-contract-matrix.md` |
| Changed-path checks、argv、receipt | `.agent/harness/policy.yaml`、`scripts/agent_harness.py` |
| 已迁移规则的 check references 与证明边界 | `.agent/harness/agent-rules.yaml` |
| 当前实现与证据边界 | `docs/v0.2-runtime-baseline.md` |
| Phase、future gates 与方向 | `docs/v0.2-agentic-production-roadmap.md` |
| Slice scope 与 tradeoffs | active spec / plan |

相关操作前 MUST 按 concern 读取下文指定 owner、matrix、policy、当前源码/tests 和 applicable spec/plan。
`.agent/context/` 是 advisory operational reference，不拥有 Product state 或授权；本文件委托的 preflight/Gate 仍须执行，不得整目录预载。

## Conflict Resolution

用户明确指令 → 当前 code/tests/runtime evidence → 本 constitution 与委托 owner → accepted spec/plan 与 canonical docs → Skill → history/handoff/drafts。低位阶不得覆盖高位阶。历史 receipt/memory/文档/模型判断不证明当前 runtime、授权、质量或 publication；契约变更同步 code/tests/canonical docs，不以文字冒充实现。

## Product Invariants

制作控制能力必须面向跨项目、跨镜头复用，具体作品只作验证案例，不以作品或单镜特例替代共享能力，也不以单例通过证明通用能力成立。

- Legacy `0.1.x` local-first / CLI-first，默认 loopback ComfyUI，remote opt-in，无隐式 fallback。`validate` 无副作用，`run` 创建 run 并 atomic 持久化 Manifest，`resume` 只恢复既有 Manifest；保留 CLI/Manifest/layout/workflow compatibility。
- v0.2 reader/Registry strict、read-only、no-network；核验 selected revision/identity/containment/bytes。Evidence content-addressed，immutable graph/Registry/receipt 不携带 mutable lifecycle。
- HyperFrames 默认 Production renderer，Providers optional；禁止隐式换 renderer、第二 timeline，或缺 Video Provider 就放弃 image/graphics/voice/captions composition。
- Exact replay 不重复副作用或无证据推进 state；unknown fail closed。禁止 blind retry、remint/reuse permit、猜 mixed state、自动激活、删除完整 orphan evidence；recovery 只经 canonical owner。
- 跨模块失败用 `AiVideoError` / `ErrorCode`、typed retryability；普通 CLI 不泄露 raw traceback。

### Final-output-first / No-regression

以原速声画成片验收，保留已满足的效果；先交片，用户认可后完整验证，通过再 commit/push。字幕时机与格式、逐镜累积审看和输出规格（含商品广告固定720p）见[成片优先](docs/canvas-continuous-production.md#formal-narrative-output-defaults)；单段认可不豁免拼接审查，接点与复用素材核验归 `open-video`。

### Empirical Validation Priority

Model-quality uncertainty 主导且有安全、有界、已授权或 local exemption、可负担、可归因的最小实验时，先取证再扩建验证工程；用户要求先 contract 时遵从。实验不产生 Production qualification/activation/P6/Final Acceptance/release/replay truth。

### Community Reference And Workflow Improvement

遇到模型质量、工作流能力或反复失败问题，先核对exact输入、结果和当前失败状态，再参考可追溯社区实践、官方/模型作者资料及反例；结合当前工具/模型/版本、授权与约束判断适用性。优先适配有证据的成熟方案，不只反复改prompt或先扩建执行工程。
在已授权且outcome已知的边界内做可归因的最小真实验证，逐项核验原目标及已满足项，保留输入/输出identity与verdict；社区推荐、技术PASS或局部效果不能代替完整验收，UNKNOWN不盲重试。
验证有效且适用范围明确后，将可复用步骤、参考职责、能力限制和验收要求写回现有workflow owner并验证；单例只记录有界经验，不自动升级普遍规则或削弱Gate。具体生图流程见[工作流](docs/canvas-production-harness.md#agent-image-authoring-workflow)，证据与学习沿Completion Standard的record/learning owner；不把素材、实验日志或第二执行链放进本constitution。

### Per-Shot Post-Media Gate

每 Shot exact MP4 落盘后、下一 Shot submit 前，显式调用 project-local `video-analysis` MCP，按 sealed intent/required findings/前序 accepted state 逐项裁决；仅全 `PASS` 推进。禁止 batch 后补、hook/score 替代；缺失/陈旧/identity mismatch/MCP 不可用为 `NOT_EVALUATED`。
`FAIL` / `NOT_EVALUATED` 停止 attempt；local exemption + known outcome 执行有界 `LOCAL_BOUNDED_REPAIR_LOOP`，证据问题先 `EVIDENCE_REPAIR_FIRST`，unknown 停止。执行前必须读取 [Per-Shot Gate](.agent/context/control-plane-playbook.md#per-shot-post-media-gate)；Harness 不代执行或代签验收。

## Canonical Ownership

Creative intent 归 Codex + approved Character/Scene/Shot；schema/revision 归 `ProductionProject`，asset identity/provenance 归 Registry，mutable lifecycle/active pointers 归 Manifest；v2 writes/activation/recovery 只归 `ProductionStateCommitter`。
`ResolvedTimeline` 独占 order/frame/sample/timing/source trim，Dependency Graph/resolver 独占 desired fingerprint、precise invalidation、rebuild frontier；不得复制推导。Render 归 HyperFrames，Generation 经 selected adapter + gates，QA/repair/acceptance 归 receipts + Manifest lifecycle。详细 surface/API/禁止旁路只由 [matrix](docs/agent-primary-contract-matrix.md) 维护。

工具成功不构成 activation、QA acceptance 或 delivery；External Skills 不拥有 Production runtime/canonical state，`runtime_skill_calls = 0`；OMX 只管理 Agent workflow state。

## Task Routing

real media/quality、Provider/model、continuity、regression/recovery、prior architecture decision：substantial execution 前使用 `retrieve-ai-video-memory`；操作与 failure behavior 由 Skill 独占。

首次 creative prompt/contract/script 前读取 [Creative Routing And Preflight](.agent/context/control-plane-playbook.md#1-creative-skill-routing-and-preflight)，再实际读取匹配 Skill、声明选择及影响。Live/paid preview/permit/POST 前报告 continuity、handoff、axis/action/camera、prompt adaptation、lint evidence，缺失停止；schema/操作由各 Skill 和 validators 独占。
Blender 资产/参考制作先读 [routing](docs/blender-routing.md)；媒体实验/Pilot/成片交付先读 [Verification/Pilot](.agent/context/control-plane-playbook.md#4-verification-pilot-and-delivery-details)；credential/paid/ceiling 续期先读 [Provider Details](.agent/context/control-plane-playbook.md#3-provider-credential-and-paid-execution-details)，授权边界仍由下文决定。

写图像/视频提示词或安排人物出场前读[提示词语言与人物身份](docs/canvas-continuous-production.md#prompt-language-and-character-identity)。每 Shot 按创作需要选择参考条件、不默认用白模，依据与制作见[参考选择](docs/canvas-production-harness.md#per-shot-whitebox-reference)；镜头覆盖、生成分组定长与修复取舍归 `open-video`。

## Agent Workflow Routing

编排、planning、roles/review 遵循全局 OMX，见 [Workflow Operations](.agent/context/control-plane-playbook.md#agent-workflow-operations)。仅用 Codex 原生 Agent；Parent 负责集成与验证，Product gates 不变。

## Change Rules

默认当前 working tree 串行，通常直接 `main`；仅用户当前明确要求才建 dedicated development worktree。
写前 `git status`；保留 unrelated dirty/staged work，same-file conflict 写前请用户决定。只编辑/stage/commit task-owned
paths，使用 `git add <specific-files>`。不 reset/clean/overwrite 他人工作；不擅自新增依赖、Provider/cloud scope。
遵循现有 patterns、public compatibility 和 module boundaries；distinct responsibility 不追加到 God Module。
800 effective LOC 与 dependency direction 由 Architecture Gate 管理。行为变更有 public/boundary/failure-path 验证；
nontrivial frontend 用 integrated browser testing。结构关系按需 CodeGraph，AOCI 只提供 advisory cognition。
非任务涉及不编辑 `.workflow/`、`runs/` 或生成媒体；tests 使用标准 Production loading/execution seam，不以裸解析旁路造证。

## Decision Gates

任务内必要 shared contract、有限预算/时间窗口、recovery rule 变更默认授权 Parent 自主判断、self-review、实现、验证、记录，不逐项请批；用户 spec-only/先审后做/不可调整上限优先。
不得削弱 Product Invariants、凭据、预算、egress、permit、真实验收。Gate/Harness 修订须说明观看体验收益，保留旧/新规则及真实历史，不为过测试降质量。
预算耗尽先停 attempt、核对真实计数/outcome，再有据封存下一有限单元，保留 predecessor/old/new bounds；禁止绕 guard、重置消费、改历史、无限执行。Unknown 禁止 retry/remint，先证据/显式 recovery。
仅 scope expansion、未授权外部效果、destructive/irreversible、same-file conflict 需用户决定。

## Provider Credential and Paid Execution Rules

Credential 仅经 injected supplier 的 exact private reference，不进 repo/.env/prompt/argv/log/error/receipt；lookup 失败 fail closed，不搜其他 secret source。
执行请求默认授权任务内必要的付费/remote 调用，自主控制有限次数与预算，不另行索要付费授权，完成时据实汇报金额或积分，未结算标待确认；用户明确禁令与硬上限优先，文档/凭据不授权执行，不为授权查价或估账。
每 submit 验 remaining count、exact preview、Budget Guard/reservation、egress、durable intent、one-use permit；monetary fields 仅消费预配置 sealed operator upper bound，续期按 Provider Details，不代表市场价。

## Local ComfyUI Authorization Exemption

Strict loopback、完全 local/unmetered、无 cloud egress 的任务内 ComfyUI lifecycle/generation/repair/variant/benchmark 免额外授权；用户 read-only/禁止 media 优先。豁免不移除 exact identity/profile/preflight、canonical seam、intent、one-use permit、唯一 committer、provenance、recovery、媒体 Gate；unknown 仍停止。

## Verification Contract

Harness 按阶段验证：修改后仅运行受影响模块的精准测试，功能完成后运行关联模块和接口契约回归，合并或发布前运行完整测试套件；receipt 必须标明级别，局部或相关回归通过不得冒充完整回归通过。
执行入口见 [Verification Details](.agent/context/control-plane-playbook.md#4-verification-pilot-and-delivery-details)；使用 exact staged snapshot 或 commit range 并保留对应级别 receipt。精准映射缺失时明确报告或升级，不静默扩跑；不刷新 baseline 隐藏 regression。
Harness 不拦截任意 tool/shell、不调度 Agent、不读 secret、不运行 live media、不 mutation Production、不代签 P6/Final Acceptance；CI 自产 evidence，workflow 文件不证明 server enforcement。离线 PASS 只证明所测行为，exit 0 / `PARSED` / tests 不代替 required review 或真实验收。
区分 execution、structure、function、criteria 与 final review 五层证据；`PASS/DONE/ACCEPTED` 须有对应证据，无法验证标 `NOT_EVALUATED`。

## Completion Standard

稳定 substantial checkpoint/blocker/handoff 前使用 `record-ai-video-session` 主动评估 record/no_record，
repository 外 effects 与无 hook 也计入。Record 后自动评估 `distill-ai-video-learning`，仅提出 pending advisory claim；用户 exact confirmation 与 target owner verification 前不修改 Skill/Policy/Gate 或标 `ADOPTED`。
所有修改（含文档、规则、配置）验证后 MUST 按 owned paths commit；每次 commit 后 MUST push 到远端 `main` 并核验 SHA。失败/受阻须报告，禁止 force push 或夹带无关改动。
Final 报 changed content、实际 verification、receipt 相对路径、publication state 和未验证风险。

<!-- aoci:begin -->
## AOCI-CODE 与 CodeGraph

跨模块修改、架构/影响分析、复杂 bug、重构、重要功能开发前读 [Cognition Tools](.agent/context/control-plane-playbook.md#cognition-tools)，按需 AOCI、CodeGraph 核对结构；源码/LSP/tests 才是事实。简单局部任务禁止机械调用 AOCI；其 cognition 永远仅 advisory，维护遵从项目 MCP 官方流程。
<!-- aoci:end -->
