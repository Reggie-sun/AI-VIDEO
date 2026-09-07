# Jieshi S01 Seedance 2.5 Repair

## Scope And Authority

用户在“是否同意追加最多 ¥85，仅生成一次 2.5 首镜，按实际用量结算”之后回复“继续”。本目录是该明确新增修复 scope，不是原 15 元 ledger 重置。主线程是三个本目录脚本的唯一 writer，native reviewer_xhigh 只读复核。没有其他 writer 的目标路径重叠。

原 `jieshi-e01-seedance20-20260905-001` paid ledger 保持不变：上限 15 CNY、实际 10.017675 CNY，active snapshot hash `1e8eac7fd6740a3e2306a1130909a7235e30eab8be96b5050515c7883ab960d6`。新增 scope 上限 85 CNY，只能一次 submit；合计旧实际加新增上限 95.017675 CNY。旧失败 MP4 不作为 accepted continuity source。

## Canonical Request

以下 request、预算与验证描述是 2026-09-05 的历史记录，不构成新的调用授权。
`prepare_first_shot.py` 保留历史 project bootstrap；当前 prepare/live 入口已在 2026-09-07
迁移到下述共同 feedback driver，不能继续用旧固定 hash 或旧授权发起新 attempt。

model：`doubao-seedance-2-5-260628`；T2V，无图像或视频上传；1080×1920、24fps，native_audio=false；timing=provider_selected（4–30秒，不承诺4秒）。exact resolved hash：`f766195d33a048d819c8199be599a7cd4724e8c345b1410c416a33747d929ea9`；paid preview：`9e4fb4163d39417db6f9c961de43e31e772df6e8248e430ebb975e8d17ade7a1`。

## Invariants And Verification

Product core、Manifest schema、原预算 ledger、原 exact_seconds FAIL、Episode 300秒结构和S01成片3秒保持原契约。仅 open_state 的空间表达为 authoring 修复变量；模型/timing单独变更，不宣称受控比较。

现有 public models 的 request/profile/authorization identity 检查及授权时效验证已执行；max token 估算 1460025，按当前 55.44 micro-CNY/token 为 80943786 micro-CNY，小于 85 CNY ceiling。实际计费取 `usage.completion_tokens` 并上取整到 micro-CNY。

exact MP4 落盘后必须调用 project-local video-analysis MCP，按 `preparation/shot-01-sealed-media-gate.json` 逐项判定。本脚本没有自动 activation、下一 Shot 或 retry。原始视频不能冒充含指定广播、字幕的3秒开场成片；P4与ResolvedTimeline仍拥有合成和裁切。

原三脚本的全量 Harness 受 `.venv` 缺少已声明 whisper 依赖及验证期间 HEAD 变化阻断。该失败不能作为本目录的新通过证据；本目录的实际执行、media Gate、record与验证结果分别保存，不相互替代。

## Current Feedback Entry

本目录与 Seedance 2.0 目录的 `prepare_request.py` / `live_first_shot.py` 均委托
`scripts/generation_feedback_driver.py`。从任意 cwd 运行 `--help` 可查看私有工具参数；
这不是新增的 public `ai-video` CLI。

默认调用需要 `--project-root <root> --config <json>`，只准备 decision，不联网、不提交。
配置 `schema_version` 为 `generation-feedback-driver/1`；必填字段为 `planning_request`、
`video_plan`、`context`、`routing_policy`、`lifecycle`、`decision_policy`、`execution_limits`、
`seedance_profile`、`output_requirement`，使用对应 typed model 的 JSON 序列化。
引用素材可附 `reference_receipts` 和按 evidence hash 索引的 `reference_confirmations_base64`。
配置必须匹配当前 selected Project、Scene、Character、Shot、Registry 与 QA inventory；
不能靠复制历史配置修复缺失的 authoring/evaluator。

一次执行另需 `--execute --attempt-id <id> --paid-preview <json> --authorization <json>
--reservation-id <id>`，消费当前外部签发的 exact authorization，经现有 service 执行。
fetch 后只报告 `evaluation_required`，不会激活、进入下一 Shot 或自动重复付费调用。

已有 exact MP4 可用 `--analyze --attempt-id <id> --mcp-python <python>` 获取当前
project-local MCP 的 raw analysis。selected evaluator 再明确判定 required findings，生成完整
`GenerationEvaluationSource` JSON array，显式包含相同 `analysis_evidence`；通过
`--evaluate --attempt-id <id> --sources <json> --mcp-python <python>` 重验并保存反馈、
产生下一 decision。若重新分析的内容发生变化，旧 source 被拒绝；须重新完成证据关联。
`--repair-evidence` 仅请求同一 fetched bytes 的显式证据重验，不授权新生成。

MCP 输出不自动成为 PASS；unknown outcome、缺失 evidence 或不满足当前 rubric 均阻断。
本次接线只做 offline verification，没有执行此目录的新 Provider/media attempt。
