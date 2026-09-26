---
record_kind: architecture_implementation
topic_id: video-mcp-generic-context-routing
learning_eligibility: ineligible
---

# Video MCP Generic Context Routing Record

Date: 2026-09-27

## Supersession Notice — 2026-09-27

下文 AOCI Governance Gap 已由[索引维护记录](2026-09-27-aoci-index-maintenance.md)
接替：7 个 stale entries 和 50 个 observed pending 已完成复核与官方维护，
Verify / Check / Guide 证明治理对齐。原 VideoMCP 能力与验收限制仍有效。

## Scope And Current Runtime Truth

用户提供 `https://github.com/EthanBobbyTR/VideoMCP.git`，明确了 [convergence plan](../superpowers/plans/2026-09-26-video-mcp-convergence.md) 的目标身份。该指令 supersede 先前对同一 repository 的排除，不再需要另一个 `video-context-mcp` 启动配置。实际服务名仍是 `video-mcp`，没有新增 alias。

本机已经存在 clean source checkout `/home/reggie/vscode_folder/MCP/VideoMCP`，commit `e01b745ba3f0efdd667d4886f39eef16c10271a7`，executable `/home/reggie/.local/share/video-mcp/venv/bin/video-mcp`。本轮复用安装，未更新上游源码/依赖，没有新建第二环境。Codex 现有用户级配置保持；project `.mcp.json` 新增同一服务供 Claude Code 加载，保留原 `video-analysis`。Claude launch command 用既有 `/usr/bin/env --chdir` 固定安装目录，无新增 wrapper 文件。客户端重连后加载更新；本轮真实 stdio 与 actual Claude CLI 均已验证，不等于已重启当前 UI session。

`README.md` 与 playbook 明确普通 visual overview 优先使用 `process_video` 的 native text/image context。strict count、精确时间/probe、language/ASR controls、逐 Shot Gate、生成反馈、typed evidence、Production QA/permit/hash、continuity/captions 与 committer/replay 继续原 seam。全部八个原 public tools 和共享 core 保留，删除集为空，没有 caller migration、wrapper、schema migration、Provider selector 或第二 owner。

Skill 中现有 `video-analysis` 引用属于 per-Shot Gate，复核后保持；没有 retired identifier/path，故无需让原 identifier 在全仓零出现。当前使用说明已按职责路由，历史 plan/record 保留明确 supersession。

## Measured Replacement Coverage And Limits

- 基于当前源码和真实 `list_tools` 确认两工具：`process_video`、`list_processed_videos`。处理参数包括 `video_path`、整数秒 `frame_interval`、`whisper_model`、`max_frames`、`use_scene_detection`、`scene_threshold`；没有独立 probe/scene-list、ASR disable/language/word timing 或逐调用 width/quality/format。
- 四秒无音轨 synthetic hard-cut fixture 返回 basic metadata、四张 fixed-interval JPEG、两张 scene JPEG、秒级时间标签，图片实际解码；重复请求返回 cache-hit header 和相同图片，listing 可找到该 fixture，source bytes 不变。MCP metadata 中的 version `3.4.7` 不当作 source commit。
- cache key 只用 first-1MB MD5 + file size 与部分设置，忽略 `max_frames`、format/quality 等。实测同一视频从 `max_frames=4` 改为 `1` 仍返回 cached 四张图片。不能把该参数当 hard resource ceiling；严格数量或 fresh exact-byte 用途直接选择原服务。
- missing-file 返回错误文字，`isError=false`；消费者必须检查 text/error/failed-image placeholder，不能以 tool success 放行。它没有 Production exact-bytes、permit、replay 或 acceptance authority，不参加原跨进程 worker lock。
- no-audio fixture 的 transcript 路径是正常跳过。真实 ASR 识别、OCR、word timing、完整相邻帧 coverage、动作/semantic continuity 均未验证。本轮无 model load/download，没有上传用户媒体或媒体 Provider submit；这些 gaps 不用于证明完全替代。

## Verification And Evidence

| Evidence | Result / binding |
| --- | --- |
| 上游 isolated environment compatibility | `uv pip check --python .../venv/bin/python`：104 packages compatible；该环境没有 pip module，使用既有 uv 检查，不安装 pip |
| 上游 tests | isolated Python，`7 passed`；源码 checkout 保持 clean |
| Codex registration stdio smoke | `.agent/harness/runs/video-mcp-convergence-live-20260927/smoke.json`，SHA-256 `b637bd489f7c56b328e12623d5ec9269e5bfa6f6aa5738cf9d882053dc12e3a1` |
| 最终 Claude project registration stdio smoke | `.agent/harness/runs/video-mcp-convergence-client-native-20260927/smoke.json`，SHA-256 `ded79bb7faa66ba583e30cd8b464cb046740e83a0276666b68b9b38595c44226`；以 repo cwd 启动 raw command/args，实际 child 由 `env --chdir` 定位 |
| 实际 Claude client discovery | repo root 执行 `claude mcp get video-mcp`：`Scope: Project config (shared via .mcp.json)` / `Status: Connected` |
| 原 `video-analysis` stdio evidence | `.agent/harness/runs/video-mcp-audit-smoke-20260927/smoke.json`；八工具、probe、图片、analysis、legacy review、no-audio/missing-file；未冒充 Production permit review |
| MCP / feedback / generation evaluation / quality rejection / Production review / quality gate / continuity / captions / visual report 回归 | `279 passed, 1 skipped`；使用本轮 known working tree，原服务 source 未修改 |
| open-video / seedance-authoring / Claude adapter 回归 | `61 passed` |
| 唯一测试修正 | `tests/test_mcp_analyze.py` 按 exact analysis command 筛选 Claude registration，继续要求唯一 analysis hook 与原 matcher/timeout/command；原已复现 FAIL 的 test 与原 MCP config test 变为 `2 passed` |

上述真实调用只使用临时 synthetic/test fixture，cache 通过进程 env override 放在同一 temporary directory，结束后清理；不触碰用户已有缓存。首轮 smoke 的 missing-file 断言假定大写 `Error` 而失败，检查实际 lowercase `error` 返回后修正验证脚本并重新运行完整 smoke；没有改上游错误行为。

初始 Claude `.mcp.json` 写入 JSON `cwd`，Python stdio client 显式应用该字段后 smoke 通过（历史 artifact `.agent/harness/runs/video-mcp-convergence-client-20260927/smoke.json`），但 actual `claude mcp get` 返回 `Failed to connect`。当前 Claude 忽略该字段，上游会在 repo cwd 读取 `.env`；没有读取/打印其中值。改用 `command=/usr/bin/env` 和 `--chdir=<install>` 参数后，从 repo cwd 完整重跑 smoke、actual client discovery 均通过。此例说明手工施加 client 不支持的启动字段会掩盖真实接入失败，不能把初始 stdio PASS 当 Claude integrated proof。

Stable delta 的 mandatory checks 以 `.agent/harness/runs/video-mcp-convergence-routing-20260927/receipt.json` 的 exact commit-range、policy、artifact hash 与 freshness 为准；本记录不是 receipt，也不预判执行结果。使用干净临时 clone 验证，不创建 dedicated worktree，不修改 Harness 放行。

## Delegation And Parent Decision

`external-subagent` read-only explorer invocation `76562593-b9e4-4d45-8575-db6503c472fc`：Docker containment、qualified `worker` route；两次 authenticated `k3-256k` / high / adaptive requests，canonical receipt 为 `PARSED`，source Reads 覆盖 exact `server.py` / `cache.py`，有 worker report。Parent 已从当前源码及实际 smoke 核对 partial identity/cache-key 和 text-error 限制；报告中其他潜在问题不扩展为上游修复。调查不是 final implementation review，`PARSED` 不是 acceptance。

Final Review Risk Gate decision：`KIMI_REVIEW_NOT_REQUIRED`。候选只有可逆客户端 registration、advisory tool routing、证据矩阵/records 与 hook-selection test；没有 credential/authority/durable-state 或 QA acceptance mutation。硬帧数/freshness 用途保持原 seam，真实两客户端 smoke 与 native tests覆盖此次改动，未发现重大后果兼实质验证缺口。Exact candidate identity 由最终 Harness `scope.head_oid` 绑定。T2/T3 shared-contract review 未触发，不另叠加 reviewer。

## AOCI Governance Gap

受管理 `README.md` 稳定后按当前 `aoci_rules` 做一次 `aoci_maintain`。MCP `0.1.0-rc14` 返回 `status=stopped` / `result=blocked` / `aligned=false` / `candidates=[]`；报告 7 个 stale indexed objects 和 50 个 observed pending reviews。除 README 外，stale 对象为已有 policy、AGENTS、matrix、baseline、roadmap 与 ecommerce execution source，不属于本次业务修改。没有 semantic generation、pending transaction、Recovery 或 third-party conflict，也没有正式 asset write。

机器要求先处理 repository scope 的 pending review，未签发可提交批次。本次没有盲目 acknowledge 全部未审对象、缩小 batch、修复 unrelated source 或重写正式认知；保留既有治理 gap，不声明 AOCI aligned 或完整系统认知。此停点不替代本任务源码、实际 client 与 Harness 验证，也不是 VideoMCP 接入失败。

## Publication And Learning Boundary

仅提交 task-owned `.mcp.json`、README/playbook、plan、hook-selection test、primary record 与直接 supersession notices。原 `.codex/config.toml` 的 AOCI dirty work 保持，不 stage/commit；不 push/release。没有 Production state、activation、QA/human acceptance 或新媒体 Provider 效应；受管 Kimi investigation 的 upstream requests 单独记录如上。

本轮 `retrieve-ai-video-memory` 的 experience 检索返回 `[]`，并报告 stale shard 自动排队 refresh；不等待/重试或前台 rebuild。`distill-ai-video-learning` evaluation：`no_candidate`。这是单一安装/工程兼容性与缓存控制验证，不是独立模型质量实验或足以更新既有 Learning Claim 的证据；不创建 placeholder 或改变 adopted rules。
