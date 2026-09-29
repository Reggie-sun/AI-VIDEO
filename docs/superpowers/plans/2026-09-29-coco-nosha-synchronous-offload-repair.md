# COCO / Nosha Synchronous GPU Offload Repair Plan

## Goal And Scope

按 [spec](../specs/2026-09-29-coco-nosha-synchronous-offload-repair.md) 继续原17 s本地出片目标。Parent self-review和默认任务授权已绑定；Native Codex串行执行。唯一新 runtime intervention为当前 Comfy支持的 `--disable-async-offload`，第五份 exact runtime grant只允许一次新实际提交。

## Contracts And Invariants

Shared schema只增加 ceiling5，default3/cap2保留；sole committer registration和consume不改。旧 v1/v2 ceiling3/4 bytes/hash/replay保持，旧runtime拒绝新ceiling5。当前Manifest39、actual5 FAILED、4 consumed、prepared-only03未提交；不删除或重置任何历史。原素材/声线/prompt/model/LoRA/profile和17 s输出全部冻结。保留Jianji/未知任务，不用paid API，不创建worktree，不push/release。

## Milestone 1: Verify Synchronous Dispatch

在 `runs/coco-nosha-sync-offload-20260929-001/` 创建有限两进程配置对照与 launcher/runtime controller。源码绑定 pinned Comfy flag、NUM_STREAMS、queue和stream seam；确认关闭 async 后仍在 CUDA上运算、same seeded小算子输出保持，累计≤120 s。复用R9 MLP/LoRA与R5 Triton exact bytes/hash及其已通过 kernel proof；不重写installed source、不重新生成无关媒体。局部对照不得称为完整模型或本次失败shape proof。

## Milestone 2: Exact Fifth Grant

Modify `src/ai_video/production/generation_runtime_repair.py` 的typed ceiling和说明，既有 committer helper无需变更。参数化 `tests/test_generation_runtime_repair.py` 以 public seam覆盖ceiling4/5的one-use、exact replay、历史消耗及再次拒绝，扩充unknown/premature/identity/revision和unsupported6/copy tamper、旧ceiling4 bytes兼容。先RED后GREEN，更新contract matrix/runtime baseline和上一record current-facing supersession；按真实 staged paths运行政策验证。

## Milestone 3: Reviewed Single Submit

新orchestration绑定Manifest39、最新attempt06 exact FAILED binding/experience、同actor/task/Shot和4 consumed grants；新的有限预算 predecessor R9 hash、actual5→ceiling6、new1、paid0、window7200/active5400。创建attempt07准备、preview/preflight/permit均经canonical owner。稳定 source/config/evidence snapshot上运行一次受管 read-only Kimi review，Parent裁决与artifact/sourcehash核验后才执行。

核实自有原服务PID/InvocationID和空队列，临时切换只带新 async flag和原pinned overlay的launcher；采样过程中收集GPU telemetry和owned service日志，禁止杀未知工作。一次 known failure/unknown停止本单元。实际MP4先fetch并核对bytes，再调用video-analysis完整观看聆听；known terminal且队列空后恢复原服务并验证。记录真实媒体/未满足项与自动learning evaluation，提交task-owned files。

## Verification And Self Review

三个 milestones分别约束新配置的真实dispatch、共享有限授权兼容性和实际生成/验收。源、receipt、policy与kernel hash绑定同一stable target；计数来自public loader，不用裸Manifest编辑或直接Comfy submit。Local arithmetic/config PASS不代替full-model和成片。未知结果继续fail closed，下一单元需新的诊断依据和有限范围，不自动重试。
