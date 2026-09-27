---
record_kind: research_note
topic_id: creative-goal-preservation-and-completion
learning_eligibility: ineligible
---

# Creative Goal Preservation Spec Record

Date: 2026-09-27

## Purpose

用户要求“和claude讨论下这个事情该怎么做，然后写一个specs”。本轮完成只读讨论和待批准 spec，未获 implementation 或新媒体授权，不能把设计写成已修复的产品行为。

## User Feedback

针对上一轮青颜 10 秒片，用户明确质问“你觉得这个全程一张图很合理吗”，随后指出“不是让你从根本上改吗，为什么做出来这个”。反馈对象是 `runs/ecommerce-qingyan-packshot-20260927-001/final/青颜_10秒_原图品牌短片.mp4`，SHA-256 `25cd328bcbf395660a0e213d0c541c1c68bd49dc6304eedb936b912aeefa76a6`。

当前创作层结论是用户拒绝这一全程单图方案，后续需要重新设计。该反馈不改写历史技术 PASS 或完整报告的 `NOT_EVALUATED`，不声称用户已经对每项 requirement 做了原速完整观看，也不是正式 Production ReviewReceipt。旧[媒体记录](2026-09-27-qingyan-original-packshot-brand-film.md)同步增加醒目的 supersession notice。

## Source Findings

重读 Director v4 validator、`FinalOutputContract`、`final_output_review.py`、`visual_quality_report.py` 和 Ecommerce handoff / QA 比较入口：已有合同保留、逐字引用与 hash、完整要求裁决实际存在。本次报告没有伪造整体 PASS。真实缺口在于前轮目标未充分承接、以避险取代创作、局部检查不足以评价作品，以及交付文件后停止任务。

CodeGraph 返回了 `prepare -> check -> reopen / adjudicate_final_output` 关系，行号已落后于当前源码；只将关系当定位线索，函数事实以实际源码为准。AOCI 33 条完整读取，delivery confirmed、attestation pass（9/10），不以索引替代当前代码。

`retrieve-ai-video-memory` experience 查询返回空结果并提示后台 refresh / last-good；没有把空检索当成没有历史。Parent 直接重开相关记录、既有 spec 和 exact run 的 brief / contract。全局 memory 仅作检索线索。

## Claude Discussion And Parent Decisions

通过 `discussion-with-claude` helper 进行两轮只读讨论，session `b3d5dd19-2491-4c5a-8408-4c4b15101020`；两轮 `ok=true`。首轮 result 文本 SHA-256 `fec46f266a8654644ee1c9e0b11acd0461fd5d9f951bf798c08366c65e995a94`；追问 result 文本 SHA-256 `a11f4639132f033d3649117e74fa2c0f19bbdc59ff6bceaca10811d17392f875`。完整结果仅存本地临时目录，本文保留经 Parent 核对的摘要，不复制原始响应。

双方收敛到三项区分：制作前 concept 复核与不足先修，才可能减少坏片；承接意图和精确映射能减少结构性遗漏；完成摘要只改善报告诚实，不能让影片变好。

Parent 否决了首轮“偏离后告知即可”以及在严格 v4 schema 新增必填字段却声称兼容的建议。Claude 在追问中认可：明确要求仅由用户变更；v4 保持原结构；交接检查属于开发侧 diagnostics。Parent 进一步保留限制：原始 inventory 根本未提取的意图，不能保证由映射检查发现；不能声称新 helper 对旧青颜输入必然自动识别所有语义遗漏。

具体设计在[待批准 spec](../superpowers/specs/2026-09-27-creative-goal-preservation-and-completion.md)：薄引用封套复用现有目标/coverage/合同，不创建新 QA 状态；广告与剧情分别做内容判断；旧 packet 与 schema 保持重开兼容。任何 implementation 或真实案例验证均留待批准和相应授权。

受管 Kimi worker 的独立、有限源码检查 invocation 为 `59ecfc8c-6edc-4cb1-b324-287b8cab4441`，seal `10ad3177127754eb772e05ffd5a5ac95110fc5d55b647864805a6fe1e1a3adc7`。receipt 为 `PROCESS_OUTPUT_LIMIT`：2 次 endpoint identity verified 请求，输出超限，无可采纳报告。未重试，未将 exit 0 或已发请求视为 review 完成。它不构成本轮 spec 的独立通过证据。

## Verification Boundary

本轮为 T2 spec：不变更 Production QA、Manifest、activation、recovery、Provider 或 runtime。独立 Native `reviewer_xhigh` 首轮审查 tree `e68d153b8550b80fe8100a7261f1db273ba68646`，发现 CGP-001（blocking：intent 与既有 constraint scope 缺少确定关系）及 CGP-002（non-blocking：原始 PASS 与有效逐项证据结果可能不一致）。Parent 采纳两项并补入 spec：引用现有 constraint scope 做精确 join；详细有效结果仍由原 adjudicator owner 一次计算，aggregate 行为保持等价。

Targeted re-review 绑定 tree `f90e197df9bbb6b4eb0ea979c4e973f8139f9729`、spec SHA-256 `87eea5307cf6199733525d687e3d6076ff4959ef3f00b22ea529a1a859309bcb`，finding set 为空。Parent 已复核修正，接受其作为待用户批准的设计草案；不是 implementation 或媒体验收。文档身份检查通过，旧媒体 evidence table 新增用户反馈 proof layer 未引入 identity errors。

Documentation Harness receipt：`.agent/harness/runs/creative-goal-spec-20260927-01/receipt.json`。实际状态、exact scope 和完整性以最终生成并复验的 receipt 为准，不沿用先前媒体记录的 receipt。

没有新渲染、抽帧、音视频生成或 Video Provider submit，没有 push / release；只有本任务明确要求的 Claude 讨论和 repository routing 要求的 Kimi 文本检查。`.codex/config.toml` 既有 dirty change 保留。独立 experience RAG 未手动 rebuild，不能声称新 spec / record 已进入其索引。

## Learning Evaluation

按 `record-ai-video-session` 自动调用 `distill-ai-video-learning` 评估，结果 `no_candidate`。当前是同一片的用户反馈和设计讨论，不是新的独立媒体实验；未产生隔离变量的对照。检索现有四个 learning claims 后，没有可由本次证据实质更新的同范围 claim。记录拒绝与修正设计有 durable value，但不能推出“静态片总是不好”或某 Provider 能力规则。

## Next Work

用户审阅 spec 后再进入 implementation plan。后续工程验证只证明映射/接线与报告条件；实际广告和剧情质量改善必须分别有真实作品及相应观看反馈，不能用本轮文档、模型讨论或 Harness PASS 代替。
