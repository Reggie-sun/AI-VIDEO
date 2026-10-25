# Authored Visual Revision Implementation Plan

**Goal:** 保留既有付费生成历史，通过正式素材修订与一次有限追加生成，交付用户选择的 D 版 S01。

**Authorization:** 用户已选择 D 版人物风格、要求开始首镜，并在说明正规执行入口阻断后明确回复“我授权”。

**Current / Target Behavior:** 已 fetched 的旧结果仍处于 VALIDATE，阻断素材更新。增加用户明确要求视觉改版时的 canonical supersession：旧结果以明确的创作改版原因结束，保留原始媒体、paid receipt、观察及未验收状态；随后使用标准 Project / Registry revision、新 goal 与现有预算和 quota extension owner 执行一次新生成。

**Invariants:** 不伪造旧 rubric 的失败或全 NOT_EVALUATED；不把用户认可表演方向冒充音画全部通过；不改历史计数、费用、UNKNOWN；不更换 provider/model、不重用 permit；新版本保留旧叙事、对白、时长、音频要求及全部验收要求。Supersession 不授予重试、验收、结算或模型 qualification。

## Ownership And Files

Parent 负责新 goal qualification admission、正常 authoring revision、执行与交付；独立叶模块负责 typed supersession receipt、committer closure 与 strict-reader 验证。所有共享文件保留现有 overlay，只增加必要接线。主要涉及 `generation_execution.py`、`_state_commit_video.py`、`_lifecycle_schema.py`、generation feedback reader、一个独立 visual revision 模块及相应测试。

## Milestone 1: Preserve And Close The Prior Version

正式 receipt 绑定明确用户授权、actor、旧 request / fetch / experience / project / goal 和新 goal / 首帧 SHA；committer 在锁内核验 paid ACCEPTED、exact fetched VALIDATE、无未知生成、无 activation，保持旧 evidence 原样。Replay 必须 exact，无副作用。Reader 拒绝篡改或缺失 receipt。测试覆盖混合 PASS / NOT_EVALUATED 观察、陈旧 revision、未知结果、错误媒体及不同 replay。

## Milestone 2: Admit One New Authored Version

新 goal 同 goal_id 不同版本并保留旧 requirements；新首帧必须确实改变。Pure binding 校验完整历史与累计 used + 1 ceiling、相同 provider/model/output、零 resample；submit lock 重新打开 exact canonical supersession，核对新 goal 与首帧，不允许 caller flag 替代。使用已有预算、quota 和 one-use permit owner，不增第二执行链。精准测试与相关契约回归通过后，一名 native reviewer 审查冻结候选。

## Milestone 3: Generate And Present D S01

先持久化上一结果的真实观察，再 supersede；标准 asset import 与 authoring revision 绑定 D 图。沿现有路由 compiler/preview/paid gate，累计额度由 2 增至 3，追加一个有时限单元，旧预算 reservation 原样保留。检查 native quote、完整动作、三轮无固定台词时间戳的对白、轴线和固定中景，再提交一次。结果已知时 fetch，显式调用 project-local video-analysis，交用户正常速度审片；UNKNOWN 停止，不重试。

## Verification And Completion

精准与相关模块测试证明软件边界，独立 review 证明审查范围；真实 provider receipt 证明生成，exact MP4 + video-analysis 记录媒体观察，用户审片才证明效果认可。先交片，用户认可后执行完整工程检查与 owned-path commit/push。当前不发布，不自动生成下一镜。费用仅报告真实 quote/settlement，未结算标待确认。
