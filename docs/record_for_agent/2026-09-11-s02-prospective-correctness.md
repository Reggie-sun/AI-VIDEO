---
record_kind: architecture_implementation
topic_id: s02-prospective-correctness
learning_eligibility: ineligible
---

# S02 Prospective Correctness

Date: 2026-09-11

## Scope And Authority

用户明确授权最小 S02 correctness 修复：拆分 framing preference 与真实 hard acceptance、
修正 FinalOutputContract、收紧 hard_basis 新 admission、解除 Director 相邻镜头类别
必须全部改变的硬拒绝，并重做 attempt02/03 的 prospective shadow。
不调用 Provider、不生成 attempt04、不修改 quota、不做 VIDEO_EDIT/best-of-N、不扩建架构。
本记录不授权任何后续生成，也不证明连续 1.0x 观看或质量通过。

## Implementation

唯一 QA semantic owner 仍是 `src/ai_video/production/requirement_semantics.py`。
新 publication/use 拒绝 Director hard_basis.necessity 为空白，或规范化 whitespace 后
与 observable/对应 source quote 完全相同；必须由 QA author 解释独立 narrative、continuity
或 quality necessity。这里只拦机械自证，不以 NLP 推断艺术必要性，不把改写同义句视作证明。

`activate_qa_policy()` 在两条 exact replay 返回之后、任何新 artifact 写入之前检查所有
QA inventories。`require_generation_evaluation_authorities()` 在共同 planning 与 submit
readiness 检查当前 rubric。历史 deserialization/hash/verdict 不追溯重算。
旧 S01 policy 的相同机械填值也不能作为新 policy 再发布，但历史选择仍可 exact replay。

`s02-chenli-boundary` 在新 inventory 中退役，lineage 指回旧 rubric。新的 hard 项是：

- `s02-narrative-focus`：林砚保持主体，关键表演不被邻座遮挡或抢走。
- `s02-question-progression`：收手→关注扬声器→转向邻座的因果关系。
- `s02-chenli-continuity`：可辨认邻座的身份、灰色连帽卫衣、耳机、手机所有权及空间关系正确，承接 S03。
- `s02-visible-artifacts`：不出现错误/复制人物、重复手机、错误肢体或关键遮挡。

原有开场、自然动作、转头终态、林砚身份/道具/车厢、无生成文字、P4对白/环境声共7项
保持 hard，observable/tolerance 未放松，仅补独立 necessity。新 hard inventory 共11项，
FinalOutput goal version `2` 逐项一致。肩部限定、不露头脸、克制 pan 和50mm侧面近景
属于 `s02-chenli-framing-preference` / 原 camera preference，均不进入 required findings。

Director 原 validator 对相邻 `beat_function`、`shot_scale`、`camera_treatment` 重复仅给
`UserWarning`；结构、枚举、source、transition、duration 校验保持不变，无新 protocol。

## Exact Shadow Evidence

新 policy：
`docs/superpowers/artifacts/drama/jieshi-episode-01/s02-prospective-qa-v2.json`
（QA content hash `b4664eb1adcbeb185329ea75783e8f6dac97a055d72ce0c28ae1909ee6c69b7e`）。
新报告：
`docs/superpowers/artifacts/drama/jieshi-episode-01/s02-prospective-shadow-v2.json`
（file SHA-256 `3315c2a40814c449627e8f1e61882a799ff2e289b0a4ee6e176b7f28e71505b5`）。

通过 `tests/test_s02_prospective_review.py::shadow_s02()` 显式传入真实 project root 与两个
Gate paths，复用 standard project loader、committer read、canonical diagnosis/feedback。
Gate 的 attempt/shot/rubric、sidecar binding 与 Manifest canonical binding/request 完整 join，
读取原 MP4 并核对 SHA/size。helper 不创建新 evaluator source，不补人审 presentation，不写 state。

| Attempt | Exact MP4 SHA-256 | Bytes | Historical Gate | New shadow |
| --- | --- | ---: | --- | --- |
| attempt02 | `382e74c78b5699ea2c1d3b4c942cca9abfc4fd2de3b1a872a06092535b7312bc` | 3152278 | FAIL | EVIDENCE_GAP / NOT_EVALUATED |
| attempt03 | `2c82bfe8197d96241dd535154faaab30dfa4d2aa54dba66e76c7b1a32020c92a` | 3049552 | FAIL | EVIDENCE_GAP / NOT_EVALUATED |

两份新 diagnosis 都无 failed requirements、无 preserved PASS、无 repair intervention，
`next_owner=evidence_owner`、`all_required_observed_pass=false`、`production_permission=false`。
attempt02 保留2份 experience；attempt03 尚无该素材对应的持久 experience，不能编造。
抽帧中的林砚主体和转向迹象不证明整段自然；邻座衣着/耳部细节仍有未解决的 identity/continuity
疑点。S03尚无实际视频，无法宣称剪接已通过。两份 raw 均无音轨，P4要求仍待原owner验收。

前后比较 `runs/jieshi-e01-i2v-20260907-attempt10/` 下 `production-s02-v2` 和
`preparation-s02-video-v1/v2/v3` 的全部183个文件 SHA-256，逐字相同；包含 Manifest、
QA、authoring、quota、Gate、binding、experience 和 MP4。Manifest revision35 仍选历史
QA `520add1dc0aeea830f41fd15cc2d08c93fcf0687686524374b490a9f68afed8d`，未激活新 policy。
旧 helper / Gate 可重开，但其无效 admission 不能获得新 generation readiness。

## Verification And Publication Boundary

- RED：旧 Director validator 拒绝重复类别；新 admission tests 在实现前失败。
- 125 focused tests PASS：semantics、replay、S02、evaluation binding、Director。
- 372 additional working-tree regressions PASS（412.03s）：generation feedback/evaluation/
  execution/guards/historical replay、feedback review、Final-output/no-regression、Production
  review/state commit。真实 project 的 `for_project().prepare()` 也在任何 candidate/Provider
  动作前拒绝旧 `s02-chenli-boundary` 的机械 necessity；无新 generation side effect。
- Independent native `reviewer_xhigh`：accept，无 blocking issue；独立纯内存 checks、source
  quote/hash 与两次真实 shadow replay通过，不替代 Harness 或 human acceptance。
- `python -m scripts.docs_contract_gate check`：PASS。
- `python -m scripts.architecture_gate check --base-ref HEAD --format json`：PASS，findings为空。
- 控制面/Skill测试：163 PASS，1 FAIL。失败是 HEAD 已存在的 unmapped paths：
  `src/ai_video/production/image_import_video_frame.py`、
  `src/ai_video/production/paid_provider_no_effect_reconciliation.py`、
  `tests/test_paid_provider_no_effect_reconciliation.py`；最后一项也未被测试清单引用。
  用 `load_policy_bytes(git show HEAD:.agent/harness/policy.yaml)` 重新 audit，得到相同基线问题。
  本 slice 不顺手修复这些无关 routing，不声称完整 Harness passing。

当前修改保留在原 working tree 并按精确 task paths 暂存；未 commit、未创建 worktree、未 push。Exact-snapshot Harness 临时
worktree 尚待用户显式授权，既有 policy-audit failure 也需单独处理；因此未生成 fresh
passing receipt，不能宣称工程 closure 已完成；未将 working-tree tests 冒充 exact-snapshot receipt。

## Production Handoff

attempt02 现在应进入 human 1.0x holistic review，而不是仅因露脸再生成。
如果真实 hard 项通过，可保留素材并停止 S02 regeneration；下一 Shot 仍需新 QA 下的
适用 proof 与既有 Gate/activation/授权条件，shadow 本身不放行 S03。
本 slice 没有引入新的 architecture blocker，也不扩大既有 human-proof 接入边界。

`record-ai-video-session` 已为旧 first-frame/S02 record 添加 prospective supersession notice，
不修改历史 chronology/verdict。`distill-ai-video-learning`：`no_candidate`；本次是已授权
的确定性分类纠错及旧素材重解释，未新增独立质量实验，不推导通过率、节省调用或模型能力。
Memory retrieval 返回 stale advisory fragments 并由既有 routing 排队后台维护；未额外
手动刷新索引，也不把 retrieval 当 production acceptance。
