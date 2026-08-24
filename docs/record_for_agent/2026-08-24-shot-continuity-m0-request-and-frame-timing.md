# Shot Continuity M0 Request And Frame Timing Record

Date: 2026-08-24

## Purpose

本文记录 Shot Continuity Phase P1 的四个 candidate-neutral checkpoint：M0 request-level
pre-submit identity guard、C4对model-native exact frame-count timing的provider-neutral表达、
live node-schema materialization与execution-stack reseal closure，以及qualification-only caller的
完整pre-effect denial seam。

本记录不证明 M0 已提交、视频已生成、candidate winner、active capability、P6 verdict、creative PASS、
Final Acceptance、push或release。

## Current Runtime Truth

selected rainy-station bundle位于
`runs/shot-continuity-rainy-station-p0-20260823-v5/production`。Manifest revision `5`现在选择
M0 stack `dc6917b7d8e810a11e075160b5b6cffacc0028aa5781c6d6103adec5838be293`与receipt
`0259f88407889d3653c78ce073456e81f3b8f6f519d29acf8e984615f5502515`。profile/compiler/workflow
hashes分别为`022d84f550f397d51ed511579029298aca86b03db5a8c61ab306f43e825d9dbc`、
`d0c711475ce2484e2d1dae158ecfcf209bc3cbbcb1f420689da57a6dc1239885`与
`963bd91ad81ca102053deb08b29a7aa8fb6849a6256a78ccbfbc6138d7a855d2`。M1保持原stack
`4d08741636647fbb29f9cf69a69a2c81d62156cef128f619d26a17b72e94c01b`与
`materialization_status=unmaterialized`，Hybrid artifact仍显式为`presence=absent` /
`content_hash=none`。

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
- 未新增winner-specific Production child、export、family registration、active capability、fallback或第二writer。
- 未修改frozen prompt、rubric、workflow topology、spec或plan；M0-owned profile仅增加上述12个
  exact node-input schema seals。

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

actual rainy-station reseal产生上述revision/hash closure；随后exact replay证明63个files zero-write。
Provider effect count为`0`，没有video output。

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

## Remaining Gates

selected rainy-station bundle当前仍没有accepted upstream video bytes。P0的terminal frame与motion-tail只是
`planned_derivation`，run root内没有可用于`reference_video`的exact MP4/MOV，因此不能构造真实四锚点M0
request。calibration artifact也没有预先固定M0 seed；真实Validation V1开始前必须先形成一个sealed request
identity，不能在观看结果后选择或修改seed。

qualification-only caller与zero-effect executable contracts已经通过policy-closed Harness、native
`reviewer_xhigh`并commit，但它只证明injected/fake pre-effect seam。尚未执行live input upload、one-use
local permit、M0 submit、poll、fetch、decoded boundary review或P6/human verdict。当前用户边界仍禁止
Provider/ComfyUI generation、媒体生成、M0 submit、T8 seed `320001`与六Shot baseline；所有external
effect count保持零。

前序live `object_info` evidence缺口已关闭，不再是M0 submit的materialization blocker。但这只证明
profile的exact node-schema identity，也不证明live request已通过。caller implementation lane已经关闭；
不得借此提前进入Validation V1。accepted upstream MP4/MOV与sealed M0 seed仍缺失，injected upstream
reopener也没有live registration，真实submit继续保持blocked与零effect。

## Agent Guardrails

- 不得用P0 image assets、旧H3视频或其他run的MP4冒充same accepted upstream motion-tail。
- 不得把request guard/Harness PASS当作live-ready、quality PASS或winner evidence。
- Join Gate J1关闭前不得创建包含M0/M1 winner identity的Production child、export或active snapshot。
- 下一步若继续实现caller，必须保持qualification-only、single writer、exact four-anchor input、one permit、
  one submit、no retry、no fallback；缺少sealed source video/anchor lineage时仍须在任何effect前拒绝。
