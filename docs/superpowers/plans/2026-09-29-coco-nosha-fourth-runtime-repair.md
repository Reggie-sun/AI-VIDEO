# COCO / Nosha Fourth Runtime Repair Implementation Plan

## Goal And Scope

在原17 s本地目标内验证完整MLP row chunking，扩展exact local第四份runtime-repair grant，并通过canonical seam执行最多一次新增submit。Spec为[Scoped Fourth Runtime Repair](../specs/2026-09-29-coco-nosha-fourth-runtime-repair.md)，由任务默认授权和Parent self-review绑定；Native Codex串行执行。

## Invariants And Compatibility

默认cap2、旧ceiling3、v1/v2旧bytes/hash/replay、同actor/task/Shot、latest known failure、prior grants consumed和atomic one-use保持。`LocalRuntimeRepairExtension.ceiling=Literal[3,4]`，default3；新ceiling4对旧runtime fail closed。完整原三图/voice/prompt/model/LoRA、1344×768/24fps/408输出帧/413 sampler帧保持。不写installed Comfy源代码，不改量化算法，不替换声线，不缩时/加速/拼镜，不使用paid fallback。Prepared-only03不计submit；actual used4与原budget/window永久保留。

## Milestone 1: Equivalent MLP Candidate

Create `runs/coco-nosha-mlp-memory-20260929-001/mlp_chunk.py`、`verify_mlp.py`及content-addressed comparison evidence。完整fc1→原linear_input_act(fc2, swiglu)按独立rows分块，原ops/weights/scales不变。global training、grad、非CUDA/FP16/BF16/2D连续或shape不兼容时stock fallback。真实plain LoRA hook保留full-row down GEMM，再经ContextVar提供exact input view的投影切片；up chunk boundary与原64 MiB一致，unsupported hook走stock。使用实际Comfy INT8/convrot/Triton路径，覆盖FP16/BF16、chunk/tail、适用LoRA组合、fallback与输入不变。原row-only候选因LoRA差异拒绝，独立新600 s单套验证预算有predecessor及失败history；要求exact equality及代表大case峰值≤stock60%。Token-row数量属于代表case，不冒充原失败shape。失败时不提交视频。

## Milestone 2: Canonical Fourth Grant

Modify `src/ai_video/production/generation_runtime_repair.py`、`_state_commit_video_runtime_repair.py`；sole committer登记typed ceiling4须恰有3份prior consumed grants，并沿用当前local scope/binding/evidence/revision/actor/latest failure检查。Test `tests/test_generation_runtime_repair.py`通过public orchestrator/service/committer验证第四grant登记、exact replay、一次consume、历史计数、再次拒绝；保留第三extension旧测试，增加premature4、unsupported5及旧receipt bytes兼容证据。同步contract matrix和runtime baseline。先RED再实现GREEN，运行execution guards与相关policy checks；不裸写Manifest，不monkeypatch default cap。

## Milestone 3: One Exact Local Submit And Media Review

Create新task-local overlay/launcher/service controller与canonical orchestration，复用已验证R5 Triton INT64和R8 LoRA chunk逻辑，manifest绑定每个overlay/source hash。对完整稳定source/kernel/orchestration candidate进行受管Kimi read-only review，Parent裁决；冻结期间不修改snapshot files。检查canonical Manifest revision/count及latest attempt05，再为同task/Shot封存新grant、attempt06、新finite unit7200 s/active5400 s/paid0/actual4→ceiling5，记录exact predecessor budget hash。只经existing generation seam签发fresh local intent/one-use permit。

重新核对own idle服务PID/InvocationID与空队列后临时切换；保留Jianji及未知工作。监控known terminal；unknown停止恢复，不remint/retry。MP4落盘后调用project-local video-analysis并完整观看、聆听，逐项PASS/FAIL/NOT_EVALUATED。known terminal且own queue empty后恢复原服务并验证健康。记录真实结果/未满足项，执行record/learning evaluation，按任务路径commit；无push/release/worktree。

## Verification And Self Review

CUDA equality与峰值只证明MLP candidate。Focused tests覆盖默认/第三兼容、第四one-use/replay/count、unsupported/premature、actor/task/Shot/binding/revision/unknown/paid/remote/tamper保护。检查真实changed-path policy，direct验证与canonical Harness receipt分别报告，不伪称未运行的isolated Harness。Spec各约束已映射三milestones；budget和permit依赖kernel、contract tests、适用review/preflight，media acceptance仍依赖实际17 s成片。
