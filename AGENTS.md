# AI-VIDEO Agent Guide

本文件是 repository constitution。默认中文沟通，path、command、API、schema 与 Skill 名保持原文。
只常驻 authority、安全边界、唯一 owner 与 completion；可执行约束交给 Harness，详细知识按任务加载。

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

先读用户请求、本文件，再按 task concern 读取 matrix、policy、当前源码/tests 和 applicable spec/plan。
`.agent/context/` 是按需读取的 advisory operational reference；不得整目录预载。

## Conflict Resolution

用户明确指令 → 当前 code/tests/runtime evidence → 本 constitution 与委托 owner → accepted
spec/plan 与 canonical docs → Skill → history/handoff/drafts。低位阶不得覆盖高位阶。
历史 receipt、memory、文档或模型判断不证明当前 runtime、外部授权、质量或 publication。
改变契约须同步 code、tests 与 canonical docs；不得只改文字宣称 runtime 已实现。

## Product Invariants

- Legacy `0.1.x` 保持 local-first / CLI-first；默认 loopback ComfyUI，remote 要 opt-in，不能隐式 fallback。
  `validate` 无副作用；`run` 创建 run 并 atomic 持久化 Manifest；`resume` 只从既有 Manifest 恢复。
  公共 `validate/run/resume`、Manifest/layout/workflow compatibility 由 Harness 绑定 tests 验证。
- v0.2 reader/Registry strict、read-only、no-network，校验 selected revision、identity、containment 与 bytes。
  Evidence content-addressed；immutable graph/Registry/receipt 不携带 mutable lifecycle。
- HyperFrames 是默认 Production renderer，Providers 是 optional capabilities；不能隐式换 renderer、
  建第二 timeline 或因缺 Video Provider 放弃基础 image/graphics/voice/captions composition。
- Exact replay 不重复外部副作用或无证据推进 state；unknown outcome fail closed，禁止 blind retry、
  remint/reuse permit、猜 mixed state、自动激活或删除完整 orphan evidence。Recovery 只经 canonical owner。
- Cross-module failures 使用 `AiVideoError` / `ErrorCode` 与 typed retryability；普通 CLI 不泄露 raw traceback。

### Final-output-first / No-regression

最终判断对象是观众正常速度观看、聆听的 exact 成片。局部修复不得破坏已满足的视觉、动作、
连续性、节奏、音频或叙事；拒绝已知降低观看质量的方案。技术 PASS、preview、成本不能代替验收。
Gate 阻断时说明所保护的具体要求与失败证据，在授权内修复/补证；无可行路径报告最小恢复条件。

### Empirical Validation Priority

媒体能力的不确定性以 model quality 为主、且存在安全、有界、已授权或适用 local exemption、
可负担和可归因的最小真实实验时，优先取证，再扩建仅服务未来验证的工程；用户要求先做 contract 时遵从。
Development experiment 不产生 Production qualification、activation、P6、Final Acceptance、release 或 replay truth。

### Per-Shot Post-Media Gate

每 Shot exact MP4 落盘后、下一 Shot submit 前，显式调用 project-local `video-analysis` MCP，
按 sealed intent、required findings 与前序 accepted state 逐项裁决；只有全部 required findings 为 `PASS` 才可推进。
缺失/陈旧/identity mismatch/MCP 不可用均为 `NOT_EVALUATED`，阻断下一 Shot；禁止 batch 后补或用 hook/score 代替。
`FAIL` / `NOT_EVALUATED` 停止 current attempt；local exemption 且 outcome known 时执行有界
`LOCAL_BOUNDED_REPAIR_LOOP`，证据问题先 `EVIDENCE_REPAIR_FIRST`。Unknown outcome 必须停止。
具体 [Per-Shot Post-Media Gate](.agent/context/control-plane-playbook.md#per-shot-post-media-gate) 仍需 Agent 显式执行，
离线 Harness 不拦截任意 tool/shell、不写 Manifest、不代签 P6 或 Final Acceptance。

## Canonical Ownership

| Concern | Canonical Owner |
| --- | --- |
| Creative intent | Codex + approved AI-VIDEO Character / Scene / Shot artifacts |
| Project schema / selected revision | `ProductionProject` |
| Asset identity / provenance | Asset Registry |
| Mutable lifecycle / active pointers | Production Manifest |
| v2 writes / activation / explicit recovery | `ProductionStateCommitter` |
| Dependency / desired fingerprint / precise invalidation / rebuild frontier | Dependency Graph / resolver |
| Order / frame / sample / timing / source trim | `ResolvedTimeline` |
| Default render | HyperFrames adapter |
| Generation | Selected Provider adapter behind AI-VIDEO gates |
| QA / repair / acceptance evidence | AI-VIDEO receipts + Manifest lifecycle |

Fetch/render/analysis/generation success 不构成 activation、QA acceptance 或 delivery。External Skills
只有 advisory authority，不拥有 Product/Agent runtime 或 canonical state；`runtime_skill_calls = 0`。

## Agent Memory Retrieval Routing

real media/quality、Provider/model、continuity、regression/recovery 或 prior architecture decision 任务，
在 substantial execution 前使用 `retrieve-ai-video-memory`；操作与 failure behavior 只由该 Skill 维护。

## Experience Learning Routing

stable substantial record 后自动评估 `distill-ai-video-learning`；只可提出 pending advisory claim，
用户 exact confirmation 与 target owner verification 前不修改 Skill/Policy/Gate 或标 `ADOPTED`。

## Creative Skill Routing
Blender 资产/参考制作见 [routing](docs/blender-routing.md)。

| Concern | Route |
| --- | --- |
| Ecommerce / SKU / product advertising | `ecommerce-ad-workflow` |
| Raw input / Director coverage / ordered Shots | `open-video` |
| Semantic Shot-state / continuity / diagnosis | `hell-grind-aigc-skill` |
| Approved Shot + selected MiniMax H3 | `h3-video` |
| Approved Shot + selected Seedance target | `seedance-authoring` |
| Non-Seedance model / Provider prompt adaptation | `higgsfield` |
| Motion / graphics / pacing | `video-shotcraft` |
| Experience synthesis | `distill-ai-video-learning` after stable record |

必须在首次 creative prompt/contract/script 编写前实际读取匹配 Skill，声明选择及影响；付费 preview/permit/POST
前报告 continuity、handoff、axis/action/camera、prompt adaptation 与 lint evidence，缺失即停止。
详细 [Creative Skill Routing And Preflight](.agent/context/control-plane-playbook.md#1-creative-skill-routing-and-preflight)
只保留 concern routing；schema 和操作由各 Skill 与现有 executable validators 独占。

## Agent Workflow Routing

Native Codex 为默认 primary；按 semantic risk 分级：T0 局部可逆 targeted validation；T1 bounded multi-file
必要时 plan；T2 architecture/workflow/Provider/Harness/shared schema 走 research → spec → plan → implement → verify
→ review；T3 ownership/verification/paid/credential/recovery/QA contract 保留严格验证，不自动触发双审。
Bug 先 root-cause/systematic-debugging 再 regression validation。Skill 按需加载，不自动成为 lifecycle owner。
Spec/plan 默认 Parent self-review，不默认 Kimi/native reviewer；authorized written spec 自动触发
`superpowers:writing-plans`。Implementation 先 tests/Harness，再按 `/home/reggie/.codex/SUBAGENTS.md`
的低频 Risk Gate 判断；未触发由 Parent 完成，触发只增加一名 Kimi read-only reviewer，不叠加 native reviewer。
Kimi review → Codex Parent 裁决/修复 → verification → 必要 targeted/full Kimi re-review；exact snapshot、
有限轮次及连续故障 native 替换均由 SUBAGENTS.md 独占。细节见 playbook 的 Implementation Review。
本规则取代旧 Spec/Plan 从 T3 推导的双审默认；历史证据保留，额外 reviewer 仅按用户新的明确要求。

## Change Rules

默认当前 working tree 串行，通常直接 `main`；仅用户当前明确要求才建 dedicated development worktree。
写前 `git status`；保留 unrelated dirty/staged work，same-file conflict 写前请用户决定。只编辑/stage/commit task-owned
paths，使用 `git add <specific-files>`。不 reset/clean/overwrite 他人工作；不擅自新增依赖、Provider/cloud scope。
遵循现有 patterns、public compatibility 和 module boundaries；distinct responsibility 不追加到 God Module。
800 effective LOC 与 dependency direction 由 Architecture Gate 管理。行为变更有 public/boundary/failure-path 验证；
nontrivial frontend 用 integrated browser testing。结构关系按需 CodeGraph，AOCI 只提供 advisory cognition。
非任务涉及不编辑 `.workflow/`、`runs/` 或生成媒体；tests 使用标准 Production loading/execution seam，不以裸解析旁路造证。

## Decision Gates

任务目标内必要的 shared contract、有限预算、时间窗口和 recovery rule 变更默认授权 Parent 自主判断、
self-review、实现、验证并记录。不要逐项请批；用户 spec-only、先审后做、不可调整上限仍优先。
默认授权与 Gate/Harness 修订不得削弱 Product Invariants、凭据、预算、egress、permit 或真实验收保护。
Gate/Harness 修订须说明如何改善实际观看体验，保留旧/新规则与真实历史，不为让测试通过降低质量。
预算耗尽先停止 attempt，核对真实计数/outcome，再有据封存下一有限单元，保留 predecessor/old/new bounds。
不绕过 guard、重置消费、改写历史或无限执行。Unknown outcome 禁止 retry/remint，先证据/显式 recovery。
只有 scope expansion、未授权外部效果、destructive/irreversible 或 same-file conflict 需要用户决定。

## Provider Credential and Paid Execution Rules

Credential 仅经 injected supplier 的 exact private reference，不进 repo/.env/prompt/argv/log/error/receipt；lookup
失败 fail closed，不搜索别的 secret source。明确要求必含 paid/remote 的执行，授权 accepted Provider/model/inputs
及最少有限 submit count；plan/docs/history/credential presence 不授权新调用，不查询官方价格或估算账单。
每 submit 仍验证 remaining count、exact preview、既有 Budget Guard/reservation、egress、durable intent 与 one-use permit。
Runtime monetary fields 只消费预配置 sealed operator upper bound；兼容续期见 playbook，不代表官方市场价。

## Local ComfyUI Authorization Exemption

strict loopback、完全 local/unmetered、无 cloud egress 的任务内 lifecycle/generation/repair/variant/benchmark
免额外授权；用户 read-only/禁止 media 优先。豁免不移除 exact identity/profile/preflight、canonical seam、intent、
one-use permit、唯一 committer、provenance、recovery 或媒体 Gate；unknown outcome 仍停止。

## Verification Contract

执行 `make harness-inspect`；完成针对 nonempty exact staged snapshot 或 exact commit range 执行现有 policy checks。
Harness 自身隔离验证 checkout 不授权开发 worktree。Fresh passing receipt 须核验 scope/policy/artifact hashes/freshness。
Unmapped path fail safe 到 full tests + task Architecture Gate；不刷新 baseline 隐藏 regression。
规则/check references、文档 links/anchors、guide/context byte/line budgets 由 `agent_rules_check` 每轮执行；
迁移的 deterministic invariants 由 `agent_rule_invariants` 与原 changed-path suites 验证。离线 PASS 仅证明所测行为。
Harness 不调度 Agent、不读 Provider secret、不运行 live media、不 mutation Production。CI 自产 evidence；
workflow 文件不证明 server enforcement。Tool exit 0 / `PARSED` / tests 不代替 required review 或真实验收。
区分 execution、structure、function、criteria 与 final review 五层证据；`PASS/DONE/ACCEPTED` 须有对应证据，无法验证标 `NOT_EVALUATED`。

## Completion Standard

稳定 substantial checkpoint/blocker/handoff 前使用 `record-ai-video-session` 主动评估 record/no_record，
记录后自动 learning evaluation；repository 外 effects 与无 hook 也计入。所有修改（含文档、规则、配置）验证后 MUST 按 owned paths commit；每次 commit 后 MUST push 到远端 `main` 并核验 SHA。失败/受阻须报告，禁止 force push 或夹带无关改动。
Final 报 changed content、实际 verification、receipt 相对路径、publication state 和未验证风险。

<!-- aoci:begin -->
## AOCI-CODE 与 CodeGraph

跨模块修改、架构理解、影响分析、复杂 bug、重构或重要功能开发时，按需先用 AOCI 获取职责、语义关系、API 与约束，再用 CodeGraph 核对 symbol、reference、dependency/call graph，以源码/LSP 为具体事实、tests 为最终验证。简单局部任务没有实际 AOCI 认知需求时，禁止仅为流程完整机械调用 AOCI。

AOCI cognition 永远不是 source of truth；Overview、Entry 与检索结果只作 advisory context，不能代替当前源码、tests、已验证 runtime evidence 或 canonical contracts。AOCI 正式认知位于 `aoci.txt`、`aoci.meta.txt`、`aoci.code.txt`；当前状态、维护顺序和安全停点以项目 AOCI MCP 的 `aoci_rules`、实时 Guide、工具返回及官方文档为准。索引语义必须基于当前源码和契约证据由模型编写；若认知与源码或 CodeGraph 不符，应修正认知，不能覆盖源码事实。受管理对象在最终稳定状态后按 AOCI 官方流程维护，不能把未对齐索引称为完整认知。
<!-- aoci:end -->
