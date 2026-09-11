---
record_kind: session_summary
topic_id: jieshi-s05-first-frame-preparation
learning_eligibility: ineligible
---

# S05 First-Frame Preparation

## Outcome

用户要求开始 S05，并明确确认 S04 画面与原生声音可保留。本轮保存 S04 exact 人审和 next-Shot raw Gate，制作 S05 首帧候选。尚未提交视频、创建 S05 Production root、导入候选或签发 permit。

S05 按既有分镜回到林砚的窗与座位，抬左手并慢慢握拳，倒影同步恢复；原生声音延续开启意图。静态候选保持左手低位，窗中已出现林砚倒影。动态同步与成片质量尚未验证。

## Evidence

- S04 MP4 SHA-256：`a2a0251715de19e52d5ba80c335db06afb89f083c0c546cf5cd7c246b64aee4e`，本轮重新计算匹配；人审原话“可以”及所回答问题保存在 `runs/jieshi-e01-i2v-20260907-attempt10/preparation-s04-v1/s04-attempt01-human-confirmation.json`。新的 `s04-attempt01-human-next-shot-gate.json` 保留旧 Gate hash；只更新 raw acceptance，不证明 P4 混音。
- 使用 `load_production_project()` strict reopen `production-s04-v1/project.yaml` 定位 S01 registered image，参考 SHA-256 `4134d69125a7b00c322bf987e2c9feef7d73ddd8968f764cc5310282d68d30fb`；不是 S04 尾帧或未注册视频截图。
- 内置 `image_gen.imagegen` 编辑该参考一次；实际 prompt、候选、测量与来源保存于 `runs/jieshi-e01-i2v-20260907-attempt10/preparation-s05-v1/`。候选名 `s05-first-frame-candidate-v1.png`，完整 SHA/尺寸见 `first-frame-result.json`。不声称具体 backend model。
- `retrieve-ai-video-memory` 已执行 experience 查询，返回含 stale 的 advisory fragments；本轮事实来自 exact 本地输入、分镜与当前代码。没有将历史提示当作当前 PASS。

## Remaining Boundary

`HumanImageImportReceipt` 需要 human approval，且时间不得早于 image import。用户对 S04 的确认不自动覆盖之后才生成的 S05 PNG；候选需展示并获确认后，才能通过既有导入与 Planner/Router/compiler/Provider seam。视频 task ceiling=1，used=0，未新建付费调用。当前首帧制作是 Agent 为 S05 机位与反射状态选择的准备动作，不宣称 Router 已比较并判定 I2V 为实证最优。

## Verification And Learning

检查图片可读性、实际尺寸、SHA-256 与 S04 exact MP4 identity；无产品 source 改动，无 fresh isolated Harness receipt，无视频生成或质量 PASS。`record-ai-video-session` 稳定 checkpoint 已记录；`distill-ai-video-learning` 自动评估 `no_candidate`：单张未获人审的候选不满足重复实验或受控对照阈值，不创建 placeholder。其他 staged/dirty files 保留。
