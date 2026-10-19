---
record_kind: architecture_implementation
topic_id: project-module-map
learning_eligibility: ineligible
---

# Project Module Map Frontend

Date: 2026-10-20

## Current Revision — Verified Evidence And Delivery Boundaries

用户继续指出静态 `maturityFor()` 缺乏可核实的证明、工程模块误用媒体未评估、固定坐标图不适合手机，并要求首屏直接说明端到端制作能力的实际证据。以下取代旧版当前结论；旧实现与证明保留在 Historical Revision。

- 页面已删除 `maturityFor()` / `proofRefs` 的静态 verdict，自动 GET 既有 loopback `/api/runs/module-evidence`，支持无缓存刷新；HTTP 失败、错误 schema、刷新期间及 `file://` 均不保留旧 PASS，也不嵌入 build-time evidence fallback。
- `scripts/provider_console_evidence.py` 按 catalog 中有限的 26 个模块、5 份历史 receipt，核验现有 seal/artifact verifier、实际文件 SHA/bytes、Git ancestor/changed paths 与源码 anchor；详情展示 actual receipt file hash、base/head commit、check ID 和 stdout/stderr/JUnit 身份。不是实时 CI 执行器，页面不运行测试；anchor 一致不代表完整依赖或当前行为验证。
- 当前读取为 21 个模块各有已核验的相关历史工程结果、5 个没有已登记的相关行为结果；这不是 21 个模块的完整资格证明。状态提交、预算和依赖等工程模块的媒体/人工维度为 N/A；人物表演、参考控制和连续性仍是媒体效果相关，保持未评估，不因参数已接线消除质量缺口。
- `scripts/provider_console_cases.py` 只读取四组预先选定的 MP4/证明束；验证 exact SHA/bytes、recognized JSON fields 与 artifact binding 后才报告结论。缺失、变化、错绑或不支持均降级 unavailable；不递归加载巨大历史 Project，也不裸解析 Manifest 推导当前 lifecycle。
- 首屏明确“从剧本到合格最终交付，所审案例尚无完整证明”，自主度未测量；这是一组有界案例审计，不是全历史搜索或成功率统计。视频身份、QA/human 证明可展开查看，未把旁证变成 Production qualification。
- 原五视图保留；三张关系图改为响应式节点与语义边，聚焦一跳上下游、淡化无关节点、恢复全图与模块详情分别操作。技术符号独占可读行，不再以 1120px 图整体横向滚动；源码导航的重复前缀已修正，19 个具体源码入口实际存在。

| Exact Case | Verified Boundary |
| --- | --- |
| 界蚀 S01 raw，`4c9589…c957f` | 5 PASS / 1 FAIL / 9 NOT_EVALUATED；完整 1× 人工听看未评估，表演自然度未建立完整验收 |
| 界蚀清理剪辑预览，`f98e2c…f4a47` | 有限画面复核；无完整 1× 人工接受或 Production qualification；不虚构逐项 QA 计数 |
| 机器人声画剪辑预览，`173cd9…2ca5c9` | exact-bound 用户记录报告完整 1× 听看接受动作、最后转向和声音；开发预览，未写入 Product QA/activation |
| Seedance 白模迁移，`127b43…fc674` | exact-bound 逐镜 Gate 8 PASS、历史 activation report；未建立完整人工听看或最终交付证明，不声称全项目从未有过镜头激活 |

### Current Verification And Publication

源码发布点 `51c3d5a6cfe5e944596e93b0d6a81a8a10a5e58c`，已 push 并核验 remote `main`。HTML SHA-256：`79fa94daed8a191ff6992c8666b417a73d9685bb2c861f12f6f3a4c9f4beea73`。

| Evidence | Result |
| --- | --- |
| 新只读投影定向测试 | 20 passed；sealed receipt、损坏/缺失、错误 check/commit range、源码变化、N/A、case 错绑、path/symlink 与无写入/网络边界 |
| Node API 定向测试 | 3 passed；loopback GET、禁止客户端路径/其他方法、每次重新读取、sanitized failure、固定 Python argv/有限输出及最小环境 |
| Chrome MCP，1440px / 375px | 五视图、节点聚焦/恢复、源码导航、receipt/commit/artifact 详情、26 行分类、未证表演、QA/human exact binding、键盘切换、搜索通过；页面无横向溢出，手机节点 317px、详情 337px |
| Chrome MCP，失败与离线 | HTTP 503 / unsupported schema 清空旧案例和成熟度；loading 不复用旧详情；`file://` 保留静态说明、禁用数据刷新与站内返回，无 resource requests；不代填证据 |
| 完整源码范围 Harness | 11/11 checks PASS，含 75 个 Provider Console Python tests、Node suite、307 个 Harness tests、Architecture Gate 0 finding 与 offline client build |

最终工程 receipt：`.agent/harness/runs/module-map-runtime-evidence-20261020-r4/receipt.json`。在上述发布点已核验 integrity、artifact_integrity、freshness、complete_completion_proof 全为 true；不是 CI server enforcement 或媒体质量证明。早期 r1 因新增测试 EOF 空行被 diff check 拒绝，已修复；r2/r3 为后续修订前的历史检查，不替代最终 r4。
浏览器证明：`.agent/harness/runs/module-map-runtime-browser-20261020/browser-proof.json`，绑定上述源码提交与 HTML hash。`npm run build` 与最终 exact client compile 均通过；本次不是 Sites 发布。

`NATIVE_REVIEW_NOT_REQUIRED`：最终候选限本机只读开发证据与说明展示，没有生产状态/授权写路径或任意客户端 filesystem root；相关身份、拒绝、失败和真实前端路径已执行验证，Parent 完成最终 diff 与证据语义核对。Native workers 分别负责隔离的投影、案例与 HTML，read-only mapper 核对历史媒体；这些工作不冒称独立审查或新的媒体验收。
本窗口无 Provider、图片/视频/音频生成或凭据读取。并行窗口的 `9caba91` 只作源码基点，3D references 不是本任务产物；全部 foreign dirty/untracked 保留。
已按 `record-ai-video-session` 更新本主记录，并自动评估 `distill-ai-video-learning` 为 `no_candidate`：这是工程证据与 UI 改进，没有新增独立模型实验，不创建 Learning Claim 或修改质量 Gate；全局 memory 未写入，未手动重建 RAG。

## Historical Revision — Feedback, Relationships And Evidence

用户指出线性主链无法表达制作反馈，并要求区分模块职责、调用/数据关系、状态所有权、失败传播以及能力成熟度。
当前页面已以五个视图取代七步线性主链，原有 26 模块搜索和详情保留：

- `反馈闭环`：检查 → 失败分析 → Agent 修改方案 → 重选策略/编译/有界生成；另画既有素材复用、局部编辑、补证和停止分支。未知结果是终止分支，不画成自动重试。
- `调用与依赖`：14 条主路径关系，区分调用链、数据依赖与显式操作，附源码位置；部分边折叠中间函数，明确不是完整 import graph。
- `状态所有权`：唯一 durable writer 与 Manifest/Registry/reader 的读写方向图，加六类语义 owner；ResolvedTimeline 和 Dependency Resolver 的唯一职责保持。
- `失败传播`：准备缺口、UNKNOWN、缺证据、质量失败、运行失败、上游失效六种路径，分别显示阻断点与恢复条件。
- `能力成熟度`：26 行、各四层独立证据；源码实现、工程测试、真实媒体与人工接受分开。不以测试文件存在标 PASS，不以历史 receipt 冒充当前全范围资格。

三张图共 33 条边；图节点与模块详情相连，详情补充关系与四层证明。人物表演保留“历史工程 PASS / 真实效果未证实”，机器人完整听看接受只绑定 exact 开发剪辑版；其原片失败、未 qualification/activation 和跨场景未证边界保持。
`provider-console/AGENTS.md` 仅新增一句持久展示原则，没有改动 Production 契约或增加状态 owner。

源码发布点：`893fe164b62f9b836d639bdb8b3e7fc4ddce32f3`，已 push 并核验 remote `main`。
HTML SHA-256：`99cea4c2037de7e9326b8de25cae31fb9de9f96ee37b77932eceff9e3966e97a`。

| Current Evidence | Result |
| --- | --- |
| 结构与脚本检查 | 内联 JavaScript 语法有效；边端点、模块绑定和源码入口存在；check 可回到 plan，UNKNOWN stop 无出边；26模块各四层证据 |
| Chrome MCP，1440px | 五视图互斥切换、三类边、六类owner/失败路径、成熟度分层与限定人审、详情、旧搜索正常；无横向页面溢出 |
| Chrome MCP，键盘 | tablist 的 End/Home 正确选中并聚焦末/首视图 |
| Chrome MCP，375px | 五视图页面均无横向溢出；图与表格在独立区域内滚动，右侧节点可达；详情及长证据路径在弹窗内 |
| 构建 HTML 的 `file://` | 五视图、图节点详情和四层证据正常；无外部脚本/样式，返回链接正确禁用 |
| 构建与 exact Harness | `npm run build`通过；8/8 checks通过，含106个原有Node测试与Architecture Gate；integrity/freshness/complete_completion_proof已在源码发布点核验 |

工程 receipt：`.agent/harness/runs/module-map-relations-20261020-r1/receipt.json`。
当前浏览器证明：`.agent/harness/runs/module-map-relations-browser-20261020/browser-proof.json`，绑定上述 HTML hash；HTTP 页面无 error/warn。
本次没有运行媒体生成、Provider、凭据读取或 Production mutation；没有为成熟度填色而重跑全部制作测试或升级历史质量结论。
两个 native `code_mapper` 仅做只读来源核对，未执行测试；Parent 负责实现与浏览器验证。
`NATIVE_REVIEW_NOT_REQUIRED`：候选限只读说明页和展示原则，未改生产状态、授权或实际调用；源码/证据对应及交互已核验。
并行窗口提交的 `d24741f` 仅作为本次源码基点，未接管其 Blender Skill 或其他 foreign 文件；剩余 unrelated dirty/untracked 保留。

## Initial Outcome

用户要求把项目各模块的职责说明输出为 HTML，并能在现有前端清楚查看。
已提供独立、无外部依赖的模块说明页，并接入 Provider Console 侧栏。
这是基于源码的说明快照，不投影项目、Shot、attempt 的实时状态或质量结论。

## Initial Implementation

- [project-modules.html](../../provider-console/src/project-modules.html)：26 个功能模块、3 条职责泳道、7 步可点击流程；支持模块/职责/源码路径搜索、分类、空结果恢复、详情弹窗、键盘关闭和打印。
- [App.jsx](../../provider-console/src/App.jsx)：侧栏“项目模块”链接进入 `/src/project-modules.html`。
- [vite.config.mjs](../../provider-console/vite.config.mjs)：保留现有入口，增加 HTML 构建入口，产物位于 `dist/client/src/project-modules.html`。
- HTML 内联 CSS 和普通 JavaScript；可经前端 HTTP 或 `file://` 打开。离线打开时禁用站内返回链接。
- 人物表演参数、模型生成、确定性剪辑、素材绑定与实际验收分别说明；不把输入表达升级为模型遵从或人工接受。

## Initial Verification

源码发布点：`a93cd08b9b5eefa292452ad121cd9e0fbea22589`，已 push 并核验 remote `main`。
HTML SHA-256：`102cc480d597104b4096495605f0971a8b2db366d17e4d373360800a29dc9ee6`。

| Evidence | Result |
| --- | --- |
| Chrome MCP，现有前端侧栏实际导航 | 打开 exact HTML URL，26 个模块可见 |
| Chrome MCP，1440px 桌面交互 | 搜索、清除、分类、空结果重置、源码路径检索、流程按钮与详情关闭通过，无横向溢出 |
| Chrome MCP，键盘 | 表演详情可打开，Escape 关闭并恢复卡片焦点 |
| Chrome MCP，375px 手机布局 | 单列卡片、26 模块可达、页面无横向溢出；337px 详情弹窗及关闭按钮留在视口内 |
| 源 HTML 与构建 HTML 的 `file://` 实际打开 | 渲染、搜索或详情交互通过；未加载外部脚本与样式 |
| 内联脚本及源码索引 | JavaScript 语法有效；83 个源码路径条目均存在，模块 ID 无重复，脚本无网络调用 |
| `npm run build`、相关原有测试 | 构建通过；library-browser 3 项、Sites 5 项通过 |
| exact commit-range Harness | 10/10 checks 通过；receipt integrity、freshness、complete completion proof 均已在源码发布点核验 |

工程 receipt：`.agent/harness/runs/module-map-ui-20261020-r1/receipt.json`。
浏览器观察保存于 `.agent/harness/runs/module-map-ui-browser-20261020/browser-proof.json`，不构成媒体验收。
Chrome 的 `file://` 页面出现文件 origin 的 self-URL 诊断，核心交互通过且 resource entries 为空；HTTP 前端页面无 error/warn。
Node suite 保留 Vite 测试服务器关闭期间的 dependency-scan 诊断，106 个测试通过；未据此修改无关运行路径。

## Initial Boundaries And Review

- 本次无 Provider、图片、视频或音频生成，无凭据读取，无 Production state 修改；原有 Shot 的 Gate 不变。
- `NATIVE_REVIEW_NOT_REQUIRED`：改动限静态说明页、导航链接与构建入口，未触及授权或持久状态；Parent 已检查最终差异、真实浏览器交互和适用 Harness。
- 未新增依赖、renderer、timeline 或状态 owner；保留全部 foreign dirty/staged 文件，源码提交后 foreign staged patch hash 保持一致。
- 页面需要在模块职责变化后按当前源码更新；当前模块说明不证明任意模型的输出质量。

## Learning Evaluation

初版及本次修订均已按 `distill-ai-video-learning` 评估：`no_candidate`。工作属于说明页工程与浏览器验证，引用已有媒体证据但未产生新的独立媒体实验或受控比较，不创建 Learning Claim，不据此修改 Skill、Policy 或 Gate。前端展示原则来自用户本次明确反馈，不是经验候选自动采纳。
