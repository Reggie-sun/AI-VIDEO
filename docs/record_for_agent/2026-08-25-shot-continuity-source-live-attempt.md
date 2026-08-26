# Shot Continuity Source Live Attempt Record

Date: 2026-08-25

> Superseded current routing (2026-08-26): 本文件继续作为v7旧endpoint失败的immutable历史证据；fresh v9
> 使用用户批准的motion-compatible A3重新执行唯一Local attempt，已消除frame 107→108 hard-cut与tail
> freeze。v9的technical continuity repair通过，但overall source acceptance仍等待canonical boundary口径与
> human/P6 verdict；详见
> `docs/record_for_agent/2026-08-26-shot-continuity-motion-endpoint-live-attempt.md`。不得再把本文件的v7 root
> 或next action当作current execution target。

## Purpose

本文记录 rainy-station A2→A3 qualification-only source 的fresh Production bundle、profile reseal、
zero-effect preflight、唯一Local submit/poll/fetch与媒体诊断。它用于关闭“是否真实执行过source attempt”
的不确定性，并保留本次失败的exact evidence；不把fetch success升级为accepted candidate、P6、activation、
M0、winner、Final Acceptance或release。

## Current Runtime Truth

Fresh root为：

`runs/shot-continuity-rainy-station-p0-20260825-v7/production`

current preparation/materialization owner重建四张canonical PNG及其真实browser metadata，随后reseal：

- Project：`b019affa15219377984643889555fe1c7c27f5479c6d0f72147de64632704f60`；
- Registry：`b292cb0b35226f6201228dbc0caa62d54823f4d03040af9fa218f9666af732e9`；
- source stack：`482da299c4e3c434ae3f92fbac88982cf989d2ff333799e3ddba3e4073b17093`；
- M0 stack/profile：`b58597090ba9c630b21ef3691905a9728da1e2bcdf9a9e89531386c31a904573` /
  `377330590b7727140baf4ac2fcef196f85a8572848736b9e1d316b78748fce72`；
- M1：`materialization_status=unmaterialized`，Hybrid artifact `presence=absent`、`content_hash=none`。

Profile reseal commit为`69dbb56d959a26cee777e5494bdb2635d707af85`。Source operator implementation commits为
`95045eb8c52ec6d662a66b70ded2dcac079face0`与
`3323a2d896a6819daa145831e58e950868541af9`；最终`VideoGenerationRequest`仍只由
`video_compiler.py`构造。

## Live Attempt Evidence

ComfyUI由repository supervisor启动在literal `http://127.0.0.1:8188`，checkout commit为
`7cee3ceb1a35503172e0dfb8dbdbdedee2aba8aa`。submit前queue running/pending均为空。

Zero-effect preflight重验ComfyUI commit、source与M0 required node schemas、exact model/component bytes、
A2/A3 PNG bytes及完整Production tree；durable state hash before/after同为
`c25505792988779c2ddd81d048540f08dfade15ee1e36764782b55cd66d03dd5`，Manifest revision保持`6`，
attempt count保持`0`。

用户授权的唯一attempt为`rainy-station-source-a2-a3-20260825-v1`：

- generation request hash：`1f0dc784bbe1b56878a77824a944de5f5360efd310b8267d21c222310b068ac1`；
- sealed seed：`3625644815483226956`；
- Provider request ID：`cff9ae91-6071-4ebe-b69c-578ac9cc757f`；
- call count：submit/poll/fetch=`1/1/1`，retry/fallback/remote/paid=`0/0/0/0`；
- terminal observation：`succeeded`，`progress_milli=1000`；
- fetch artifact SHA-256：`5ac292e7ad42dc3a1692b699a3a54378d7b9feabbd23d82cc8209adc506c8f02`；
- repository-relative MP4：
  `runs/shot-continuity-rainy-station-p0-20260825-v7/production/state/video-generation/fetch/files/5ac292e7ad42dc3a1692b699a3a54378d7b9feabbd23d82cc8209adc506c8f02.mp4`。

fetch后Manifest revision为`11`，唯一attempt保持`status=running`、video phase/next action为`validate`；
没有candidate asset ID、candidate activation或后续P6/M0 state。Queue清空后supervisor已停止，
`127.0.0.1:8188`不再监听。

## Media Verification And Quality Assessment

Technical media verification通过：

- 2,965,696 bytes，H.264 High、`1344x768`、`24 fps`、124 frames、5.167 seconds；
- AAC、32 kHz、stereo、5.167 seconds；decoded PCM SHA-256为
  `eaed9b9e3fdf1953bd70f500f533e158aab095a42816b014721418997acc9687`；
- audio mean/max volume为`-40.6/-20.6 dB`，只证明非静音，不证明可接受听感；
- `ffmpeg`完整video/audio decode通过；Project-local `video-analysis`抽取7帧并报告single scene；
- decoded frame hashes 124/124 unique；first/A2与last/A3 SSIM分别为`0.882664`与`0.845630`。

Frozen boundary/motion hard gate失败：

- frames 107→108，即4.458s→4.500s，decoded RGB consecutive-frame MAD为`42.681249`；
- 同一strip可见人物、站台与clock framing在一个frame boundary上明显跳变，违反prompt与rubric中的
  no-cut、no-teleport、stable-scale与continuing-gait要求；
- frames 120→123三对RGB MAD仅为`0.064198 / 0.043291 / 0.055885`，尾部几乎静止；
- default及threshold `0.1` scene detector仍报告single scene，说明该detector对本次单帧跳变不敏感，
  不能推翻decoded frame evidence。

用户随后明确授权对existing exact MP4进行真实媒体复核。Codex直接查看从该MP4解码的全片
12-frame contact sheet、frames 104–111逐帧条带与frames 116–123尾部条带；这不是fixture、历史媒体或
仅从metric推断。Direct visual review确认frames 107→108间人物、柱列、站台与clock framing同时瞬移到
另一套终点构图，视觉上呈现hard-cut式discontinuity；frames 116–123则几乎没有可见动作。该直接视觉
观察与MAD结果一致，因此source hard gate仍为`FAIL`。

本次真实媒体复核没有被伪装成human/P6 verdict。Exact resolved source request的
`continuity_binding=null`；current `HybridContinuityEvaluatorV1`要求exact continuity binding并对缺失binding
fail closed，而`VideoGenerationService.validate_once()`进入canonical durable candidate-preparation seam。
不得为运行evaluator而合成不存在的binding、绕过qualification contract或推进candidate state。因此当前
proof layer为direct Codex visual review + deterministic frame evidence；automatic P6仍为`NOT_EVALUATED`，
human/P6 verdict仍未记录。

因此本次结论分层为：technical execution/fetch `PASS`；source boundary/motion quality `FAIL`；automatic
P6 `NOT_EVALUATED`；human/P6 verdict未记录。由于任一frozen hard gate失败即禁止promotion，本artifact不得作为
accepted upstream source，也不得派生M0 terminal/motion-tail或触发M0/M1 submit。

## Verification And Review

Non-test operator与single compiler-owner closure已有fresh receipt：

`.agent/harness/runs/shot-continuity-source-operator-fix-3323a2d/receipt.json`

Profile reseal exact range
`faaf0ff3a5794df8e0978480e4d0c2941a15756a..69dbb56d959a26cee777e5494bdb2635d707af85`
的fresh receipt为：

`.agent/harness/runs/shot-continuity-profile-reseal-69dbb56/receipt.json`

该run中workflow tests `9 passed`、Shot Continuity P0 tests `240 passed`，docs contract、policy audit与
Architecture Gate通过；receipt integrity、freshness、exact snapshot/scope、workspace stability/cleanliness与
closure flags均为`true`。Native `reviewer_xhigh`对profile reseal给出`Verdict: accept`，focused offline suite
为`138 passed`。

## Remaining Gate

本次授权已消耗，且failure outcome已知。不得blind retry、换seed、改prompt、换endpoint/model/profile、fallback
或把successful fetch改写为quality PASS。Milestone 4 M0没有开始；conditional M1 gate也没有因source failure
而触发。若未来要重新尝试source generation，必须由新的explicit scope重新冻结attempt identity与允许改变的
唯一变量，并重新通过preflight、permit、no-retry与P6/human gates。

## Agent Guardrails

- `submit/poll/fetch succeeded`不等于candidate accepted或activated。
- SSIM、single-scene detector与unique-frame count不能覆盖visible one-frame discontinuity。
- technical audio stream存在不等于听感、P4 adoption或Final Acceptance。
- failed source不授权M0、M1、retry、fallback、threshold drift或active capability registration。
