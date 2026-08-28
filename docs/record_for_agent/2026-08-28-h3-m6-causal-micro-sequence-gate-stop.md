# H3 M6 Causal Micro-Sequence Gate Stop Record

Date: 2026-08-28

## V3 Current Checkpoint — 2026-08-28

本 section 是当前 M6 empirical decision checkpoint；下方 v2/v1 evidence 保留为历史。v3 在不重复
holder-only experiment 的前提下，修正了 v2 的 doorway-path wording，并使用当前 M1–M5 contracts 完成
Shot B 与 conditional Shot C 的 exact local H3 submit。Shot B 六项 required findings 全部 PASS，因此 executable
barrier 允许唯一一次 Shot C submit；Shot C 随后触发 required Gate FAIL，sequence 在 review assembly 前停止。

### V3 Authorization And Fixed Scope

- Experiment root: `/home/reggie/ai-video-experiments/h3-causal-micro-sequence-20260828-m6-v3`
- Exact preview SHA-256: `176aa45a7c2bf741b83879640a6627296d70038c2878317c06de031338c8f49c`
- Authorization sidecar SHA-256: `0c2ec6f85560ed7ec2981b8ef0634913ee4228da6de5d6f862414270e9f3ba69`
- Authorization source: 用户对该 exact preview 选择 `A`；scope 仅覆盖 local H3 Shot B 与 conditional Shot C，
  Provider submit ceiling 为 `2`。
- Provider/profile: `comfy-local-h3` / `minimax-h3-fl2va-quality`；model/capability 为
  `minimax-h3-fl2va` / `minimax-h3-fl2va-local-v1`。
- Profile content hash: `a154259fa9530e7c2df8865539eaeeef1886c0da51385a61d02c5c93fdb1ad6d`
- Workflow SHA-256: `8b6c338279d8af768fae8106034f9f26e8e9d59583e95a8ca8b16d36a930ad65`
- Binding SHA-256: `e0ae28bdaaa81ac70578b11e97f95cacab826273ec09f82bfcf430176fb05a4c`
- Exact ComfyUI execution / restore commits:
  `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa` /
  `e01fb4c56b7a88149d469b99cbbfe3223d715054`。
- Sequence contract: 3 Shots / `15.500s`；每 Shot `768x768`、`124 frames @ 24 fps`、
  `5.1667s`。Shot A exact technical PASS bytes 从 v1 复用，不发生 Provider call。
- Actual calls: local H3 submit `2`；project-local `video-analysis` `8`，即每个新 Shot 固定
  `video_probe`、`video_scene_detect`、`video_extract_frames`、`video_transcribe` 各一次；image、remote、
  paid、retry、fallback、best-of-N 与 30s assembly calls 均为 `0`。
- Attribution limit: prompt change 通过 deterministic request derivation 改变 effective seed，因此 v2/v3
  不是 strict same-seed A/B；technical verdict 不得被表述为 isolated prompt-only model attribution。

Shot A reuse：

- Path: `/home/reggie/ai-video-experiments/h3-causal-micro-sequence-20260828-m6-v1/outputs/shot-a-elder-entrance-recommend.mp4`
- SHA-256: `9ecf69e3a3e22fd6a49a5cd5b1e0bb9ea7b456abfd1944cf4ca87d6c061473f7`
- Existing technical Gate: `PASS`；本次 Provider submit: `0`。

### V3 Shot B Exact Gate

- Path: `outputs/shot-b-handoff-doorway-depth-v3.mp4`
- SHA-256: `bd47e8ee13729a1c6bdc3832cc9419907d00460cb00f91ff6f6887aa75c1971c`
- Size: `1,237,417 bytes`
- Provider request ID: `d0828ccf-d907-4951-960c-6f1561e9555b`
- Effective seed: `738567603592176006`
- Requirement / compiled / resolved hashes:
  `01fe87e00745d9dd102b240ed28a5e0aa730739713fec83d0ef1ee1a88be0026` /
  `21bb5814d31a48a0c71f96c47cf216aefe81a1b7602742e1cd2aee46a6ce0375` /
  `41a4187dd1ec54d59f6ca03028c87524025968152e75f015a64c47e399b2e475`
- Gate: `sidecars/gates/shot-b-gate.json`
- Gate SHA-256: `4f8e33349a2e34058112afd88f27000c47f955fcbea1d3b140975bb44db40651`
- Measured media: H.264 High、`768x768`、`24 fps`、`124 frames`、`5.167s`；AAC
  `32 kHz` stereo；video/audio full decode PASS；first/last decoded anchor SSIM
  `0.938035` / `0.944899`。

| Requirement | Verdict | Evidence summary |
| --- | --- | --- |
| causal state | PASS | elder sole holder -> shared touch -> girl sole holder -> empty-hand release -> visible doorway threshold crossing -> elder absent；无 duplicate bottle |
| conditioning | PASS | endpoint adherence、subject scale、doorway/window geometry 与 elder-absent terminal composition 保持 compatible |
| camera | PASS | one continuous scene；locked geometry 与 subject scale 保持固定，无 cut、pan、push-in 或 terminal reframe |
| intent/performance | PASS | elder 在 release 后沿 depth axis 进入 visible doorway、跨过 threshold 并清出 doorframe，不再从 extreme frame edge 消失 |
| dialogue/lip-sync | PASS | exact AAC full decode；Whisper small 对 exact `5.167s` 返回 zero segments 与 empty text |
| readability | PASS | handoff、release、turn、doorway traversal、threshold clear 与 empty-doorway hold 在 `1.0x` cadence 可区分 |

Shot B 的六项 required findings 均为 PASS，`technical_gate=PASS`、`next_submit_allowed=true`；这只授权
preview 中已列明的 conditional Shot C，不是 HUMAN PASS 或通用 retry authorization。

### V3 Shot C Exact Gate Stop

- Path: `outputs/shot-c-open-use-effect-v3.mp4`
- SHA-256: `cc9e19016cd3c6f85222d5f66e8c73480a9a6f96e55b22e3ec8740373dbf4d7c`
- Size: `1,294,533 bytes`
- Provider request ID: `6a915a33-cc05-481b-9be3-4cf11e3e3c18`
- Effective seed: `4089209248844712091`
- Requirement / compiled / resolved hashes:
  `09833c46b5a44a475ec30b02df69570f031841e6e8fab2e96dbc3a275f63ff0b` /
  `037e8505dfa8126c1917d7e452770a42b5d638ef8a7853010f0dcf4fa1501e47` /
  `c22193ee0c2b72ff2e6382cf8541d06a2f9e6c8a1ed16fc36616b30ed5b8fe53`
- Gate: `sidecars/gates/shot-c-gate.json`
- Gate SHA-256: `5d51620c70852e417f7ab2e115eecfe271d1634f5c9ad2bbdabdf38344dc20e5`
- Measured media: H.264 High、`768x768`、`24 fps`、`124 frames`、`5.167s`；AAC
  `32 kHz` stereo；video/audio full decode PASS；one continuous scene；first/last decoded anchor SSIM
  `0.928877` / `0.914874`。

| Requirement | Verdict | Evidence summary |
| --- | --- | --- |
| causal state | FAIL | capped start、cap removal、arm raise、single bottle 与 elder absence 均存在，但 spray trace 从约 `2.0s` 持续到 `4.8s` sampled frame 与 exact terminal frame；没有 sealed `2.4-3.1s` short spray 后的 stopped-use terminal state |
| conditioning | PASS | girl identity、wardrobe、单一 yellow-and-white bottle、subject scale、doorway/window geometry 与 elder-absent endpoints 保持稳定 |
| camera | PASS | one continuous scene；background geometry 与 girl scale 保持 locked，无 cut、pan、push-in 或 terminal reframe |
| intent/performance | FAIL | girl 没有在 short spray 后降低 bottle 并 settled；raised arm、aimed nozzle 与 spray trace 持续到 exact terminal frame，relief smile 与 ongoing-use pose 重叠 |
| dialogue/lip-sync | FAIL | exact AAC full decode，但 Whisper small 返回 `3.76-5.16s` 的非空 in-range segment `1 coats egg`；按预授权 audio rule 不得覆盖为 no-intelligible-speech PASS |
| readability | FAIL | open、raise、aim 与 relief 可读，但 use 与 effect 没有可分离的先后，terminal 仍是 visible spray pose |

Shot C 的 `technical_gate=FAIL`、`stop_rule_triggered=true`、`next_submit_allowed=false`、
`retry_authorized=false`，`human_verdict=NOT_EVALUATED`。conditioning PASS 与 endpoint SSIM 不能覆盖 causal、
performance、audio 或 readability failure。尤其是 Shot C last anchor 本身包含 aimed bottle 与 visible spray trace，
而 sealed intent 同时要求 spray 已停止、bottle lowered 与 settled relief；v3 output 对 anchor 的高 adherence 反而暴露了
terminal conditioning 与 causal close-state 的 semantic conflict。

### V3 Cleanup And Current Boundary

Shot C Gate FAIL 后未创建
`outputs/m6-causal-review-15.500s-v3.mp4`，也没有 retry、fallback 或额外 Provider/MCP call。ComfyUI queue
在停止前为空；supervisor 已停止，`8188` 无 listener；`/home/reggie/ComfyUI` 已恢复到 clean
`e01fb4c56b7a88149d469b99cbbfe3223d715054`。

因此 M6 causal micro-sequence 仍没有 uninterrupted `1.0x` causal HUMAN verdict；不得称为 HUMAN PASS 或
HUMAN FAIL。30s assembly 未获授权且未创建；M7–M9、remaining adapters、qualification 与 aggregate Gate
expansion 继续 deferred。任何 Shot C anchor/intent repair、new request/seed/variant、additional analysis call 或
Provider submit 都必须先形成新的 exact preview 并获得新的 task-scoped authorization；本次 ceiling 已终止，不能
被解释为 retry authorization。

## V2 Follow-Up — 2026-08-28

本 section 是当前 M6 checkpoint；下方 v1 evidence 保留为历史。v2 已完成 v1 指向的
Shot B terminal-anchor remediation：重新 authored anchors 在相同 subject scale、camera axis 与
composition 下通过静态 anchor Gate，并获得新的 exact task-scoped authorization。它没有复用 v1 的
Shot B request/seed，也没有重复 holder-only experiment。

### V2 Authorization And Exact Request

- Experiment root: `/home/reggie/ai-video-experiments/h3-causal-micro-sequence-20260828-m6-v2`
- Exact preview SHA-256: `28cf08cc4ce77d1c2772277e6197abe1827e2d94ac658f6300f26171c083584e`
- Authorization sidecar SHA-256: `f69287a86259c96e83251cc5bcc462afa47e2ca48086f302967872743818f697`
- Provider/profile、workflow、binding 与 ComfyUI pin 仍与 v1 相同；selected Registry revision 为
  `fc80bc06a0d528ca28453423aafcf70ef3b2176ac0a2b0e4a501f90a4ad340b7`。
- Shot B first anchor SHA-256: `b408d98a99e354e9e34ca81cbce3106ea548e378e47e95a80ff8ef5e3f930f45`
- Shot B last / Shot C first anchor SHA-256:
  `062877fc2c6c09ef10cade29f0baa8fa8f884c5675cb13125f2e627b3d672fd3`
- Shot C last anchor SHA-256: `1b4a0ad18aa50304a9c08b3561241f3d0859da0c967716e83bc7a6dd0ad82340`
- Shot B effective seed: `4171215187320495411`
- Shot B requirement hash: `b6a6fd1df235f79eeeb56778d455f9ae5e503f50d4919fbe7e97a9de8811fdcc`
- Shot B compiled request hash: `df64a7dfe860bc2dcbbfbfec91fb9ba2d6d1b8b265029087e23e0a184feef3ef`
- Shot B resolved generation hash:
  `3ded2188abd9c1880643efac065c79d6369e7c338ab5910a96fee536eb37e8fa`
- Authorization ceiling: at most two local H3 submits, B then conditional C；actual v2 H3 submits: `1`；
  retry/fallback/remote/paid calls: `0`。

Stage 1 使用两次逐次 image-edit call author B/C terminal anchors，retries 为 `0`。这些 image-level
anchor PASS 只用于 conditioning preflight，不是 video technical PASS 或 HUMAN PASS。

### V2 Exact Media And Gate

Shot B exact output：

- Path: `outputs/shot-b-handoff-elder-exit-v2.mp4`
- SHA-256: `355c0ba5e33d84c5f699abe8236407880abd8d8b05db8ededdeb35d26548e383`
- Size: `1,267,910 bytes`
- Provider request ID: `b7b98271-01c6-4125-802a-d30df98900d6`
- Measured video: H.264 High、`768x768`、`24 fps`、`124 frames`、`5.167s`
- Measured audio: AAC、`32 kHz`、stereo；video/audio full decode 均 PASS
- Gate: `sidecars/gates/shot-b-gate.json`
- Gate sidecar SHA-256: `70177925e5d8190997e14e98b1dd1b3a9c1eb1aaa3f01af16a0a55ace8bd13fd`

project-local `video-analysis` 对该 exact MP4 调用 `3` 次：`video_probe`、`video_analyze` 与
`video_extract_frames`。综合 evidence 为 one continuous scene、13 个 `0.4s` interval sampled frames、
decoded first/last anchor SSIM `0.943956` / `0.949567`。Requirement-level verdict：

| Requirement | Verdict | Evidence summary |
| --- | --- | --- |
| causal state | PASS | elder sole holder -> shared touch -> girl sole holder -> elder empty-hand release -> elder absent；无 duplicate bottle |
| conditioning | PASS | exact endpoints 高 adherence；subject scale、window/doorway layout、portrait crop 与 elder-absent terminal composition 不再发生 v1 forced push-in |
| camera | PASS | one scene；background geometry、girl scale 与 side-fill boundaries 保持固定，无 cut、pan、push-in 或 terminal reframe |
| intent/performance | FAIL | handoff/release/turn 清楚，但 elder 在 `2.8-3.6s` 从 extreme right frame edge 离开，没有按 sealed intent 走入 visible screen-right doorway |
| dialogue/lip-sync | NOT_EVALUATED | requirement 为 dialogue none；Whisper 返回一个结束于 `21.78s` 的 segment，超过 exact `5.167s` clip，无法可靠证明 intelligible speech 存在或不存在 |
| readability | PASS | sole-holder start、shared touch、release、turn、disappearance 与 terminal state 均可区分，单瓶状态清楚 |

因为 required `intent/performance=FAIL` 且 `dialogue/lip-sync=NOT_EVALUATED`，Agent-side Gate 的
`technical_gate=FAIL`、`next_submit_allowed=false`。`run-shot c` 的 executable barrier 在 Provider 层前返回
`Shot C blocked by Shot B Gate`；Shot C result/MP4 均不存在。ComfyUI queue 清空后 supervisor 已停止，
`8188` 无 listener，checkout 已恢复到执行前 clean
`e01fb4c56b7a88149d469b99cbbfe3223d715054`。

### V2 Assessment And Current Boundary

v2 证明 v1 的 anchor conditioning/camera failure 可以由 compatible terminal authoring 修复，同时也把新的
最小 failure owner 隔离到 generated spatial performance 与 audio evidence：compiler 已把 doorway exit 写入
exact prompt，但 model output 只完成 frame-edge exit；冲突的 ASR evidence 又不足以关闭 no-dialogue finding。
不得用 causal-state PASS、high endpoint SSIM 或 camera PASS 覆盖这两个 required non-PASS finding。

因此 v2 Shot C 未提交，`15.500s` causal review assembly 与 30s assembly 均未创建。micro-sequence 仍无
`1.0x` HUMAN verdict；M7-M9、remaining adapters、qualification 与 aggregate Gate expansion 继续 deferred。
任何 doorway-path repair、audio-isolated diagnosis、new request/seed/variant 或 Provider submit 都需要新的
exact preview 与 task-scoped authorization；不得把本次剩余的一次 ceiling 当作 retry authorization。

## Purpose

本文记录 Phase B / Milestone 6 的首个真实 causal micro-sequence checkpoint。目标是以当前 M1–M5
`GenerationIntent`、causal readiness、deterministic H3 compiler v2 与 local Stock20 FL2VA adapter，验证：

`visible elder entrance/presence -> recommend/show -> handoff/receive -> explicit elder exit/release -> open/use -> effect`

本记录只声明 exact local development evidence。它不是 HUMAN PASS、Production qualification、candidate
activation、P6、Final Acceptance、publication 或 30s assembly evidence。

## Authorization And Exact Preview

用户先批准原 preview，随后在 fixed legacy seed 与当前 compiler contract 冲突被指出后，再次选择推荐的 A1：
使用 `ComfyUIVideoProvider.resolve()` 从 exact request hash 派生 seed。授权范围为最多 3 次 local H3 submit，
每 Shot 落盘后必须先通过 project-local `video-analysis` Gate；不得 retry、fallback、remote call 或在 Gate
失败后继续。

- Experiment root: `/home/reggie/ai-video-experiments/h3-causal-micro-sequence-20260828-m6-v1`
- Exact preview: `sidecars/exact-preview.json`
- Provider/profile: `comfy-local-h3` / `minimax_h3_fl2va_quality_local`
- Profile content hash: `a154259fa9530e7c2df8865539eaeeef1886c0da51385a61d02c5c93fdb1ad6d`
- Workflow SHA-256: `8b6c338279d8af768fae8106034f9f26e8e9d59583e95a8ca8b16d36a930ad65`
- Binding SHA-256: `e0ae28bdaaa81ac70578b11e97f95cacab826273ec09f82bfcf430176fb05a4c`
- Exact ComfyUI commit during execution: `7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`
- Output contract per Shot: `768x768`, `124 frames @ 24 fps`, `5.1667s`, native AAC
- Selected input Registry revision: `79c64822efb1bae4e9eb460b2144e951f73a1ae2b41332e7c56b3d37332038a2`
- Registered input lineage: `true`
- Planned Shot count: `3`; actual Provider submits: `2`; retry/fallback/remote/paid calls: `0`

Exact derived seeds and request identities:

| Shot | Effective seed | Requirement hash | Compiled request hash | Submit |
| --- | ---: | --- | --- | --- |
| A — elder entrance/recommend | `8471272577284581728` | `6f4f74c1ec1ee8abe4fab5eeb06dd86fbb2b0a20ad7a8bde4190fee46e8912ff` | `185de3decae3e91da76158c835ac418d2dba0ee2fe5f0ba03d0b23848d861009` | completed once |
| B — handoff/elder exit | `1226207925675661853` | `d512f8a76697dc1d47442e45daa04a0c38096c707cb04c368ad3629472acce72` | `c2d1c1b8866c49032ec3ca79b92ffc107a7848287d4f1be15be9a3b6667b985d` | completed once |
| C — open/use/effect | `4887572727654871213` | `66d782d176599e105aaf1c04eaa6a034daef2efad10ab577aef3c2018f040b36` | `16c995ac9c28c7d268622c52bd5c9b4eb39b8edc0daaa75bc1066cc484802e2b` | not submitted |

## Exact Media Evidence

Shot A:

- Path: `outputs/shot-a-elder-entrance-recommend.mp4`
- SHA-256: `9ecf69e3a3e22fd6a49a5cd5b1e0bb9ea7b456abfd1944cf4ca87d6c061473f7`
- Size: `1,710,226 bytes`
- Measured video: H.264 High, `768x768`, `24 fps`, `124 frames`, `5.167s`
- Measured audio: AAC, `32 kHz`, stereo; estimated speaking duration `0.0s`
- Gate: `sidecars/gates/shot-a-gate.json`

Shot B:

- Path: `outputs/shot-b-handoff-elder-exit.mp4`
- SHA-256: `e0e8639ef6e20a131830d7b0e51111f03c8d75e48e8f9088a2d35d78774682df`
- Size: `1,837,611 bytes`
- Measured video: H.264 High, `768x768`, `24 fps`, `124 frames`, `5.167s`
- Measured audio: AAC, `32 kHz`, stereo; transcription segments `0`
- Gate: `sidecars/gates/shot-b-gate.json`

两条 MP4 都完成全流 decode。ComfyUI execution 后 queue 为空；supervisor 已停止，`8188` 无 listener，
`/home/reggie/ComfyUI` 已恢复到执行前 commit
`e01fb4c56b7a88149d469b99cbbfe3223d715054` 且 working tree clean。

## Requirement-Level Gate Results

Shot A 的 project-local `video-analysis` 与 exact decoded endpoint evidence：

| Requirement | Verdict | Evidence summary |
| --- | --- | --- |
| causal state | PASS | girl-alone/no-product 起点；elder 从 screen-right doorway 进入，sole holder 展示并推荐；终点 girl empty-handed |
| conditioning | PASS | first/last decoded SSIM 分别 `0.933366` / `0.903384`，exact endpoint state 可读 |
| camera | PASS | one continuous scene；window-left / doorway-right 与 same-side axis 保持可读 |
| intent/performance | PASS | entrance、raise/show、open-palm recommendation 与 girl positive acknowledgement 可读 |
| dialogue/lip-sync | PASS | requirement 为 dialogue none；speaking duration `0.0s` |
| readability | PASS | entrance、attention、show/recommend 与 terminal state 分拍清晰，只有一个产品 |

Shot B 的 Gate：

| Requirement | Verdict | Evidence summary |
| --- | --- | --- |
| causal state | PASS | elder sole holder -> shared touch -> girl sole holder -> elder empty-hand release -> doorway exit -> elder absent |
| conditioning | FAIL | endpoint adherence 虽高（SSIM `0.902678` / `0.945307`），但双人 medium-wide 到更紧单人 framing 反证 sealed `same_subject_scale=true` / `composition_compatible=true` |
| camera | FAIL | one scene 无 cut，但 subject scale、doorway 与 side-fill 边界持续位移，违反 locked camera 与相同 start/end framing |
| intent/performance | PASS | girl reaches/receives/watches；elder release 后才转身并离开 |
| dialogue/lip-sync | PASS | no transcription segment；speaking duration `0.0s` |
| readability | PASS | shared touch、release、turn、exit 与 elder-absent terminal state 均可区分，无 duplicate bottle |

`video-analysis` MCP 共调用 5 次，均绑定上述 exact MP4 bytes。Shot A 的通用 `low_resolution` heuristic 以
`1024x576` 为基线，但本实验 sealed contract 为 `768x768`，因此该 generic hint 不替代 requirement verdict。

## Assessment And Stop Rule

本次 evidence 支持 M1–M5 contracts 成功保留了 causal authoring intent：Shot B 首次在完整 chain 中清楚生成
`shared touch -> receive -> empty-hand release -> elder exit`，没有重复 holder-only 实验。它同时反证
pre-generation `ConditioningCompatibilityEvidence` 中对 B anchors 的 `same_subject_scale` 与
`composition_compatible` 声明；endpoint adherence 本身不能证明 camera continuity。

最小责任 owner 是 Shot B 的 conditioning/anchor authoring 与 empirical compatibility decision，而不是把
compiler correctness、exact request hashes 或 causal state PASS 升级为 camera/HUMAN PASS。当前 B first/last
anchors 在 locked camera contract 下不可接受；不得自动重用相同 request/seed retry。

因为 required `conditioning` 与 `camera` finding 为 FAIL：

- Shot C 未提交；local Provider submit count 停在 `2`。
- `15.500s` causal review assembly 未创建。
- 30s assembly 未创建，也未获授权。
- micro-sequence 没有 HUMAN playback verdict；不得称为 HUMAN FAIL 或 HUMAN PASS。
- M7–M9、remaining adapters、qualification 与 aggregate Gate expansion 继续 deferred。

## Remaining Risk And Next Work

> **V2 supersession:** 下方“先重新 author/validate Shot B last anchor”是 v1 历史 next action；v2 已完成该
> anchor remediation，并将 conditioning/camera 提升为 requirement-level technical PASS。当前 blocker 已变为
> v2 `intent/performance=FAIL` 与 `dialogue/lip-sync=NOT_EVALUATED`，以本记录顶部 V2 section 为准。

若继续 M6，应先重新 author/validate Shot B 的 last anchor（同时是 Shot C first anchor），使其在 elder absent、
girl sole holder、bottle still capped 的 causal state下，与 Shot B first anchor 保持相同 subject scale、camera
axis 与 composition。任何新 anchor、request、seed、Provider submit、variant 或 retry 都需要新的 exact preview
与 task-scoped authorization；现有授权已在 stop rule 处终止。

现有两条媒体与 sidecars 仅位于 repo-external development root，未 publish、未 activate，也未进入 Git。
