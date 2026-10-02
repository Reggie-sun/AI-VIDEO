---
record_kind: architecture_implementation
topic_id: video-library-demand-loading
learning_eligibility: ineligible
---

# Video Library Demand Loading

Date: 2026-10-02

## Problem And Current Behavior

用户报告 `http://127.0.0.1:5174/` 视频加载缓慢。当前 catalog 有 192 个工作区；旧
`useLibraryData.refreshRuns` 启动三路完整 detail 遍历，同时自动请求全量
`media-context-index`、external catalog 和 SSE。真实浏览器观察到部分 detail 耗时
47.685s，thumbnail 请求等待约 12.65s 后取消。Strict reader 和完整证据关联需要的校验
不能靠削弱验证消除；默认浏览调度不应把整库读取放在播放之前。

`library-data.js` 仍独占临时调度，首批只读取最近六个工作区，detail 并发上限为二。
`library-load-contract.js` 提供 batch selection 和可取消的渐进读取。已加载工作区及用户
显式选择的旧记录保留在后续刷新范围；追加加载只读取缺失 detail。原 detail API、strict
reader、hash/token/file identity、排序、manual pin 和 Production 状态契约均保留。

UI 提供六个一批的“继续加载工作区”，生成记录仍列出整个 bounded catalog，点击旧工作区
时读取其详情。“关联全部 Runs 证据”由用户显式启动；未关联前仍经原
`attachRunsMediaIndex` fail-closed 投影，未知绑定保持 `NOT_EVALUATED`，不补造 Prompt
或生命周期。覆盖提示明确标注按需加载、不完整范围及不可用来源。

## Verification And Evidence

通过本机 Chrome DevTools MCP + 独立 headless Chrome 读取页面；没有关闭用户浏览器。
默认 MCP 遇到共享 profile 冲突，使用已安装 SDK 连接专用 loopback debug port。

- 真实页面：本轮已有 external catalog 缓存条件下，首批 12 张卡片在约 2076.9ms 出现，
  当前合并 624 段；六个 detail 请求、零个自动 index 请求。该时间不是冷启动性能承诺。
- 受控浏览器：192-workspace fixture 的初始 detail=6、peak=2、index=0；追加后
  detail=12、unique=12；直接打开 `run-100/project.yaml` 后只新增一次请求并展示详情；
  显式关联按钮触发 index=1。Fixture 不构成实际 Project/media acceptance。
- 真实播放：`/api/runs/media/ef7e4ae85c718e02c666b17fc8069d233a4ea0d5`，
  readyState=4、duration=15.083333s、videoWidth=1344，播放后 currentTime=0.872972；
  Chrome console 没有 error/warn。本检查不构成媒体质量、P6 或 Final Acceptance。
- 回归 tests 覆盖首批上限、旧记录选择、二路并发、渐进结果、失败及取消后禁止迟到更新。
  相关 Node suite 初次 Harness 为 102 passed，focused tests 为 16 passed；Vite build 通过。
- 最终 task-only commit-range proof 及 scope/policy/check/artifact hashes 以
  `.agent/harness/runs/video-loading-20261002-owned/receipt.json` 为准。初次 staged Harness
  含用户既有 staged `.codex/config.toml`，不作为 task-only scope 的最终凭据。

只读 Kimi 调查 invocation `e8498a99-78c0-40c6-88ca-d14aa28f0118`：qualified deep route、
Docker containment、四个 wire requests、六个 complete observed reads、terminal `PARSED`。
封存材料和调查结果在 `runs/video-library-loading-20261002/`；Parent 以 current source 和
浏览器证据裁决，仅采用调度修复，不采用额外 backend cache 或 transport rewrite 建议。
这次调用是调查，不能充当 final implementation review。

## Review And Boundaries

Risk Gate：`KIMI_REVIEW_NOT_REQUIRED`。本次只修改可逆的浏览调度与显示，保留 server、
canonical reader、token 校验和所有 mutation 边界；没有 critical credential/authority/
durable-state consequence，也没有验证后仍然存在的重大运行时语义缺口。最终 exact snapshot
由 task-only commit range 和 Harness receipt 绑定；Parent 负责最终 diff 与 completion。

剩余限制：external cold scan、用户主动读取的复杂旧工作区及全量关联仍可能耗时；未知或
不支持解码的原文件继续按既有逻辑报告，未新增转码或替换媒体。没有新增 dependency、
Provider/media generation、Manifest mutation、push 或 release。用户既有 staged config 保留。

AOCI Maintain 返回 `observed_pending`，本次 frontend paths 属于 observe 范围，未返回受管理
Entry candidates；另有其他会话文档待复核。没有全局 acknowledge 未拥有的路径，没有改写
索引，也不声明全仓 cognition aligned。CodeGraph 已索引并核对 `useLibraryData` 关系。

`record-ai-video-session` 已执行；`distill-ai-video-learning` 评估为 `no_candidate`：这是有界
工程调度修复，未形成符合 admission threshold 的跨媒体实验 Learning Claim。没有创建占位
claim、改变 Skill/Policy/Gate 或更新单独 RAG index。
