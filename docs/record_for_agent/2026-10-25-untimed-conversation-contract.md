---
record_kind: architecture_implementation
topic_id: untimed-conversation-contract
learning_eligibility: ineligible
---

# Untimed Conversation Contract Checkpoint

Date: 2026-10-25 (Asia/Hong_Kong)

## Media Continuation Notice

下方共享guard checkpoint中的“未生成视频/未新增付费调用”是该工程检查时的历史边界。用户随后明确“继续生成啊”，本任务已实际submit两次S01：首样fetch后由用户指出声画不同步并canonical质量拒绝，一次有界修复也已fetch但待声画确认。exact媒体、paid计数、原audio UNKNOWN保留、最小质量修复入口及当前验收边界见 [drama media record](2026-10-25-shizhen-episode01-jimeng25.md)。此前Harness共享staging问题与未commit/push状态未被媒体下载消除；工程测试不等于口型通过。

## Continuation — Shared Guard Applied

用户回复“继续”，解除下方历史 checkpoint 的共享文件写入归属 blocker。Parent 先核对真实 compiler baseline SHA-256 `93482091757b9f57af1f348b9974bf7f9557da74ec53e3e6aadf159a92988daa` 未变，再仅追加已审查的22行 guard；结果 SHA-256 `777471d3befa228857e951d01122dc7904f009c78d918b9f5e7681101bf5f376` 与候选完全一致，其他窗口 overlay 保留。`shared-compiler-applied.json` 记录授权与前后字节。

真实工作树已重新执行 S01 canonical `prepare`，request hash 与 binding hash均保持下方原值，paid effects=0。`contract-workspace-regression.log` 保存实际工作树365项相关回归通过，333.79秒，包括审查后补充的重新封存删词、换说话人、换轮次断言。source/tests 字节核对无漂移；实际 compiler 与独立审查候选完全一致，不将此应用操作称作新的语义修订。

代码实现已落地，工程发布仍 `BLOCKED`。Parent 仅暂存自有10个完整文件及 compiler 的22行自有 hunk，运行 `python -m scripts.agent_harness verify --staged --level focused --run-id shizhen-untimed-contract-focused-20261025-001`。Harness 在执行检查前拒绝：`staged scope also has unstaged edits: ['src/ai_video/production/video_compiler.py']`，见 `harness-focused-attempt.log`。该失败不是回归测试FAIL，也没有产出可声称PASS的精确 Harness receipt；不能用工作树测试或隔离副本结果覆盖它。focused受阻后未继续related/full，没有改规则或stage他人overlay。

保存 `task-staged-attempt.diff` 后，Parent逐项核验index只有自己的文件及hunk，释放自己的staging，工作树全部字节保留，index恢复原先空状态。当前既有即梦 native grammar owner `src/ai_video/production/jimeng_prompt.py` 也仍是其他窗口的untracked文件；不把它夹带进本轮提交。未commit/push、未发布、未生成视频，也未新增付费调用。

最小恢复条件是共享 compiler 的其余改动由原owner先完成独立归档，使本轮能形成没有同文件unstaged overlap且包含所需既有依赖的精确快照；之后沿原Harness focused→related→发布前full与owned-hunk Git流程。无需重复索要本次22行hunk的授权。当前工具树中没有该其他窗口的writer可供接手协调，已保留其现有工作。

最新development-only总状态见 `contract-workspace-final-receipt.json`；下方是授权前的保留历史，不再代表当前工作树的guard应用状态。自动 `record-ai-video-session` / `distill-ai-video-learning` 复评仍为 `no_candidate`：确定性工程证据不构成独立媒体质量实验。

## Initial Checkpoint — Before Shared-File Authorization

用户原任务是原创三至五分钟3D悬疑剧《失帧》EP01，并指定 Jimeng Provider / `seedance_2.5`，随后明确“那你先把契约改了”。媒体生成因此暂停，先补不带台词时间戳的多人自然交谈契约。原任务剧本、31镜头与276秒弹性预算保存在 `docs/superpowers/artifacts/drama/shizhen-episode-01/`，不是已生成或验收的成片。

**当时未完成/未发布。** `video_requirement.py`、共享 remote prompt 和 H3 grammar 的本轮改动已在 working tree；必要的统一编译拦截当时只有隔离副本候选，没有写入真实 `video_compiler.py`。该文件与 `voice_routing.py` 均存在其他窗口 dirty 工作，当时已向用户请求保留全部既有修改、只追加自有校验的归属确认。该初始停点现由上方Continuation取代；不能将隔离副本 PASS 当作当时工作树已修复全部路径。

## Contract And Implementation

现有 `DialogueIntent` 新增 `mode=conversation`，整体 language 加有序 turns，逐轮保存 speaker、原句、画内/画外、口型与听者反应；不接受台词时间字段或旧 scalar 字段混用。旧 `none` / 定时单人 `dialogue` 不增加空 turns，历史无 language 的已固定 hash 回归仍通过。画内说话人必须是 Shot Character，禁止静音的 conversation 和画外可见口型要求。

第一适配范围只到即梦 `seedance_2.5` 原生声音表达；其他尚未适配 Provider/型号、separate voice 和 neutral fallback 应 fail closed。H3 显式拒绝新模式；shared remote compiler 校验 exact provider/model/native audio，输出按顺序、逐字且无台词时间窗的原生文本。旧 separate-voice 动态控制字段清单显式排除新增 turns，避免改变历史控制路径。

真实复现一个必须关闭的失败：旧 MiniMax neutral 路径接受 conversation，却不输出它的对白。拟追加公共 guard 拒绝非所选 surface、静音、分离声音或缺 native prompt；允许的输入还须与 Jimeng canonical grammar 的 exact 重编译一致。该 guard 不重新选择模型、不触及付费状态、permit、资格或 committer。

## Verification And Evidence

证据前缀：`runs/shizhen-episode01-jimeng25-20261025-001/`。

- `contract-red.log`：先运行的两个测试因 mode/turns 尚未存在而失败，确认原缺口；`contract-neutral-fallback-red.log` 保存真实静默丢词回归。
- `contract-related-partial.log`：工作树相关子集136项通过，含旧 hash、schema、原声音路由与现有语法；未覆盖仍待追加的统一 guard。
- `contract-candidate-regression.log`：独立源码副本加拟议公共 guard，365项通过，201.19秒；不是工作树或 Harness receipt。
- 独立 native `reviewer_xhigh` `/root/conversation_contract_review` 对候选作只读审查。`UCR-001` 为 non-blocking 的反向回归缺失；Parent 确认并加入重新计算合法 hash 后的删词、换说话人、交换轮次测试。`contract-candidate-tamper-green.log` 四个帧模式测试通过，覆盖两种帧模式各三种改写；这些测试与365项有交集，不能相加作为独立总数。
- `S01-v3-prepare-output.json`：通过真实本集 canonical strict bootstrap、Planner、Router、orchestrator.prepare 与 Paid preview 的零效果准备；未 start/submit。原首帧经声明的 `first_frame` asset role 绑定，没有假造 accepted 视频终态。
- `S01-contract-preview-verification.json`：native文本3509个UTF-16 units；三轮原句各出现一次、顺序保持，无 `Dialogue timing:`。request hash `cd125af0263d2a763f65b790da8841d25d75f1fc19628ee79ad279bdcabd9bfd`，native prompt SHA-256 `7e9e232e48020fb91ea357849c3797ba3f155e20f5bc5a91b6f334cbaba35941`。此预检不是生成、质量、Production qualification 或 HUMAN/P6验收。

`contract-review-snapshot.json`、`contract-owned.diff`、`shared-compiler-proposed.patch` 与 `shared-compiler-proposal.json` 保存候选字节和真实 shared baseline；总状态由 development-only `contract-checkpoint-receipt.json` 标为 `BLOCKED_PENDING_SHARED_FILE_OWNERSHIP`。

## Ownership And Publication

未编辑其他窗口的 compiler、voice routing、Policy、Skills 或模型资格；没有 stage、commit、push 或外部发布。尚无 Harness receipt，也未宣称完整工程回归。确认共享归属后，先重验当前 shared baseline；漂移时按现有 owner 重新合并，不覆盖其他窗口工作，再对实际写入的候选作 fresh 验证和 owned-hunk Git 操作。

任务尚无视频提交、MP4或积分消费回执。此前内置 imagegen 共3次，输出已复制到本任务 input，结算费用未知；本轮没有以0次视频调用冒充所有制作费用为0。一个本任务新画布与空视频节点已建立，既有项目/账号/历史尝试未复用。模型仍 `UNQUALIFIED`，后续只能按现有 qualification/development preview 与逐镜声画 Gate继续。

按 `record-ai-video-session` 记录此真实归属 blocker；自动 `distill-ai-video-learning` 评估为 `no_candidate`。本轮是确定性契约及编译验证，尚无独立真实媒体对照，不创建学习占位项、不修改全局 memory、不升级 Skill、Policy 或 Gate。
