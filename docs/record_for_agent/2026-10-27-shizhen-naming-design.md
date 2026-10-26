---
record_kind: session_summary
topic_id: shizhen-season01-naming
learning_eligibility: ineligible
---

# Lost Frames Naming Record

## Scope And Authorization

研究三个指定开源Skill、审查现有Bible、完成全套命名设计。用户先要求提案、禁止直接覆盖Canon；随后明确“主角名字不要改”“其它人的名字都可以改”，最终要求“你还要干多久,直接改命吧”。按当前任务语境将最后一句理解为直接改名，落实首选名称，不再扩展研究。林序、片名不改；其他人有选择地改名，没有改变身份、关系、机制或剧情。

## Delivered Changes

首选称谓统一进入现有10份第一季开发正文。Character／Ability／Faction／Anomaly Bible继续各自拥有相应对象；原A/F/N编号不变，未另建世界规则权威。Canon Review与Creative Decisions保留旧V1输入，仅增加历史名称提示。完整对照与未应用备选：`docs/superpowers/artifacts/drama/shizhen-episode-01/naming-candidates.md`。

六能力：拾遗／余响／守更／借步／验契／留影。五势力：堤务处／望归社／存照馆／新邻／未然组。留底人／后来人／夹页区分亲历者、生命自称和空间行话。不增战力阶位，不把认知类型改成等级。

研究报告：`docs/research/2026-10-27-shizhen-naming-skills.md`。固定三个上游commit，核查目标Skill入口、所引参考、脚本依赖与MIT许可。只取隐喻领域、命名语体、人物关系叫法与声音检查方法；没有安装Skill或pypinyin、没有运行上游脚本、没有新增生产依赖／付费生成。研究writer仅写该报告，Parent核对关键许可证与方法边界；最终命名与应用由Parent完成。

## Preservation And Verification

原剧本、coverage、字幕、认可媒体与Production state不改。改名后的正文仍继承原有PROPOSED CANON／AUTHOR SECRET等级，名称落实不代表其他故事提案获批。前轮`series-bible-verification.json`是改名前的历史证据，新快照为同目录`naming-verification.json`，不能拿旧审读哈希证明新稿。

本轮按映射重建并比较正文、检查旧名残留、本地链接、Markdown空白及受保护来源哈希。普通话拼读与有限公开作品相似性检查见`naming-checks.md`；真人叫名、延时复述、配音听辨均NOT_EVALUATED。Parent Risk Gate为NATIVE_REVIEW_NOT_REQUIRED：仅可逆的开发文本称谓变更，无生产执行或关键状态损坏路径；不把前轮reviewer意见冒充本轮改名审读。

实际验证：12份既有开发／历史文档逐字重建比对，变化仅为名称、个案标题、命名解释与状态提示；96个本地链接有效，47项原始创作／媒体哈希未变，docs contract与whitespace通过。focused Harness通过；full attempt的scope和docs通过，在agent_rules_check因共享AGENTS.md的document budget exceeded停止，未运行完整工程套件。保留原回执，记录更新后的最终回执为`.agent/harness/runs/shizhen-naming-focused-final-20261027/receipt.json`和`.agent/harness/runs/shizhen-naming-full-final-20261027/receipt.json`；不修改他人规则文件或放宽Gate。提交仅含本轮命名与关联文档，publication以Git commit、push及远端SHA读回为准。

## Learning Evaluation

已使用record-ai-video-session形成稳定记录，并按distill-ai-video-learning自动评估为`no_candidate`：命名研究与案头判断没有独立模型实验或人类比较证据，不创建学习候选、不修改Skill／Policy／Gate、不写全局memory。
