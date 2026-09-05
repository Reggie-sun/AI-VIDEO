---
record_kind: session_summary
topic_id: jieshi-episode-01-authoring
learning_eligibility: ineligible
---

# Jieshi Episode 01 Authoring

## Current Model Selection Update

2026-09-05用户最新指令“用seedance2.0吧”取代初版2.5选择。
当前目标为标准版 `doubao-seedance-2-0-260128`，capability
`seedance-2-0-260128-image_to_video`，1080p、9:16、1080×1920、24fps。
下方初版2.5选择与review/receipt均保留为历史，不证明更新后的执行状态。

本次仅修改原创作包的模型目标、画幅参数、源约束及派生hash，没有修改Runtime路径或契约。
由主线程完成这一有界文档调整；没有新增subagent或Provider调用。
现有capability的canonical SHA-256：
`10a7f345de52722d419b0a41f6cf514e3f0a32bc1027e67d09bfd99ca00f3a29`。
当前proposal SHA-256：
`433434377d96a14fa3dc4efce4428acfa1b599d3c81db6afedfd26a2ddf459e8`。
65个计划生成素材均为4–9秒，符合本地capability的4–15秒范围。
实际运行Director validator与verification.md内只读检查：16beats、52shots、300秒、
69个typed artifact及hash通过；逐项对比前版story/cast/scenes/beats/ordered_shots完全一致。
输入素材仍未绑定，不能把静态参数支持当作账号权限、实测清晰度或执行就绪。

当前模型版本的commit-range Harness receipt预定为
`.agent/harness/runs/jieshi-e01-seedance20-20260905/receipt.json`，实际结果以receipt为准。
record-ai-video-session评估为更新同一主题记录；distill-ai-video-learning为`no_candidate`，
没有新增独立媒体实验或现有Learning Claim变更证据。

## Purpose

为《界蚀》第一集《不存在的终点站》完成用户要求的300秒创作包：
剧情节拍、Scene、Shot、台词、动作、镜头与生成提示信息。
用户后续允许Seedance 2.0或2.5并要求更高清，本轮选定Seedance 2.5原生1080p档，
目标9:16、1080×1920、24fps。没有请求或交付已生成MP4的虚假状态。

## Artifact Owner

主创作包目录：`docs/superpowers/artifacts/drama/jieshi-episode-01/`。

- `creative-input.md`：用户brief与模型、清晰度补充。
- `director-coverage.json`：现有open-video schema v3，16个beat，300秒。
- `episode-01.proposed.json`：详细创作提案的唯一内容源，52个剪辑Shot、66个素材component。
- `episode-01.md`：由提案整理的人读全分镜与逐镜提示。
- `creative-artifacts.json`：69个现有Pydantic模型的派生快照，绑定源JSON SHA-256。
- `verification.md`：验证范围、结果、可复现命令与未验证媒体边界。

不存在新的Episode Runtime类。复用既有ProductionBrief、Story、Character、Scene、
Storyboard、Shot字段；B-D0固定2–3镜的fixture acceptance不适用于本集，未复用其PASS。
本包未materialize ProductionProject，也未调用load_production_project、Manifest或Registry writer。

## Decisions

- 先执行retrieve-ai-video-memory，再完成open-video Director coverage并通过validator；
  semantic continuity参考hell-grind-aigc-skill，Seedance表达仅使用2.5 overlay。
- RAG返回tagged stale experience fragments；未作为本次能力或验收事实，也未前台重建。
  当前模型结构和profile从代码重新核对；主线程另用codegraph查看Shot的关系。
- Exact authoring target：`doubao-seedance-2-5-260628` /
  `seedance-2-5-260628-image_to_video` / `seedance-2026-08-19`。
  I2V使用adaptive比例，1080×1920是首帧/成片目标，实际输出尺寸必须实测。
  未创建带pricing/egress的执行profile，也未读取credential。
- 三秒钩子保留用户广播与字幕原句；最后十五秒固定母亲遗忘、监控缺席和J-000提示。
  预见是七秒后的可干预错误分支。两次使用之后，林砚的工作群记录与工牌先后清空。
- 独立审读发现并修正首镜动作提示遗漏、先上车不能回应先下车规则、
  P2局部身体漏登记、C/D门混淆、手机/布袋状态及跨素材短口型等问题。
  修正保留原时长；普通乘客明确先从相邻既有车门下车，两位主角才离车。
- 用户随后要求不用字母当姓名。正文、台词标注和prompt现用林砚、苏遥、周伯祥、
  陈立、许雯、郭向东、沈嘉程、何静、周惠、赵晨；广播保留声源名称。
  稳定character_id/speaker_id仅供机器关联。苏遥姓名只作制作标注，本集不新增身份揭露。
  已逐镜对照改名前暂存版本：镜头顺序、时长、角色ID、逐字台词与生成目标均未改变。

## Verification

实际运行Director validator：`passed`，16个coverage units、300秒。
实际运行现有模型与canonical hash验证：69个artifact通过；17个Storyboard分组，52个Shot。
实际检查逐镜连续时间、角色/Scene闭包、source SHA、台词窗口、24fps素材裁切、
首镜逐字广播/字幕、最后十五秒与监控中的LY缺席，结果通过。

Native `reviewer_high`完成独立审读与同tier scoped re-review，最终 `accept`，
无剩余Blocking issues；主线程直接复核重要修正，并重验派生hash与focused checks。
改名前复核的proposal SHA-256（保留历史）：
`48ec205ef97e4df55744dec3f80d4fc77a2cdc2e59920a53c26278aa87ddab3f`。
姓名修改后的proposal SHA-256：
`6f1bdb6d8f0f42cb3a9f3d41ffc1db2206f991330dfdbcac17d14c8b790143ee`。
该姓名修改另经同一native reviewer_high scoped re-review，结果为`accept`，无阻断。

65个候选生成素材最少计划源时长337秒，加1个末帧复用，剪辑恰好300秒。
这不是已发生调用数，不包含首帧准备和重试，也不是预算reservation。

最终exact-snapshot Harness receipt：
`.agent/harness/runs/jieshi-e01-authoring-names-20260905/receipt.json`。
实际状态、freshness与artifact integrity以该receipt和本次最终交付为准，本文不预写结果。

## Learning Evaluation

按distill-ai-video-learning自动评估为 `no_candidate`。
本轮没有两个独立真实实验、受控多arm比较或更新既有学习claim的媒体证据，
不创建占位Learning Claim，不修改Skill、Provider Policy、Preflight或Gate。

## Remaining Boundaries

本轮没有Provider submit/poll/fetch、图片或视频生成、音频生成、上传、发布、P6或Final Acceptance。
首帧均为待准备需求，prompt是未绑定实际asset的草稿。
实际制作前仍需exact参考素材、连续性binding、当前profile、有限budget/egress/intent/permit、
现有合成能力确认、逐Shot video-analysis以及全速人工观看。
静态authoring验证和review不能证明清晰度、口型、连续性体验、抖音审核或观众留存。

当前checkout其他writer的变更保持原状，未纳入本任务stage/commit。
