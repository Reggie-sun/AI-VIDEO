# Awesome Seedance Pilot Brief

Status: DRAFT / NOT_APPROVED / NO_VIDEO_SUBMITTED

## User Request

那你用awesome-seedance测试下我看看

## Director Proposal

全新虚构人物与调度室，非《失帧》作品或已认可镜头。12秒，16:9，30岁中国女调度员，灰蓝工作衬衫，无logo。桌面固定鹅颈麦克风底座一个红色PTT按钮，另有小扬声器。她原本平静记录，听到扬声器突发短电流声，右食指可见按住按钮，克制急促说“三号岗，收到请回答。”，说完可见松开，手退到桌面。等不到回应，视线转向小扬声器，眉头收紧、呼吸短暂停顿。一个固定略侧中近景，脸与右手、按钮全程可见，无切镜。表达职业镇定被沉默打破。人物、衣服、麦克风、按钮、扬声器与空间保持一致。禁止以切镜、遮挡或道具消失代替接触与释放过程；不增加对白、字幕或logo。动作节拍可在12秒内自然变化，不承诺精确时点控制。

## Method Under Test

来源：LearnPrompt/awesome-seedance 固定版本 `67df3707a4f25f860088790fb0a74d8f99a50cbb`，`agents/skills/seedance-production-workflow/SKILL.md` 与 `references/editable-template.md`。采用 brief、参考作用映射、进入/退出状态与具体失败检查的组织方法。内容为本次独立创作，不复制案例剧情或完整原 prompt。不执行上游脚本，不引入其 plan/run-manifest 或第二条执行链。

本地 `open-video` 继续负责 Director coverage；后续所选模型 authoring 只作能力与语法适配。此单样本是方法可用性试镜，不是对照实验，不能单凭结果证明比旧方法更优。

## Reference Plan

先制作一张干净开场候选图：身份、服装、场景、麦克风/按钮/扬声器位置及起始姿态。它不证明动作过程和表演自然，也不强制模型逐像素继承。不继承图中可能出现的意外文字、错误姿态或道具缺失。是否另补按住/释放状态图，取决于实际首图可见性与检查结果；这些图默认供审核，是否送模型另按模式核对。当前所有图片生成、路径、SHA与认可状态均待主Agent实际结果，不伪填。

## Planned Route And Budget

拟12秒 Seedance 2.0、1080p、16:9；exact profile、variant、mode、渠道可用性、预算金额与最终图片绑定尚未选定或封存。计划仅一次有界视频提交、无自动重抽，后续仍需 exact preview 认可、原有预算与一次性 permit。当前不具备视频提交资格。

## Observable Review

- 起点：人物正在记录，右食指未压红键，麦克风、底座、红键和扬声器可见。
- 动作：右食指接触并按住红键；通话时保持；说完再松开并退手。不能用遮挡、切镜或凭空换姿态完成。
- 声音：短电流声在询问之前；唯一对白为“三号岗，收到请回答。”；结束等待没有回复。口型、声音、节奏需实际声画核对。
- 表演：注意力变化与等待反应可见；“紧张是否可信、是否好看”只由用户判断。
- 连续性：人物身份、衬衫、麦克风位置、红键、扬声器和手指数量稳定；无意外切镜、字幕和logo。
- 结束：按钮释放、手退桌面、视线指向扬声器。

## Approval And Evidence Boundary

coverage validator 只证明已登记结构/引用，不证明意图提取完整、图片合格或视频质量。三个 coverage unit 的3/5/4秒是内部节拍预算，不向模型承诺精确时间码，不是三个生成任务。参考预览尚未获用户认可；没有填写 preview_approval、human quote、Registry 或 Manifest。
