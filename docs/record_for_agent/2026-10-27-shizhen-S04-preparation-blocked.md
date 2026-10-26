---
record_kind: recovery_incident
topic_id: shizhen-S04-predecessor-audio-unknown
learning_eligibility: ineligible
---

# Shizhen S04 Preparation And Audio Unknown

## Reference Supplement After User Review

用户指出只有两张取帧不够后，实际补做两张Shot4动作关键帧：`S04/references/03-check-side-passage.png`（保持右手近身持手机，查看既有侧通道）与 `04-phone-lowered-look-to-rider.png`（同一右手手机降低至髋侧，头/视线转向画外骑手）。两次image_gen均已取得明确结果、复制到任务目录并实际查看；瓶直立、枪落台且在瓶左、饭团仍在白纸，店员没有重现。source.json保存实际输入图hash、完整prompt、输出hash/尺寸及工具原始路径；帧间运动、声音、口型或人类接受仍未验证。当前共4张，前2张actual取帧、后2张拟定动作图；`S04-intent.draft.json`与`reference-evidence.json`已同步4个planned参考，不代表视频模型已收到素材。

本次补图新增image调用2、video0、audio0，图像费用未暴露；原声音UNKNOWN/已消费permit保留，未重试、未生成Shot4。下方“两张/无额外图像调用”是补图前检查点，已由本节更新参考准备状态。模型兼容性与S03 Gate阻断不因参考变多而解除。

## Current Result

用户明确“开始shot 4”。S04真人镜头意图与两张actual source参考已准备，GenerationIntent结构验证通过；未提交S04视频。不是已完成镜头，也不是只凭工具成功签PASS。当前硬阻断为S03-005声音补证的已消费调用UNKNOWN，不能盲重试。

## Exact Source And Prepared Work

源S03-005 SHA `51bf0aaea2deaa8f02fb2a8f3f4f2666a8cd6304e5f9f80f5598fd7eab87368f`，当前33.875秒连续版 SHA `45fb4e45f815bbe00f42165429dd5f19335e2dbf60ef4206710e09755308f233`。S03末尾已俯身找过柜台下、右手手机在胸腹前，所以S04不再演一遍发现或探头；保留原文两句疑问，再查侧通道、降手机、叫师傅、看向画外骑手。旧剧本CG媒介和S04固定8秒不作为当前约束。

`live-action-regeneration-01/S04/S04-intent.draft.json` 是未封存草稿，不是原生已编译请求。
`reference-evidence.json` 给出实际两图的SHA、尺寸、原MP4身份、请求取帧时刻及原生PTS/序号；
图片1为当前末态，图片2为柜台和稳定物件，不迁移其更早的姿态。没有额外图像生成调用。
最初草稿误用了不存在的dialogue模式名，随后按当前schema改成untimed conversation结构，通过真实模型校验；没有封存或提交错误草稿。

平台只读账号/能力核验：2.0 VIP、multimodal、10秒、1080p可选；按现有native `quoteActions([{id,action}])` 得到available/330credits。首次诊断误用object参数，已保留该无效诊断并以 `native-capability-quote-corrected.json` 更正，不是平台生成或付费重试。当前common compiler的untimed conversation限制为2.5，故模型选择尚未最终封存，不声称2.0可直接执行此对白合同。

## Unknown Evidence Operation

为满足下一Shot提交前的原Per-Shot Gate，使用project-local `audio_understand` 对同exact S03补声音观察。离线preview成功，source34,353,935bytes，完整PCM derivative SHA `d820e0b2ce4a84ec1cfabb007144b29fc0ece03652df2b2290e6593e5f71ddbe`；新建一个development-only unit，固定USD0.05内部上限、count1、25分钟窗口、原supplier与固定Google origin，经fresh project MCP和真实一次性permit提交一次。

`S04/S03-005-predecessor-audio-operator/outcome.json` 明确记录 `consumed=true`、`status=UNKNOWN`、`code=transport_unknown`，intent SHA `3ec46760d937d883f638ce32d3487a0118a006fa9a80ce17172a7987dc90816e`。MCP外层`isError=false`并不证明理解成功；实际content里的typed UNKNOWN已读取并作为停止依据。没有声音观察或可签PASS的结果，未重试、未重铸permit、未更换模型重跑该分析，真实费用待确认。没有把waveform、ASR或native音轨存在当作声音语义通过。

## Counts And Stop

重新严格读取全部当前production roots：S01七、S02二、S03五、cold-open三，共17次已知paid video，均已fetch；Manifest running+validate不被误报为仍生成。未知的是这次额外声音分析，不是历史视频。当前S04 video新增0、无新video节点/root/request/budget/permit。`preparation-status.json` 保留17个历史attempt、拟议下一有限17→18单元、音频UNKNOWN与未封存状态。未生成S05、字幕或新累计片，未发布。

下一步必须先由原证据owner恢复或补齐可靠同bytes声音证据，使S03满足实际逐项条件，再完成S04 exact模型适配与原有准入。不能借“用户要求下一镜”伪造前镜PASS。计划见 `docs/superpowers/plans/2026-10-27-shizhen-S04-production.md`。

学习评估 `no_candidate`：一次UNKNOWN不能证明模型或网络的普遍质量；没有将本次失败扩张为新Skill/Policy规则。此次仅run-local准备和本记录/计划，无共享源码变更；结构验证、native只读quote与真实UNKNOWN分别保留，不当作最终接受。
