# COCO / Nosha Host Pin Recovery Plan

## Goal And Scope

按[spec](../specs/2026-09-29-coco-nosha-host-pin-recovery.md)继续原17 s本地成片目标。Parent完成scope/self-review，Native Codex串行实施。唯一新runtime variable是`--disable-pinned-memory`；既有同步offload和所有数学overlay保持。Canonical第六grant只允许一个新实际submit。

## Execution Checkpoint — 2026-09-29

Milestones1/2已完成：native pin dispatch/CUDA局部对照、typed ceiling6实现、80 focused PASS、exact staged direct-policy及受管Kimi/Parent review均有记录，code commit `df90028`。Milestone3的单次attempt08已实际完成GPU生成/canonical fetch17 s MP4，并执行exact-media Gate；质量FAIL/NOT_EVALUATED保留，未达到faithful目标或Final Acceptance。原正常GPU服务恢复后，独立finite quality resample仅改seed，actual attempt09 known GPU OOM，无新媒体；当前Manifest59、8 physical submits、6 consumed grants、retained MP4=1。

本plan不授权重跑已消费的controller/permit。后续须针对实际rms_rope allocation和known质量偏差形成新的有据有限unit，默认任务授权仍适用；current evidence与真实未满足项见[当前记录](../../record_for_agent/2026-09-28-reference-capabilities-and-local-canvas-method.md#current-continuation--actual-17-second-gpu-video-quality-rejected-and-resample-oom)。下方Manifest45/MP4=0为本plan开始时的历史precondition，不是当前状态。

## Contracts And Invariants

Typed ceiling增加6，default3/cap2不变；sole committer及one-use/known-outcome/binding/revision检查保持，旧v1及v2 ceiling3/4/5 bytes/hash/read/replay保持。Manifest45、actual6 FAILED、5 consumed，prepared-only03不计；不删除/重写旧预算、grants、intents、permit和review证据。原17 s、三图/voice/prompt/model/profile不变，保留Jianji/未知工作，无paid media、worktree、push/release。

## Milestone 1: Native Pin Dispatch And Recovery Evidence

在新run目录创建有限两进程验证与pinned launcher/controller；复用R10 overlay/proofs exact bytes，source-hash绑定CLI、model management、native pin与ops。核对关闭pin后的capacity/dispatch和局部真实CUDA输出相同，≤120 s，不做额外media。记录R10 actual 4/4 sampling、kernel global OOM、existing canonical failure recovery和原服务restoration，保留无MP4/声线未验收的边界。

## Milestone 2: Exact Sixth Grant

先为`tests/test_generation_runtime_repair.py`扩充6的public-seam覆盖并取得RED，再更新`src/ai_video/production/generation_runtime_repair.py`的literal及docstring。Unsupported/copy-tamper改为7，旧5 bytes兼容加入。同步contract matrix/baseline；运行focused与真实staged-path policy，检查exact hashes/freshness。

## Milestone 3: Reviewed Single Submit And Media Gate

新orchestration必须绑定Manifest45、attempt07 exact FAILED binding/experience、same actor/task/Shot及5 consumed grants。封存predecessor R10 hash、actual6→ceiling7、新1、paid0、7200/5400有限窗口；准备attempt08通过canonical routing/compiler/preflight/preview/intent/permit。Telemetry增加host MemAvailable/RSS/locked memory，低于4 GiB时只可cancel exact running job一次，unknown停止。Stable final source/config/evidence snapshot完成一次T2受管Kimi review和Parent裁决后执行；故障fallback依SUBAGENTS。

核实原unit/PID/InvocationID及空队列后只切换自有服务。Known terminal后恢复默认GPU服务并验证；worker死亡走已验证的absence/terminal evidence恢复条件。实际MP4 fetch核对bytes后显式project-local video-analysis，完整观看/聆听，记录PASS/FAIL/NOT_EVALUATED；没有成片不得称完成。稳定record自动learning evaluation，不为记录增加Provider/network/tests，task-owned staged paths单独commit。

## Verification And Self Review

局部pin/transfer proof、shared compatibility proof、review和full-model/media proof分别记录。源码与receipt/hash绑定同一stable target，禁止裸Manifest编辑/直接Comfy submit、permit复用、旧controller重跑和未知结果盲重试。一次known failure后先诊断再决定新的有限范围，不用无限执行取代预算。
