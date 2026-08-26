# Shot Continuity M0 Quality V1 Live Attempt Record

Date: 2026-08-26

## Purpose

本文记录current v9 source-boundary P6关闭后，用户显式选择`quality-v1`并授权exact A4 feasibility与一次
local M0 submit的完整结果。它区分engineering closure、runtime-capacity failure与尚未发生的media/P6 quality
acceptance；不把Harness PASS、Provider receipt或terminal OOM解释为M0 quality verdict。

## Current Runtime Truth

Production root为：

`runs/shot-continuity-rainy-station-p0-20260826-v9/production`

M0 submit前的exact closure：

- selected policy：`quality-v1`，Stock20、Turbo off、20 steps、`dual_clock_euler`、`native_flow`；
- M0 stack：`c37f6a594e473a5d73ed6a19a4d3e9892420880a99ed71149e8e525b4c519b4d`；
- profile document：`367de2fa959634781849d152932b4fc0ef5cc984218144e00670ad04d5b0b8c1`；
- sealed seed：`5696170359736854830`；
- active Project：`f05a3f681bfedcf804e9fb59fb6fa85537aa45ec37e987b8449723f5b05de8f5`；
- active Registry：`dbd9cc9c7cbadd0a324c137f946317d543b7474ee0d32fa7eee396a90c2b6ab7`；
- P0 prepared receipt：`bd69e6f9edcae76d1acb1996215192bf8c0a459f4a7c3b88a7ca86342681497d`；
- M1 stack：`4d08741636647fbb29f9cf69a69a2c81d62156cef128f619d26a17b72e94c01b`，
  still `unmaterialized`，Hybrid component `presence=absent` / `content_hash=none`。

Accepted source MP4 SHA-256为
`5324a2b0c65fea658b0ab5267020dbb00ecc080988a50987c46c1f9d21e4bbdf`。本轮以独立derived asset
`video-shot-rainy-station-3-motion-tail-m0-quality-v1`建立full-source zero-copy motion tail；不复制或重编码
媒体。Receipt
`83d2b14a0b1f23bfdf96edcc211d685cdef9b2b71b143b29f879a81698b3b77e`绑定exact source bytes、
frames `0..123`与terminal evidence。Fixed ffmpeg analyzer v2对frames `0..61`与`62..123`分别测得61个
non-zero consecutive transitions，关闭“只看孤立帧变化”的motion prerequisite。

Exact A4 feasibility approval
`1c9da8c69fb16b705eaf8e39c7e6747a15531303d0de774aead98f9578886c37`由human actor `reggie`签发，
逐项绑定attempt、generation、output、policy、stack、profile、identity A2、endpoint A4、terminal与motion tail；
`submit_limit=1`、`retry_allowed=false`、`fallback_allowed=false`。该approval只关闭submit前feasibility，不是
generated-video P6或human quality verdict。

## Live Attempt Evidence

Implementation commit `61ced56`之后，real `open_m0_quality_operator()`与caller-owned `preflight()`在零effect
状态重验exact code/runtime commits、model bytes、live node schemas、四个anchor bytes、policy/profile/stack与
approval。ComfyUI checkout为`7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`；T8在submit期间切到sealed
`977df788fcf8b971dc3d0fc7d6baa79a0edfaf40`。

唯一attempt：

- attempt：`rainy-station-m0-quality-v1-20260826-v1`；
- generation：`rainy-station-shot-4-m0-quality-v1-20260826-v1`；
- output asset ID：`video-shot-rainy-station-4-m0-quality-v1`；
- resolved request hash：`392e098918b6dfb4aacd05db0e546735a7288e90ad5bfe4d3d5fa8ff96992163`；
- submit intent：`705ce712e5272d00dd46a640c874f73e4fb328065f333b936c6111f530f0b178`；
- submit result：`49edcb84b06575dd6d4608f127ea591e23603c7c85d41b29192f3667d1b3f384`；
- Provider request ID：`1873dc95-b44c-4218-8407-5b2610b31d07`；
- actual action count：submit/poll/fetch=`1/1/0`；retry/fallback/remote/paid=`0/0/0/0`。

提交后一个独立ComfyUI job先占用GPU；本attempt保持同一request ID在pending，未取消、重排或重复提交。前序
job结束后，本attempt进入running并开始exact quality workflow。约`48.80` seconds后，node
`SamplerCustomAdvanced`抛出`torch.OutOfMemoryError: Allocation on device`；Comfy history为
`status_str=error`、`completed=false`、`outputs={}`。这证明本次runtime capacity failure，不证明模型输出的
continuity或quality表现。

Canonical poll将observation
`3efe1d80eb02dd29b51a6fe5467ba0a1bf532c00455d52386094eed1c0372db4`持久化为`state=failed`。
Manifest `2.14` revision `31`中attempt为`status=failed`、`error_code=video_provider_failed`、
`error_message=Local video runtime reported terminal failure.`、`phase=polling`；local fetch receipt为`null`，
candidate video assets为空，operator `next_action=stop`。

Queue清空后ComfyUI supervisor已停止，`127.0.0.1:8188`不再监听；T8恢复到session前commit
`28cb160827c245b2d6a37539df30c1d7c5e7aecd`且checkout clean。没有生成目标MP4，因此不存在可执行的
ffprobe/full decode、project `video-analysis`、P6或human visual acceptance。

## Engineering Verification

M0 runtime/operator/feasibility/motion-tail implementation commit为`61ced56`。Exact commit-range Harness：

`.agent/harness/runs/m0-quality-v1-61ced56/receipt.json`

Receipt SHA-256为`db868e6032a4c0fd0f538ac68cbe989d043d7e193e8621abb8a7c44e9fa0edb5`。
`verify-receipt`确认`integrity=true`、`passed=true`、`complete_completion_proof=true`、`fresh=true`、
`snapshot_matches=true`、`scope_worktree_clean=true`与`workspace_stable_confirmed=true`。Mandatory groups为
Harness `185 passed`、Production reader `551 passed`、Shot Continuity P0 `318 passed`、Production video
provider `718 passed`与provider-neutral requirement `300 passed`；Architecture Gate `PASS`（0 errors，1 warning，
1 info）。

该engineering receipt证明code/contract snapshot可复现，不改变上述live OOM。它不能代替generated MP4、
media analysis、P6或human verdict。

## Assessment

- source-boundary prerequisite：`PASS`，沿用existing Manifest `2.14` exact evidence；
- A4 feasibility与pre-effect closure：`PASS`；
- M0 `quality-v1` submit discipline：`PASS`，exactly one submit、no retry/fallback；
- M0 runtime execution：`FAIL`，sampler GPU OOM；
- generated artifact/probe/decode/media analysis：`NOT_EVALUATED`，没有MP4；
- M0 P6/human quality verdict：`NOT_EVALUATED`；
- M0 winner/activation：未发生；
- M1：未执行，exact validated pruned pair仍`absent/none`；
- Final Acceptance、push、release：均未发生。

## Remaining Boundary

Milestone 4不再是not started，而是M0 attempted/failed。当前授权已在唯一submit中消费，且durable attempt为
terminal `stop`；不得blind retry、remint permit或把OOM解释为可以自动切换`fast-v1`。只有用户新的明确授权才可
开始新的M0 attempt、改变policy/profile/geometry/runtime capacity strategy，或准备/提交M1。

如果未来选择继续M1，必须先关闭exact validated pruned pair inventory/build gate；当前`absent/none`不允许把
M1当作automatic fallback。如果未来选择重试M0，应将GPU capacity作为独立engineering变量处理，同时保持
frozen quality policy、anchors、rubric与one-submit attribution，除非用户明确批准改变这些contract。

## Isolated Retry Preparation Blocker

用户随后授权一个新的、exactly-one-submit `quality-v1` attempt，并选择只在其他ComfyUI job/unit完整退出、
fresh process且至少`30 GiB` free VRAM时重试。新attempt/generation/output为：

- `rainy-station-m0-quality-v1-isolated-lowvram-20260826-v2`；
- `rainy-station-shot-4-m0-quality-v1-isolated-lowvram-20260826-v2`；
- `video-shot-rainy-station-4-m0-quality-v1-isolated-lowvram-v2`。

Canonical committer以zero Provider effect写入并strict reopen human decision
`b3fd661d87cd43063757eb0ac5af8b9af9236e00f59ca3fb87ee6aaa555bd4d1`与approval
`6e0cf3ea32f2f1d57f950584053e524ae655f3aff77b8608908962517381635e`；scope fingerprint为
`186bca2bb144bb04dbdf3a5dde9311350f8b2f25231e7451fd711d55965d50b0`。Manifest revision到`33`，
real `open/status`产生request hash
`904db7adfbe0d4d5236ab970ec91f32539ebd759a164137d77a850b319d315fc`，attempt仍absent、
`next_action=submit`；没有intent、permit、upload或submit。

外部ComfyUI owner完成其jobs与post-media analysis并正常停止unit，8188随后关闭；但共享常驻
`video-analysis` MCP持续占约`6.5 GiB` GPU，连同桌面进程使free VRAM稳定在约`21.0 GiB / 32.6 GiB`。
上一M0 attempt本来已经使用`--lowvram --use-sage-attention`，因此再次使用lowvram不是新变量；H3经验边界为
约`22–30 GiB`，不能把21 GiB静默解释为安全阈值。MCP未公开model-unload API，Agent也未kill共享进程。

后续`novram` contract、停止共享MCP或继续等待三种capacity路径均需要明确选择；本次选择请求未返回结果。
因此v2保持prepared/blocked、submit count=`0`，其one-submit authorization尚未消费。T8 checkout未切换，
仍保持session前`28cb160827c245b2d6a37539df30c1d7c5e7aecd`。
