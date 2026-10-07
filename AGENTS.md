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

- Legacy `0.1.x` local-first / CLI-first，默认 loopback ComfyUI，remote opt-in，无隐式 fallback。`validate` 无副作用，`run` 创建 run 并 atomic 持久化 Manifest，`resume` 只恢复既有 Manifest；保留 CLI/Manifest/layout/workflow compatibility。
- v0.2 reader/Registry strict、read-only、no-network；核验 selected revision/identity/containment/bytes。Evidence content-addressed，immutable graph/Registry/receipt 不携带 mutable lifecycle。
- HyperFrames 默认 Production renderer，Providers optional；禁止隐式换 renderer、第二 timeline，或缺 Video Provider 就放弃 image/graphics/voice/captions composition。
- Exact replay 不重复副作用或无证据推进 state；unknown fail closed。禁止 blind retry、remint/reuse permit、猜 mixed state、自动激活、删除完整 orphan evidence；recovery 只经 canonical owner。
- 跨模块失败用 `AiVideoError` / `ErrorCode`、typed retryability；普通 CLI 不泄露 raw traceback。

### Final-output-first / No-regression

验收对象是正常速度观看、聆听的 exact 成片；修复不得破坏已满足的视觉/动作/连续性/节奏/音频/叙事，拒绝已知降质方案。技术 PASS、preview、成本不代替验收；Gate 阻断须说明具体要求和失败证据，授权内修复/补证，无解报告最小恢复条件。

### Empirical Validation Priority

Model-quality uncertainty 主导且有安全、有界、已授权或 local exemption、可负担、可归因的最小实验时，先取证再扩建验证工程；用户要求先 contract 时遵从。实验不产生 Production qualification/activation/P6/Final Acceptance/release/replay truth。

### Per-Shot Post-Media Gate

每 Shot exact MP4 落盘后、下一 Shot submit 前，显式调用 project-local `video-analysis` MCP，按 sealed intent/required findings/前序 accepted state 逐项裁决；仅全 `PASS` 推进。禁止 batch 后补、hook/score 替代；缺失/陈旧/identity mismatch/MCP 不可用为 `NOT_EVALUATED`。
`FAIL` / `NOT_EVALUATED` 停止 attempt；local exemption + known outcome 执行有界 `LOCAL_BOUNDED_REPAIR_LOOP`，证据问题先 `EVIDENCE_REPAIR_FIRST`，unknown 停止。执行前必须读取 [Per-Shot Gate](.agent/context/control-plane-playbook.md#per-shot-post-media-gate)；Harness 不代执行或代签验收。

## Canonical Ownership

Creative intent 归 Codex + approved Character/Scene/Shot；schema/revision 归 `ProductionProject`，asset identity/provenance 归 Registry，mutable lifecycle/active pointers 归 Manifest；v2 writes/activation/recovery 只归 `ProductionStateCommitter`。
`ResolvedTimeline` 独占 order/frame/sample/timing/source trim，Dependency Graph/resolver 独占 desired fingerprint、precise invalidation、rebuild frontier；不得复制推导。Render 归 HyperFrames，Generation 经 selected adapter + gates，QA/repair/acceptance 归 receipts + Manifest lifecycle。详细 surface/API/禁止旁路只由 [matrix](docs/agent-primary-contract-matrix.md) 维护。

Fetch/render/analysis/generation success 不构成 activation、QA acceptance 或 delivery。External Skills
只有 advisory authority，不拥有 Product/Agent runtime 或 canonical state；`runtime_skill_calls = 0`。

## Task Routing

real media/quality、Provider/model、continuity、regression/recovery、prior architecture decision：substantial execution 前使用 `retrieve-ai-video-memory`；操作与 failure behavior 由 Skill 独占。

首次 creative prompt/contract/script 前读取 [Creative Routing And Preflight](.agent/context/control-plane-playbook.md#1-creative-skill-routing-and-preflight)，再实际读取匹配 Skill、声明选择及影响。Live/paid preview/permit/POST 前报告 continuity、handoff、axis/action/camera、prompt adaptation、lint evidence，缺失停止；schema/操作由各 Skill 和 validators 独占。
Blender 资产/参考制作先读 [routing](docs/blender-routing.md)；媒体实验/Pilot/成片交付先读 [Verification/Pilot](.agent/context/control-plane-playbook.md#4-verification-pilot-and-delivery-details)；credential/paid/ceiling 续期先读 [Provider Details](.agent/context/control-plane-playbook.md#3-provider-credential-and-paid-execution-details)，授权边界仍由下文决定。

## Agent Workflow Routing

Native Codex 默认 primary，Skill 不自动拥有 lifecycle。流程选择前读 [Workflow Operations](.agent/context/control-plane-playbook.md#agent-workflow-operations)；authorized written spec 自动触发 `superpowers:writing-plans`，Spec/Plan 默认 Parent self-review。
Implementation 先 tests/Harness，再按 `/home/reggie/.codex/SUBAGENTS.md` 的 Risk Gate 判断；未触发由 Parent 完成，触发仅一名受管 read-only Kimi reviewer，不叠加 native reviewer。Parent 裁决/修复，exact snapshot、有限轮次、re-review 和连续故障 fallback 由该 owner 独占；required review/unresolved blocker 不得绕过。额外 reviewer 仅按用户新的明确要求。

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
明确要求必含 paid/remote 的执行仅授权 accepted Provider/model/inputs 及最少有限 submit count；plan/docs/history/credential presence 不授权新调用，不查官方价格或估算账单。
每 submit 验 remaining count、exact preview、Budget Guard/reservation、egress、durable intent、one-use permit；monetary fields 仅消费预配置 sealed operator upper bound，续期按 Provider Details，不代表市场价。

## Local ComfyUI Authorization Exemption

Strict loopback、完全 local/unmetered、无 cloud egress 的任务内 ComfyUI lifecycle/generation/repair/variant/benchmark 免额外授权；用户 read-only/禁止 media 优先。豁免不移除 exact identity/profile/preflight、canonical seam、intent、one-use permit、唯一 committer、provenance、recovery、媒体 Gate；unknown 仍停止。

## Verification Contract

执行 `make harness-inspect`，完成前按 [Verification Details](.agent/context/control-plane-playbook.md#4-verification-pilot-and-delivery-details) 验 nonempty exact staged snapshot 或 exact commit range 的全部 policy checks 与 fresh receipt。Unmapped path fail safe 到 full tests + task Architecture Gate，不刷新 baseline 隐藏 regression；Harness 隔离验证 checkout 不授权开发 worktree。
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
