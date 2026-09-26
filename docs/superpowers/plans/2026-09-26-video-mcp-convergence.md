# Video MCP Convergence Plan

Date: 2026-09-26

Status: implementation requested；2026-09-27 已完成现有服务审计和本地 smoke，Milestone 1 的替代服务 identity/coverage 仍 blocked；Milestone 2/3 未完成。未替换或删除 MCP。

## Execution Checkpoint — 2026-09-27

用户本轮要求实施本计划。审计 source checkpoint 为 `7fa6dbd`；当前 `.codex/config.toml` 的既有 AOCI 改动保留。下方 Starting Point、矩阵和 Self-Review 保留 planning 时的判断；矩阵中的 `Replace` 是满足前置条件后的候选方向，当前所有候选实现仍为 `Keep`，删除集为空。

- 已检查 project `.codex/config.toml`、`.mcp.json`，用户级 Codex/Claude 配置、Claude Desktop 配置与本地 MCP 安装目录，未定位 `video-context-mcp`。用户指定 session `01a0de3d-d9f4-7ef3-9d2a-0e13d462005d` 的原始记录同样只证明 EthanBobbyTR/VideoMCP 安装，且随后明确排除它；提供的 `src/ai_video_mcp` 仍为原服务源码。不能由该历史 session 推断替代身份。
- 当前 `server.py` 注册八个公开 tools；`tools/analyze.py` 直接复用 `probe.py`、`frames.py`、`scene_detect.py`、`transcribe.py`。`tools/review.py` 的 legacy 分支和 `analysis_hook.py` 消费该 core；`generation_feedback.py` / `analysis_client.py` 经 stdio 消费 `video_analyze`，`GenerationAnalysisEvidence` 仍固定 tool name、path、summary 和 measured size。CodeGraph 已调用；其对同名工具的部分调用定位混淆 server wrapper 与 core，最终 import/caller 结论以源码为准。
- 通过真实 project command 的 stdio handshake/calls 验证原服务：八个工具、probe、三张可解码 `160x120` JPEG、时间戳、scene detection、聚合分析、公开 legacy review、重复 probe 返回相等、`no_audio_stream` / `file_not_found`。图片在 text/structured JSON 的 base64 字段中返回；不宣称原服务输出 native MCP image blocks。无音轨 synthetic fixture，不加载 Whisper、不下载模型、不调用媒体 Provider、不写 Production state。
- Smoke artifact：`.agent/harness/runs/video-mcp-audit-smoke-20260927/smoke.json`，SHA-256 `be15f6beb72289d4a35dd1ee9db4dc3ea3a76967325d2f9ded2f4fee3215d96d`；fixture SHA-256 `156d231b9dc1cc05bbcb08ebfcc362e04f3439f7d58018d4d268875dd0dfc532`。重复返回只证明本次结果一致，不是 Production exact replay 的 zero-effects 证明。
- Focused regression：`tests/test_mcp_*.py` 加 generation feedback/evaluation/quality rejection 四组，`132 passed, 1 skipped, 1 failed`。唯一失败为 `tests/test_mcp_analyze.py::test_claude_project_hook_reuses_the_local_analysis_queue`：测试要求全部 `PostToolUse` 注册仅一个，HEAD 的 Claude 配置已有 record 与 analysis 两个 hook。单测再次复现；两个文件都与 HEAD 一致，属于已有不一致，不删除正常 hook 或修改测试来伪造收敛通过。

替代 coverage 仍全部 `NOT_EVALUATED`；没有达到通用入口迁移、公开 catalog 删除或底层实现删除条件。下一最小输入是准确的目标服务启动 command / 安装路径 / repository identity。取得它后继续 Milestone 1 的 schema、synthetic fixture、failure/cache 验证，满足条件再实施 Milestone 2。真实 QA 完整回归仍受上述已有失败影响；新服务 ASR/OCR、连续帧与语义质量均未验证。详见 [execution audit record](../../record_for_agent/2026-09-27-video-mcp-convergence-audit.md)。

## Goal And Scope

将通用的“视频 → 抽帧/转写 → Agent 理解”入口交给经实际验证的 `video-context-mcp`，减少重复维护，同时保留 AI-VIDEO 的精确媒体取证、确定性 QA、生成反馈和 Harness 契约。收敛单位是具体能力与调用链，不是整个 MCP 或目录。

本计划约束 Agent 工具选择与可证明冗余的公开入口。第一批实现保持现有 Production、MCP evidence schema 和内部 QA 调用兼容；不新建 wrapper、Provider adapter、分析抽象层或第二套验收 owner。若审计证明没有可安全删除的独立实现，只收敛工具路由，并记录保留原因。

依据：当前 `AGENTS.md`、[contract matrix](../../agent-primary-contract-matrix.md)、[Harness policy](../../../.agent/harness/policy.yaml)、[control-plane playbook](../../../.agent/context/control-plane-playbook.md)，以及下方当前源码。无已接受的 MCP 迁移 spec；本文不授权修改 shared schema、durable evidence 或 acceptance semantics。后续若确需改变这些契约，先按仓库 T2/T3 routing 补齐对应 spec/approval/review，不能把它作为本计划的附带清理。

## Verified Starting Point

- 原有服务由 `src/ai_video_mcp/server.py` 注册为 `video-analysis`。本轮真实 stdio `initialize/list_tools` 返回八个工具：`video_probe`、`video_extract_frames`、`video_transcribe`、`video_scene_detect`、`video_analyze`、`video_review`、`video_optimize_plan`、`video_apply_optimization`。
- `tools/analyze.py` 聚合元数据、图片、scene detection 与转写，不调用 VLM；Agent 消费这些 raw observations。`tools/review.py` 另外包含按 Production 帧窗口测量、产物 hash 校验和 committer-issued one-use permit 校验的 Python 分支。公开 `server.video_review` 不接受这个 permit 对象，不能将普通 MCP tool call 等同于该 Production 分支。
- `generation_feedback.py::review_generation_attempt`、`analysis_client.py` 与 `scripts/generation_feedback_driver.py` 仍调用 `video_analyze`。`production/generation_evaluation.py::GenerationAnalysisEvidence` 固定其 tool name，并检查 `video_path`、`analysis_summary` 和 `probe.file.size_bytes`。删除或替换此接口会影响既有 evidence/replay 契约。
- `analysis_hook.py` 与全部公开 MCP tools 共用 `serialization.py` 的跨进程 lock。自动 hook 使用只读 snapshot、source SHA-256 和 profile fingerprint，最多四帧、scene detection 开启、Whisper 关闭，且 `production_verdict=null`。它是 advisory convenience，不能替代显式逐 Shot Gate。
- 尚未定位用户所说的另一个 `video-context-mcp` 的实际启动配置或 schema。已核验的用户级 `video-mcp` 指向 EthanBobbyTR/VideoMCP，工具为 `process_video/list_processed_videos`；用户明确说明它不是本次替代目标。`src/ai_video_mcp` 是原有服务源码，不能作为替代服务的身份凭据。
- 因此，所有“新 MCP 完整覆盖”的判断目前为 `NOT_EVALUATED`。本轮未跑 QA 回归或真实替代服务视频调用；先前安装 smoke 不能作为本次替代验证证据。Agent Memory 检索因所选 Python 缺少 `langchain_core` 未完成；计划以当前源码和实际 schema 为依据，不修复检索环境。

## Capability Matrix

`Replace` 表示完成 Milestone 1 后可收敛的普通 Agent 使用入口；不自动允许删除被 QA 复用的底层实现。没有一项当前获得无条件 `Remove`。

| Existing capability / owner | Coverage by video-context-mcp | AI-VIDEO-specific responsibility | Decision |
| --- | --- | --- | --- |
| `tools/probe.py`：普通元数据查询 | NOT_EVALUATED | 普通查询非专有；Production held-FD probe、codec/count/hash validation 是专有边界 | Replace 普通入口；Keep QA/生成/渲染 probe |
| `tools/frames.py`：间隔抽帧、base64 图片 | NOT_EVALUATED | 普通看图非专有；现有 review/analyze 内部依赖须保留 | Replace 普通入口；内部依赖存在时 Keep 实现 |
| `tools/scene_detect.py`：hard-cut timestamps | NOT_EVALUATED | 一般 scene hints 非专有；不能证明相邻帧或动作连续性 | Replace 普通入口；Keep 仍被 QA/evidence 使用的实现 |
| `tools/transcribe.py`：Whisper segments、语言与时间戳 | NOT_EVALUATED | 普通 transcript 非专有；语言/精度/错误语义需要逐项对照 | Replace 完整等价的普通转写入口；不足则 Keep |
| `tools/analyze.py` / `server.video_analyze`：聚合视频上下文 | NOT_EVALUATED | 已被 generation feedback、typed evidence、hook 和 legacy review 消费 | Replace 普通使用路由；Keep 既有 QA tool/schema/core |
| `tools/review.py`：帧窗口、重复度、luminance/audio measurements、hash/permit | NOT_EVALUATED | exact render/timeline/window-bound raw evidence；verdict 仍归 Production | Keep，不以 VLM 判断替换 |
| `production/review.py`、`quality_gate_coordinator.py`：黑画面/静音/削波/required-motion freeze 等裁决 | NOT_EVALUATED | policy-selected deterministic adjudication、coverage、FAIL/NOT_EVALUATED blocking | Keep；裁决器不是测量器，须保留对应证据来源 |
| `continuity_evaluator.py`、`continuity_onnx_backend.py`、review coordinator | NOT_EVALUATED | exact frame-index sampling、模型/profile identity、主体 tracking 与 human fallback | Keep；稀疏采样不宣称完整相邻帧覆盖 |
| `scripts/visual_quality_report.py`：固定时间戳、frame/video SHA、human packet | NOT_EVALUATED | exact evidence binding；报告不自行签发 Production PASS | Keep，实施前复核其他 writer 的最新版本 |
| `caption_quality.py`、`captions.py`：caption/alignment 与 final-media evidence | NOT_EVALUATED | cue/audio/render/timeline binding、六组 coverage 与 authority | Keep；这些模块不等于已实现 OCR/ASR 引擎 |
| `analysis_hook.py`、`serialization.py`：自动 advisory analysis 与跨进程串行 | NOT_EVALUATED | exact snapshot、安全排队、取消与 lock semantics；不是 semantic acceptance | Keep 现有安全语义；本轮不自动改接新 MCP 或删除 hook |
| `ffmpeg_tools.py`、Production media/renderer helpers：校验、末帧、trim、normalize、composition | 不适用通用理解替代 | Legacy pipeline、Provider validation、唯一 timeline/renderer 的执行职责 | Keep |
| `video_optimize_plan` / `video_apply_optimization` | NOT_EVALUATED | 包含 repo-file suggestions/显式写入批准边界，不能推断被“看懂视频”覆盖 | Keep；不扩展本次范围做 optimization subsystem 清理 |

## Major Milestones

### Milestone 1: Establish Replacement Identity And Coverage

检查范围：真实客户端 MCP 配置、其指向的安装版本/commit、启动 command/cwd、工具 schema 和最少相关源码；重新扫描 `src/`、`scripts/`、`tests/`、`.agents/skills/`、`.agent/`、客户端配置、`AGENTS.md`、`README.md` 与 `docs/` 中的全部相关能力和引用。用 CodeGraph 核对候选删除项的实际 caller/consumer，再用源码与 tests 验证；名称相似不是覆盖证据。

在一次新的、有限的本地 fixture 验证中记录服务身份、schema、输入 SHA、返回的 text/image blocks、时间戳、metadata、scene/ASR options、no-audio/missing-file failures 和 cache replay。只使用临时 synthetic/test fixture，不生成 Production Shot、不调用 paid Provider、不让目标服务未经授权上传用户媒体或自动下载模型。若真实依赖不可用，将对应 capability 保持 `NOT_EVALUATED`。

完整覆盖必须包含当前用途所需的控制参数、输出可用性、时间精度、错误与缓存行为。OCR、word timing、连续帧、freeze 或 semantic continuity 只有真实 schema、源码和执行证据支持时才可标为覆盖。MCP 抽帧成功只证明 Agent 收到图片，不证明模型理解正确或质量通过。

产物：更新本计划矩阵为证据绑定的 `Keep / Replace / Remove` 决策，为每个拟删除项列出 exact paths、调用方迁移及最接近的测试；在任何删除前向用户展示简短执行范围。找不到目标服务时停止替代阶段，完成现有能力审计即可，不猜 alias、不使用上轮 `video-mcp` 冒充目标。

### Milestone 2: Converge Generic Agent Entry Points

条件性修改面：`README.md` 的 MCP 使用说明、`.agent/context/control-plane-playbook.md` 的工具选择说明，以及确实引用普通理解入口的 Skill。仅当需要 durable routing anchor 时修改 `AGENTS.md`；matrix/policy 分别保留唯一 human/machine owner，不复制完整能力 catalog。

通用视频概览和内容理解首选已通过 Milestone 1 的 `video-context-mcp`。逐 Shot Gate、生成反馈、Production review、exact evidence 与显式 QA 继续走原 canonical seams；新 MCP 的图片、文字或 VLM verdict 不得被重标为这些 seams 的原始证据或 accepted receipt。保留 `GenerationAnalysisEvidence` 兼容、exact replay zero-effects、fail-closed、permit 与 committer ownership。

候选代码面为 `src/ai_video_mcp/server.py` 和 `tools/{frames,scene_detect,transcribe,analyze,probe}.py`。先核对每个工具公开 schema、内部 imports 与所有 consumers：确认完全覆盖且调用方已迁移的独立重复实现才 `Remove`；仍由 review/analyze/feedback 使用的函数 `Keep`，不为了删除文件复制到新模块。公开 tool catalog/schema 的删除属于另一个兼容性决策，不能当作无语义变化的路由调整；未满足 applicable contract gate 时保持 catalog。

客户端配置仅在确有必要时修改 `.codex/config.toml` / `.mcp.json`；保留原 QA 服务。已有同文件 dirty work 或 writer ownership 必须在写入前解决，不自行整合或覆盖。删除只采用已审计的 exact paths，保留对应有效 failure-path tests，不删除测试来消除失败。

### Milestone 3: Verify No Regression And Close The Delta

先在同一 known snapshot 跑改动相关测试，再用真实配置启动通用理解服务并调用其工具；确认返回 usable image/text context，而不只核对注册成功。单独验证原 `video-analysis` 握手、保留的 QA tools，以及 generation feedback 的 exact response/replay 边界。

按实际 changed paths 使用 `.agent/harness/policy.yaml` 选择 mandatory checks，并验证 exact staged snapshot 或 commit-range receipt 的 scope、policy、artifact hashes 和 freshness。无 dedicated development worktree；若适用 isolation policy 要求不同验证方式，使用 canonical Harness 可支持的干净临时 clone，不修改 Harness 来放行。稳定实现 checkpoint 再判断适用 review tier；本文的 Parent Self-Review 不替代未来 required implementation review。

对每个真实 retired identifier/path 搜索 tracked source、tests、配置、`AGENTS.md`、Skill、policy 与当前文档，要求无 active dead reference。历史 spec/record 不伪造删除历史：必要时添加明确 supersession/link。仅被路由替换但因 QA 保留的 identifier 不属于废弃引用，不能通过要求全仓零出现强迫删除它。

只提交 task-owned paths，按 record skill 记录实际边界；最终报告替换/删除项、保留理由、两边职责、已跑测试/Harness、真实 MCP 验证和 gap。不得将技术 PASS、schema、receipts 或局部 sampling 宣称为 human quality acceptance。

## Focused Verification

命令以实施时重新核对的 project Python 为准；当前 `.venv/bin/python` 可用。选择与实际修改有关的组，其他组由 policy 决定，不为文档路由改动无差别运行全仓测试。

```bash
PYTHONPATH=src:. .venv/bin/python -m pytest tests/test_mcp_*.py -q
PYTHONPATH=src:. .venv/bin/python -m pytest tests/test_generation_feedback_review.py tests/test_generation_feedback_driver.py tests/test_generation_evaluation.py tests/test_generation_quality_rejection.py -q
PYTHONPATH=src:. .venv/bin/python -m pytest tests/test_production_review.py tests/test_production_quality_gate_coordinator.py tests/test_production_continuity_evaluator.py tests/test_production_continuity_review_coordinator.py tests/test_production_caption_quality.py tests/test_visual_quality_report.py -q
PYTHONPATH=src:. .venv/bin/python -m pytest tests/test_agent_harness.py tests/test_record_ai_video_session_hook.py tests/test_claude_code_adapter.py -q
```

回归必须覆盖：static-image 合法而 required-motion freeze 失败；错误/缺失/陈旧/hash-mismatched evidence 不产生 PASS；permit 不可重用；反馈重开与 exact replay 不重跑外部 effects；跨 Agent lock/取消与 hook recursion 防护；原有 Legacy/Production FFmpeg 执行不改为 VLM。OCR/ASR 的真实识别质量、完整连续帧能力、human motion/continuity judgement 若未执行，保持单独 gap。

## Acceptance And Stop Conditions

- 替代服务身份与实际 schema 可复核；完整覆盖项有真实调用证据，未知项不进入删除集。
- 通用工具选择已收敛；每项删除都完成 caller、tests、配置、Skill、policy 和文档闭包，或明确只替换路由且保留共享实现。
- AI-VIDEO QA/evidence/public compatibility、timeline、committer、permit 与 replay 契约未退化；没有新增 wrapper、隐式 fallback、第二 owner 或无关重构。
- Relevant tests、真实通用入口 smoke 和 exact-snapshot mandatory Harness 各自有证据；不混同三者证明范围。
- 目标服务缺失、覆盖不足、同文件 ownership 冲突、需要未经接受的 schema/acceptance migration、真实 mandatory check failure 或 required review 不可用时停止受影响 slice，报告最小恢复条件。不删除底层函数来强行满足收敛目标，也不刷新 baseline 隐藏问题。

## Parent Self-Review

已对照用户要求检查：研究先于修改；矩阵显式区分 unknown coverage 与专有验证；公开工具、内部共享实现、typed evidence、自动 hook 和 Production owners 分开；未承诺尚未验证的 OCR/连续帧/转写覆盖；明确 retained references 与 dead references 的区别；当前交付是 plan-only，实施与 QA/媒体验收均未发生。
