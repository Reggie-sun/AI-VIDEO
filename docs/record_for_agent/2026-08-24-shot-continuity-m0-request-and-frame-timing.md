# Shot Continuity M0 Request And Frame Timing Record

Date: 2026-08-24

> **Superseded current-facing status (2026-08-25):** qualification-only source
> lifecycle、fresh bundle、non-test operator、profile reseal与唯一Local A2→A3 attempt均已
> 完成。Exact MP4已fetch，但frames 107→108发生明显跳变，未通过frozen boundary/motion
> gate；下文关于accepted source、P6与motion-tail的gates仍有效，M0 effect仍为零。见
> `2026-08-25-shot-continuity-source-live-attempt.md`。

## Purpose

本文记录 Shot Continuity Phase P1 的六个 candidate-neutral checkpoint：M0 request-level
pre-submit identity guard、C4对model-native exact frame-count timing的provider-neutral表达、
live node-schema materialization与execution-stack reseal closure，以及qualification-only caller的
完整pre-effect denial seam、content-addressed M0 seed seal与independent source execution stack closure。

本记录不证明 M0 已提交、视频已生成、candidate winner、active capability、P6 verdict、creative PASS、
Final Acceptance、push或release。

## Current Runtime Truth

selected rainy-station bundle已由旧v5 supersede为
`runs/shot-continuity-rainy-station-p0-20260824-v6/production`。Manifest revision `4`现在选择
source stack `1635abc300b33e94c513b2c92b6b99b770944b51d88a2689c69d619d861db2b4`、M0 stack
`8f9661c358162544a3cefd0f7ff4483063658fcb37de09f301ef7fe2500039d2`与receipt
`286991af1b8c08ef213af794f353d4ad84becad69b117b15a9836a6a53487937`。M0
profile/compiler/workflow hashes分别为`9bf6588c04712887b117a8fd3c7496c15b5667b112d8cea750047928ccc36517`、
`e2ba38bb110e26a5221a5582ea19f777752a1946ffacbe31b1445073d1530d19`与
`963bd91ad81ca102053deb08b29a7aa8fb6849a6256a78ccbfbc6138d7a855d2`。M1保持原stack
`4d08741636647fbb29f9cf69a69a2c81d62156cef128f619d26a17b72e94c01b`与
`materialization_status=unmaterialized`，Hybrid artifact仍显式为`presence=absent` /
`content_hash=none`。

M0 profile现在将seed seal为`6369959770063611369`，derivation contract为
`content-addressed-m0-closure-sha256-low63-v1`。该值只消费candidate、initial M0/M1、prepared
receipt、Project、Registry与prompt hashes，不观察generation output或human verdict；profile load会重算并
拒绝missing/tampered seed，request guard与caller会拒绝任何不同seed。offline reseal后actual exact replay保持
Manifest revision `4`，project tree metadata hash
`b71ef90b420da8e5ae63c7a51558fdaf3a9a4019d7ab1524aef7a737abc04707`与bytes hash
`d3a7a632243c569448ba8f534e0bd8756729adbf645773cf5bde9a482227bde3`不变，Provider effect count仍为零。

一次明确授权的loopback read-only `GET /object_info`观测到1177个已注册node，并将M0
workflow所需12个exact node-input schema seals写入M0-owned profile。对runtime file chooser的当前文件
inventory先归一化，避免把可变的local inventory误当作node contract。该preflight只发生一次GET；
没有POST、prompt queue、Provider submit或媒体生成。

`ProductionStateCommitter.materialize_p0_qualification()`现在以exact-current stack hash作为CAS
reseal边界，在任何artifact/Manifest write之前重哈希bundle内全部当前materialized source
artifacts，然后重新seal/reopen依赖M0 identity的qualification inputs、transition policies、
validation set与receipt。actual exact replay保持revision `5`，63个project files的size/mtime/SHA-256
全部不变。

`M0ValidationPreSubmitGuard`现在在任何preview、durable intent、permit或Provider POST之前重新打开 exact
P0 closure与execution sources，并验证：

- request绑定重新打开的materialized `execution_stack_hash`；
- candidate/provider/model/capability、raw profile document、materialized compiler hash均为exact identity；
- execution为local/unmetered `image_to_video` motion boundary；
- image/media grammar严格为`first_frame=1`、`last_frame=1`、`reference=1`、
  `reference_video=1`，且motion-tail evidence存在；
- prompt hash、non-negative sealed seed、`1344x768`、`24 fps`、MP4/native-audio与model-native
  `frame_count=124`均匹配。

`VideoFlexibleOutputRequirement.exact_duration_milliseconds()`现在由output contract拥有 exact timing
projection。C4 request可将`124 frames @ 24 fps`绑定为rounded `5167 ms` endpoint evidence；
`provider_selected` timing或不匹配的endpoint milliseconds继续fail closed。现有integer exact-seconds C4
contract与legacy hashes保持兼容。

`M0QualificationCaller`现在只通过injected read-only owners消费current materialized M0 closure、
accepted upstream evidence与immutable input bytes。它在任何upload/queue effect前重验live 12-schema
profile、完整`M0ValidationPreflightSnapshot`、exact four-anchor cardinality/lineage、same-source terminal与
motion-tail、P6 acceptance/extraction/materialization evidence、sealed deployment与compiler seed range；
同一snapshot还会在generic service guard与committer intent-lock guard内保持exact。transport只接收已验证的
immutable bytes，并且仍只能消费一个committer-issued permit、执行一次submit、不得retry或fallback。
该caller没有concrete live registration或active capability，也不是新的evidence/writer owner。

## Session Work And Decisions

- Commit `7291959`：强化M0 request-level pre-submit identity与zero-effect denial。
- Commit `513eeed`：允许C4 exact frame-count output绑定endpoint milliseconds。
- Commit `e3d6834`：将live node schemas物化为profile seals，并为M0实现exact-current
  execution-stack reseal、cross-candidate tamper denial与dependent evidence closure。
- Commit `76c6d95`：实现candidate-neutral qualification-only caller、zero-effect denial contracts与
  exact Harness policy routing。
- 本checkpoint：为M0 profile建立content-addressed exact seed owner，并以同一materialization owner
  reseal current stack与全部dependent P0 evidence；本checkpoint的exact staged Harness与task commit
  由本轮final delivery报告。
- Commit `2d232b9`：为P0增加独立local FL2VA quality source stack的persist、materialize、reopen、
  recovery与source/M0 joint reseal，并把v6 bundle推进到上述exact runtime hashes。
- Commit `cb45198`：要求accepted upstream canonical generation request显式绑定sealed source
  `execution_stack_hash`；同时让profile/workflow/binding的语义校验与materialization消费同一次no-follow
  reopen bytes，关闭internally resealed semantic drift与path re-read TOCTOU。
- 未新增winner-specific Production child、export、family registration、active capability、fallback或第二writer。
- 未修改frozen prompt、rubric、workflow topology、spec或plan；M0-owned profile仅增加上述12个
  exact node-input schema seals，并在本checkpoint增加`seed_derivation`与`sealed_seed`。

implementation前使用一个MiniMax external read-only explorer：Role=`explorer`，Scope=实际M0 Validation V1
caller与Hybrid workflow reuse boundary，model=`MiniMax-M3`，reasoning=`high`，transport=Claude-compatible，
runner status=`success` / agent status=`DONE_WITH_CONCERNS`。它正确确认现有T2VA与T8-native Turbo adapters
不能执行frozen M0 Hybrid Stock20 workflow；其“新增Production child”建议因Join Gate J1前禁令被拒绝，
后续保持qualification-only方向。sanitized capture：
`/home/reggie/.codex/session-diagnostics/minimax/01a02b2a-befa-7a43-8426-801a9bce5697-7dcb1f9ab61750e0.md`。

execution-stack I1实现前另使用一个MiniMax external read-only explorer：Role=`explorer`，
Scope=M0 profile/compiler/workflow materialization、dependent evidence与single-writer reseal seam，
model=`MiniMax-M3`，reasoning=`high`，transport=Claude-compatible，runner status=`success` /
agent status=`DONE_WITH_CONCERNS`。它没有nested delegation，也没有修改workspace。sanitized capture：
`/home/reggie/.codex/session-diagnostics/minimax/01a02b2a-befa-7a43-8426-801a9bce5697-09294cf38e430041.md`。

qualification-only caller实现使用MiniMax external writer，Role=`writer`，Scope严格限制为
`src/ai_video/production/shot_continuity_m0_caller.py`与
`tests/test_shot_continuity_m0_caller.py`，model=`MiniMax-M3`，reasoning=`high`，
transport=`Claude-compatible safe-edit`。首次dispatch与一次bounded fresh retry均因生成的verification
command不匹配exact `--allow-command`而以runner status=`error`、agent status=`BLOCKED`、
reason=`tool_error_loop`结束；parent没有继续扩大command grants或第三次retry，而是保留两文件ownership并
完成bounded implementation。sanitized automatic capture：
`/home/reggie/.codex/session-diagnostics/minimax/01a0312f-4ddf-7c23-b3ec-1246f8c90e3c-d7b578c1cdbd9a62.md`。

本checkpoint另使用一个MiniMax external read-only explorer，Role=`explorer`，Scope仅为upstream accepted
video、terminal/motion-tail与canonical source-stack bootstrap seam，model=`MiniMax-M3`，reasoning=`high`，
transport=Claude-compatible。首次dispatch因`DONE_WITH_CONCERNS`携带未关闭questions而被runner判为
`PROTOCOL_ERROR`；一次bounded fresh retry补充现有`C4MotionTailEvidence` context后，runner status=`success` /
agent status=`DONE_WITH_CONCERNS`。其“current M0仍unmaterialized”结论与runtime evidence冲突而被parent拒绝；
其余mapping作为只读线索使用。两次均未修改workspace或触发live effect。

该mapping的后续automatic sanitized capture为
`/home/reggie/.codex/session-diagnostics/minimax/01a0312f-4ddf-7c23-b3ec-1246f8c90e3c-035a49bdbe991613.md`；
原始runner status=`success`，agent status=`DONE_WITH_CONCERNS`。本轮未因该capture重复大范围exploration。

caller checkpoint保持candidate-neutral且qualification-only：它消费
`M0ValidationPreSubmitGuard`与existing `VideoGenerationService` / committer-owned local intent seam，使用
injected transport、asset resolver与accepted-upstream reopener重开sealed source video及exact four anchors，
重验live node schemas、full P0 snapshot、same-video terminal/motion-tail lineage、P6/extraction/materialization
evidence与non-negative compiler-bounded sealed seed，并只允许one permit、one submit、no retry、no fallback。
它已由commit `76c6d95`进入local `main`；未创建winner-specific child、family registration、active
capability、第二writer或新的durable lifecycle owner。

## Verification And Evidence

M0 live-schema materialization/reseal exact staged Harness：

- receipt：`.agent/harness/runs/shot-continuity-m0-object-info-reseal-20260824-v3/receipt.json`；
- receipt SHA-256：`a4255488be99a28c7e3b7c590280e6296e1790640f8ea3d7c00687b92a60f47a`；
- focused tests `85 passed`；Harness记录workflow `9 passed`、Production State `950 passed`、
  Shot Continuity P0 `97 passed`；
- receipt integrity、artifact、freshness、policy、exact scope、snapshot、cleanup与closure全部为true；
- Architecture Gate PASS，仅有已存在oversized committer owner的growth warning，没有error或第二writer。

该checkpoint当时的actual rainy-station reseal与63-file exact replay已被下述seed-seal checkpoint的
revision `7` / 88-file closure supersede；两个checkpoint的Provider effect count均为`0`，没有video output。

M0 request guard exact staged Harness：

- receipt：`.agent/harness/runs/shot-continuity-m0-request-seal-20260824-v2/receipt.json`；
- receipt SHA-256：`d0a0931b82b1d4723d540276f466b8a84079c2fa0ac1511164487896e0b12aa9`；
- `89 passed`，Documentation Contract与Architecture Gate PASS；
- receipt integrity、artifact、freshness、policy、snapshot、cleanup与closure全部为true。

C4 frame timing exact staged Harness：

- receipt：`.agent/harness/runs/shot-continuity-c4-frame-count-20260824-v2/receipt.json`；
- receipt SHA-256：`981d71d2d35b88faa38efe37504f011135073a978704e3df9d9c65ac747b5da8`；
- production video provider suite `1094 passed`；
- provider-neutral video requirement suite `292 passed`；
- Documentation Contract与Architecture Gate PASS，receipt verification全部为true。

native `reviewer_xhigh`使用`gpt-5.6-sol` / `xhigh`。第一次request-guard review因未验证exact
`frame_count=124`而`reject`；修复并增加wrong mode、125 frames、missing frame count与pre-effect denial后，
scoped re-review为`accept`。C4 frame-timing review为`accept`，无blocking issue。

execution-stack reseal同样由同一tier独立review。reviewer依次找到“tampered current target source可被
reseal掩盖”与“tampered non-target materialized source在post-write才被发现”两个blocking issue。两个
RED regression分别证明原路径错误，修复后为它们增加typed denial、Manifest unchanged与whole-tree
zero-write证据；最终scoped re-review为`accept`，无remaining concern。

qualification-only caller使用native `reviewer_xhigh` `gpt-5.6-sol` / `xhigh`。首次review找到四个
blocking issue：未重开P6/extraction/materialization evidence、未跨intent-lock绑定完整snapshot、compiler
seed上界在upload后才失败、以及validation-to-upload path TOCTOU。修复后reviewer又发现profile中的
pre-materialization receipt与current resealed receipt被错误强制相等；真实hash分别为
`da932addfaf01310b69a8287093ad1fac734487d7916620c209d0885132b8a2e`与
`0259f88407889d3653c78ce073456e81f3b8f6f519d29acf8e984615f5502515`。最终实现改为只信任canonical
current pointer reopen并保持full snapshot exact，success regression明确证明两者不等仍可通过。
v4 scoped re-review最终verdict为`accept`，无blocking或non-blocking concern。

qualification-only caller final verification：

- caller focused tests：`28 passed`；
- exact staged Harness receipt：
  `.agent/harness/runs/shot-continuity-m0-qualification-caller-20260824-v4/receipt.json`，SHA-256
  `ed7ea82600f58e9108270bc833a73f00b2a27c118bf3d857f61c4e032ad569a6`；
- Harness control tests `154 passed`；Shot Continuity P0、caller与adjacent
  `VideoGenerationService` / local lifecycle组合`160 passed`；
- Documentation Contract与Architecture Gate均为PASS；receipt integrity、policy、exact scope、artifact
  hashes、freshness、snapshot、workspace stability、cleanup与closure全部为true；
- RED coverage包含missing source/seed、negative/boolean/`2^63` seed、schema/deployment、stack、完整
  dependent snapshot、four-anchor cardinality/order/lineage、P6/extraction/materialization、source/input bytes、
  permit replay、immutable validation-to-upload bytes与unknown-outcome no-retry/no-fallback。

用户明确授权了最小`.agent/harness/policy.yaml`映射；caller source与test现在进入
`shot_continuity_p0_tests`，该check同时覆盖`tests/test_video_generation.py`与
`tests/test_production_local_video_state.py`。早期v1 policy-audit failure与v3 receipt均已被上述v4 exact
snapshot supersede。commit与receipt仍仅存在于local repository，没有push、release或publish。

M0 content-addressed seed checkpoint：

- profile load会从pre-generation closure重算`sealed_seed`；compiler、request guard与caller只接受exact
  `186510892520232452`，different valid non-negative seed也在任何effect前拒绝；
- 首次native `reviewer_xhigh`发现materialized reseal可替换`initial_execution_stack_hash`或
  `prepared_receipt_hash`并重算seed，verdict=`reject`；两项RED均真实复现原缺陷；
- 修复后materialization owner先从current stack的content-addressed immutable profile source重开这两个
  roots，再允许reseal。两项exploit现均在writer/effect前拒绝，且whole project tree保持exact；同tier
  scoped re-review verdict=`accept`，无blocking或non-blocking concern；
- focused seed/materialization/caller tests `75 passed`；policy-routed workflow tests `9 passed`，Shot
  Continuity P0与adjacent lifecycle tests `165 passed`；`git diff --check`通过；
- actual rainy-station offline exact replay保持Manifest revision `7`、M0 stack/profile/compiler/workflow与
  dependent receipt hashes不变，并明确返回`provider_effects=0`、`video_generated=false`；
- 本checkpoint的exact staged Harness receipt与local task commit由本轮final delivery报告；未push、release
  或publish。

Independent source execution-stack checkpoint：

- focused loader/workflow/caller tests `78 passed`；P0、recovery、workflow、Comfy source、caller与validation
  宽回归`419 passed`；`git diff --check`通过；
- exact commit-range Harness覆盖`00c5d7194afb893d6938b1e4fcdeca9d76fcd2d0..cb45198f780c214c0146a7e3a3e61981b8b22831`，
  receipt为`.agent/harness/runs/shot-continuity-independent-source-stack-20260824-v4/receipt.json`，
  file SHA-256为`3e7bd9dd61f8e349fd0cb6da6a705dccb64f28228514d8faab73a66021d188fb`；
- Harness记录control `176 passed`、workflow `9 passed`、production contracts
  `2604 passed, 3 skipped`、CLI/config `13 passed`、Shot Continuity P0 `176 passed`与
  provider-neutral requirement `292 passed`；receipt integrity、freshness、policy、snapshot、workspace
  stability、cleanup与closure self-verification全部为true；
- native `reviewer_xhigh`先后拒绝未绑定source generation stack、未验证workflow/binding语义，以及
  profile/workflow path二次读取TOCTOU。三个blocking defects各自修复并加入zero-effect、internally resealed
  semantic drift与replace-after-read regressions后，同tier最终verdict=`accept`，无blocking issue；
- 上述证据全部为offline/local technical qualification evidence；没有ComfyUI POST、input upload、prompt
  queue、Provider submit、媒体生成、P6/human verdict或creative acceptance。

## Remaining Gates

selected rainy-station v6 bundle当前仍没有accepted upstream video bytes。P0的terminal frame与motion-tail
仍是`planned_derivation`，run root内没有可用于`reference_video`的exact MP4/MOV，因此不能构造真实四锚点
M0 request。M0 seed与independent source-stack bootstrap缺口均已关闭，不再允许观看结果后选择seed，或
把source与destination stack混为一谈。

qualification-only caller与zero-effect executable contracts已经通过policy-closed Harness、native
`reviewer_xhigh`并commit，但它只证明injected/fake pre-effect seam。尚未执行live input upload、one-use
local permit、M0 submit、poll、fetch、decoded boundary review或P6/human verdict。用户已授权在全部前置
契约关闭后执行bounded local upstream prerequisite与一次M0，但当前technical source-stack、P6、motion-tail
与reopener gates仍使submit保持为零；remote/paid execution、T8 seed `320001`、六Shot baseline、自动M1、
winner/active registration与越过exact gates的P6或Final Acceptance claim仍不在授权范围内。

前序live `object_info`与sealed seed evidence缺口均已关闭，不再是M0 submit的materialization blocker。
下一真实gate是仅通过已sealed的FL2VA source stack形成A2→A3 upstream Shot 3 request、执行一次bounded
local generation、走existing generated-video lifecycle与P6/human acceptance，再从同一accepted MP4/MOV
派生terminal与motion-tail。只有这些canonical evidence和concrete read-only upstream reopener全部exact后，
才允许一次M0 edge 3→4 submit。当前真实M0 submit仍保持blocked与零effect。

## Agent Guardrails

- 不得用P0 image assets、旧H3视频或其他run的MP4冒充same accepted upstream motion-tail。
- 不得把request guard/Harness PASS当作live-ready、quality PASS或winner evidence。
- Join Gate J1关闭前不得创建包含M0/M1 winner identity的Production child、export或active snapshot。
- 下一步实现source request/execution时必须绑定上述independent materialized source stack、presealed seed与
  exact A2/A3 assets，并保持single writer、one permit、one submit、no retry、no fallback；缺少canonical
  source video/P6/derivation/anchor lineage时，M0仍须在任何effect前拒绝。
