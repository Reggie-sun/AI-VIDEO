---
record_kind: session_summary
topic_id: video-library-open-folder
learning_eligibility: ineligible
---

# Video Library Open Folder Record

Date: 2026-10-06

## Current Runtime Truth

视频库右侧预览标题旁新增“打开所在文件夹”。按钮绑定当前 `entry.url` 的既有 opaque
video token，支持 Runs 与 External Media；不可用文件禁用按钮，切换视频清除旧操作提示。
打开目录不改变播放地址、媒体 bytes、Project、Registry、Manifest 或质量裁决。
Implementation commit：`049397b`。

本机桥接仅接受 loopback、same-origin、专用 action header 的 POST；拒绝 arbitrary
path/root、未知 token、文件替换、symlink 与跨站请求。返回内容不包含 absolute path
或 desktop stderr。新职责位于 `provider-console/scripts/media-folder.mjs`，原
`runs-api.mjs` 沿用唯一已登记媒体 cache，没有新增 catalog。

## Verification And Evidence

- exact staged tree：`06cf26913b8fc3f16cb2a6cec011b0f48374ebb9`。
- Harness receipt：`.agent/harness/runs/video-library-open-folder-20261006/receipt.json`；
  11 个 required checks 通过，commit 前核验 `fresh_for_snapshot`、`snapshot_matches`、
  `complete_completion_proof` 均为 true。包含 103 项 Node tests、53 项 Python Console
  tests、275 项 Harness tests、44 项 rule invariants、Architecture Gate 与 Vite build。
- Chrome DevTools MCP 主连接因共享 profile 占用不可用；改用已安装的
  `chrome-devtools` CLI，同一 MCP engine 完成本机 integrated QA，没有关闭他人的 Chrome。
  自启 `127.0.0.1:5175` 服务及现有 `127.0.0.1:5174` 服务均实际点击验证。
  所选 12.500s 成片点击返回“已请求打开所在文件夹”，播放器 token 保持不变；
  切换至另一视频后 token 改变且旧 notice 清空。无 Browser console errors。
- 初次 `xdg-open` 实点失败：Agent 启动环境无 DISPLAY / desktop bus。用本机已安装
  GIO 与当前 UID 的标准 session bus 完成 desktop activation；缺少 desktop service
  时仍返回 sanitized failure，不能把请求成功解释为媒体质量或 Final Acceptance。

## Review And Learning Evaluation

稳定 implementation snapshot 按 `SUBAGENTS.md` 判为 `KIMI_REVIEW_NOT_REQUIRED`：
用户未指定 final reviewer；新入口无 Provider/credential/Production-state mutation；
主要失败结果为目录打不开，token、origin、containment、stale identity 与 error paths
已有 executable coverage 和本机点击证据，没有重大后果加实质验证缺口的组合。
Parent 完成最终 diff 裁决；独立只读 mapping invocation 与 final review 不混为一层。

受管 Kimi mapping：`265f41c6-dae5-4c89-b2aa-1d70618bca71`，sealed pre-change
source copies、Docker read-only、requested `deep/k3[1m]/max`，4 次 authenticated
`k3` wire requests，canonical receipt 为 `PARSED`。实际 Read evidence 完整；
Parent 核对 per-click identity 与 cross-origin 建议已由实现和 tests 覆盖，并从当前
Python/External token derivation 确认 token 绑定 content hash。未新增 catalog、
平台泛化或 rate-limit；额外目录检查不能消除 desktop pathname opener 的竞态。
残余本机恶意 rename race 不由 pathname desktop opener 消除；没有向 Browser
返回路径或文件内容，也不把 mapping transport 成功当成 implementation acceptance。

`record-ai-video-session` outcome 为 `recorded`；`distill-ai-video-learning` 为
`no_candidate`。本次是单项 UI implementation，缺少独立实验/对照或既有 claim 更新，
不创建 Learning Claim，不修改 Skill、媒体 Gate 或 RAG index。

## Remaining Boundaries

本机 desktop integration 依赖 Linux GIO / session bus。Browser QA 证明本机入口与选中
文件绑定；没有生成/修改媒体，不证明成片质量、Production activation 或云端部署。
