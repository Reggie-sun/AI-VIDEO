# Project Module Map Frontend

Date: 2026-10-20

## Current Revision — Feedback, Relationships And Evidence

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
