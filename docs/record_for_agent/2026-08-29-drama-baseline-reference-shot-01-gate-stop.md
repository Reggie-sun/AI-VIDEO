---
record_kind: media_experiment
topic_id: drama-baseline-reference-acquisition
learning_eligibility: eligible
evidence_index_version: "1"
---

# Drama Baseline Reference Shot 01 Gate Stop Record

Date: 2026-08-29

## Supersession Notice — 2026-08-29 Package Accepted

下方“authoring-package v3仍等待exact acceptance”与`B-D0=BLOCKED_BEFORE_MEDIA`的current-facing描述现为
historical。Primary agent已根据用户委托的accepted v2 documentation-authority overlay自主确认exact
package candidate，acceptance envelope为
`docs/superpowers/artifacts/drama/b-d0/authoring-package/key-at-the-waiting-room-v3.accepted.json`，SHA-256
`e36a1338fcec94fc6b3a7ecae08bfaab3ee6f54d6d91c065c986eefa02913edd`。Current state：
authoring package已accepted/sealed；`B-D0=BLOCKED_BEFORE_MEDIA`，remaining blocker为
`CURRENT_EXECUTION_GATES_AND_EXACT_EVIDENCE_PATH_NOT_VERIFIED`；`M6-D=NOT_EVALUATED`。原baseline reference
取得过程、media identity与当时gate-stop作为
historical evidence保留；本次supersession不授权任何Provider/media/P6行为。

## Supersession Notice — 2026-08-29 Reference Review PASS

Current user已在收到exact MP4 path、SHA-256与`1.0x` full-audio instruction后明确返回PASS decision。该决定绑定
SHA-256 `6a9e0504fe946c7320b93895c66e8c5423db7cc1eff0f46bbe9e7b3712259331`，并将Shot 1提升为
`HUMAN_PASS`的usable baseline-reference component。Original gate stop与下方五项`DRAMA-MEDIA-SHOT-* =
NOT_EVALUATED`仍作为历史且正确的M6-D proof-layer结论保留：当时以及当前都缺少accepted baseline selection和
sealed authoring package identities，因此reference review PASS不得改写成formal M6-D HUMAN PASS。

Current baseline-selection candidate为
`docs/superpowers/artifacts/drama/b-d0/baseline-selection/key-at-the-waiting-room-v3.proposed.json`。它仍需current
user对其exact committed bytes单独accept；在此之前`B-D0=BLOCKED_BEFORE_MEDIA`、`M6-D=NOT_EVALUATED`不变。

## Supersession Notice — 2026-08-29 Baseline Selection Accepted

Current user随后确认exact baseline-selection candidate commit `f9329547c0f59111838b64fafa7b7261ddfce991`、SHA-256
`bab68c8e43a36e33e12d8c3c5b8e0aea683db2b9889e8ef417a261ca77fd06bb`。Acceptance envelope位于
`docs/superpowers/artifacts/drama/b-d0/baseline-selection/key-at-the-waiting-room-v3.accepted.json`，commit
`db03d6154c4b2f00c1baf0dd6c48b1a32011c209`，SHA-256
`3056fd344cc2485fe6ddf089d7d50d6461b27b62756f293c9b1968d69a5d08f5`。

Baseline现为`ACCEPTED`；current remaining blocker只剩new exact authoring-package candidate尚未accepted。该变化不
retroactively创建formal `DRAMA-MEDIA-*` verdict，也不改变`M6-D=NOT_EVALUATED`。在package另行accepted前，
`B-D0=BLOCKED_BEFORE_MEDIA`。

## Purpose

本文记录dual-domain Shot-to-H3 continuity plan的独立Drama baseline-reference acquisition checkpoint。用户明确要求
由当前Agent自行生成并提供reference；该授权只用于取得可供HUMAN选择的development reference，不进入`M6-D`
empirical candidate execution，也不自动接受baseline或authoring package。

本次只提交一次local loopback ComfyUI request。Exact Shot 1落盘后，Agent在任何下一次submit之前调用project-local
`video-analysis`，并按exact per-Shot gate停在`NOT_EVALUATED`。没有生成Shot 2/3，没有retry、repair、activation、
composition、P6或Final Acceptance。

## Current Gate Truth

- `B-D0 = BLOCKED_BEFORE_MEDIA`；Drama spec、fixture与baseline selection已accepted，authoring-package v3
  candidate仍未exact accepted/sealed。
- reference-review layer：exact Shot 1为current-user `HUMAN_PASS`，只可作为usable baseline-reference component。
- `M6-D Drama = NOT_EVALUATED`；本reference不是M6-D candidate，formal `DRAMA-MEDIA-*` findings没有取得PASS。
- `M6-C Commercial = HUMAN_FAIL`；本地Drama reference不改变或继承Commercial verdict。
- minimum reference count已满足；本轮不需要、也未提交Shot 2。当前只剩authoring-package v3 exact acceptance。
- M7–M9继续deferred；单个technical PASS或reference bytes不能解除dual-domain gate。

## Exact Generation Identity

本轮使用accepted fixture lineage：

- fixture payload commit：`3b436195e939f7bc8fff5999438e9018030a38fe`；
- fixture payload SHA-256：`73a3a57e78859f8a508dd21cea3493a8d2a32ccb8a08c173a304b516fc5d34ab`；
- fixture acceptance envelope SHA-256：`e2601e8ac7af4686c3a4290a05d956c87d8bcea73bc146f16bad4ee5fad52e1d`；
- exact fixture Shot mapping：canonical `drama.shot.waiting-room.001@1` → runtime
  `drama-shot-waiting-room-001`。Generation与gate evidence都保存同一mapping，且fixture-level commit/SHA绑定不变。

Generation只走canonical public provider/committer/service lifecycle并停在fetch/`VALIDATE`：

- provider：`comfy-local-h3-t8`；
- model：`minimax-h3-t8-t2va-quality`；
- capability：`minimax-h3-t8-t2va-quality-v1`；
- profile logical SHA-256：`4b299a689723bb856026776500119774ee9490c777a6460e932007be022e05e7`；
- provider request ID：`b27178a4-23b3-4df5-beee-8b668c72893f`；
- provider-bound request hash：`fe1892016820290eadc854af8e35f6b59b77fe0f83201eb27182fab6f2f94f0c`；
- resolved generation hash：`44105e30484a2814c781dfc182d9a07dd97c8c0bc89a12343e7cf54a592e491a`；
- local submit count：`1`；remote submit count：`0`；
- activation performed：`false`；manifest phase：`validate`。

Quality T8当前tracked compiler不能表达requirement v4 native H3 prompt；本次reference acquisition没有修改Shared
Core或Provider实现，而是使用现有supported v1 provider-neutral input生成一个可供baseline选择的single-Shot
reference。这个限制使该bytes不能被解释为完整M6-D authoring package execution。

## Exact Media And Raw Evidence

提供给HUMAN review的exact MP4：

```text
runs/drama-baseline-reference-20260829/raw/shot-01-take-01-audio.mp4
SHA-256: 6a9e0504fe946c7320b93895c66e8c5423db7cc1eff0f46bbe9e7b3712259331
size: 1774445 bytes
```

Canonical fetched bytes位于：

```text
runs/drama-baseline-reference-20260829/projects/shot-01-take-01/state/video-generation/fetch/files/6a9e0504fe946c7320b93895c66e8c5423db7cc1eff0f46bbe9e7b3712259331.mp4
```

Fresh `ffprobe`与`video-analysis` raw evidence一致：H.264 High、`1344x768`、`24 fps`、`124` frames、
`5.167s`；AAC LC stereo、`32000 Hz`；one detected scene，未报告decode/container technical issue。

Exact evidence files：

- `runs/drama-baseline-reference-20260829/evidence/shot-01-take-01-generation.json`，SHA-256
  `29504670a5c6a891c5da27702c7e00ad87314b0651cfd5782d0c7d68c265c69d`；
- `runs/drama-baseline-reference-20260829/evidence/shot-01-take-01-agent-gate.json`，SHA-256
  `cd7943ec9da372e39f805cc5ad4e6eef423825623b28845e03aef63892fc49c7`；
- `runs/drama-baseline-reference-20260829/evidence/shot-01-take-01-contact-sheet.png`，SHA-256
  `48801b395936717a31f2de888b883464dce0f13a4e13ebdaab22b29206adb7c4`。

## Original Pre-Review Per-Shot Evidence Assessment

Visual sampled evidence可观察到locked medium-wide、Lan在screen-left seated、Jun在screen-right standing、Jun右手
展示钥匙、Lan由低头转为看向钥匙/Jun、没有伸手、没有cut或axis cross。这些observations支持后续HUMAN review，
但不拥有Drama subjective acceptance authority。

Whisper small返回两段中文transcription：`要是还在`与`回去一起开门`。第一段是required text
`钥匙还在`的同音表示，ASR不能证明exact spoken semantic wording；标点也不能由该证据裁决。因此
`DRAMA-MEDIA-SHOT-DIALOGUE-001`不能升级为PASS。

以下required findings全部保持`NOT_EVALUATED`：

- `DRAMA-MEDIA-SHOT-NARRATIVE-001`；
- `DRAMA-MEDIA-SHOT-DIALOGUE-001`；
- `DRAMA-MEDIA-SHOT-PERFORMANCE-001`；
- `DRAMA-MEDIA-SHOT-BLOCKING-001`；
- `DRAMA-MEDIA-SHOT-EMOTION-001`。

在initial gate时，exact HUMAN authority尚未完成，因此Per-Shot Post-Media Gate正确停止。后续current-user
reference-review PASS只关闭baseline-reference component review，不补齐initial gate时尚不存在的accepted
baseline/package bindings；technical analyzer、contact sheet、single score或Agent visual observation仍不得替代
formal HUMAN verdict。

## Evidence Index

| evidence_id | independence_key | experiment_id | attempt_id | arm_id | artifact_sha256 | proof_layer | verdict | failure_class | relation_kind | related_evidence_id | source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DRAMA-BASELINE-S01-E1 | drama-baseline-reference-20260829-shot01-take01 | drama-baseline-reference-20260829 | shot01-take01 | quality-t8-v1 | 6a9e0504fe946c7320b93895c66e8c5423db7cc1eff0f46bbe9e7b3712259331 | PROVIDER_FETCH | PASS | NONE | NEW_ATTEMPT | NONE | runs/drama-baseline-reference-20260829/evidence/shot-01-take-01-generation.json |
| DRAMA-BASELINE-S01-E2 | drama-baseline-reference-20260829-shot01-take01 | drama-baseline-reference-20260829 | shot01-take01 | quality-t8-v1 | 6a9e0504fe946c7320b93895c66e8c5423db7cc1eff0f46bbe9e7b3712259331 | TECHNICAL_MEDIA_VALIDITY | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | DRAMA-BASELINE-S01-E1 | runs/drama-baseline-reference-20260829/evidence/shot-01-take-01-agent-gate.json |
| DRAMA-BASELINE-S01-E3 | drama-baseline-reference-20260829-shot01-take01 | drama-baseline-reference-20260829 | shot01-take01 | quality-t8-v1 | 6a9e0504fe946c7320b93895c66e8c5423db7cc1eff0f46bbe9e7b3712259331 | HUMAN_PER_SHOT | NOT_EVALUATED | HUMAN_REVIEW_MISSING | SAME_EVIDENCE_NEW_PROOF_LAYER | DRAMA-BASELINE-S01-E1 | runs/drama-baseline-reference-20260829/raw/shot-01-take-01-audio.mp4 |
| DRAMA-BASELINE-S01-E4 | drama-baseline-reference-20260829-shot01-take01 | drama-baseline-reference-20260829 | shot01-take01 | quality-t8-v1 | 6a9e0504fe946c7320b93895c66e8c5423db7cc1eff0f46bbe9e7b3712259331 | HUMAN_REFERENCE_REVIEW | PASS | NONE | SAME_EVIDENCE_NEW_PROOF_LAYER | DRAMA-BASELINE-S01-E1 | docs/superpowers/artifacts/drama/b-d0/baseline-selection/key-at-the-waiting-room-v3.proposed.json |

四个rows属于同一attempt，不能计为四次independent evidence；technical、formal per-Shot HUMAN与reference-review
proof layers不得互换。

`distill-ai-video-learning` automatic evaluation与baseline acceptance / package-candidate checkpoint后的re-evaluation
结果均为`no_candidate`。Evidence identity validator通过，但本topic只有一个`independence_key`、没有controlled
multi-arm，也没有需要由本次evidence materially update的existing Learning Claim；因此不创建placeholder claim，
不进入confirmation或adoption flow。

## Runtime Restoration And Boundaries

为匹配sealed profile，local ComfyUI checkout曾临时切到`7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`并通过
loopback service执行exact request。取得analysis evidence后，service已停止，`/home/reggie/ComfyUI`已恢复到本轮
开始时的detached commit `e01fb4c56b7a88149d469b99cbbfe3223d715054`；没有留下active service。

本次reference output只在ignored `runs/`中保留，未stage或commit媒体。它不属于Asset Registry、Production
Manifest activation、P6、Final Acceptance、publish、release或remote availability。任何rerender、re-encode、
audio replacement或bytes变化都会产生new SHA并要求新的HUMAN verdict；本次gate不授权自动retry。

## Remaining Work

Shot 1 reference review与baseline selection均已accepted；minimum reference count满足，不需要为了流程完整性继续
生成Shot 2/3。自然停止点改为current user对new exact authoring-package candidate bytes给出
accept/revise/reject。在package无`BLOCKER`且exact accepted前，B-D0仍不能解除blocker。

本记录自身不是acceptance envelope，也不把generated reference、continuity plan或technical PASS写成Drama truth。
