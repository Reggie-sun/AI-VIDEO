# Dandelion Postman

## Current Request

用户原话：不要用之前的图和剧情,你用这个skill重做视频我看看

## Creative Brief

全新原创《蒲公英邮差》，12秒，16:9，微缩定格动画质感。一个浅青色小邮差机器人，黄色邮袋，一株蒲公英，午后草地。观众先看见机器人认真赶路，继而看见它因一粒种子停下；以小小意外带来温暖幽默。

动作：机器人向蒲公英迈两步停下；一阵风吹散部分种子；它随种子缓慢抬头，一粒落在头顶，保持短暂停顿。一个连续镜头，机器人左、蒲公英右，不越轴；相机缓慢微推。开始种子完整、头上无种子；结束部分种子飞散、机器人停下、头上一粒种子。不要求精确关键帧时间控制。

声音：草叶风声、两步轻金属脚步；无对白、无字幕、无音乐。同期声音须对照实际视频验证。

## Skill Application

实际读取 LearnPrompt/awesome-seedance 的 seedance-production-workflow，固定commit 67df3707a4f25f860088790fb0a74d8f99a50cbb。来源 https://github.com/LearnPrompt/awesome-seedance/blob/67df3707a4f25f860088790fb0a74d8f99a50cbb/agents/skills/seedance-production-workflow/SKILL.md

采用：简单单镜、清楚入口出口、每张参考单独说明职责、实际结果逐项检查、有问题定点修复。题材和具体画面为本次独立创作，不复制案例剧情或prompt。不安装、不运行外部脚本、不另造Production owner。

## References

全新imagegen图一张；不输入任何旧图片。用途是机器人身份、衣物/邮袋、蒲公英与空间、美术的软参考；不保证精确首帧或种子落点。禁止继承其他作品的人物、场景、剧情与音频。低速简单单主体，暂不制作白模或动作视频；微小种子落点仍属待验证的模型控制风险。

## Status

全新参考图已生成并展示，见reference-v1.png及reference-review.json；视频未提交。新的exact参考图展示后，用户回复“可以”，已认可本片参考与12秒方案。预算下一步封存一次12秒单元，不复用旧permit或旧submit意图。

## Checks Before Delivery

只出现一个机器人；两步→停下→种子飞散→抬头→一粒落头顺序；身份与邮袋保持；种子不变鸟/火花；连续单镜无宫格；同期声音、完整12秒原速观看；好不好看由用户判断。静态图不能证明上述动作完成。

## Generated Review

已一次生成12.065秒1080p原片，dandelion-postman-001.mp4。步数偏多，声音要求未完全确认，Gate FAIL；未继续重抽。原片待用户观感判断。详细见production/post-media-gate.json。
