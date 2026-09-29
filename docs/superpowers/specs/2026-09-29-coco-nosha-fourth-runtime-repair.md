# Scoped Fourth Runtime Repair For COCO / Nosha

## Authorization Supersession — 2026-09-29

用户已将任务内 shared contract、有限预算与 recovery规则变更设为默认授权，见[规则变更记录](../../record_for_agent/2026-09-29-default-task-contract-budget-recovery-authority.md)。下文 `NOT APPROVED`及“须获批准”保留为历史 proposal状态，不能再要求用户逐项批准。技术内容仍是待 Parent对当前 source核对、self-review及定稿的 candidate；本次规则变更未实施MLP mitigation、cap4 contract、grant/window/permit或视频 submit，不声称 runtime ready。

## Status And Goal

`PROPOSED / NOT APPROVED / NOT IMPLEMENTED`。目标仍为原COCO / Nosha **17 s、一镜到底、正常速度、完整因果链与原声线**。本提案先处理已知MLP GPU allocation failure，再允许同task/Shot第四份runtime-repair grant和**仅一次**新增physical video submit；不要求用户再次批准既有17 s要求或已完成审查，不把本地unmetered解释为永久自动重试。

## Verified Boundary

标准loader实测Manifest revision33；task `user-approved:coco-nosha-local-17s-20260928`、Shot `causal-chain`已有4个实际submitted FAILED attempts和3份consumed grants。Latest attempt `coco-nosha-attempt-05`、prompt `e5d7d03a-a1f7-47c9-b26e-6ceb7320ce48`，execution binding `5ca94c5af1d1d4c1352f9caaa4529e71e269ac121813a69e2fc7da31d05c3cf1`，runtime-failure experience `ad4688691d40dcea336dc2d9f4273d6c8c7ad24b9f905cac9a2a9a42b25f5a63`。Known terminal、own queue empty、没有MP4或fetch；prepared-only attempt03继续不计physical submit。

实际RTX 5090运行38.69 s后在`MLP.forward -> linear_input_act -> int8_linear -> _rotate_activation -> torch.matmul`发生OOM。Peak allocated19157 MiB、reserved21952 MiB来自该service的PyTorch摘要；错误tensor的exact shape未测量。LoRA row chunking及原Triton INT64 mitigation已加载，本次失败位置不同；这不证明完整模型或成片通过。

## Candidate And Bounded Verification

- 候选在task-local overlay对完整MLP的独立token rows处理，范围覆盖fc1、原SwiGLU、原Hadamard rotation、原per-row INT8 quantization及fc2，避免只分块旋转却保留所有完整中间张量。保留weights、scales、ops顺序及原fallback，不更改模型、量化规则、attention或sampler。
- 实施前重新核对原源码、patched runtime和真实shape条件；无法证明rows独立、出现training/incompatible layout或原调用语义不匹配时保留stock并停止该候选，不静默改变算法。
- 仅一套有界local CUDA controlled comparison，累计wall ceiling600 s，分别核对支持路径与fallback、多个chunk/tail、FP16/BF16及适用INT8/LoRA组合。支持路径的stock/chunked结果要求exact equal；representative large case的peak allocated必须明显下降（候选≤stock的60%），否则拒绝候选，不降低数值标准来争取出片。
- 尽量覆盖新失败的真实dimensions；若stock因容量无法完成，明确保留该large-case equivalence缺口，不能将小case/shape假设当full-shape proof。Parent据当前GPU headroom与整条MLP峰值决定是否有可信执行条件；未具备则不签发下一video permit。

## Proposed Repair Contract

默认per-Shot cap2保留；旧third-extension ceiling3、v1/v2 receipt bytes/hash/read/replay全部兼容。新增typed exact ceiling4只在上述task/Shot latest known local failure、相同actor、当前revision和3份prior consumed grants经sole committer重开验证后允许。不得直接把所有任务默认cap改为4、monkeypatch常量、编辑Manifest或绕过已有repair intent的原子one-use consume。具体版本/codec在批准后的plan中对当前loader定稿。

新的finite执行预算只封存**1次新增physical submit**，从actual used4到batch ceiling5、local total limit=None、paid0；原3份grants、4次失败、原budget与clock renewal全部独立保留。旧R8 window只属于已消耗的slot，不复用、再次续期或重置其started_at。若本提案获准并通过全部preflight，才为这个新的有限执行单元记录一次7200 s window、active prompt wall5400 s、exact predecessor budget/hash及used4；不更改task/Shot逃避count/history。一次known failure或unknown即停止，不自动增加第五份repair或第六次physical submit。

在candidate verification、共享契约focused/public/failure-path tests及适用policy/review完成后，只由现有canonical generation seam创建fresh attempt/request/local intent/one-use permit。保持loopback、无cloud egress和paid fallback。Unknown停止显式恢复；known terminal且own queue empty后恢复临时切换服务、验证健康并保留Jianji/未知任务。

## Frozen Output And Acceptance

保持原三图/COCO voice exact bytes/provenance、完整prompt、pinned model/LoRA、V3 1344×768@24fps/408输出帧、413 sampler帧及仅尾部grid-padding trim。不得缩短、加速、切镜拼接或替换声线；canonical fresh repair seed与上一actual attempt关系单独记录，不宣称same-seed A/B。

实际MP4落盘后调用project-local `video-analysis`，完整观看、聆听并按frozen requirements逐项PASS/FAIL/NOT_EVALUATED。Kernel PASS、审查通过、service active或Provider success均不是media acceptance。无MP4时交付真实未满足项，不用旧广告/剧情视频冒充成果。

## Verification And Self Review

批准written spec后自动生成durable implementation plan；需覆盖default cap2、旧ceiling3兼容、exact fourth local grant仅一次、paid/remote拒绝、task/Shot/actor/binding/evidence/revision mismatch、unknown/tamper/double-use及prior3 consumed验证。按真实changed paths验证，fresh evidence如实区分direct policy checks与canonical Harness receipt；不创建worktree、push或release。

Self-review：当前repeat submit只会复现未处理的MLP分配问题，因此先验证mitigation再扩展执行；没有足够数值/显存证据则停止。新有限单元保留原task全history，不把用完的旧slot重命名为未提交，也不将GPU kernel对照外推为17 s模型能力。新增scope同时涉及MLP runtime行为与exact repair ceiling3→4，须获批准；本提案本身不授权implementation、kernel/media effects、grant、window或permit。
