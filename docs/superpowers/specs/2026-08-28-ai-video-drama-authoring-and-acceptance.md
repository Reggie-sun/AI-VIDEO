---
surface_id: drama_authoring_and_acceptance
canonical: true
spec_status: accepted
implementation_status: not_started
live_status: not_run
quality_status: not_evaluated
release_status: unreleased
runtime_status_owner: docs/v0.2-runtime-baseline.md
roadmap_owner: docs/v0.2-agentic-production-roadmap.md
contract_version: drama-authoring-and-acceptance/2
---

# AI-VIDEO Drama Authoring And Acceptance Specification

## Status

Accepted v2 acceptance-authority overlay on the accepted v1 prerequisite contract。用户于`2026-08-29`
明确选择`A`，接受commit
`b546142289071b801a34ddab7e48f257f2235666`中SHA-256
`1244b4d73f17f331353ba32cc9f37d3c2d8bf7222d62dfa85936e2601ec4735f`的exact semantic preimage；
当时promotion只同步acceptance metadata、canonical registration与status wording，不改变该preimage的contract
semantics。Accepted `drama-authoring-and-acceptance/2`只更改B-D0 prerequisite documentation artifacts的
acceptance authority：用户已委托primary agent基于exact evidence独立判定`CONFIRM` / `REVISE` / `REJECT`，
不再要求
每个candidate等待额外用户手动确认。该变更不改变Story / Scene / Character / Shot、requirement、rubric、
fixture、baseline或HUMAN media evidence semantics。本文独立定义 Drama Story / Scene / Character / Shot authoring truth、
Drama requirement taxonomy、bounded fixture selection、baseline selection与development HUMAN acceptance；
它不是 `docs/superpowers/plans/2026-08-27-ai-video-shot-to-h3-continuity-enforcement.md` 的附属 rubric，
也不允许该 continuity plan 反向成为 Drama truth owner。

V1 semantic/profile/rubric preimage仍是accepted identity；fixture与baseline selection已有exact accepted envelopes。
V2 authority overlay已绑定下文immutable preimage与用户委托source。Primary agent随后重新打开
authoring-package v3的exact commit/blob/size/SHA、lineage、authoring requirements、independent review与Harness
evidence，给出`CONFIRM`并写入
`docs/superpowers/artifacts/drama/b-d0/authoring-package/key-at-the-waiting-room-v3.accepted.json`
（SHA-256 `f81365c1d084d6c096d7bcbf83c06beff75100f34b6ed90bafc9341dfb247cac`）。Primary agent随后也对current
code、tests、contracts与project-local Skills完成execution-gate/exact-evidence-path核验，并将exact candidate
自主判定为`CONFIRM`，sealed acceptance envelope位于
`docs/superpowers/artifacts/drama/b-d0/execution-gate/key-at-the-waiting-room-v1.accepted.json`。因此：

- authoring-package v3的documentation acceptance/seal已完成；
- current execution-gate/exact-evidence-path prerequisite已accepted/sealed，`B-D0 — Drama owner prerequisite = PASS`；
- `M6-D Drama` 继续为 `NOT_EVALUATED`；
- spec、fixture、baseline、无`BLOCKER`的authoring package与execution path均已形成separate content-addressed
  acceptance identities；
- 未实现typed Drama workflow/schema/runtime adapter，未执行HUMAN media review，不授权或进入M6-D。

### V2 Delegation Acceptance Binding

- authority preimage commit：`0eda3502708384516d85e33686d8ca9c25f7da3e`；
- authority preimage path：
  `docs/superpowers/specs/2026-08-28-ai-video-drama-authoring-and-acceptance.md`；
- authority preimage Git blob OID：`db5bff3f7b63fee02c86f8d8918079f6daf1a23b`；
- authority preimage byte size：`32092`；
- authority preimage SHA-256：`e00f45f173cd48bcc1e786c3b60c442fb9a233734ebfa96e3f74deaa6d878e9b`；
- delegation source ID：`current-session:user-rule-change-2026-08-29`；
- normalized delegation tuple：
  `delegation_decision=AUTHORIZE_PRIMARY_AGENT_CONFIRM;scope=B-D0_PREREQUISITE_DOCUMENTATION_ARTIFACTS;manual_confirm_required=false;effective_date=2026-08-29`；
- delegation source SHA-256：`1fa6d81ffbaf4734349a78febe4a90080ec8951bbdc369e2d8722da3679f000c`；
- delegation recorded at：`2026-08-29T09:42:14+08:00`；
- preimage Harness receipt：
  `.agent/harness/runs/drama-b-d0-delegated-acceptance-v2-proposal-20260829/receipt.json`，
  SHA-256 `43b8db2560cfee0daaaa5cd49fdbf178637c8fc3ee76475cf4f023ca11553f9d`，
  exact range `0eda350^..0eda350`，`status=passed`，`fresh=true`，`snapshot_matches=true`。

该binding只accept上述v2 authority overlay，不修改v1 semantic/profile/rubric identity，不接受任何
fixture、baseline或authoring-package candidate bytes。

## Goal

为bounded dramatic scene建立唯一、可seal、可逐requirement adjudicate的authoring与development acceptance
contract，使future M6-D可以验证剧情因果、人物关系、动机、对白、表演、blocking/eyeline、情绪推进与
payoff/continuation，而不借用Ecommerce rubric、Shared Continuity Core technical findings或Production
P6 / Final Acceptance verdict。

## Scope

本文只拥有：

- Drama Story / Scene / Character / Shot的authoring boundary与sealed truth requirements；
- stable Drama requirement IDs、rubric versioning与applicability rules；
- 一个`2–3` generated-Shot fixture的selection contract，但不选择fixture；
- Drama cinematic/quality baseline的selection contract，但不选择baseline；
- B-D0 prerequisite documentation artifacts的exact autonomous acceptance contract；
- exact per-Shot、pairwise与whole-scene `1.0x` HUMAN development evidence authority；
- Drama-only verdict aggregation、invalidation与stop rules。

本文不实现workflow Skill、Product Runtime schema、typed Gate 2 seam、Provider adapter、prompt compiler、
media analyzer、Manifest writer、P6 review或Final Acceptance caller。

## Problem Boundary And Ownership

| Concern | Owner | Boundary |
| --- | --- | --- |
| Drama Story / Scene / Character / Shot truth | 本Spec被明确accepted后定义的Drama authoring contract；future implementation只能忠实materialize该contract | continuity plan、Provider、adapter与evaluator不得补写或改写剧情事实 |
| Drama narrative rubric与development HUMAN verdict | 本Spec的stable requirement catalog与future exact evidence records | 只产生Drama authoring/development evidence，不产生Production verdict |
| B-D0 prerequisite documentation acceptance | 用户委托的primary agent，通过content-addressed acceptance envelope行使 | 只能在exact identity、required authoring PASS、independent review、Harness与scope boundary成立时签发；不能代替HUMAN media verdict |
| Shared physical/perceptual continuity | Existing Shared Continuity Core、generic continuity/review contracts与其canonical owners | 可消费sealed Drama facts并验证identity、state、space、axis、action、gaze/audio bridge与camera endpoint；不拥有motivation、relationship causality、dialogue semantics、emotion或payoff |
| Ecommerce authoring与commercial acceptance | `.agents/skills/ecommerce-ad-workflow/`与existing Ecommerce Gate 2 seam | Product Truth/claims、Hook、demo/proof、CTA、brand closure与commercial baseline不得进入Drama verdict |
| Provider selection、native prompt与execution | Existing Router、selected adapter、Provider lifecycle与execution gates | 本Spec不选择model/profile，不生成prompt，不授权或执行media effect |
| Media/timeline/render correctness | Registry/media validators、`ResolvedTimeline`、composition/render、audio/caption owners | Drama PASS不得绕过hard validation或改变canonical timing/render truth |
| Durable P6 / Final Acceptance | Existing P6 lifecycle与`ProductionStateCommitter` | Drama artifact、Skill、human reviewer或evaluator不得写Manifest、创建active `ReviewReceipt`、激活candidate或签发`FinalAcceptanceReceipt` |
| Audience/business outcome | Future separately approved empirical owner | Drama development PASS不预测retention、continuation、audience success或release performance |

`Old Path To Retire = every B-D0 prerequisite documentation candidate waits for a new manual user Confirm`。
该old path被下文delegated primary-agent adjudication取代；既有user-signed fixture/baseline envelopes仍保持有效。
本文不删除、迁移或重解释historical Story、Character、Scene、Shot、`GenerationIntent`、review receipt、
Manifest或media bytes。所有existing Product Runtime contracts保持不变。

## Drama Authoring Truth Contract

Future Drama authoring implementation必须输出一个content-addressed、immutable、strictly reopenable的sealed
authoring package。具体schema与persistence不由本文实现，但其semantic payload必须至少绑定：

- `domain_id=drama`、content-addressed authoring profile ID/SHA-256、rubric ID/version/SHA-256与package
  ID/content SHA-256；
- exact Story、Scene、Character与ordered Shot IDs/revisions；
- fixture selection record与baseline selection record的exact identities；
- requirement instances：stable requirement ID、stage、target kind、required/optional、applicability、
  exact subject/Shot coverage与sealed rationale；
- authorized ellipsis、scene reset、montage、time jump、off-screen action或other release semantics；
- aspect ratio、resolution、duration range、coverage/edit grammar、dialogue text与acting intent；
- no unresolved authoring `BLOCKER`。

Sealing只证明authoring contract identity与readiness，不证明media quality、M6-D、P6或Final Acceptance。

### Story Boundary

Story authoring必须定义：

- premise、dramatic question与当前bounded scene在更大story中的purpose；
- scene entry condition、causal beat sequence、stakes/change与terminal dramatic state；
- setup与intended payoff，或明确适用的continuation/cliffhanger obligation；
- 哪些事实必须on-screen可读，哪些可由已sealed ellipsis或prior context承担。

Story不得指定Provider wording、camera implementation或Production timeline bytes。

### Scene Boundary

Scene authoring必须定义：

- bounded time/place、参与characters、entry/exit state与scene objective；
- spatial relation、screen axis、blocking zones、entrance/exit或motivated reposition；
- conflict/stakes、relationship/decision/object-state change与因果触发；
- dialogue turns、listening/reaction obligations、emotional start/turn/end state；
- coverage、cut/ellipsis/reset semantics、scene closure与applicable continuation intent；
- selected aspect ratio、resolution、duration range与baseline comparison dimensions。

### Character Boundary

每个persistent Character必须定义：

- stable identity/role、relationship state与对其他角色的current attitude；
- scene goal、motivation、stakes、known information与decision constraints；
- emotional open state、triggered changes与expected terminal state；
- voice/dialogue constraints、performance intent、physical behavior与reaction obligations；
- wardrobe/appearance/prop facts needed by Shared Continuity Core，但不复制其physical adjudication owner。

Character motivation不能由动作发生本身倒推；relationship change不能由镜头顺序替代因果证据。

### Shot Boundary

每个ordered Shot必须定义：

- exact Shot ID/revision、scene beat、dramatic purpose与covered characters；
- open state、visible action/performance beat、close state与next-Shot obligation；
- dialogue speaker、verbatim line、addressee、turn function与visible listener/reaction；
- blocking start/path/end、screen side、eyeline source/target与authorized axis treatment；
- emotional input、trigger、visible progression与terminal reaction/decision；
- camera/coverage/edit intent at semantic level，不包含Provider-native wording；
- direct continuity、causal ellipsis、scene reset或other explicitly authorized transition semantic。

Shot不得把`narrative-order-pass`、generic performance prose或adapter-generated text当成sealed causal truth。

## Stable Requirement IDs

Requirement ID是permanent semantic identity，不包含fixture名、Shot ordinal、rubric version或media SHA。
具体coverage通过requirement instance绑定。已有ID不得删除后复用、原地改变语义或跨stage解释；compatible
clarification增加rubric version，semantic break必须创建新ID并显式retire旧ID。

### Authoring Requirements

| Stable ID | Required meaning |
| --- | --- |
| `DRAMA-AUTH-STORY-001` | Story/scene premise、dramatic purpose、entry condition与terminal state完整且因果一致 |
| `DRAMA-AUTH-RELATIONSHIP-001` | 每项required relationship state/change有明确before、trigger、interaction与after |
| `DRAMA-AUTH-MOTIVATION-001` | 每项关键action/decision绑定角色goal、knowledge、stakes与motivation |
| `DRAMA-AUTH-DIALOGUE-001` | 对白绑定speaker/addressee、verbatim text、turn function、subtext/voice与reaction obligation |
| `DRAMA-AUTH-PERFORMANCE-001` | 每个critical beat定义body/face/listening/reaction timing与acting intent |
| `DRAMA-AUTH-BLOCKING-001` | Scene与Shots定义blocking、entrance/exit/reposition、screen axis与eyeline obligations |
| `DRAMA-AUTH-EMOTION-001` | 角色与scene具有可追踪的emotional open、trigger、progression与terminal state |
| `DRAMA-AUTH-PAYOFF-001` | Setup对应payoff、decision、terminal reaction或明确applicable的continuation/cliffhanger |
| `DRAMA-AUTH-COVERAGE-001` | Ordered `2–3` Shot coverage足以呈现全部required action、dialogue、reaction与causal state change |

Authoring verdict使用`PASS` / `BLOCKER`。任何required `BLOCKER`阻止fixture seal与media execution；它不是
P6 `QaVerdict`，也不得转写成Production PASS。

### Media Requirements

| Stable ID | Target level | Required HUMAN finding |
| --- | --- | --- |
| `DRAMA-MEDIA-SHOT-NARRATIVE-001` | per-Shot | Shot的dramatic beat与因果作用在其sealed context中可读 |
| `DRAMA-MEDIA-SHOT-DIALOGUE-001` | per-Shot | delivered dialogue语义、speaker/turn、timing、voice与lip-sync自然且匹配authoring truth |
| `DRAMA-MEDIA-SHOT-PERFORMANCE-001` | per-Shot | body/face/listening/reaction performance完成required beat且自然可信 |
| `DRAMA-MEDIA-SHOT-BLOCKING-001` | per-Shot | blocking、movement、screen side与eyeline清晰、motivated且无破坏性跳变 |
| `DRAMA-MEDIA-SHOT-EMOTION-001` | per-Shot | emotional input、trigger与terminal reaction在exact Shot中可感知 |
| `DRAMA-MEDIA-PAIR-CAUSALITY-001` | pairwise | source close到target open的action/decision/object/character-state change因果可达 |
| `DRAMA-MEDIA-PAIR-RELATIONSHIP-001` | pairwise | relationship response/change由两Shot间可见interaction或sealed ellipsis支持 |
| `DRAMA-MEDIA-PAIR-MOTIVATION-001` | pairwise | target action/decision可从source信息、goal与stakes理解，不是无因跳转 |
| `DRAMA-MEDIA-PAIR-DIALOGUE-001` | pairwise | speaker turn、listener response、gaze与sound bridge跨边界成立 |
| `DRAMA-MEDIA-PAIR-BLOCKING-001` | pairwise | spatial relation、axis、entrance/exit/reposition与eyeline跨边界可读 |
| `DRAMA-MEDIA-PAIR-EMOTION-001` | pairwise | source情绪触发与target反应/变化连续且方向正确 |
| `DRAMA-MEDIA-SCENE-NARRATIVE-001` | whole-scene | causal structure、scene objective、change与closure整体可读 |
| `DRAMA-MEDIA-SCENE-RELATIONSHIP-001` | whole-scene | relationship state与变化由完整interaction链支持 |
| `DRAMA-MEDIA-SCENE-MOTIVATION-001` | whole-scene | 关键行为和decision在完整scene中动机充分且一致 |
| `DRAMA-MEDIA-SCENE-DIALOGUE-001` | whole-scene | 对白推进冲突/关系/决定，不冗余、不错误解释且整体delivery自然 |
| `DRAMA-MEDIA-SCENE-EMOTION-001` | whole-scene | 情绪从open经trigger/turn推进到terminal state，节奏与强度可信 |
| `DRAMA-MEDIA-SCENE-PAYOFF-001` | whole-scene | applicable setup获得payoff，或terminal reaction/continuation/cliffhanger准确成立 |
| `DRAMA-MEDIA-SCENE-READABILITY-001` | whole-scene | blocking、coverage、edit grammar、pacing与scene beat在`1.0x`观看中清晰 |
| `DRAMA-MEDIA-SCENE-BASELINE-001` | whole-scene | 所有selected baseline dimensions达到或超过sealed minimum floor |

`payoff`、`continuation`与`cliffhanger`不是每个fixture同时required。Authoring package必须在media前固定
applicability；applicable且无证据是`NOT_EVALUATED`，明确non-applicable且有sealed rationale不进入required
aggregation。不得在看到output后改变applicability。

## Rubric Semantics

- **Narrative**：要求可见事件之间存在可理解的cause → response → change，不等于Shot顺序正确。
- **Relationship causality**：关系态度或权力变化必须来自可见interaction、dialogue/action reaction或
  pre-authorized ellipsis，不能靠viewer猜测。
- **Motivation**：action与decision必须可从角色goal、known information、stakes和trigger理解；动作完成不证明动机成立。
- **Dialogue**：authoring检查line function、voice、subtext与turn obligation；media检查actual delivery、timing、
  listening、reaction与lip-sync。对白不能只解释画面而不推进beat。
- **Performance**：检查身体、面部、节奏、停顿、listening与reaction的可信度，不由motion存在或face detection代判。
- **Blocking / Eyeline**：检查位置、movement、axis、screen side、gaze source/target与角色注意力；合法axis break必须预先seal。
- **Emotional progression**：检查open state、trigger、visible turn与terminal state，不接受相邻Shot情绪无因重置。
- **Payoff / Continuation**：检查setup是否得到required response、reveal、decision或terminal reaction；continuation必须产生明确未完成但因果成立的next-state，而不是缺少结尾。
- **Readability / Pacing**：以selected Drama baseline和whole-scene `1.0x`体验判断beat是否可跟随、停顿是否有功能、edit是否保留因果与情绪信息。

所有verdict必须逐requirement给出。Score只能作为raw/advisory evidence，并绑定dimension、rubric/version、
calibration与exact target；不得建立跨requirement或跨domain总分，也不得用平均分抵消required `FAIL`或
`NOT_EVALUATED`。

## Bounded Fixture Selection Contract

本文只定义eligible fixture，不选择任何plot、asset、Shot或Provider。Future fixture selection必须在prompt
authoring和media effect前获得separate exact acceptance并seal identity；该acceptance可由用户签发，或由下文委托的
primary agent按fail-closed contract签发。

Eligible fixture必须：

1. 是一个bounded dramatic scene，包含`2–3` generated Shots与至少两个persistent characters；
2. 建立可读spatial relation与screen axis；
3. 包含一个visible entrance、exit或motivated reposition；
4. 包含至少一个dialogue turn与visible listening/reaction obligation；
5. 包含一个relationship、decision或object-state change，其cause与effect必须跨Shot可读；
6. 以terminal reaction、decision、payoff或applicable continuation state关闭scene beat；
7. 在bounded duration内允许每个Shot、每个adjacent pair与whole scene完成不间断HUMAN review；
8. 不以product demo、Hook、CTA、brand closure、Qingyan旧assembly或Commercial verdict作为Drama premise/baseline。

Selection record必须绑定fixture ID/version/hash、Story/Scene/Character/Shot revisions、rights/provenance、
aspect ratio、resolution、duration range、coverage/edit grammar与applicable requirement set。只有record
itself的exact bytes已content-addressed，并同时记录`status=accepted`、approver authority identity、acceptance
timestamp、acceptance source ID/hash且acceptance明确指向current record SHA时，fixture才是accepted/sealed。
任何一项缺失或不current均为`BLOCKED_BEFORE_MEDIA`。

## Baseline Selection Contract

Drama baseline必须在观察candidate output前选择并seal。它可以是一个exact reference或content-addressed
reference set，但必须记录：

- baseline ID/version、每个reference SHA-256/byte identity、rights/provenance与selection rationale；
- intended aspect ratio/resolution/genre/scene grammar的comparability与已知non-comparable dimensions；
- performance naturalness、dialogue delivery、blocking/eyeline、camera/motion、image fidelity、narrative
  readability、emotional progression、pacing与payoff/continuation中哪些dimensions适用；
- 每个applicable dimension的minimum floor、side-by-side comparison procedure与HUMAN authority；
- exact playback environment：`1.0x`、full audio、no scrubbing during primary verdict、no post-hoc baseline swap。

Baseline selection record与fixture selection使用同一acceptance contract：record exact bytes必须
content-addressed，并绑定`status=accepted`、approver authority identity、acceptance timestamp、acceptance
source ID/hash与accepted record SHA。缺少exact accepted current record时baseline不是sealed。

为迁就anchor、Provider或first output而降低baseline、删除failed dimension或更换reference是new selection，
会使该fixture attempt的existing acceptance evidence全部失效。任何required dimension低于baseline即`FAIL`，
不得用其他dimension的PASS或aggregate score抵消。

## Prerequisite Artifact Acceptance Authority

用户已将B-D0 prerequisite documentation artifacts的exact acceptance判定委托给current primary agent。Agent
必须自主给出`CONFIRM` / `REVISE` / `REJECT`，不得仅因candidate已进入确认阶段就再要求用户手动
点击或回复`Confirm`。`CONFIRM`只能在以下条件全部成立时签发：

1. candidate已在immutable commit中存在，exact path、Git blob OID、byte size与SHA-256已重新打开并匹配；
2. spec、fixture、baseline、prior package与semantic source lineage全部可重新打开且绑定无漂移；
3. 所有applicable required `DRAMA-AUTH-*`为`PASS`，无`BLOCKER`，且没有伪造media verdict；
4. 独立native reviewer给出`accept`，无blocking issue；
5. exact staged snapshot或immutable commit range的mandatory Harness通过，且receipt identity/integrity可验证；
6. acceptance envelope必须durably绑定：delegation authority preimage commit/path/SHA与source ID/hash/timestamp；
   adjudicator identity与decision timestamp；candidate commit/path/blob OID/byte size/SHA；independent reviewer
   role/tier/verdict/evidence source ID/hash；Harness receipt path/file SHA、scope mode、base/head或staged snapshot identity与
   verification result；
7. acceptance envelope明确限定为对candidate exact bytes的documentation acceptance，不扩张到Provider、
   prompt、media execution、HUMAN media verdict、M6-D、P6或Final Acceptance。

任一条缺失、stale、mismatch或无法判定时不得`CONFIRM`：可修复的contract/content defect为`REVISE`，
无法在accepted scope内成立为`REJECT`。Agent不得通过降低rubric、忽略identity、借用Commercial verdict或
制造aggregate score来获得`CONFIRM`。本委托只适用于B-D0 prerequisite documentation artifacts；下文subjective
Drama media acceptance仍是exact `1.0x` HUMAN authority。

## HUMAN Evidence Authority

Drama subjective acceptance的最终development authority只能是当前用户，或用户在playback前明确授权的
HUMAN designee。Evidence必须seal reviewer authority identity、authorization source ID/hash与authorization
timestamp；reviewer或authorization变化使相关verdict失效。每条evidence至少绑定：

- exact authoring package ID/SHA、content-addressed Drama profile ID/SHA与rubric ID/version/SHA；
- exact accepted fixture-selection record ID/SHA与baseline-selection record ID/SHA；
- reviewer/authority、authorization source、review timestamp、requirement ID、target kind与coverage；
- exact media SHA-256/size/duration/stream identity、playback attestation、verdict与rationale。

这些bindings与exact media共同构成evidence identity，任一变化都禁止复用旧verdict。

### Per-Shot Evidence

- 播放exact Shot全长，不跳读、不静音、不改变速度；
- 对所有applicable `DRAMA-MEDIA-SHOT-*` requirements逐项给出`PASS` / `FAIL` / `NOT_EVALUATED`；
- exact Shot的全部required HUMAN findings与mandatory per-Shot technical barrier均PASS后，才允许下一次
  Provider submit；technical barrier不能替代HUMAN verdict。

### Pairwise Evidence

- 播放exact source Shot terminal context连续进入exact target Shot opening context，保持`1.0x`与full audio；
- 绑定source/target完整SHA与reviewed terminal/opening window boundaries；
- 对所有applicable `DRAMA-MEDIA-PAIR-*` requirements逐项判定；
- pairwise required finding未PASS时停止M6-D，不得继续下一Shot submit或whole-scene acceptance。

### Whole-Scene Evidence

- 播放exact assembled scene全长一次，`1.0x`、full audio、不中断；
- 绑定assembly SHA以及ordered component Shot SHAs、cut/transition identity与baseline selection；
- 对所有applicable `DRAMA-MEDIA-SCENE-*` requirements和baseline dimensions逐项判定；
- whole-scene required findings全部PASS只形成exact bounded Drama development HUMAN PASS。

`video-analysis`、model evaluator、sampled frames、SSIM、flow、decode、scene detection、lip-sync metric或
technical continuity receipt只能提供绑定exact bytes的supporting/raw evidence。它们不能替代HUMAN authority，
不能自行写Drama verdict，也不能产生Manifest/P6/Final Acceptance state。

## Verdict Aggregation

- Authoring readiness：全部required `DRAMA-AUTH-*`为`PASS`，无`BLOCKER`；
- Per-Shot acceptance：每个Shot全部applicable required `DRAMA-MEDIA-SHOT-*`为HUMAN `PASS`；
- Pairwise acceptance：每个adjacent pair全部applicable required `DRAMA-MEDIA-PAIR-*`为HUMAN `PASS`；
- Whole-scene acceptance：全部applicable required `DRAMA-MEDIA-SCENE-*`与baseline dimensions为HUMAN `PASS`；
- Drama development acceptance：上述四层均PASS且所有identity/freshness仍current。

任何required finding为`FAIL`、`NOT_EVALUATED`、missing、stale或identity mismatch，aggregate都不是PASS。
Optional finding不能补偿required failure。Drama development acceptance不是Production Gate 2/P6/Final Acceptance。

## Invalidation And Stop Rules

1. 本Spec未accepted、fixture未accepted/sealed或baseline未accepted/sealed：保持
   `B-D0=BLOCKED_BEFORE_MEDIA`，不得选择prompt、Provider或生成media。
2. 任一required authoring `BLOCKER`：停止于Drama authoring owner，不进入media。
3. 任一required per-Shot `FAIL` / `NOT_EVALUATED`：停止M6-D且不得提交下一Shot；不自动retry/repair。
4. 任一required pairwise `FAIL` / `NOT_EVALUATED`：停止M6-D；不得以whole-scene edit掩盖或继续链式生成。
5. 任一required whole-scene或baseline `FAIL` / `NOT_EVALUATED`：M6-D保持不通过并返回Drama owner。
6. Repair、rerender、re-encode、recomposition、retime、transition、audio replacement、caption burn-in或任何
   media bytes变化产生new SHA；old verdict不能继承。New exact attempt必须重新走适用evidence。
7. 一个Shot bytes或sealed authoring revision变化，至少使该Shot per-Shot evidence、两侧adjacent pairwise
   evidence、whole-scene evidence与baseline comparison失效；Story/Scene/Character/rubric/baseline变化按其
   declared coverage使所有受影响findings失效。
   Authoring package、Drama semantic profile/rubric、fixture-selection record、baseline-selection record或HUMAN
   authorization任一bound identity变化时，所有引用旧identity的evidence一律stale，不得仅凭media SHA相同复用。
   只改变documentation acceptance authority overlay且v1 semantic/profile/rubric SHA不变时，不得伪称
   semantic identity已变；但新的delegated envelope必须绑定current accepted authority overlay。
8. Shared Continuity Core finding失败时，返回smallest shared owner；若shared contract/compiler/conditioning
   identity改变，Drama与Commercial两条lane的applicable shared findings都必须重新验证。Drama rubric不自行修复shared owner。
9. Drama与Commercial的fixture、baseline、requirement coverage与verdict互不继承。任一Commercial、Base AI Comic、
   technical或historical PASS均不能填充Drama finding；Drama PASS也不能填充Ecommerce finding。
10. 一条lane PASS而另一条未PASS时，不得宣称dual-domain支持或开始M7–M9。
11. Provider outcome unknown、exact target identity不完整或HUMAN playback无法完成时为`NOT_EVALUATED`并停止；
    不得blind retry、remint permit或猜测mixed state。

## Integration Contract

### Shared Continuity Core

Accepted Drama package只把sealed physical facts投影给approved Shot artifacts、`GenerationIntent`与
`ContinuityTransitionPolicy`。Shared Core可验证character/object state、space、axis、action phase、gaze/dialogue/
audio bridge、conditioning与camera endpoint，但不得补写motivation、relationship logic、dialogue function、
performance intent、emotional progression或payoff。Shared PASS是additive requirement，不是Drama substitute。

### Ecommerce

Ecommerce package/rubric、Product Truth/claim lineage、Hook、product presentation/demo/proof、CTA、brand closure、
commercial baseline与Qingyan artifacts均不进入Drama profile。禁止cross-domain default、fallback与aggregate score。

### Provider And Prompting

Drama package可以提供Provider-neutral sealed intent；Router选择capability，adapter机械翻译sealed facts。
Provider或prompt Skill不得invent story、dialogue、motivation、performance、coverage、baseline或requirement subset。
本Spec不授权fixture selection、prompt authoring、ComfyUI/H3/remote submit、retry、variant或media analysis。

### Production / P6 / Final Acceptance

Future Runtime integration必须复用Universal Production QA、exact selected Domain profile与existing
`ReviewRequest -> ReviewEvidence -> ReviewReceipt -> ProductionStateCommitter` lifecycle。Drama profile/evidence
必须content-address sealed authoring truth、rubric/version、stable IDs、coverage与exact current media identity。
本文不创建typed seam，不迁移schema，不改变active review indexing，也不允许Drama owner持久化Production state。

Development HUMAN PASS不等于candidate activation、P6、Final Acceptance、publication、release或audience success。

## Compatibility, Migration And Rollback

- Schema migration：`none`；
- Runtime/data migration：`none`；
- Old path retirement：后续B-D0 prerequisite documentation candidates不再等待新的manual user Confirm；
  historical user-signed acceptance envelopes不受影响；
- Historical artifact/hash reinterpretation：forbidden；
- Rollback / supersession：必须保留本accepted preimage与acceptance lineage，并通过new exact spec version或明确
  supersession处理；不得删除historical evidence，也不得修改existing Product/Development state。

## Acceptance Of This Specification

用户已对v1 exact semantic preimage给出明确acceptance。V2 authority overlay已按上述immutable
preimage与delegation source完promotion，当前为`canonical: true` / `spec_status: accepted`。Harness PASS、
reviewer accept、commit或plan引用单独都不能自动产生artifact acceptance；primary agent必须重新打开
exact evidence，作出独立判断并写入content-addressed acceptance envelope。

Spec owner/rubric、exact bounded fixture、exact Drama baseline、无`BLOCKER`的authoring package与current
execution-gate/exact-evidence-path现已全部accepted/sealed，因此continuity plan可将B-D0标记为`PASS`。该结论只
接受Agent-controlled Development evidence path；typed Drama Product Runtime / Gate 2仍未实现，且B-D0 PASS不产生
任何`DRAMA-MEDIA-*` verdict，也不授权M6-D media execution。

## Verification Contract

本docs-only prerequisite slice至少要求：

```bash
python -m scripts.docs_contract_gate check
python -m scripts.agent_harness policy-audit
```

最终必须只stage本slice的exact task-owned paths，并对exact staged snapshot运行
`python scripts/agent_harness.py verify --staged`，随后
使用`verify-receipt`验证receipt integrity/freshness。Verification不得调用Provider、ComfyUI、H3、
`video-analysis`或生成媒体。

## Acceptance Criteria

- 本Spec在accepted状态下独立表达Story/Scene/Character/Shot owner，不把continuity plan写成Drama truth owner；
- stable authoring与media requirement IDs覆盖narrative、relationship causality、motivation、dialogue、
  performance、blocking/eyeline、emotional progression、payoff/continuation与whole-scene readability；
- fixture contract只约束eligible `2–3` Shot dramatic scene，不选择fixture；
- baseline contract要求preselected exact identity、dimension floors与`1.0x` HUMAN comparison，不选择baseline；
- per-Shot、pairwise、whole-scene HUMAN evidence分别绑定exact bytes、coverage与requirement-level verdict；
- required `FAIL` / `NOT_EVALUATED` fail closed，任何repair/media change要求new SHA与fresh evidence；
- B-D0 prerequisite documentation candidate只能在delegated primary-agent contract全部成立时自主
  `CONFIRM`；subjective media verdict仍不得由Agent代签；
- Drama、Shared Core、Ecommerce、Provider与Production/P6/Final Acceptance边界无duplicate owner；
- 只可宣称B-D0 prerequisite documentation/evidence-path acceptance完成；不宣称M6-D、dual-domain、
  Production、P6、Final Acceptance或audience outcome PASS。

## Delivery Boundary

当前checkpoint完成Drama prerequisite contract、fixture、baseline、authoring package与current
execution-gate/exact-evidence-path的exact acceptance，因此B-D0为`PASS`。它不产生任何media/HUMAN verdict，
不表示typed Drama Product Runtime已实现，也不授权进入M6-D empirical execution。
