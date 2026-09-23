---
record_kind: media_experiment
topic_id: ninebot-h3-first-frame-conditioning-head-continuity
learning_eligibility: eligible
evidence_index_version: "1"
---

# Ninebot H3 First-Frame Conditioning Head Continuity Record

Date: 2026-09-20

## Purpose

记录 Ninebot N3 照明广告 live run（`runs/ninebot-n3-lighting-ad-20260920-001`）中 Per-Shot Post-Media Gate 首次真实 FAIL：MiniMax H3 fl2va `image_to_video` 会把 first-frame conditioning 图忠实渲染在成片头部，明亮门店 conditioning 帧导致 shot 头部 scene/lighting 连续性违约。本文固化诊断证据、单变量修复设计与有界 repair loop 约束，供后续 Shot 与同类 run 复用。

## Current Runtime Truth

- Provider 为本机 loopback ComfyUI MiniMax H3 fl2va（`comfy-local-h3`），`image_to_video` 模式，first-frame 绑定注册资产 `ff-*`（均由同一张用户确认门店实拍照片 `n3-85c-white-front-price-4199.jpg` 裁剪派生）。
- 派生配方在 `runs/ninebot-n3-lighting-ad-20260920-001/live_driver.py` `stage_assets()`：`ff-hook` 使用 `brightness=0.28, saturation=0.75` 暗化；`ff-body` / `ff-demo` / `ff-proof` 为全亮度。`SHOT_GENERATION` 原本将 `ff-body` 绑定到 shot-intro 与 shot-close。
- shot-hook（conditioning=`ff-hook` 暗化帧）Gate 全项 PASS 并已激活；shot-intro（conditioning=`ff-body` 全亮度门店照）Gate `shot.continuity.in_out` FAIL，attempt-shot-intro-2 已 STOP，未激活、未推进下一 Shot。
- 修复循环已按 `LOCAL_BOUNDED_REPAIR_LOOP` 封存在 `runs/ninebot-n3-lighting-ad-20260920-001/evidence/repair-loop.json`：单变量 = shot-intro 的 first_frame 资产身份（`ff-body` → 已注册暗化资产 `ff-hook`），prompt/seed/frame_count/provider 全部不变；repair attempt identity = `attempt-shot-intro-4` / `ninebot-shot-intro-generation-4`；max 2 次 repair。
- attempt-shot-intro-3 在提交前被取代（`superseded_before_submit`）：其 decision binding 封存早于 attempt-2 的 canonical media evaluation，frozen `DecisionInputs` 未携带 experience history，被 submit guard 以「stale relative to durable history」正确拒绝；attempt-3 从未离开 `phase=request`，零 Provider 副作用，已持久化 `not_submitted` evaluation experience。修复以内容完全相同的 attempt-4 继续，decision 按 canonical planner（`generation_feedback.py`）补齐 `evidence`/`experiences` history。
- shot-close 的 sealed open state 本来就是「clean bright showroom」（`live_driver.py` `_sealed_generation_intent`），因此 shot-close 继续使用 `ff-body` 不构成违约，不在本次修复范围。

## Session Work And Decisions

1. shot-intro 首轮生成（`ninebot-shot-intro-generation-2`）fetch 成功：416x736@24fps、124 帧、5.167s、AAC 音轨，prompt 元数据与 sealed intent 一致（scene-night-street、dolly_in forward、VO「九号 N3 系列，ALC 全境光幕照明系统」）。
2. Gate 逐项取证：ffmpeg 头部抽帧发现帧 0-1 为明亮门店内部（N3 85C 价格海报、NimbleOS 横幅、瓷砖地面），帧 2 起硬切到夜间道路；帧 2-123 主体 identity、动作、运镜、VO 均符合 sealed intent。Whisper 转写「9號N3系列,ALC全境光目照明系統」与 sealed 台词语音等价。
3. 判定：`shot.continuity.in_out` = fail（违反 sealed open state「dark stage, headlight off」、VisualTreatment palette「deep blue-black night」、LightingIntent「single continuous lighting state within the shot」）；其余 4 项 pass。判定写入 `evidence/shot-intro.review.json`（小写 verdict，绑定 artifact sha256 `55edf382…d6d70`）。
4. 根因隔离（单变量）：对比已 PASS 的 shot-hook——其 conditioning `ff-hook` 使用暗化配方，头部为纯黑夜景；shot-intro 的 `ff-body` 是全亮度门店照，provider 按 i2v 语义忠实渲染 conditioning 帧后再向 prompt 场景过渡。变量精确归因到 first_frame 资产身份，而非 prompt/seed/provider。
5. 修复设计取舍：canonical 中途无 registry asset 新增 seam（`bootstrap_initial_state` 对已初始化 root 拒绝不同 registry；`prepare_repair_input` 仅 bootstrap 期、仅 video 输入），因此不采用「新建暗化 ff-body-night」方案，而是复用已注册的 `ff-hook`（同一车辆暗化夜景帧，recipe 与 PASS 头帧完全相同），零 registry mutation。放弃 trim 头部 2 帧方案：会篡改 content-addressed fetch artifact，无 canonical seam。
6. Driver 变更（最小 diff）：`SHOT_GENERATION["shot-intro"] = ("ff-hook", 124)`；`_ff_by_shot["shot-intro"] = "ff-hook"`（一致性）；shot-intro 的 attempt/generation suffix 条件性升为 `-4`，`stage_shot_fetch` 的 manifest lookup 同步修正；`_prepare_generation_execution` 的 `DecisionInputs` 按 canonical planner 补齐 `evidence`/`experiences`（提交期 guard 要求 sealed decision 携带完整 durable experience history，否则任何已记录评估都会使后续 submit 失败）。
7. 提交期 guard 修复链：attempt-2 的 media evaluation 经 canonical MCP bridge（`review_generation_attempt`）持久化（outcome=`media`，evidence hash `38242e7f…`）；MCP venv 调用必须保留 `video-analysis-mcp/bin/python` symlink 未解析（`ProjectAnalysisSession.__init__` 的 `Path.resolve()` 会破坏 venv `pyvenv.cfg` 上下文导致 `No module named 'mcp'`），本次经保留 symlink 的 session 封装完成。

## Verification And Evidence

- 视觉取证：`evidence/shot-intro-frame-{1..5}.png`（n=0/30/60/90/123）、`evidence/shot-intro-head-{1..10}.png`（n=0..9），两轮独立抽取一致。
- 音频取证：video-analysis MCP `video_transcribe`（whisper base, zh），segment 0.0-4.2s。
- 元数据取证：video_probe 确认 416x736、124 frames、24fps、AAC；内嵌 ComfyUI prompt 与 sealed intent 匹配。
- 资产取证：`references/ff-body.png`（全亮度门店照）与 `references/ff-hook.png`（brightness 0.28/saturation 0.75）视觉对比；registry AssetRecord `ff-hook` 已注册。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N3-HOOK-PASS | attempt-shot-hook-2 | ninebot-h3-first-frame-conditioning | attempt-shot-hook-2 | arm:darkened-ff-hook | 24a71b0c7f49bfa18eaa852720dfcdc2d7e84428d2e2b6cf5257470c54b497c1 | AGENT_GATE | PASS | NONE | NEW_ATTEMPT | NONE | `runs/ninebot-n3-lighting-ad-20260920-001/evidence/shot-hook.review.json` |
| N3-INTRO-FAIL | attempt-shot-intro-2 | ninebot-h3-first-frame-conditioning | attempt-shot-intro-2 | arm:bright-ff-body | 55edf38230e4e0ea43b339049aad6264fde279d3623469dd15e36b55ca7d6d70 | AGENT_GATE | FAIL | CONTINUITY_HEAD_SCENE_MISMATCH | NEW_ATTEMPT | NONE | `runs/ninebot-n3-lighting-ad-20260920-001/evidence/shot-intro.review.json` |
| N3-INTRO-HEAD-FRAMES | attempt-shot-intro-2 | ninebot-h3-first-frame-conditioning | attempt-shot-intro-2 | arm:bright-ff-body | 55edf38230e4e0ea43b339049aad6264fde279d3623469dd15e36b55ca7d6d70 | ANALYZER | FAIL | CONTINUITY_HEAD_SCENE_MISMATCH | SAME_EVIDENCE_NEW_PROOF_LAYER | N3-INTRO-FAIL | `runs/ninebot-n3-lighting-ad-20260920-001/evidence/shot-intro-head-{1..10}.png` |
| N3-INTRO-VO | attempt-shot-intro-2 | ninebot-h3-first-frame-conditioning | attempt-shot-intro-2 | arm:bright-ff-body | 55edf38230e4e0ea43b339049aad6264fde279d3623469dd15e36b55ca7d6d70 | ANALYZER | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | N3-INTRO-FAIL | video-analysis MCP video_transcribe on exact fetched MP4 |
| N3-FF-ASSET-DIFF | asset-diff:attempt-shot-intro-2 | ninebot-h3-first-frame-conditioning | attempt-shot-intro-2 | arm:variable-isolation | 5fd290c6eb1d415d9ddfb1ef1041ab6c37997281e79d5e90058018518a18eb29 | TECHNICAL | PASS | NONE | INPUT_REUSE_ONLY | N3-INTRO-FAIL | `runs/ninebot-n3-lighting-ad-20260920-001/references/ff-body.png` vs `ff-hook.png` |

## Assessment

- 已确证的 runtime 结论：在本地 H3 fl2va `image_to_video` lane 上，first-frame conditioning 资产的场景/亮度属性会原样出现在生成片头部（至少前 2 帧 / ~83ms），与 sealed intent 的 open state 冲突时构成真实的连续性违约，且能被 Per-Shot Gate 的头帧取证稳定捕获。
- 该结论是 media/empirical 层证据（同配方对照 arm），不是 offline test 结论；它不评估 seed 敏感性、不证明其他 provider 有相同行为。
- shot-hook 的 PASS 与 shot-intro 的 FAIL 构成单变量对照（暗化 vs 全亮度 conditioning，同一源照片、同一 provider/prompt 结构），支持「conditioning 帧亮度/场景属性 → 头部连续性」的因果归因。

## Remaining Risks Or Next Work

- repair attempt-4（conditioning=`ff-hook`）生成结果尚未取证；完整 Gate 需重新执行，若同类连续性失败重复且无新可隔离变量，按 repair-loop.json 停止条件终止并报告。
- `ff-hook` 是车头近景暗化帧，而 shot-intro sealed framing 为 medium front view；头部可能存在轻微 framing 跳变，需以实际输出帧判定，不得预设 PASS。
- shot-demo / shot-proof 仍为 COMPOSITOR_ONLY，无需生成；shot-close 维持 `ff-body`（showroom intent），但其 Gate 仍需逐帧验证门店场景一致性。
- compose → review → deliver 尚未执行；delivery 前需按 policy.yaml 对 task-owned changed paths 运行 Harness 验证。

## Agent Guardrails

- 本次 FAIL 未触发 blind retry、permit remint 或 Provider 切换；本地 lane outcome known 且存在单变量证据，符合 `LOCAL_BOUNDED_REPAIR_LOOP` 准入。
- 未对 Asset Registry / Manifest 做任何手写 mutation；attempt-shot-intro-2 保持未激活 STOP 状态。
- 用户提出「不行用api也可以」的 paid fallback 已记录但未启用：本地豁免 lane 未阻塞，切换 Provider 会违反 repair loop 单 Provider 约束并扩大 scope。
- content-addressed fetch artifact 未被 trim 或重写；所有判定绑定 exact bytes sha256。
