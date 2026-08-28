# Qingyan Seedance Fast Dialogue Benefit Shot Blocker Record

Date: 2026-08-28

## Purpose

本文记录一次用户明确要求的 Qingyan 人物补镜尝试：在现有 28 秒 review-only 成片中增加一个
6 秒双人对话 Shot，用可观察的“小瓶随身放包”动作表达便携优势，并在生成通过逐 Shot Gate 后
本地烧录对白字幕。

该尝试在唯一一次 Ark submit 后进入明确的 Provider 终态失败，因此停在 genuine blocker。没有
新 MP4、没有 post-media Gate、没有本地合成，也没有替代 Provider/model 或 retry。

Primary run：

`runs/qingyan-seedance2-fast-dialogue-benefit-20260828-001/`

## Accepted Shot Boundary

锁定的对白为：

- 男：`你出门也带着它？`
- 女：`嗯，小小一瓶，放包里刚刚好。`

产品利益点只使用可观察的 60 ml 小瓶便携性，不加入医学、机制、量化功效、持续时长、testimonial、
endorsement、popularity 或 absolute claim。计划镜头为男左女右的稳定双人中景；女方始终持有一瓶
产品，并在回答时把瓶身半放入小包外袋，产品保持可见。该 Shot 不主张与原人物段使用同一演员身份。

Source contract 与输入：

- `runs/qingyan-seedance2-fast-dialogue-benefit-20260828-001/shot-contract.md`
- `runs/qingyan-seedance2-fast-dialogue-benefit-20260828-001/prompt.txt`
- Prompt SHA-256: `670c044caea2ad0c9d80e45bc63de6fea2d1f7b7493a3bce4816bacc0f9c190c`
- ordinary non-character bottle reference: `runs/qingyan-seedance2-fast-dialogue-benefit-20260828-001/references/01-qingyan-bottle-only.png`
- reference SHA-256: `406b36ab8a8531d9a4ea60178f395823cf1ea3e1c642bc78e98463aabf37ba2f`
- real-person reference egress: `0`

`hell-grind-aigc-skill` Prompt auditor 对最终 Prompt 返回 `PASS`、structural score `100/100`。
Seedance capability/input/budget preflight 也已通过，并写入：

`runs/qingyan-seedance2-fast-dialogue-benefit-20260828-001/evidence/preflight-preview.json`

## Paid Provider Execution

Exact request：

- model: `doubao-seedance-2-0-fast-260128`
- mode: `REFERENCE_TO_VIDEO`
- output: 6 seconds, `720p`, `9:16`, `24fps`, `generate_audio=true`
- references: 1 张 ordinary non-character bottle PNG
- exact submit ceiling: 1 POST
- estimated token upper bound: 129,600
- estimated cost upper bound: 4.7952 CNY
- finite task ceiling: 6 CNY

唯一一次 POST 于 `2026-08-28T09:48:55Z` 被接受。Immutable submit receipt：

`runs/qingyan-seedance2-fast-dialogue-benefit-20260828-001/production/state/paid-provider/submits/50866a055536dc4a3202e7b847718ba985683d3df2d5074068e005465e42a75a.json`

- external effect id: `cgt-20260828174901-bswn5`
- submit receipt fingerprint: `50866a055536dc4a3202e7b847718ba985683d3df2d5074068e005465e42a75a`
- submit POST count: 1
- blind retry / permit remint / fallback: 0 / 0 / 0

Provider 在 poll 16 返回 `state=failed`、`progress_milli=1000`。Exact observation：

`runs/qingyan-seedance2-fast-dialogue-benefit-20260828-001/production/state/video-generation/status/1456770472ef8c88254f58b825bf981b29ae4a8c580e6fcdc7ef7fc59b087cf3.json`

- observation SHA-256: `ced1f74881d824f4ffec5ecdd3925ff329cb9ad845dee1c0d3385d6e44a7ae74`
- Manifest error code: `video_provider_failed`
- Manifest error message: `Video Provider reported terminal generation failure.`
- provider reason: response/evidence 中未提供
- candidate video asset IDs: empty
- fetched output / activation: 0 / 0

这是一项已知终态失败，不是 timeout、network ambiguity 或 unknown outcome；它不授权 retry。

## Evidence Correction And Budget Boundary

自动生成的 `evidence/live-report.json` 同时记录 `submit_posts=1` 和
`paid_provider_outcome=not_submitted`，后者与 immutable accepted submit receipt 及 Manifest 冲突，
不得作为 outcome truth。没有覆盖原始 report；纠正边界单独记录在：

`runs/qingyan-seedance2-fast-dialogue-benefit-20260828-001/evidence/terminal-failure-boundary.json`

当前 active budget snapshot 中 reservation 仍为 `reserved`，`actual_cost_microunits=null`。因此：

- 4.7952 CNY 只是 preflight 上限，不是已验证实扣金额。
- 不得凭 Provider failure 自行将 reservation settled/refunded，也不得声称零费用。
- 后续若要 recovery，必须先核对 Provider billing/task truth，再建立新的 exact preview、预算、egress 和
  one-use permit；不得复用或 remint 本次 permit。

## Current Artifact Truth

现有 V4 文件没有被修改：

`runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/final/qingyan-seedance2-fast-image-cards-caption-repaired-v4-28s-review-only.mp4`

- SHA-256: `087497ae1b4be12b260899706c19698c8d7d88635708528a6b8cf0d1fd7ac4e1`
- 当前人物同行段仍约 2.5 秒
- 该人物段仍没有双人对白或对应字幕
- V4 仍是 current local review artifact；本失败尝试没有 supersede 它
- 三张尾卡 claim 仍未核验，V4 仍不可发布

因为没有新 MP4，repository 的 `Per-Shot Post-Media Gate` 没有可分析的 exact bytes，所有要求均
保持 `NOT_EVALUATED`，不得创建伪造 Gate 或进入本地 composition。

## Assessment

产品真值、对白、画面动作、字幕边界与一次性 paid gate 已收敛，但目标 Shot 未生成成功。用户目标
“人物出现更久、展示产品优势、有对话、有字幕”尚未完成；当前自然停止点是 Provider terminal
failure，而不是质量 rejection。

## Remaining Risks Or Next Work

- Provider 没有暴露 terminal failure 的具体原因，不能断言是审核、Prompt、模型容量或输入问题。
- 实际账单和 reservation recovery 尚未验证。
- 任何 retry、Prompt 变体、不同 Provider/model、local lip-sync/TTS 替代或新预算都属于新的 live
  scope，需要用户重新授权。
- 若后续生成成功，仍必须对 exact MP4 逐项验证人物数、产品 identity、便携动作、对白、speaker/lip
  sync、镜头连续性、文字排除与 native audio；只有全部 required findings 为 `PASS` 才能本地烧字幕和
  合成。

## Agent Guardrails

- 不得把 submit accepted、100% progress 或 terminal failure 当成生成成功。
- 不得把 estimated upper bound 当作实扣费用。
- 不得因为没有 output 就跳过逐 Shot Gate并直接制作 final。
- 不得复用本次 consumed permit，或在没有 exact recovery evidence 时自动 settlement、retry、fallback、
  activation、publication、P6 或 Final Acceptance。
