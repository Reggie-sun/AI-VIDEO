# COCO / Nosha Scoped Third Runtime Repair Implementation Plan

## Goal And Authority

落实用户明确批准的[spec](../specs/2026-09-29-coco-nosha-third-runtime-repair.md)，仅为原task `user-approved:coco-nosha-local-17s-20260928` / Shot `causal-chain`提供一份新的local/unmetered runtime-repair grant，再尝试一次17 s真实GPU生成。Native Codex串行执行，不新增worktree、dependency、付费媒体路径或自动activation。

## Current And Target Behavior

当前已有三次known GPU OOM、两个consumed grants、零MP4；默认cap2阻断新grant。目标是新增显式`LocalRuntimeRepairExtension`输入，封存exact task/Shot、failed execution binding hash、当前Manifest revision与ceiling3；只在默认两个grants均已消耗时授予第三份。默认调用仍cap2；同receipt replay不写入，新失败不得再授予第四份。

## Contract Surfaces And File Ownership

- `generation_runtime_repair.py`：新增typed extension及`runtime-repair/2` codec；v1 serialization省略新增字段，保持旧JSON字段、content hash与file bytes/read/replay，不迁移Manifest pointer。
- `_state_commit_video_runtime_repair.py`：独立private helper承接完整runtime-repair registration transaction及grant validation；仍使用同一个committer lock、immutable artifact writer、atomic Manifest writer，不新增writer。`_state_commit_video.py`保留既有MRO与薄delegation method，移出原完整事务职责，避免继续扩张1712行owner。
- `tests/test_generation_runtime_repair.py`及必要focused test：通过原public committer/orchestrator/service证明兼容性、扩展及一次性消耗；拒绝stale revision、wrong task/Shot/binding/evidence/actor、paid/remote、unknown及再扩展。
- `docs/agent-primary-contract-matrix.md` / runtime baseline：同步receipt兼容及新的显式scope；现有policy的`_state_commit_video*.py`已覆盖新helper，按实际routing验证。
- `runs/coco-nosha-lora-memory-20260929-001/`：task-owned GPU LoRA/既有Triton overlay launcher、hash/proof、预算及attempt-05 evidence；不编辑installed ComfyUI/source/model或历史产物。

## Invariants And Compatibility

默认`MAX_RUNTIME_REPAIRS_PER_SHOT=2`不变。extension登记重开selected binding，并要求local execution、local_unmetered billing、同task/Shot、exact source binding、当前revision、两个已消耗grants及同runtime owner actor；known FAILED + exact durable runtime_failure仍必需。submit再次重开并核验extension scope与source binding，沿既有同次atomic write消耗grant及写intent；未知outcome、paid/remote和counter reset不获扩展。v1无extension，v2必须有；tamper及version/field mismatch拒绝。

新finite batch保留累计used3，limit4、total=None、paid ceiling0；只有一个新增submit slot，active wall5400 s / elapsed7200 s。原profile、1344×768/24fps/408输出帧、完整prompt/三图/声线不变，保留GPU text encoder与verified Triton mitigation。LoRA分块只作用已验证plain CUDA linear inference，其余路径原样fallback。

## Milestones And Verification

1. **Receipt And Sole-Committer Extension**：先新增可复现RED tests，再实现codec和完整事务helper。验证旧v1 exact payload/hash/read/replay，default2、third-only explicit local grant、paid/remote及身份/unknown拒绝、grant和submit intent原子消耗、历史计数保留。
2. **Stable Candidate Verification And Review**：按actual changed paths运行policy checks；无worktree时如实保存exact staged tree/direct-check hashes及缺失canonical Harness receipt边界。Parent审查diff与适用Risk Gate；T2 runtime-repair budget contract不改变unknown recovery或QA语义，required implementation review绑定同一exact snapshot，Kimi route/receipt机械核验，findings由Parent裁决。验证或required review未完成不能submit。
3. **One GPU Attempt And Terminal Recovery**：验证own ComfyUI unit/PID/InvocationID、空queue、GPU余量、LoRA/source/test hashes后，临时通过既有supervisor seam启动pinned combined overlay。canonical committer登记一份grant、建立新attempt/intent/permit并submit，记录真实状态。known terminal恢复原GPU-capable服务且健康；unknown停止并显式恢复，禁止新submit。
4. **Media Evaluation Or Honest Blocker**：成功exact MP4后调用project-local video-analysis并完整观看聆听，逐项评估17 s/一镜到底/正常速度/完整因果链/原声线；无MP4或required finding不满足如实报告，不追加第五次生成。stable checkpoint按record/learning skill归档，commit task-owned changes，local-only publication。

## Acceptance And Rollback

工程完成需要fresh executable evidence、compatibility和review adjudication；成片完成需要真实MP4及媒体Gate，二者分开。回滚仅停止本任务temporary own overlay并恢复原已验证service，保留全部历史/grants/intents及unknown证据，不删除Manifest或重置counter。

## Self Review

receipt version兼容通过conditional serializer而非改旧bytes；新module按完整runtime-repair职责拆分，transaction lock/atomic write归属不变。operator扩展输入必须显式精确绑定，不能凭caller布尔声称local。isolated kernel proof不替代全模型/媒体验证；approval已有，不再添加重复用户gate。

## Approved Recovery Continuation — 2026-09-29

承接spec的Approved Continuation Window Amendment：用户“继续”授权一个新增targeted review和一次同slot7200 s window extension。Native Codex为唯一task writer；本轮不修改共享implementation、已验证LoRA/Triton code、generation/recovery wrapper或installed package。

1. **Exact Review Candidate**：保存fresh snapshot/最小packet，绑定accepted spec/plan amendment、corrected `generate_next.py` / `recover_pre_submit.py`、已通过guard/AST证明、当前3 FAILED/revision28/unconsumed grant及续期proposal；完成actual changed-path documentation checks。新seal核对deep/max/1M及maximum有限budgets，只发起第5轮。Canonical receipt/route/artifact hashes/full Read与terminal report由Parent核验并裁决；无report/未解决blocker即停止，不消费video slot。
2. **One Auditable Clock Extension**：review通过后，重新读取same Manifest、grant和original budget exact hash；独立保留原budget bytes，计算从固定original started_at到now+7200 s的new elapsed ceiling，其余fields逐项相同。保存单次extension evidence、new budget hash/原始clock/当前revision/count3/review identity后atomic replace；拒绝重复续期，mixed state fail closed。只修改task budget，不通过新writer修改Product state。
3. **Exact Owned GPU Runtime And Existing-Grant Recovery**：重新核验own unit/PID/InvocationID与empty queue，保存旧ownership observations，沿已有supervisor切换相同pinned combined launcher。start返回结果单独保留，main_pid以status取证，核对activation-PID/source hashes。调用原 `recover_pre_submit.py`，不能重跑 `generate_next.main()`或remint grant/budget；canonical seam一次submit，剩余elapsed和active wall同时约束。
4. **Terminal Artifact Or Blocker**：known terminal后恢复本任务临时切换服务并验证健康；unknown不重提、不杀未知prompt。实际MP4必须video-analysis及完整观看/聆听、逐项frozen Gate，否则如实保留NOT_EVALUATED。按session record/learning routing保存新状态与task-owned commit，unrelated dirty保留。

Self-review：本次新增的是task-local finite window activation，不改变receipt/schema/CLI或共享owner；review input显式包含续期contract，避免审完后追加未审scope。原window、3次失败、prepared-only03及第三grant均保留。只有review通过才续期，不让review耗时提前吃掉新的7200 s generation window；剩余physical submit仍1，无第五次physical submit授权。
