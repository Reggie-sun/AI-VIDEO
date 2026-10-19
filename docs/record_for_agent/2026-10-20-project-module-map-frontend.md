# Project Module Map Frontend

Date: 2026-10-20

## Outcome

用户要求把项目各模块的职责说明输出为 HTML，并能在现有前端清楚查看。
已提供独立、无外部依赖的模块说明页，并接入 Provider Console 侧栏。
这是基于源码的说明快照，不投影项目、Shot、attempt 的实时状态或质量结论。

## Implementation

- [project-modules.html](../../provider-console/src/project-modules.html)：26 个功能模块、3 条职责泳道、7 步可点击流程；支持模块/职责/源码路径搜索、分类、空结果恢复、详情弹窗、键盘关闭和打印。
- [App.jsx](../../provider-console/src/App.jsx)：侧栏“项目模块”链接进入 `/src/project-modules.html`。
- [vite.config.mjs](../../provider-console/vite.config.mjs)：保留现有入口，增加 HTML 构建入口，产物位于 `dist/client/src/project-modules.html`。
- HTML 内联 CSS 和普通 JavaScript；可经前端 HTTP 或 `file://` 打开。离线打开时禁用站内返回链接。
- 人物表演参数、模型生成、确定性剪辑、素材绑定与实际验收分别说明；不把输入表达升级为模型遵从或人工接受。

## Verification

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

## Boundaries And Review

- 本次无 Provider、图片、视频或音频生成，无凭据读取，无 Production state 修改；原有 Shot 的 Gate 不变。
- `NATIVE_REVIEW_NOT_REQUIRED`：改动限静态说明页、导航链接与构建入口，未触及授权或持久状态；Parent 已检查最终差异、真实浏览器交互和适用 Harness。
- 未新增依赖、renderer、timeline 或状态 owner；保留全部 foreign dirty/staged 文件，源码提交后 foreign staged patch hash 保持一致。
- 页面需要在模块职责变化后按当前源码更新；当前模块说明不证明任意模型的输出质量。

## Learning Evaluation

已按 `distill-ai-video-learning` 评估：`no_candidate`。本次为单次说明页工程与浏览器验证，未产生新的独立媒体实验或受控比较，不创建 Learning Claim，不修改 Skill、Policy 或 Gate。
