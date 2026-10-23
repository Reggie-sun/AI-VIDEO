---
record_kind: architecture_implementation
topic_id: director-specialists-authoring-integration
learning_eligibility: ineligible
---

# Director Skill Integration Record

Date: 2026-10-24

## Scope And Result

用户要求执行已讨论的五库专责方案，并补充 `coreyhaines31/marketingskills` 的 `ad-creative`；
执行中明确允许删除不合理、冲突和重复内容。本轮完成本地 Agent-side Skills/方法接入与清理，
没有生成、修改或验收热敷贴媒体，没有安装上游项目工具或引入新的 Runtime 执行链。

实现提交：`4118931985a06572806f025105edc102ec59d6c0`；路由精简修复：
`a168f8d8a34867b8f0d1773393c67ce52e24747c`。实现/验证范围为 `285c9f7..a168f8d`，
后续本记录和历史状态更新仅为文档 checkpoint，不改变已验证 Skill 内容。

## Implemented Responsibilities

| Local owner | Implemented content |
| --- | --- |
| `.agents/skills/drama-authoring/` | Zenstory 的剧情/分集/剧本方法与 Shuohao 的人物/场景/道具设定分开渐进读取；回 accepted Drama contract 和唯一 Director，不建立平行剧情或站位状态 |
| `open-video/references/professional-specialists.md` | DirectorSKILL 的整场调度交接与 Kangarooking 的可观察表演/接触因果；保留批准动机、台词、夸张强度和真实前镜状态 |
| `seedance-authoring/references/seedance-2.5.md` | Liyue 的素材职责、受保护内容、前/后续接与时间容量方法；只从 selected 2.5 overlay 读取，不向2.0加载专属模式/限制 |
| `.agents/skills/ad-creative/` | 从核实事实提出广告角度/Hook/形式/文案与受控变体；冷启动不虚构赢家；原声和必要后期声音一起设计，回现有 ecommerce G0–G7 |

`open-video`、ecommerce Skill、control-plane playbook 和 owner matrix 已接通这些窄职责入口。
不是五套平行总导演，也不要求每次读齐所有方法。每个来源保留固定 commit、改写范围和许可。

## Deletions And Consolidation

- 删除 ecommerce Skill 和 Ad QC 中“whole-ad post-media acceptance 尚未实现 / future seam”的过时状态，指向已存在的 Gate 2 / P6 owner；不把 authoring ready 当媒体验收。
- 删除按 episode/serial/cliffhanger 词汇误拒剧情广告的路由，改按任务目的区分。独立 fiction 与 commercial package 仍分离，禁止平行 fiction payload 的 schema/test 不变。
- 删除30秒竖屏的通用假设，消费请求的 `duration_seconds` 与画幅；原 beat/Shot 预算一致性不变。
- 解除“只能读阶段列出的 reference”与专业读取之间的冲突，明确知识读取不等于执行 fallback；blocker 条件不变。
- 新专业参考重复的空间/注意力/声音/故障归因段落已删并回链 `creative-completion`，保留真正的专业细化；control-plane 路由进一步合并到原篇幅预算，未放宽预算或 Gate。

## Verification

- 两个新入口及现有 `open-video` / `seedance-authoring` 的 Skill quick validation 通过。
- 14份相关 authoring Markdown 的61条相对链接/anchor通过。7份许可/NOTICE内容保留；6份副本 bytes 与源完全相同，Liyue MIT副本仅规范末尾空行以通过 whitespace check，版权和条款文字不变。
- live focused 检查先通过58项 Director/Seedance/Runtime边界测试。广告套件初次94通过、1失败：已有 discovery test 将跨技能 reference 链接误认为本目录文件；调整为经 Director 入口读取，定向复验通过。没有改测试去掩盖问题。
- 最终 exact committed snapshot 的11项 Harness检查全部通过，含504项测试：runtime boundary 2、Harness 307、agent rule invariants 44、ecommerce Skill 95、Seedance authoring 8、open-video 48；Architecture Gate为0 error/0 warning。
- 四类无媒体 forward test 实际产出45秒剧情、8秒夸张局部修订、2.0提示词和54秒冷启动广告；实际结果、文字澄清、缺口与 Parent观察见[forward artifacts](../superpowers/artifacts/director-skills/2026-10-24-forward-tests.md)。这些不是媒体/观众/商业验收，也不是504项工程测试的组成。

最终 receipt：`.agent/harness/runs/director-skill-integration-range-v2-20261024/receipt.json`，
SHA-256 `104dc89d44279d853a6e442e8a7833bd2688310c713c20b96c679250b45b2316`，
`status=passed`、11项 checks全 passed、workspace stable/cleanup confirmed。

共享工作区保留旧改动，因此对它直接 freshness检查的 `scope_worktree_clean=false`；使用现有
Harness `isolated_verification_workspace` 重开 exact `a168f8d` committed snapshot，并以同一
`python`解释器调用 `receipt_freshness`，实际得到 `fresh=true`、`complete_completion_proof=true`、
`check_records_valid=true`、`artifact_integrity=true`。这个结论只针对所交付提交快照，不宣称整个
共享 dirty 工作区通过。最初误用系统 `python3` 的核验因 argv不同而不成立，已改用Harness同一解释器。

保留失败历史：staged模式因两个相同路径仍有原先 unstaged改动而拒绝；改用正常 commit-range。
初版范围 receipt `.agent/harness/runs/director-skill-integration-range-20261024/receipt.json`
因 control-plane篇幅超限失败；合并路由后由最终v2范围验证，旧回执未删除或改写。

## Ownership And Native Agents

`drama_skill_implementation`（`bounded_worker`）只写新Drama目录；
`ad_creative_implementation`（`bounded_worker`）采集6份固定版本广告原文/许可，未落盘Skill，
Parent中断其当前轮次并明确接回唯一写权限后完成广告目录；
`skill_conflict_cleanup_audit`（`architecture_auditor`）只读定位5类旧冲突与重复；
`director_skill_forward_test`（`conceptual_planning_agent`）只读完成具体文本任务与澄清。
没有 nested delegation，也未将 writer/文本测试员冒作独立工程 reviewer。

Parent保存既有 shared dirty 文件的exact baseline，只将 matrix两条注册行和ecommerce Skill
的本任务插入/替换投影到 index；实际核对 staged bytes等于task-only候选。其余4份共享
baseline保持byte一致，未夹带旧dirty内容、清理未知文件或改写他人index。

Risk Gate：`NATIVE_REVIEW_NOT_REQUIRED`。候选为上述exact实现提交，只改变advisory知识、路由
与许可，不改变 credential、Product Python/JS、durable state、Provider或QA Runtime行为；
相关可执行检查及独立文字任务覆盖本轮范围，Parent负责最终裁决。

## Learning Evaluation And Limits

达到 substantial implementation checkpoint，按 `record-ai-video-session` 记录，并按
`distill-ai-video-learning` 评估为 `no_candidate`：没有新的独立媒体实验、对照或实际广告数据，
四类文本演练和多个代理不计为媒体经验独立性；不生成占位 Learning Claim。

本轮视频/语音Provider调用为0，没有新广告账号操作或媒体发布。实现推送到远端main的SHA由
交付时核验；后续记录checkpoint另作文档提交。软件/媒体release和P6/Final Acceptance不因本轮
Skills接入发生变化。新流程的真实成片、听感、审美和传播效果仍未验证；54秒测试稿尤其不能
冒作此前热敷贴作品的已批准新方案。
