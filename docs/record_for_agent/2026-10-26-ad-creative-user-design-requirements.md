---
record_kind: session_summary
topic_id: ad-creative-user-design-requirements
learning_eligibility: ineligible
---

# Ad Creative User Requirements

Date: 2026-10-26

## Scope And Authority

用户明确否定当前广告效果，要求把已提出的设计要求写入广告 Skill。本次直接修改
`ad-creative`，属于用户授权的作者要求更新，不是从媒体实验推导或自动采纳 Learning Claim。
此前对7秒开场的认可不能扩展为对新15秒合片或完整广告的认可。

## Changes

入口明确3秒内产品可辨识、场景与人物处境、问题到使用及效果的因果、后段产品功效表现、
完整品名入声，以及接镜必须规划剪辑。视频参考补充真实前镜 handoff、参考与首尾约束的区别、
逐接缝检查画面及声音、删除重复动作/台词/无意停顿并保留完整对白。

颜生源的40–60秒、完整产品名和“栖澜百货商贸”慢水印独立标为该项目 brief，
不把商户名与时长套用到其他商品。保留既有 Product Truth、制作/时间线 owner 与验收边界；
这些文字不代表新建或已实现 Harness enforcement。

## Verification And Limits

`skill-creator/scripts/quick_validate.py .agents/skills/ad-creative` PASS；任务路径
`git diff --check` PASS，Parent逐项对照用户原要求。仅改 Skill 与本记录，不运行媒体、Provider、
网络研究或完整工程测试；既有其他窗口及先前影片工作的 dirty/index 不纳入本次提交。

自动学习评估：`no_candidate`。本次来源是用户明确要求，没有把失败试片或单次技术通过当成
可泛化的模型效果结论。影片仍未获整体认可、未发布，Skill 不保证模型效果。
