# Scoped Third Runtime Repair For COCO / Nosha

## Status And Authority

`APPROVED / IMPLEMENTATION PENDING`。用户于本窗口明确选择“A：批准这 1 次任务内扩展并继续生成”，批准本文件的exact task/Shot第三份repair（2→3）。用户此前已批准17 s、一镜到底、正常速度、原声线的本地复刻；local/unmetered累计quota已于`21fd766`纠正，GPU-capable默认启动已于`a5e3eeb`应用。本扩展只处理现有`MAX_RUNTIME_REPAIRS_PER_SHOT=2`与新的、已隔离验证的LoRA allocation mitigation之间的继续执行条件，不恢复永久本地额度。

## Verified Blocker And Candidate

原task `user-approved:coco-nosha-local-17s-20260928`、Shot `causal-chain`已有两份consumed runtime-repair grants；第三次实际submit为`coco-nosha-attempt-04`，prompt `768b1c3b-bedc-4099-9db2-19b3cdcb4879`，known GPU LoRA OOM、MP4 0。sole committer `record_runtime_repair_authorization`在同Shot grant数达到2时拒绝新增；`tests/test_generation_runtime_repair.py::test_runtime_repair_budget_is_per_shot`明确保护该条件。累计真实submit仍3，prepared-only attempt-03不计。

`runs/coco-nosha-lora-memory-20260929-001/`的task-local候选按token行分块LoRA up projection，保留完整down projection及scale后add的rounding顺序；只支持plain linear inference、同CUDA dtype、独立contiguous base output，training/conv/mid/DoRA/reshape/alias/不兼容layout仍走原路径。未安装、未激活到ComfyUI，未修改model、LoRA weights、workflow或profile。

真实RTX 5090隔离对照：BF16 `[100032,5376,21504,64]`代表性case，stock peak allocated **14007132160 bytes**、chunked **5469888512 bytes**；全部**2151088128**个输出元素比较，relative RMS/max absolute error均0。六个FP16/BF16小矩阵和输入storage alias fallback同样PASS。这是kernel-level memory/numerical evidence，shape不是上一轮失败调用的实测shape，也没有证明完整17 s模型、训练或所有layout通过。证据为`kernel-verification.json`及原源码/候选hash；不可用该PASS替代媒体Gate。

## Proposed Contract

- 默认每Shot runtime-repair cap仍为2；已有paid/remote行为与count checks不变。
- 为上述exact task/Shot允许一个显式封存的local/unmetered ceiling **3**，只增加第三份runtime-repair authorization，对应**一个**新的真实video submit；不reset history/counters，不改变task/Shot ID逃避旧grant。
- 只在重开当前sealed local/unmetered selected binding、attempt-04 exact known runtime-failure evidence、actor、scope、Manifest revision及既有两个grants后，由`ProductionStateCommitter`记录该扩展并新建authorization。不得通过caller monkeypatch constant、编辑Manifest、裸POST、复用permit或remint同evidence实现。
- 优先复用现有runtime-repair authorization/Manifest pointer owner；如需versioned receipt，保留旧v1 bytes/hash/read/replay兼容，不新增第二个ledger、writer或自动activation owner。具体codec/interface在批准后的plan中对当前loader定稿，未实现前不得宣称可执行。
- 新batch仅一个新增slot；既有三次submits保留，local total limit=None，elapsed ceiling7200 s、active prompt wall5400 s。一次known failure或unknown即停，无自动第五次submit或quality-repair扩展。
- 仅当task-local runtime overlay已核对原source/patch hashes、numerical proof、compatible plain-LoRA条件及loopback ownership/queue后，才接入原canonical generation seam。保留GPU text encoder配置与已有verified Triton INT8 mitigation；不得混入base-MLP量化scale改变、step减少或其他新优化。

## Frozen Output And Recovery

原三图/COCO voice exact provenance、完整prompt、pinned model/LoRA、V3 1344×768@24fps/408输出帧、413 sampler帧及仅尾部grid-padding trim保持。仍为17 s、一镜到底、正常速度、完整因果链；无切镜/缩短/加速/paid fallback。新exact attempt、local intent及one-use permit必须由现有owner创建。

unknown outcome停止并显式恢复；known terminal后只恢复本任务临时切换的服务并验证健康，保留Jianji与未知任务。成功MP4落盘后调用project-local `video-analysis`，完整观看/聆听，再按frozen requirements逐项PASS/FAIL/NOT_EVALUATED。kernel PASS、service active或Provider成功均不构成视频验收。

## Verification And Self Review

批准后自动生成durable implementation plan。Executable coverage必须包括旧cap2默认拒绝、exact local ceiling3仅一个新增grant、paid/remote拒绝扩展、task/Shot/evidence/actor/revision mismatch、tamper/double-use/unknown拒绝、旧v1 receipt bytes/hash/replay兼容，以及新intent原子消耗/累计计数不归零。按真实changed paths完成policy verification及适用Implementation Review Risk Gate后，才执行唯一新增submit。

Self-review：本契约不把local quota与runtime-repair cap混为一谈；不借新task/Shot绕过history；不将isolated exact numerical对照外推成17 s media或所有GEMM equivalence。新增权限严格限定一个local exact repair；批准不替代implementation及适用verification gates。Publication保持local-only，无push/release或worktree授权。

## Approved Continuation Window Amendment — 2026-09-29

用户在明确解释“审查未完成、原两小时实验window已过期、原remaining slot仍在，继续需要完成审查并续期window”之后回复“继续”。本次授权据此限为**一个新增targeted review round（第5轮）**，以及该review通过后为同一未消耗slot提供**一次7200 s window extension**；仍只有一个新增physical video submit，active prompt wall仍5400 s。Global新seal采用用户已选择的`kimi-maximum-v1`，不把64 wire requests解释为64轮review；第5轮失败后不自动启动第6轮。

续期前必须重开当前canonical Manifest（revision28、actual submitted3均FAILED、无attempt-05、prepared-only03无side effects）、原第三grant `48342361f437b2f6e9276f008c50b5c0b8048faebbb0ca4b6f368a96367d19b4`未消耗，以及原budget exact SHA-256 `74c5efa98ee983ca8d1481f2da9054df9199951b4de5c51c5c6c25a00aaa0c42`。Required review acceptance和source/runtime hashes必须先验证。只允许task-owned experiment budget的`elapsed_ceiling_seconds`延长到review通过后操作时刻加7200 s对应的原始clock offset；`started_at=2026-09-28T18:40:58.266294+00:00`和其余所有budget fields原样保留。

原budget exact bytes必须独立保存；一次续期evidence先记录original/new budget hashes、原/new ceiling、固定started_at、authorized7200 s extension、exact task/Shot/grant/review identity、Manifest revision和count3，然后通过same-directory atomic replace更新task budget。存在续期evidence或old-budget/hash/state不符即拒绝重复执行，不删除旧证据或补造permit。崩溃造成receipt/budget不一致时禁止media side effect，须按exact hashes显式恢复。此操作不写Production Manifest、不新增grant/intent、不会改写旧sealed review，也不改变canonical writer、unknown recovery、QA/activation或17 s frozen output。

Self-review：expired clock与local/unmetered额度分开；只续期尚未提交的同一slot，保留原clock与已耗时，不更名task逃避history。Required review未通过前无budget activation或media submit；本次“继续”不授权更多生成、付费媒体fallback、无限review或再次续期。
