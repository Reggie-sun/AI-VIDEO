# AI-VIDEO Agent Guide

本文件是仓库根本规则（constitution），每次会话都加载，只放授权、安全、唯一归属（owner）与完成标准；程序可检查的约束归 Harness，细节见下文链接，用到再读。

本文件对 Codex 与 Claude Code 通用：「主会话」（Parent）指直接与用户对话的 Agent，「子代理」指它派出的 Agent，「编排层」指全局 workflow 工具（Codex 为 OMX，Claude Code 为 OMC）。默认中文；path、command、API、schema、Skill 名保持原文。

## Runtime Truth Sources

| 关注点 | 唯一来源 |
| --- | --- |
| 授权、安全、归属、完成标准 | `AGENTS.md` |
| 各 surface 的 owner、不变量、禁止旁路 | `docs/agent-primary-contract-matrix.md` |
| 改动路径对应的检查、argv、receipt | `.agent/harness/policy.yaml`、`scripts/agent_harness.py` |
| 已迁移规则的检查引用与证明边界 | `.agent/harness/agent-rules.yaml` |
| 当前实现与证据边界 | `docs/v0.2-runtime-baseline.md` |
| 阶段、未来 Gate 与方向 | `docs/v0.2-agentic-production-roadmap.md` |
| 单个 slice 的范围与取舍 | 当前 spec / plan |

相关操作前 MUST 按 concern 读取上表来源、下文指定的 owner 及当前源码、tests 和适用 spec/plan。
`.agent/context/` 是操作参考（advisory），不拥有 Product state 或授权，但本文件委托的 preflight 和 Gate 必须执行；按需读章节，不整目录预载。

## Conflict Resolution

冲突时靠前的胜出：用户明确指令 → 当前代码、tests 与运行时证据 → 本文件及其委托 owner → 已接受的 spec/plan 与 canonical docs → Skill → 历史记录、handoff、草稿。

历史 receipt、memory、文档或模型判断不证明当前 runtime、授权、质量或发布状态。改契约须同步代码、tests 和 canonical docs，写了不等于实现了。

## Product Invariants

制作控制能力要做成跨项目、跨镜头复用的共享能力；具体作品只是验证案例，不用单个作品或镜头的特例代替共享能力，单例通过也不证明通用能力成立。

- **Legacy `0.1.x`**：本地优先、CLI 优先，默认本机 loopback ComfyUI，远程须显式开启，无隐式 fallback。`validate` 无副作用，`run` 新建 run 并原子写入 Manifest，`resume` 只恢复已有 Manifest；CLI、Manifest、目录布局与 workflow 保持兼容。
- **v0.2 读取**：reader 与 Registry 严格、只读、不联网，核验所选 revision、identity、路径包含与 bytes；Evidence 按内容寻址，不可变的 graph、Registry、receipt 不带可变生命周期状态。
- **渲染**：HyperFrames 是默认 Production renderer，Provider 可选；不得悄悄换 renderer、另建第二条 timeline，或因缺视频 Provider 就放弃图片、图形、配音、字幕的合成。
- **重放与恢复**：exact replay 不重复副作用，无证据不推进 state；unknown 一律 fail closed。禁止盲目重试、重签或复用 permit、猜测混合状态、自动激活、删除完整的孤立证据；恢复只经 canonical owner。这是为了防止重复扣费和状态错乱。
- **错误**：跨模块失败用 `AiVideoError` / `ErrorCode`，并用类型化字段标明能否重试；普通 CLI 不泄露原始 traceback。

### Final-output-first / No-regression

验收看正常速度、带声音的成片；任何改动（含修复）都不能破坏已满足的效果。先交片，用户认可后再跑完整验证，通过才 commit/push，避免工程验证拖慢交片。字幕时机与格式、逐镜累积审看和输出规格（含商品广告固定720p）见[成片优先](docs/canvas-continuous-production.md#formal-narrative-output-defaults)；单段认可不代替拼接审查，接点与复用素材核验归 `open-video`。

新创作的付费视频生成前，先把该镜头将使用的参考包（决定性时刻的关键帧、人物、细节、环境、已认可片段的风格帧）作为预览交给用户，取得明确认可并封存为 `preview_approval` 才能提交；“好不好看、怪不怪”只由用户判，Agent 的检查表 PASS 不代替。2026-10-30 用户要求修订，原因：多次纸上定稿后直接付费生成、成片被否定（细则见[参考规划](docs/shot-reference-planning.md)）。

### Empirical Validation Priority

遇到模型质量问题、工作流能力不足或反复失败时，先取证再扩建工程：

1. 核对 exact 输入、结果和当前失败状态。
2. 查可追溯的社区实践、官方或模型作者资料及反例，按当前工具、版本、授权和约束判断适用性；优先采用有证据的成熟方案，不只反复改 prompt。
3. 模型质量不确定性占主导、且能做安全、有界、已授权（或属本地豁免）、成本可承受、可归因的最小实验时，先实验再扩建验证工程；用户要求先定 contract 时照做。工作流能力不足或反复失败时，做可归因的最小真实验证。两种情况都只在已授权且结果可知的边界内进行。逐项核对原目标与已满足项，保留输入/输出 identity 和结论；UNKNOWN 不盲目重试。
4. 验证有效且范围明确后，把可复用步骤、参考职责、能力限制和验收要求写回现有 workflow owner 并验证；单例只记有界经验，不自动升级为普遍规则，也不削弱 Gate。

实验结果、社区推荐、技术 PASS 或局部效果不代替完整验收，也不构成 Production 资格、激活、P6、Final Acceptance、发布或 replay 依据。细则见 [Empirical Uncertainty Triage](.agent/context/control-plane-playbook.md#empirical-uncertainty-triage)，生图流程见[工作流](docs/canvas-production-harness.md#agent-image-authoring-workflow)；证据与经验走 Completion Standard，素材、实验日志或第二条执行链不写进本文件。

### Per-Shot Post-Media Gate

每 Shot exact MP4 落盘后、下一 Shot submit 前，必须显式调用 project-local `video-analysis` MCP，对照封存意图、必查项和前序已接受状态逐项裁决；仅全 `PASS` 推进，问题不带进后续镜头。

- 禁止整批生成后补查，禁止用 hook 或评分代替；证据缺失、过期、identity 不符或 MCP 不可用都算 `NOT_EVALUATED`。封存要求未达即 `FAIL`，不写“PASS 但有偏差”；改判次要、移出或延后须用户当次决定；观感不由 Agent 判。
- `FAIL` / `NOT_EVALUATED` 停止 attempt。本地豁免且结果已知（local exemption + known outcome）时执行有界的 `LOCAL_BOUNDED_REPAIR_LOOP`；证据本身有问题先走 `EVIDENCE_REPAIR_FIRST`；结果未知则 unknown 停止。

执行前必须读取 [Per-Shot Gate](.agent/context/control-plane-playbook.md#per-shot-post-media-gate)；Harness 不代为执行，也不代签验收。

## Canonical Ownership

每类状态只有一个 owner，其他地方只读取或调用；`ResolvedTimeline` 与 Dependency Graph / resolver 两行所列内容不得复制推导。

| 内容 | 唯一 owner |
| --- | --- |
| 创作意图 | 主会话 + 已批准的 Character/Scene/Shot |
| schema 与 revision | `ProductionProject` |
| 素材 identity 与来源 | Registry |
| 可变生命周期与 active 指针 | Manifest |
| v2 写入、激活与恢复 | `ProductionStateCommitter` |
| 顺序、帧、采样、时间与源素材裁切 | `ResolvedTimeline` |
| 期望 fingerprint、精确失效与重建范围 | Dependency Graph / resolver |
| 渲染 / 生成 | HyperFrames / 所选 adapter + gates |
| QA、修复与验收 | receipts + Manifest lifecycle |

详细 surface、API 与禁止旁路只在 [matrix](docs/agent-primary-contract-matrix.md) 维护。工具成功不等于已激活、通过 QA 或已交付；外部 Skill 不拥有 Production runtime 或 canonical state（`runtime_skill_calls = 0`）；编排层只管理 Agent workflow state。

## Task Routing

首次 creative prompt/contract/script 前读取 [Creative Routing And Preflight](.agent/context/control-plane-playbook.md#1-creative-skill-routing-and-preflight)，再实际读取匹配的 Skill 并说明选择及影响；其他工作按下表先读，操作与失败处理由各 Skill 独占。

| 开始做什么之前 | 先读 |
| --- | --- |
| 真实媒体/质量、Provider/模型、连续性、回归/恢复、以往架构决策相关的实质工作 | `retrieve-ai-video-memory` |
| 写图像/视频提示词、安排人物出场 | [提示词语言与人物身份](docs/canvas-continuous-production.md#prompt-language-and-character-identity) |
| 每 Shot 按创作需要选参考条件（不默认白模） | [参考选择](docs/canvas-production-harness.md#per-shot-whitebox-reference) |
| 镜头覆盖、生成分组定长、修复取舍 | `open-video` |
| Blender 资产或参考 | [routing](docs/blender-routing.md) |
| 媒体实验、Pilot、成片交付 | [Verification/Pilot](.agent/context/control-plane-playbook.md#4-verification-pilot-and-delivery-details) |
| credential、付费、额度续期 | [Provider Details](.agent/context/control-plane-playbook.md#3-provider-credential-and-paid-execution-details)，授权边界见下文 |

镜头覆盖、生成分组定长与修复取舍归 `open-video`。Live 或付费的 preview/permit/POST 前，必须报告连续性、交接、轴线/动作/机位、prompt 适配和 lint 证据，缺一项即停止；schema 与操作归各 Skill 和 validator。

## Agent Workflow Routing

编排、规划、角色分工和 review 遵循当前运行时的编排层，见 [Workflow Operations](.agent/context/control-plane-playbook.md#agent-workflow-operations)。只用当前运行时原生的子代理；主会话负责集成与验证，Product gate 不因编排方式改变。

## Change Rules

- 默认在当前 working tree 串行工作，通常直接在 `main`；用户当次明确要求才建独立的开发 worktree（dedicated development worktree）。
- 写前先看 `git status`，保留与本任务无关的未提交或已暂存改动（不论来源）；same-file conflict 时写前先问用户。
- 只编辑、暂存、提交本任务拥有的路径，用 `git add <specific-files>`。不 reset、clean 或覆盖他人工作；不擅自新增依赖、Provider 或云端范围。
- 遵循现有模式、公开兼容性和模块边界，新的独立职责不堆进大模块（God Module）。单文件 800 有效行上限与依赖方向由 Architecture Gate 管理。
- 行为变更验证公开接口、边界和失败路径；非简单前端用集成浏览器测试。结构关系按需查 CodeGraph，AOCI 只作参考。
- 与任务无关时不编辑 `.workflow/`、`runs/` 或生成的媒体；tests 走标准 Production 加载与执行入口，不绕开它直接解析文件造证据。

## Decision Gates

**主会话自己决定**：任务内必需的 shared contract、有限预算或时间窗口、recovery 规则变更，自行判断、自审、实现、验证、记录，不逐项请示；用户要求只出 spec、先审后做或上限不可调时从用户。

**只有这些需用户决定**：扩大范围、未授权的外部效果、破坏性或不可逆操作、same-file conflict。

**任何情况都不做**：

- 削弱 Product Invariants、凭据、预算、egress、permit 或真实验收（2026-10-30 用户授权的 `.env` 凭据来源修订见下文，不视为削弱）。
- 预算耗尽后绕过 guard、重置消费、改历史或无限执行；应先停 attempt、核对真实计数和结果，再有据封存下一有限单元并保留前序与新旧上限。
- unknown 时 retry 或 remint；应先取证或走显式 recovery。

修订 Gate/Harness 须说明观看体验收益，保留新旧规则及真实历史，不为过测试降低质量。

## Provider Credential and Paid Execution Rules

- **凭据**：只经注入 supplier 获取，来源依次为仓库根 `.env` 的 exact 变量、再 exact Secret Service reference（映射见 [Provider Details](.agent/context/control-plane-playbook.md#3-provider-credential-and-paid-execution-details)）；值不进 Git、prompt、argv、日志、错误或 receipt，Agent 不读取或回显 `.env`；两处都无值或 `.env` 无效即 fail closed，不找其他 secret 来源（不读进程环境、cwd 或其他文件）。2026-10-30 用户授权修订，旧规则为"只经 exact private reference，不进 repo/`.env`"；收益：配音/音频生成不再因缺 Secret Service 条目而阻断交片。
- **付费授权**：执行请求即默认授权任务内必要的付费/远程调用，自控有限次数与预算，不另要付费授权；完成时如实报告金额或积分，未结算标"待确认"。用户明确禁令与硬上限优先；文档或凭据本身不授权执行，不为授权查价或估账。
- **每次 submit 前**核对剩余次数、exact preview、Budget Guard/预留、egress、持久化 intent 和一次性 permit；金额字段只用预配置并封存的 operator 上限（不代表市场价），续期见[续期细则](.agent/context/control-plane-playbook.md#operator-ceiling-renewal)。

## Local ComfyUI Authorization Exemption

只连本机 loopback、完全本地且不计费、无云端 egress 的 ComfyUI 操作（生命周期、生成、修复、变体、benchmark）在任务内免额外授权；用户要求只读或禁止生成媒体时从用户。豁免只免授权，其余要求全部保留（exact identity/profile/preflight、canonical seam、intent、一次性 permit、唯一 committer、provenance、recovery、媒体 Gate），unknown 仍停止。

## Verification Contract

Harness 分级验证：修改后仅跑 `focused`（受影响模块精准测试），功能完成后跑 `related`（加关联模块与接口契约回归），合并或发布前跑 `full`（完整套件）；receipt 须标明级别，低级别通过不得说成完整回归。

入口见 [Verification Details](.agent/context/control-plane-playbook.md#4-verification-pilot-and-delivery-details)；必须用 exact staged snapshot 或 commit range 运行，并保留对应级别 receipt。缺精准映射时明确报告或升级，不悄悄扩跑，不刷新 baseline 掩盖 regression。

Harness 不拦截任意 tool/shell、不调度 Agent、不读 secret、不跑 live media、不改 Production、不代签 P6/Final Acceptance。CI 证据由 CI 自产，workflow 文件不证明服务端执行。离线 PASS 只证明被测行为，exit 0、`PARSED` 或 tests 通过不代替要求的 review 或真实验收。

证据分 execution、structure、function、criteria、final review 五层；`PASS/DONE/ACCEPTED` 须有对应证据，无法验证标 `NOT_EVALUATED`。

## Completion Standard

1. **记录**：稳定的实质节点、阻塞或交接前，用 `record-ai-video-session` 主动评估 record/no_record；仓库外效果也算，无 hook 提醒也要做。
2. **经验**：Record 后自动评估 `distill-ai-video-learning`，只提出 pending advisory claim；用户 exact confirmation 且目标 owner 验证前，不改 Skill/Policy/Gate，也不标 `ADOPTED`。
3. **提交**：所有修改（含文档、规则、配置）验证后 MUST 按本任务路径 commit；每次 commit 后 MUST push 到远端 `main` 并核对 SHA。失败或受阻要报告；禁止 force push 或夹带无关改动。
4. **汇报**：最终说明改了什么、实际验证、receipt 相对路径、发布状态和未验证风险。

<!-- aoci:begin -->
## AOCI-CODE 与 CodeGraph

跨模块修改、架构/影响分析、复杂 bug、重构、重要功能开发前读 [Cognition Tools](.agent/context/control-plane-playbook.md#cognition-tools)，按需 AOCI、CodeGraph 核对结构；源码/LSP/tests 才是事实。简单局部任务禁止机械调用 AOCI；其 cognition 永远仅 advisory，维护遵从项目 MCP 官方流程。
<!-- aoci:end -->
