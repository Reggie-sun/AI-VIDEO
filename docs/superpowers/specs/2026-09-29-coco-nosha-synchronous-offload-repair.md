# COCO / Nosha Synchronous GPU Offload Repair

## Goal And Authority

`SCOPE AUTHORIZED / SELF-REVIEWED`。依当前任务默认授权继续原 COCO / Nosha 17 s、一镜到底、正常速度、完整因果链和原声线；只为最新已知失败增加一份 exact local runtime-repair grant 和最多一次 physical submit。Parent 自主定稿，Native Codex 串行实施；无需新增用户批准。

## Current Evidence And Hypothesis

`b25c2ac` 的第四份 repair contract、15 项 direct exact-staged policy checks及受管 Kimi review/Parent acceptance 已完成。Task-local MLP/LoRA candidate 的逐元素 CUDA 对照通过，但不能外推为完整模型能力。`coco-nosha-attempt-06` 实际 prompt `2822aecf-549a-49b4-840f-3fdc931ed82f` 在 RTX 5090 上运行 41.46 s 后，0/4 sampling 时失败在 `model_prefetch.prefetch_queue_pop -> cast_modules_with_vbar -> VRAMBuffer.get`，`VRAM grow failed: 646288384 bytes`。标准 loader 当前 Manifest39、5 个 actual submitted FAILED、4 份 consumed grants、fetch0/MP4=0；prepared-only03不计提交。已恢复原 GPU ComfyUI，队列为空，Jianji/未知任务保留。

失败位置是异步 dynamic-vbar 权重预取所需缓冲区，尚未证明 MLP 修复在完整模型中的行为。当前 pinned Comfy source 的 `--disable-async-offload` 将 `NUM_STREAMS` 设为0，`make_prefetch_queue` 返回 None、`get_offload_stream` 返回 None，使原 ops 使用同步权重传输；它不选择 CPU inference、不改变模型数学运算。新单变量假设是同步传输可避开本次预取缓冲分配，代价为更慢的权重搬运。模型权重整体约32 GB，大于当前可用显存；不能声称关闭预取必能完成，完整模型显存和媒体质量仍待真实取证。

## Contract And Compatibility

`LocalRuntimeRepairExtension.ceiling` 仅从 `Literal[3,4]` 扩为 `Literal[3,4,5]`，default3和默认 per-Shot cap2不变。复用 sole committer 的 typed revalidation、`granted == ceiling - 1`、全部 consumed、同 actor/task/Shot/local-unmetered、latest known FAILED、exact binding/evidence/revision 和原子 one-use consume。第五份只能在前四份已消耗后登记；第六份、premature、unknown、paid/remote、identity mismatch仍拒绝。旧 `/1` 与 `/2` ceiling3/4 bytes/hash/read/replay 保持，新 ceiling5 对旧 runtime fail closed；不改 Manifest pointer/layout、canonical owner 或恢复语义。

## Runtime And Finite Execution

在新 task-local directory `runs/coco-nosha-sync-offload-20260929-001/` 创建 launcher/controller/orchestration；复用 exact 已验证 MLP/LoRA/Triton overlay bytes，不编辑 installed Comfy/model，不更改 sampler、attention、量化算法或 profile。唯一新 runtime flag 为 `--disable-async-offload`。先以两个隔离进程核对默认/关闭 async 的真实 CUDA dispatch、queue、stream 和相同小算子输出；累计 wall ceiling120 s，不提交媒体。这只证明配置传播/算子稳定性，不证明全模型能运行。

所有 verification 与适用 independent review 后，新有限执行单元封存 predecessor R9 budget/hash、used5、batch ceiling6、local total=None、paid0、new physical ceiling1、window7200 s/active5400 s。保留旧 budget/grants/intents及 actual count，不重命名 task 或重置历史。仅 canonical generation seam 创建 fresh attempt07、intent/one-use permit，fresh repair seed按 canonical owner记录，不能称 same-seed A/B。一次 known failure或unknown即停本单元；unknown必须补证/显式恢复，不能 blind retry。known terminal且 own queue empty 后恢复临时服务并核对健康。

## Frozen Acceptance And Verification

保持原三图/COCO voice exact bytes/provenance、prompt/model/LoRA/profile、1344×768@24fps、408 output/413 sampler frames、仅尾部 grid-padding trim。禁止缩短、加速、切镜拼接、替换声线和 paid fallback。MP4落盘后显式调用 project-local video-analysis，完整观看/聆听，逐项 PASS/FAIL/NOT_EVALUATED；无 MP4 不声称媒体目标完成。

Public orchestrator/service/committer tests覆盖 ceiling4旧行为和 ceiling5 登记/replay/one-use/history/耗尽、unknown、premature、identity/revision、copied-model tamper及旧 receipt。按 changed-path policy运行 exact-staged checks，用户禁止 worktree 时如实报告 direct checks而非 canonical Harness receipt。稳定 implementation candidate做一次受管 read-only Kimi review，Parent核验 exact snapshot/receipt及裁决；不以 PARSED代替 acceptance。记录真实结果，无 push/release。

## Self Review

诊断基于本次 GPU stack与 pinned source，没有把失败后 free VRAM当采样峰值。单一配置变化直接避开已观察失败路径，既有数学修复及素材保持；未证明之处由一次 finite真实执行验证。默认授权覆盖任务内有限 ceiling扩展，one-use、known-outcome及全部技术保护保留。新长期数学/架构功能不在本范围。
