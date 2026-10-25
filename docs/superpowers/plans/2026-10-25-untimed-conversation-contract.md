# Untimed Conversation Contract Plan

## Goal

按用户“那你先把契约改了”，先实现不带台词时间戳的有序多人对白契约，保留《失帧》完整制作目标并暂停媒体生成。使用现有 `DialogueIntent`、requirement、Jimeng compiler 与 lifecycle，不建立第二执行链。

## Contract

新增显式 `mode=conversation`，包含整体语言与有序 turns；每个 turn 封存 speaker、逐字台词、在/画外、口型要求与听者反应义务，不含时间戳。保留原有 `none` 和单人定时 `dialogue` 的输入、序列化及 hash，不自动迁移旧 artifact。Conversation 与旧 scalar/timing 字段互斥。原生模型自由安排说话、停顿和倾听；不能把自然节奏当作精确时间保证。

首个可执行 surface 只支持当前用户选择的 Jimeng `seedance_2.5` 原生声音路径，按实际 profile 验证；其他尚未适配的 compiler 和 separate-voice 路径明确 unsupported。真实质量、资格、预算、permit、UNKNOWN、逐镜 Gate 和用户审片要求保持。

## Files And Verification

在 `video_requirement.py` 的现有契约 owner 增加 turns 与兼容序列化；在 `_remote_video_native_prompt.py` 的实际共享编译路径表达有序对话并校验 exact selected provider，在必要的其他 grammar owner 明确拒绝。修改前核对各文件 live Git 状态，只碰未由其他窗口改动的文件。

严格 red→green：先在既有 mapped tests 中复现无时间多人对白无法建模；验证 turns 保序与原文、禁止混用时间、完整 native 编译/resolve、声义与说话人控制路径、旧 hash、unsupported provider/voice 与 no-audio 边界。完成受影响模块精准测试和相关契约回归后，一名 native read-only reviewer 核验 exact snapshot。独立审查不能代替视频效果。

## Completion

Canonical 使用说明记录新输入与明确支持范围。用《失帧》S01真实首帧和原台词做零付费编译预检，封存 native preview 和自然对话顺序。此阶段不提交视频。按当前分级 Harness/owned-path Git 规则验证与提交，受其他窗口或既有回归阻断则保留证据并说明；不擅自修改 dirty shared owners 或偷过全量验证。
