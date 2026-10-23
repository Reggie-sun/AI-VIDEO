---
record_kind: research_note
topic_id: five-drama-skills-role-design
learning_eligibility: ineligible
---

# Five Drama Skills Role Discussion Record

Date: 2026-10-24

## Purpose And Scope

用户提供 Shuohao、Zenstory、Liyue Seedance 2.5、DirectorSKILL、Kangarooking 五个仓库，要求原生团队讨论如何各司其职，允许修改或优化。随后收窄为 Drama / 剧情短剧层，广告层暂不动；允许识别共用能力，并希望增加子代理。

本轮形成 advisory 接入方案与一手源码审计。没有安装、修改 Skill 或 Runtime、接管广告层、提交生成任务，也没有新的视频输出。之前热敷贴制作的未提交文件和媒体保持原状，不属于本次提交范围。

## Findings And Decisions

完整设计归 [role design](../research/2026-10-24-five-drama-skills-role-design.md)，固定版本与许可依据归 [source audit](../research/2026-10-24-five-drama-skills-source-audit.md)。五库并非五个同等层级的单技能，其中三库含多个子技能，整体安装会重复编剧、分镜、执行和状态职责。

建议分工：Zenstory 负责剧情/分集/剧本；Shuohao 负责角色/场景/道具制作设定及开场站位提案；DirectorSKILL 提供动态调度、摄影覆盖与剪接方法；Kangarooking 只取表演和按需动作编排；Liyue 仅作为选定 Seedance 2.5 后的表达参考。Native Codex + `open-video` 保持唯一导演整合，剧情事实遵守已 accepted 的 Drama contract；既有 `seedance-authoring` 与 exact adapter 保持模型表达职责。

不引入第二项目状态、独立 active 站位表、表演 timeline、剪辑 timeline、外部 Dashboard / project_tool / Miora/watch 或第二验收链。保留上游有用的分镜、审读和剪辑方法，由对应本地 owner 调用；不是全删重复功能。

连续性可以在同场景或跨场景成立；必须承接剧情因果、人物知识/动机/情绪、实际动作/物件/空间和声音。没有明确场景重置时，续拍从已接受实际前镜状态继续，不能回到旧 Prompt 的预期开场。文本或技能审读不能替代 exact 媒体及相应 HUMAN evidence。

## Team Discussion

使用四名原生子代理，无 nested delegation；前三名并行，第四名在并发位释放后检查交接反例。

| Agent | Actual profile | Scope / outcome |
| --- | --- | --- |
| `five_skills_local_ownership` | `architecture_auditor` | 只读核对本地 owner、accepted Drama spec、continuity 与 authoring 边界，参与交叉质疑 |
| `five_skills_sources` | `bounded_worker` | 唯一 writer：source audit；核对五源实际 SKILL、许可与限制，参与交叉质疑并明确交还文件 |
| `five_skills_drama_design` | `conceptual_planning_agent` | 只读设计五职、交接和条件路由，反对平行站位 truth、全删有用审读方法及强制五库参与 |
| `five_skills_handoff_stress` | `test_analyzer` | 只读检查跨场景、夸张局部修复、2.0/2.5 错配、真实前镜与开场提案冲突四个文本案例 |

交叉质疑促成三项具体修正：Shuohao 开场提案并入 Director 整场调度同一稿；Zenstory 的方法保留但不导入独立执行/接受状态；Kangarooking 固定动作秒数、反馈和运镜配方降为条件建议，不覆盖用户表演强度。第四名检查发现初稿手机示例把扣屏错误地当成拒接，已换成更简单的钥匙跨场景例，并限定无场景重置时的承接规则。

这些是设计讨论与文本反例检查，不是四名独立工程 reviewer 或四次真实审片。Parent 对最终方案自审；本轮仅新增研究文档，不触及 Runtime、安全或 durable state，`NATIVE_REVIEW_NOT_REQUIRED`。

## Verification And Evidence

读取当前 `AGENTS.md`、`SUBAGENTS.md`、owner matrix、accepted Drama spec 与现有 `open-video` / `seedance-authoring`。跨类别 Agent Memory 查询返回 stale last-good advisory 片段并自动排队维护；直接重开当前 owner 核对，不等待、重试或把历史片段当当前实现。

五源固定版本及完整 Markdown/许可下载清单位于 `/tmp/ai-video-five-skills-20261024/`；该缓存不是 durable 产品资产。Parent 对全部 **514** 份已下载文件核对 byte size、SHA-256 与 Git blob SHA-1，全部匹配，无下载错误。未核查未下载的脚本、图像或二进制，不构成代码安全审计。

文档快照：

- `docs/research/2026-10-24-five-drama-skills-source-audit.md` SHA-256：`d2839d9b2ff8e34d5e01dd59064a9f9a58136e6d5dd9ab9bd1f972357584ddf5`。
- `docs/research/2026-10-24-five-drama-skills-role-design.md` SHA-256：`c131d5446ad79ea67500a8236a3447e779a5b5f9a8766cdefffedb86c19e49f8`。

相对链接存在性检查通过；`python -m scripts.docs_contract_gate check` 实际返回 `Documentation contract gate passed.`；提交前对本任务三份文档运行 scoped `git diff --cached --check`。没有运行上游脚本、Provider、媒体、完整回归或观众实验。本次 Provider 消费为零；公开 GitHub 文本读取不涉及视频积分。

## Learning Evaluation And Remaining Work

按 `record-ai-video-session` 评估达到 substantial research checkpoint。随后按 `distill-ai-video-learning` 评估为 `no_candidate`：此次是来源与职责研究，没有新的独立媒体实验/对照，也不将五库数量、514 个文件或四名代理作为经验独立性证据；不创建 Learning Claim。

后续 Skill 接入与媒体效果验证仍未实施；Drama Runtime Gate 2、P6 和 Final Acceptance 不因这次设计完成而变化。可共用的调度、表演、连续性和模型表达原则与 Drama 专属语义已分开；广告层实施与新广告 Skill 研究均 deferred。

本次 checkpoint 的 task-owned paths 仅为本记录与上述两份研究文档。文档发布状态以最终 commit/push 核验为准，软件/媒体 release 状态未改变；没有本轮 Harness 或媒体验收 receipt。
