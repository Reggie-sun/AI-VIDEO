# Qingyan Dialogue Benefit Shot And Mini Match-Cut Record

Date: 2026-08-28

## Current Checkpoint — V6 Old Static Tail Reuse

本节 supersede 下方 V5 作为当前 local review artifact。用户明确要求保留 Mini 衔接与对白，但把最后
一个 Shot 换回旧片的 Fast Hero、三张静态卡和对应声音，并把字幕放到底部。该要求只触发 local
deterministic re-composition；没有新的 Provider submit、network、paid call、permit、reservation、
activation 或 publish effect。

用户指定的旧片为：

`runs/qingyan-seedance2-fast-supported-hero-image-tail-20260828-001/final/qingyan-seedance2-fast-image-cards-captioned-28s-review-only.mp4`

- SHA-256: `e965db27a4f67ce4fcf2258ae83ef67643e8474c170e3c85cced2af1330fd694`
- 复用范围：旧片 `19.541667-28.041667s` 的 exact audio interval
- 视觉顺序：Fast Hero 4 秒 -> card 1 1.5 秒 -> card 2 1.5 秒 -> card 3 1.5 秒
- 为满足新的字幕位置要求，没有复制旧片已经烧录的灰色 caption box 或 disclosure overlay；Hero 和
  三张卡从相同 accepted/raw visual sources 重新组装，内容和顺序保持不变

新 review-only 成片：

`runs/qingyan-seedance2-mini-linked-ad-v6-old-tail-20260828-001/final/qingyan-seedance2-mini-linked-ad-v6-old-static-tail-36s-review-only.mp4`

- SHA-256: `d0d2f4f621f5536e6db525aec7fc965a16ae63c21ff60ae3e853dfaefe54356f`
- size: 17,938,537 bytes
- media: 35.645 秒；H.264 High、720x1280、24fps、854 frames；AAC stereo、44.1kHz
- audio level: mean `-15.2 dB`、max `-1.0 dB`

Timeline：

| Final time | Advertising role | Source |
| --- | --- | --- |
| `0.000-15.041667s` | problem hook -> recommendation -> application -> result | accepted Shot 01 |
| `15.041667-21.041667s` | product macro -> extended same-couple social payoff | accepted Shot 02 `0.0-6.0s` |
| `21.041667-27.121667s` | linked product portability proof + two-line dialogue | gated Mini Shot |
| `27.121667-31.121667s` | old supported product Hero | old Fast Hero source |
| `31.121667-32.621667s` | old static card 1 | old card source 1 |
| `32.621667-34.121667s` | old static card 2 | old card source 2 |
| `34.121667-35.621667s` | old static card 3 | old card source 3 |

品牌尾段字幕全部改为画面底部的白字、黑色描边和阴影，不使用矩形 backing：`青颜`
`28.70-29.42s`、`抑汗净味` `29.86-30.90s`、`清爽舒适` `31.02-32.18s`、`近距离`
`33.46-34.26s`、`更从容` `34.62-35.54s`。Mini 两句对白及其字幕保持不变。

Final local review Gate：

`runs/qingyan-seedance2-mini-linked-ad-v6-old-tail-20260828-001/evidence/post-composition-review-gate.json`

- Gate SHA-256: `fda0db4c3928e4b3aff9f1c2c583bb84b82d99144bafbf0246bcc3711e3bbb6a`
- overall verdict: `PASS_FOR_LOCAL_REVIEW_ONLY`
- full ffmpeg decode: `PASS`
- project-local `video-analysis`: exact final MP4 的 H.264/AAC、时长、分辨率、frame count 与对白/尾段
  speech 均已重新测量
- exact tail 与 overall contact sheets 已人工检查：旧 Hero、三张卡顺序正确，V5 绿色顶部 callout 已移除，
  品牌字幕位于底部

三张旧卡仍含 `15%`、`全天`、`14天`、`96.67%`、`93.33%`、机制和 testimonial 类文案；本轮没有
取得 claim substantiation，所以 `STATIC_CARD_CLAIM_SUBSTANTIATION=NOT_EVALUATED`。因此该文件只能
用于本地人工 review，不产生 candidate activation、P6、Final Acceptance 或可发布广告结论。V5 保留为
历史 artifact，不再是当前交付版本。

## Current Checkpoint — Mini Product Match-Cut V5 Review Artifact

本节 supersede 下方 “Option A Raw Candidate Gate Stop” 作为当前交付状态；Fast raw candidate 的
`NOT_EVALUATED` 与 STOP 仍是有效历史证据，但不再是当前 next action。用户随后明确指出该人物
Shot “不像广告”且与前一 Shot 断裂，并将新的 live scope 限定为“就调用 mini 就好”。本轮只产生
一次 Mini Provider submit，没有复用或重试下方 Fast attempt。

### Continuity And Advertising Decision

当前 V4 的人物同行段仅使用 accepted Shot 02 trimmed source 的 `2.0-4.5s`，实际约 2.5 秒；
`4.5-6.0s` 的人物/持瓶 tail 未进入 V4。旧 Fast dialogue raw Shot 又引入新的女性外观、刘海、
服装和包，虽然局部技术要求通过，但不能形成“上一镜女主仍拿着同一产品”的广告因果链。

本轮先从 accepted predecessor 精确取出 frame 96 作为同人物 continuation first frame。该方案在
任何 POST、permit 或 reservation 创建前被 synthetic-person egress policy fail closed：

- run: `runs/qingyan-seedance2-mini-linked-ad-dialogue-20260828-001/`
- zero-effect report:
  `runs/qingyan-seedance2-mini-linked-ad-dialogue-20260828-001/evidence/live-report.json`
- report SHA-256: `d3fe16ca8ba852fa28a5e964117a196f5d07b63a491121851d21b313448de18f`
- `submit_posts=0`、`paid_provider_outcome=not_submitted`、没有 permit/reservation、没有费用效果

因此没有猜测身份 continuity，也没有绕过 egress policy。最终改为 product-only match cut：先把
accepted Shot 02 扩展到 `0.0-6.0s`，让同一男女继续走远且女方手中产品保持可见；随后切到同一
花园色调、ivory/white/brown 服装 palette 下的局部身体和产品动作。该 Shot 不显示脸或嘴，不声称
演员 identity；continuity 由同一产品、持瓶手位、服装色调、花园方向与动作承接建立。

广告作用从“再走一段”改为可观察的 benefit proof：一瓶产品被举到 label-facing commercial beat，
再放到右侧裤袋边并保持可见。两句 off-camera 对话为：

- 男：`你出门也带着青颜？`
- 女：`小小一瓶，随手带着刚刚好。`

后续 commercial close 只使用当前 product truth 支持的
`青颜 / 抑汗｜净味 / 清爽舒适 / 近距离，更从容`；V4 的三张未核验 claim cards 已从新 composition
移除。

### Single Mini Submit And Raw Gate

Effective Mini run：

`runs/qingyan-seedance2-mini-product-bridge-dialogue-20260828-002/`

- Provider/model: `volcengine_ark_seedance` / `doubao-seedance-2-0-mini-260615`
- capability/mode: `seedance-2-0-mini-260615-reference_to_video` / `REFERENCE_TO_VIDEO`
- ordinary product-only reference SHA-256:
  `406b36ab8a8531d9a4ea60178f395823cf1ea3e1c642bc78e98463aabf37ba2f`
- output: 6 秒、720×1280、24fps、native audio
- exact ceiling: 1 POST；estimated upper bound `2.9808 CNY`，task ceiling `4 CNY`
- Provider effects: 1 submit POST、9 query GET、1 download GET
- blind retry / permit remint / fallback / activation: `0 / 0 / 0 / 0`

Fetched raw MP4：

`runs/qingyan-seedance2-mini-product-bridge-dialogue-20260828-002/output/seedance2-mini-product-bridge-dialogue-native-audio-6s.mp4`

- SHA-256: `a7bf49dcbf16f8703eb84331c6de68e1ddfd1ef081c75bd74edd37adbb212c3a`
- size: 4,168,778 bytes
- media: 6.080 秒；H.264 High、720×1280、24fps、145 frames；AAC stereo、32kHz
- audio level: mean `-18.5 dB`、max `-1.1 dB`

在任何字幕或 composition 前，project-local `video-analysis` MCP 对 exact MP4 执行 0.5 秒 dense
analysis、Whisper small + medium、scene review；同时完成完整 ffmpeg decode 和 predecessor/new-Shot
match-cut contact sheet。全部 required findings 为 `PASS`：

- 同一产品/服装 palette/花园/动作形成 predecessor association；
- 恰好一瓶稳定的黄色标签白盖产品；
- 产品从随行持握进入 label-facing hero，再落到裤袋边；
- 不显示脸或嘴，因此没有 visible lip-sync requirement；
- 两句对白各一次、顺序正确且无额外 speech；
- 单一连续镜头，无生成字幕、graphics 或 unsupported claim。

Whisper 将声音相同的品牌 proper noun 记为 `青言` / `青岩`；medium pass 仍完整恢复
`你出门也带着青岩 / 小小一瓶 / 随手带着刚刚好`。该 ASR homophone 不等同于错误发音，但最终人耳
音色和自然度仍属于 human review。

Raw Gate：

`runs/qingyan-seedance2-mini-product-bridge-dialogue-20260828-002/evidence/post-media-gate.json`

- Gate SHA-256: `5342e1dce449a4777fdb1c4fbc220dedef0f3375307f9c263d2cb6f95876e348`
- overall verdict: `PASS`
- boundary: 只允许 deterministic local captions/composition；不产生 activation、P6 或 Final Acceptance

### V5 Deterministic Composition

新 review-only 成片：

`runs/qingyan-seedance2-mini-linked-ad-v5-20260828-001/final/qingyan-seedance2-mini-linked-ad-v5-31s-review-only.mp4`

- SHA-256: `632490ed082ea0688a05273884b3516d245b82e4f1f2f7b4219491a2db9c86d7`
- size: 17,490,218 bytes
- media: 31.145 秒；H.264 High、720×1280、24fps、746 frames；AAC stereo、44.1kHz
- final audio level: mean `-16.7 dB`、max `-1.0 dB`

Timeline：

| Final time | Advertising role | Source |
| --- | --- | --- |
| `0.000-15.041667s` | problem hook -> recommendation -> application -> result | accepted Shot 01 |
| `15.041667-21.041667s` | product macro -> extended same-couple social payoff | accepted Shot 02 `0.0-6.0s` |
| `21.041667-27.121667s` | linked product portability proof + two-line dialogue | gated Mini Shot |
| `27.121667-31.121667s` | controlled product Hero + supported commercial close | accepted Fast Hero |

最终 MP4 再次通过 project-local `video-analysis`：medium Whisper 只恢复既有 opening voiceover 与新增
两句对话，新增对白时间为 `22.56-23.76s` 和 `24.40-26.48s`。Authored subtitles 使用正确品牌字形，
覆盖 `22.46-24.38s` 与 `24.38-26.64s`；Hero 上方 commercial callouts 与底部 dialogue subtitle
使用不同 role/style。完整 ffmpeg decode 无 error，三张 final contact sheets 验证人物/产品 match cut、
字幕可读性、便携动作与 Hero close。

Final local review Gate：

`runs/qingyan-seedance2-mini-linked-ad-v5-20260828-001/evidence/post-composition-review-gate.json`

- Gate SHA-256: `fed4f81d1356fce35be26fff26b5b52c96449e75f4287dfba87f9f67b5d4d9e2`
- overall verdict: `PASS`
- boundary: review-only；未 activation、未 P6 / Final Acceptance、未 publish、未验证 external actual billing

### Current Assessment And Remaining Human Review

用户提出的技术目标已经在新 review artifact 中实现：人物/产品关联 passage 从约 `17s` 延续到
`27.12s`，不再于 2.5 秒后断开；产品优势由可见 portability action 和两句对白表达；对白均有字幕；
结尾回到干净 Hero 和 supported benefits，旧 unverified cards 不再出现。

仍需用户人工确认两项 subjective acceptance：生成男女声是否自然且符合预期，以及 product-action
match cut / 绿色 commercial callout 是否符合品牌审美。该人工确认不能由 raw Gate、ASR、FFmpeg、
Harness 或本文记录替代。外部 Provider 实际账单未读取，`2.9808 CNY` 只能描述为 preflight estimated
upper bound。没有追加 Provider submit、candidate activation、push 或 release。

## Current Checkpoint — Option A Raw Candidate Gate Stop

本节 supersede 下方“首次 Provider terminal failure、没有新 MP4”的当前状态；下方正文保留为第一次
尝试的历史证据。用户随后明确选择 Option A，只授权同一 Seedance Fast model、6 秒、6 CNY ceiling
下的一次简化 Prompt 重新生成。该唯一追加 submit 已消费，没有授权第三次 submit、替代 Provider/model
或扩大预算。

第二次 run：

`runs/qingyan-seedance2-fast-dialogue-benefit-20260828-002/`

Prompt 只缩短了措辞、减少相对 beat 描述与 negative constraints；人物数、产品 reference、对白、
便携动作、稳定双人中景、native audio 与逐 Shot Gate 均未放宽。最终 Prompt SHA-256 为
`19f5431a4626b71c1f162bf58003e8101823a0ab9bf445d6eae8a15b0184f29d`，
`hell-grind-aigc-skill` auditor 返回 `PASS`、`100/100`。Preflight 对第一次 terminal observation 的
exact SHA-256 做了 fail-closed 校验，并锁定最多 1 次 POST、129,600 tokens、4.7952 CNY estimated
upper bound 与 6 CNY ceiling。

唯一一次追加 POST 于 `2026-08-28T10:12:21Z` 被接受，并在第 11 次 poll 后成功 fetch：

`runs/qingyan-seedance2-fast-dialogue-benefit-20260828-002/output/seedance2-fast-dialogue-benefit-v2-native-audio-6s.mp4`

- exact MP4 SHA-256: `309b919c00fc86bfd9540802c445a2fca2b1db36ebf44f87c94db3c14c65ff5b`
- size: 2,531,033 bytes
- media: 6.080 秒、H.264 High、720×1280、24fps、145 frames；AAC stereo、32kHz
- Provider effects: 1 submit POST、12 query GET、1 download GET
- blind retry / permit remint / Provider fallback / activation: `0 / 0 / 0 / 0`

对 exact bytes 执行 project-local `video-analysis`、Whisper small + medium、完整 ffmpeg decode、
0.5 秒 contact sheet 与独立 `reviewer_xhigh` 复核后，当前逐项结论是：

| Requirement | Verdict | Evidence boundary |
| --- | --- | --- |
| `EXACT_TWO_PEOPLE` | `PASS` | 全部采样只出现男左女右两人，无复制或第三人。 |
| `PRODUCT_IDENTITY` | `PASS` | 只有一瓶稳定可辨认的黄色标签白盖瓶，无盒子、重复或明显形变。 |
| `PORTABILITY_ACTION` | `NOT_EVALUATED` | 能确认女方把瓶子放入包口并保持半露、手未脱离；0.5 秒采样不能明确证明 contract 指定的 `outer pocket`。 |
| `DIALOGUE_EXACTNESS` | `NOT_EVALUATED` | Medium Whisper 确认 `你出门也带着它 / 小小一瓶 / 放包里刚刚好`，但 small 与 medium 都漏掉女声开头的 `嗯`；Agent 无直接音频听审能力，不能认证 exact copy。 |
| `SPEAKER_AND_LIP_SYNC` | `NOT_EVALUATED` | 采样外观符合男先女后，但当前 project-local surface 无 lip-sync 专用能力，0.5 秒采样不能证明 phoneme-level sync。 |
| `CAMERA_AND_CONTINUITY` | `PASS` | 单一连续 Shot、稳定慢推、轴线与人物位置不变，无切镜或 morph。 |
| `TEXT_AND_CLAIM_EXCLUSION` | `PASS` | 无生成字幕、overlay、百分比、医学/机制、时长、testimonial 或 absolute claim。 |
| `NATIVE_AUDIO` | `PASS` | Exact MP4 含可解码且有信号的 AAC；两次 ASR 检出男先女后的两句语义，无重复广告音频。 |

Raw Gate：

`runs/qingyan-seedance2-fast-dialogue-benefit-20260828-002/evidence/post-media-gate.json`

- Gate SHA-256: `6c111f798cecb9fed624f8968ff5029831100d96b4e5e522c58515a37c28f586`
- overall verdict: `STOP_NOT_ALL_REQUIRED_FINDINGS_PASS`
- independent review verdict: `accept with concerns`；reviewer 的 outer-pocket concern 已收紧为
  `PORTABILITY_ACTION=NOT_EVALUATED`

因此当前只交付 raw candidate 供人工查看；没有烧录 authored subtitles、没有重新 composition、没有
新 final、没有 candidate activation，也没有 P6 / Final Acceptance。原 V4 仍是 current local
review-only artifact，并继续受未核验尾卡 claim 限制。

Manifest 已保存 exact fetch receipt，但 generation attempt 仍为 `running`、phase=`validate`、candidate
列表为空；paid-provider phase 为 `settled`。`evidence/live-report.json` 是 submit/fetch 时快照，其中的
`post-media requirement gate pending` 不是当前 lifecycle truth。内部 ledger 以 estimated upper bound
4.7952 CNY settle reservation；本轮没有读取外部 Provider 实际账单，不能把该估算描述成已核验实扣。

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
