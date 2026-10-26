---
record_kind: session_summary
topic_id: shizhen-season01-world-and-survival-bible
learning_eligibility: ineligible
---

# Lost Frames Season One Creative Bible Record

## Naming Supersession — 2026-10-27

下文保留前轮输入、旧名称与原快照身份。用户随后要求直接改名，第一季正文的现用称谓和验证入口已更新，见 [Naming Record](2026-10-27-shizhen-naming-design.md)。原世界机制、人物身份、剧情与媒体接受边界不变；下文旧名称不再代表当前开发正文称谓，前轮审读不冒充新名称的人类验收。

## Scope And Current Creative State

用户提供完整世界观V1，随后明确要求补足现实校正、主动猎杀、规则求生、能力实战、势力围捕与具体主要对手；最终收窄为“就写第一季就够了”。本轮按最终范围完成第一季创作开发，不展开以后各季，不执行付费图片、视频或音乐生成。

入口：`docs/superpowers/artifacts/drama/shizhen-episode-01/series-index.md`。同目录12份Markdown包含十类要求的实质创作稿、第一季整体框架、12集推进与第一集可演出的求生增补。W01–W12是唯一底层规则，A01–A06能力、F01–F05组织、N01–N08异常只引用，不另设运行权威。

新增世界观、人物、组织、事故解释与新戏均为PROPOSED CANON。AUTHOR SECRET继承待确认状态，不等于已有制作依据。原剧本、原coverage、已认可媒体与Production state不因落盘、Git提交或审读而升级／覆盖。

## Sources And Preserved Boundaries

使用retrieve-ai-video-memory的all查询发现带stale标记的advisory片段，随后重开原剧本、设计、coverage、提示词、冷开场、音乐与用户反馈来源；没有等待或重试索引更新。只读原生context_search_agent整理历史反馈，Parent核验关键原文与exact边界。

`source-review-snapshot.json`共80个来源条目，其中47项原创作文件／受保护媒体字节在本轮复核未变。它是identity与来源目录，不表示每个历史视频已全片听看。S01 HD005与《两位》组合片通过project-local video-analysis重读元数据／实际帧，未进行新的完整原速听看、remote识音或旧UNKNOWN重试。

重要区分：S01 HD005历史CG原片有用户“认可”；后续“全部变成真人感觉”替代旧视觉目标。S04获准对象是接点修正版；S05-001因笑意与发声失败，002已fetch但读取时仍待用户接受。《两位》概念获准，组合片REVIEW_READY、human接受仍NOT_EVALUATED。旧纸穿透、悬枪、口型和接点错误不能改成剧情伏笔。

## Creative Results

- 生存发动机：首集实际受伤、普通自救与求助；E02身份／帮助断裂，E04兑现第一次03:17窗口。无新增每日第二次失帧。
- 六能力分工、存在代价、反制、训练与完整走廊冲突；普通人的工程与救护可决定结果。唐姐、骑手维持普通人和真实善意，不回收为阴谋角色。
- 自觉体陆衡为本季主要对手，保护来源与主动猎杀并存；余像群不是全恶。五组织均有资源、交易、内部路线与季内变化。
- 候选未来有来源但非命令；原片中的人仍是真实候选林序，脸必须本来存在于源像素。林晚未完成全因果删除，故旧照片与报案可以存在；照片非万能免疫。
- 季终何萍、冯有年两名悬置者自愿返回；赵芸来源耗散无法救回；高峥仍缺足够来源，罗敏保留见证。妹妹共同体自主决定有限接应，不预写重逢或未来季。

## Independent Review And Candidate Identity

使用一名原生read-only `reviewer_high`，无nested delegation。工程Risk Gate未发现凭据、运行／持久化等重大风险；独立文本审读用于用户要求的创作交叉核验，不替代媒体或用户审美判断。

1. 初审候选package `e10132b7e27f4561a7b3cf6f4fd434160ad0855b9791c1f32b085260cf72a074`：SZ-C01 non_blocking指出首夜目标识别无普通信息渠道。Parent判CONFIRMED。
2. 修订为普通外勤隔窗观察求证、普通电台派单、首夜仅疑似，E04才确认跨侧支撑、E05核验业务记录。候选 `b2a09435066f078eb53fbbf17eb1ccd251ec1192398edf1015bc0564b748e44f` 定向复审finding set为空。
3. 用户收窄第一季后删除后续季剧情，同步人物、组织、揭露表与具名救援结果。最终候选package `f8af9ece8b338eb3c74ffecd9b2f326a9520c902d483ed5b6d4ab6973680186f`，13份正文／plan哈希由同一reviewer重开，第三轮定向审读finding set为空。轮次未重置、未增第二reviewer。

候选清单与各文件SHA在同目录`series-bible-verification.json`；reviewer没有审读或签署尚不存在的成片。Parent完成最终范围与原来源保护核对，没有未解决的创作finding。

## Verification And Evidence

当前正文的docs contract检查通过；61个本地文件链接有效；12条W规则、16个逻辑问题、6能力、5组织、8异常、12集存在与placeholder扫描通过；未来季剧情章节已移除。这些只是结构／文本证据，不证明人物表演、镜头可行性或观众理解。

首轮focused Harness仅运行适用docs_contract_check并通过，后因作者修订变为旧快照，不冒充最终证据。最终exact snapshot／commit-range回执入口：

- `.agent/harness/runs/shizhen-season01-bible-focused-final-r2-20261027/receipt.json`
- `.agent/harness/runs/shizhen-season01-bible-full-r2-20261027/receipt.json`
- `.agent/harness/runs/shizhen-season01-bible-commit-focused-20261027/receipt.json`

全仓policy audit已有13个未映射工程路径，其中7个测试未被check引用，涉及authored retarget、qualification、preview与watermark等；不是本轮创作文档。本轮不修其他writer源码、不放宽policy、不刷新baseline。full attempt与receipt freshness必须据实际回执报告，不能把局部文档通过升级成完整工程回归。

初次最终staged focused实际通过，`fresh_for_snapshot=true`、integrity=true；随后full attempt的scope与docs通过，在`agent_rules_check`因共享`AGENTS.md`超出文档预算停止，未运行full suite，也尚未到policy audit。原失败回执保留为`.agent/harness/runs/shizhen-season01-bible-full-20261027/receipt.json`；不是本轮owned路径，不修改该规则文件。为使最终记录也被exact验证，重封本记录和开发核对JSON后，使用上列r2回执入口，不覆写旧回执。没有把工程阻断扩大成创作未完成或新增Canon已确认。

仅stage并提交本轮新增文档、两份开发核对JSON、plan及本记录，不携带共享dirty工作。Git publication以实际commit/push与远端SHA读回为证；无媒体发布、Production activation、P6或Final Acceptance。

## Learning Evaluation

`record-ai-video-session`评估为record；自动`distill-ai-video-learning`评估为`no_candidate`。这是创作开发与既有来源核对，没有新增可归因的模型多次实验或受控比较，不制造学习候选、不修改Skill／Policy／Gate，不写全局memory。

## Remaining Limits

新增Canon仍待用户明确创作确认；后续集长为建议，当前制作风格及已认可媒体保留。新增检修口接触、空间错接、能力对抗、声音与整集容量尚未实拍／生成验收。完整事故解释可以作为本季作者秘密存在，不意味着已编写以后各季。
