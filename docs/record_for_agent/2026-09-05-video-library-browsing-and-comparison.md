---
record_kind: architecture_implementation
topic_id: video-library-browsing-and-comparison
learning_eligibility: ineligible
---

# Video Library Browsing And Comparison Record

Date: 2026-09-05

## Scope And Implementation

用户明确要求实施 `docs/superpowers/specs/2026-09-05-ai-video-video-library-browsing-and-comparison.md`。
本次替换旧 workspace-first 浏览调度，保留既有诊断组件和本机 reader/transport。默认统一视频库
逐步加载 canonical Runs 与 allowlisted external 视频，按 SHA-256 + bytes 去重，保留全部角色
和上下文；来源筛选不再切换列表 owner。生成记录保留无媒体 attempt、失败和无 attempt 工作区。

`library-contract.js` 独占临时列表合并、筛选、排序与 strict version grouping；`library-data.js`
负责三路并发 detail 加载、request cancellation 与既有 media-context-index 的恢复旁证关联。
`library-browser.jsx` 提供首屏播放器、明确 pin、显式跟随最新和双视频比较；`library-preview.js`
只从 exact token 做本地缩略图/时长解码，最多两个 detached preview decoder，并释放离屏媒体。
卡片每页 12 项，不为整个媒体库保留 video elements。删除旧 `video-library-source-contract.js`；
`App.jsx` 只保留现有细节展示及轻量接入，不再拥有第二套来源/选中/刷新调度。

reader additive `candidate_media_items` 有界保留各 candidate，兼容原 `candidate_media`。
bridge 对坏哈希、缺文件与变更后的 descriptor 去除 token、标记 unavailable，并保留其他有效媒体。
刷新期间有效 cache 继续受原 `sendMedia` exact file identity 校验；重新验证完成后原子 replace
或失败 delete，不提前清空可用 token。没有新增 scanner、持久化 catalog、dependency、Provider
调用、媒体生成、Manifest/Registry mutation、自动 activation、push 或 release。

## Verification And Evidence

真实 local UI 使用已有 `127.0.0.1:5173`。Chrome MCP 因共享 profile 占用不能连接，采用独立
headless Chrome profile 与本机已安装的 Playwright/CDP 完成检查，没有关闭用户浏览器。

| Fixture | Exact SHA-256 | Bytes | Browser measurement |
| --- | --- | --- | --- |
| Greenhouse Mini / `director-seedance-mini-greenhouse-20260905-002` | `1c033786221ed269f4872be4d9fdef61ccc75b378d04095a044a0809df57b564` | 9746506 | 15.104s，1280×720，readyState=4 |
| Greenhouse 2.5 / `director-seedance25-greenhouse-20260905-001` | `26a38204acef51d48bfe92f0d337bfee885629932efedd788358c91367c8679a` | 40462083 | 30.080s，1280×720，readyState=4 |

两者均在默认来源中用 `greenhouse` 搜索找到，有 exact 缩略图；播放时间分别递增至 1.04774s /
1.039821s，media error 为 null；请求 `bytes=0-1023` 均为 HTTP 206 且 total bytes 与 identity 一致。
raw lifecycle 仍为 `running / validate`，显示等待验证，不升级为质量通过。

| Acceptance | Evidence and result |
| --- | --- |
| A1–A3 | 真实两个 fixture 的默认统一搜索、缩略图、顶部播放器、模型/实测时长及三维状态已检查。 |
| A4 | Pure contract tests + 浏览器受控 responses：同 bytes 合并两个上下文；不同 Project/Prompt 明示歧义，显式选择后才显示所选 Prompt。Registry 同 owner 角色不制造歧义，跨 owner 不任取标题。 |
| A5 | 真实双视频比较：默认均 muted；开启右侧声音后为 `[true,false]`；定位分别为 2s/10s，播放速度 `[1,1]`，loop 均 false；退出恢复 greenhouse 筛选与 2.5 exact 选中 identity。strict version tests 保持两个 Project 独立。 |
| A6 | 浏览器受控 no-attempt workspace 与 failed/no-media attempt 可从生成记录查看 Project/Shot 和 `FETCH_FAILED`；没有假视频卡片。 |
| A7 | 浏览器延迟 response 到达后 manual pin 保持；删除所选内容显示 unavailable，清空比较选择可恢复操作。真实 MP4 concurrent HEAD 复核为 200；新增回归测试曾 RED 404，修复后 GREEN。 |
| A8 | 受控 external 503 / truncated catalog 保留两段有效视频，同时标记覆盖不完整；保留 media-context-index 原有 incomplete/recovered evidence semantics。 |
| A9 | 真实大列表按 12 项分页，thumbnail 不使用常驻 card video；受控 browser 跟踪 detached decoder 峰值 2。390px 窄屏无水平内容溢出，播放器 343×192.94；Tab 到来源 select 有 solid focus outline。缩略图失败不禁用有效播放入口。 |
| A10 | 受控交互所有 API 请求均 GET，页面 JS errors 为空；本轮不调用生成、submit/retry/activate。原 Run 媒体只读，transport 失败路径沿既有 exact/no-follow/Range contract 测试。 |

本地可丢弃 browser reports/screenshots 位于
`.agent/harness/runs/video-library-browser-qa-20260905/`：`real-media.json`、
`controlled-interactions.json`、`comparison.png`、`mobile.png`。受控 response fixtures 仅进入
测试 browser，不写 repository `runs/`，也不是实际生成/质量 evidence。

Focused validation 已运行：Python reader tests 46 passed；library contract 9 passed；
library browser SSR/audio tests、transport stale/concurrent tests 通过；offline Vite build 通过。
Native `reviewer_xhigh` 完成 review，已报 blockers 均修复；其 SSR/交互覆盖 concern 已用上述
interactive evidence 补齐，snapshot mismatch fixture 已改为合法 SHA 并验证存在但不能归组。

首轮 Harness 的 9 项检查全部通过；其 reader LOC warning 通过简化本次新增的单用 helper 消除，
未调整 Architecture baseline。最终 exact commit-range 验证使用 `python -m scripts.agent_harness verify`；该检查的实际状态与
policy/check/artifact hashes 以 `.agent/harness/runs/video-library-browsing-20260905-final/receipt.json`
为准，不能由本 record 或上述 focused/browser results 代替。

## Boundaries And Learning Evaluation

实现和验证均为 local-only。历史 RAG 返回部分 stale last-good advisory fragments，仅用于找
既有 follow/preview 经验；实际结论来自 current code、tests 和本轮 browser。先前 follow record
已加 2026-09-05 supersession notice，保留旧故障 chronology。

此 checkpoint 是工程实现及 UI/transport 验收，没有独立的 model-quality experiment，也没有
足以提出或修改既有 Learning Claim 的跨实验证据。`distill-ai-video-learning` evaluation：
`no_candidate`。不创建占位 claim，不修改 Skill/Policy/Gate adoption target。

## Active Render Follow-up — 2026-09-05

用户报告 `director-h3-lighthouse-30s-20260905-001/final-production/state/render/outputs/`
下的 `3749b1e53c4fe674279b7bf50b8c496b67daa66428569e8f25c77d397c83bd38.mp4`
未出现在视频库。真实 API 证明 catalog 已发现该 workspace、strict detail 为 valid，但 detail
只有六段 Registry source-video，`attempts=[]`。根因为投影遗漏已经由 strict Project reader
验证的 `loaded.render_state.output`；此前 greenhouse 验证不能覆盖 render 成片入口。

本次新增有界只读 `provider_console_render.py`，消费严格重开后的 active render pointer，
复验 containment/no-follow、SHA/大小后才向原 transport `_media` 注册 opaque token。
`active_render_media` 为 additive projection；没有 active render 返回 null，恢复旁证不提供
render token，文件在重开后改变则保留无 token 的不可用 descriptor。不扫描历史 render 目录。
UI 保留 `active_render` 角色与“合成成片”标题，按 canonical render attempt 时间排序，
不借用源 Shot 的 Provider/model/Prompt/version。详情请求沿 catalog 顺序先读取最近更新的
workspace，避免 render-only 项目等所有 video-generation workspace 加载完才出现。

回归测试先在旧代码复现 Python `KeyError: active_render_media` 与 Node `1 != 2`，修复后
Python Console/index suite 53 passed、Node library contract 10 passed。Python fixture 经
canonical fake-render lifecycle 和标准 Project loader 重开，确认只读、无 video attempt 仍可
浏览，等长篡改阻断 strict 输出，recovered reader 不泄漏 render token。Native
`reviewer_xhigh` verdict `accept`，无 blocking/non-blocking findings。

本轮 Chrome DevTools MCP 在真实 `http://127.0.0.1:5173/` 验证：默认全来源中成片位于首项，
完整 MP4 文件名搜索命中一项；标题 `The Lighthouse Awakens — 30 seconds · 合成成片`，
缩略图有效。Exact SHA 如上、18956501 bytes、实测 30.000s / 1344×768、readyState=4，
播放时间从 0 增至 1.111593s，media error=null；Range `bytes=0-1023` 返回 206/1024 bytes，
Content-Range `bytes 0-1023/18956501`，页面 error/warn 为空。

Staged Harness 九项全部通过，Architecture Gate 零 warning；实现 commit `2819582`。
最终 exact commit-range Harness receipt：
`.agent/harness/runs/video-library-active-render-20260905-final/receipt.json`；完成状态以该 receipt
及 freshness verifier 为准。本次仅修复读取/浏览，未生成或复制媒体、未修改 Production state，
未 push/release，不对媒体质量作新验收。Learning evaluation：`no_candidate`；单个工程缺陷
及回归/播放验证不构成独立 model-quality experiments。

本轮不证明媒体感知质量、P6、Final Acceptance、activation、remote availability 或 publication。
扫描仍受原 catalog/reader allowlist 与数量限制；stale、truncated、恢复旁证及来源失败明确可见。
