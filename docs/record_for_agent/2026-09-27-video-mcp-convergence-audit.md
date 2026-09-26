---
record_kind: session_summary
topic_id: video-mcp-convergence-audit
learning_eligibility: ineligible
---

# Video MCP Convergence Audit Record

Date: 2026-09-27

## Supersession Notice — 2026-09-27

用户随后提供准确 repository `https://github.com/EthanBobbyTR/VideoMCP.git`，解除下文 target identity blocker；实际注册名为 `video-mcp`。已完成适用通用 visual-context 路由与 project-client 接入，原 hook-selection 测试不一致已修正，相关组合 `279 passed, 1 skipped`。当前结果见 [routing record](2026-09-27-video-mcp-convergence-routing.md)。下文保留早先 blocked checkpoint 的调查与失败证据；ASR/完全等价能力仍未验证，无 public tool/core 删除。

## Scope And Status

执行 [Video MCP Convergence Plan](../superpowers/plans/2026-09-26-video-mcp-convergence.md) 的现有能力审计与本地验证。原 plan 由用户本轮要求实施；不是 schema migration、Provider/media Production submit 或 QA acceptance 授权。Milestone 1 的原服务审计已完成，替代 identity/coverage blocked；Milestone 2/3 未完成，不声称收敛实现完成。

Source checkpoint：`7fa6dbd`。本轮 task-owned changes 仅本记录与 plan 的 Execution Checkpoint。原 `.codex/config.toml` AOCI 改动保持原样，不 stage/commit；source、tests、MCP 配置、Skills、QA/evidence/public catalog 均未修改。只创建临时 synthetic fixture 与本地 derived smoke evidence，没有生成 Production Shot、上传媒体、下载模型、改变 Manifest/Registry、activation、P6 或 Final Acceptance；不 push/release。

## Identity And Consumer Evidence

读取用户指定 session `01a0de3d-d9f4-7ef3-9d2a-0e13d462005d`：历史安装目标是 `https://github.com/EthanBobbyTR/VideoMCP.git`，注册名 `video-mcp`。后续用户明确另一个 MCP 才是替代目标；所给 `src/ai_video_mcp` 是原 `video-analysis`。该 session 最终 plan 也保留 identity 未解决这一前置条件，不能拿历史安装 smoke 冒充替代验证。

本轮检查 project `.codex/config.toml` / `.mcp.json`、用户级 `.codex/config.toml`、`.claude.json` / `.claude/.mcp.json`、Claude Desktop 配置与 `vscode_folder/MCP` 安装目录。未找到目标服务的有效启动配置；此结论仅针对已检查位置，不是全机器不存在的证明。

| Retained path / symbol | Current consumer and reason |
| --- | --- |
| `tools/probe.py::video_probe` | `tools/analyze.py`、`frames.py`、`scene_detect.py`、`transcribe.py` 与公开 wrapper；存在共享实现依赖 |
| `tools/frames.py::video_extract_frames` | `tools/analyze.py`、公开 wrapper；未完成替代 schema/smoke 对照 |
| `tools/scene_detect.py::video_scene_detect` | `tools/analyze.py`、公开 wrapper；仍是 analysis/hook observations 来源 |
| `tools/transcribe.py::video_transcribe` | `tools/analyze.py`、公开 wrapper；ASR 等价性未测 |
| `tools/analyze.py::video_analyze` | `tools/review.py` legacy 分支、`analysis_hook.py`、server wrapper；反馈 stdio 与 `GenerationAnalysisEvidence` 要求原 schema/tool identity |
| `tools/review.py::video_review` | legacy review 和独立 Production permit/hash/frame-window 分支；公开 MCP wrapper 未暴露 Production permit |
| `serialization.py` / `analysis_hook.py` | 跨进程串行、取消、只读 snapshot、hash/profile 与 advisory boundary；非可证明冗余 |

表内 `tools/*`、hook、server 路径均相对 `src/ai_video_mcp/`。`src/ai_video/production/generation_evaluation.py` 固定 `video_analyze`，并检查 exact path、summary 与 measured size。CodeGraph index/relationships 用于核对图关系；同名 server/core 的部分边有歧义，parent 已按源码 imports 和实际调用复核，不把索引当源码事实。

现有能力全部保留，删除集为空；没有新增 wrapper、Provider adapter、第二 owner 或修改 deterministic QA。`video-context-mcp` 的职责尚未接线，不能将未来通用入口方向描述成当前 runtime truth。

## Verification And Evidence

- 使用 project 配置指向的 isolated Python 启动原服务，真实 `initialize` / `list_tools` 返回 `video-analysis` 与八个工具；initialize 中 version `1.29.0` 不作为项目源码版本。
- 本地两秒无音轨 `testsrc2` MP4：probe 的 measured size、三张 JPEG 的解码尺寸/时间戳、scene detection、`video_analyze` summary、公开 legacy `video_review`、重复 probe response 相等、`no_audio_stream` / `file_not_found` 均通过。没有 Whisper model load、Production permit review、替代 MCP 调用或 human semantic verdict。
- Artifact：`.agent/harness/runs/video-mcp-audit-smoke-20260927/smoke.json`；SHA-256 `be15f6beb72289d4a35dd1ee9db4dc3ea3a76967325d2f9ded2f4fee3215d96d`。临时 fixture SHA-256 `156d231b9dc1cc05bbcb08ebfcc362e04f3439f7d58018d4d268875dd0dfc532`，已随 temporary directory 清理；报告保留生成命令与图片 SHA，不保留用户媒体或完整 base64。
- `PYTHONPATH=src:. .venv/bin/python -m pytest tests/test_mcp_*.py tests/test_generation_feedback_review.py tests/test_generation_feedback_driver.py tests/test_generation_evaluation.py tests/test_generation_quality_rejection.py -q`：`132 passed, 1 skipped, 1 failed`。失败为 Claude hook 注册数假设；对照 `git show HEAD` 确认配置/测试已存在于 source checkpoint，独立重跑同一 test 再次失败。本轮没有 code delta，不能将已有失败归为替换 regression，也不能称 QA 全通过。
- 本轮文档 delta 按 policy 选择 mandatory checks；exact commit-range receipt 目标位置 `.agent/harness/runs/video-mcp-convergence-audit-20260927/receipt.json`，以最终实际 receipt 与 integrity/freshness 验证为准。本记录不预判检查结果，文档 receipt 不证明 MCP 替代或完整 QA 回归。

## Delegation And Retrieval Boundary

使用 `retrieve-ai-video-memory` 的 `superpowers` scope 完成一次检索；返回 stale last-good historical fragments，并自动排队 refresh，不等待/重试/前台 rebuild。当前源码与用户指定 session 是 identity/caller 判据，未将检索片段当 accepted contract。

通过 `external-subagent` / `subagent` CLI 封存 read-only shared-consumer audit，profile `deep`，Docker containment doctor 通过。Invocation `52048c71-ae76-4af2-aa87-ec089cbbb34c` 的 canonical receipt 分类 `PROCESS_OUTPUT_LIMIT`：一次 wire request，authenticated `k3` / adaptive / max identity，输出截断，`observed_reads=[]`，`parent_acceptance=NOT_EVALUATED`。调用不产生可依赖的 source audit/report；没有自动重试、换 backend 或声明 independent review PASS。Parent 直接审计源码。本轮不修改 external route 基础设施。

本 checkpoint 是阻断审计记录，没有 implementation candidate 或 T2/T3 shared-contract delta；不触发 final implementation review。未来实际迁移仍须按稳定 candidate 重新判断 applicable Review Risk Gate。

## Remaining Work And Learning Evaluation

最小恢复条件：准确目标服务的安装路径、启动 command 或 repository identity。然后验证其 schema 与本地 synthetic context/failures/cache，在满足覆盖和兼容性条件后才推进路由收敛。不能猜 alias 或重新用已排除的 VideoMCP。

原服务真实 ASR/OCR、完整连续帧/semantic continuity、替代返回的 image/text 可用性、替代工具错误/cache 行为均未验证。完整 QA 回归存在上面的已知测试/配置不一致；此记录不扩大 scope 修复它，也不刷新 baseline。

`distill-ai-video-learning` evaluation：`no_candidate`。本轮是单次工程审计，没有独立模型质量实验、controlled comparison 或足以 materially update 既有 Learning Claim 的证据；不创建 placeholder、不改变 adopted rules。
