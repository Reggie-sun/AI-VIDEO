# T8 H3 Seedance Mixed Shot Continuity Handoff Record

Date: 2026-08-22

## Purpose

本文记录 `T8 Turbo T2VA -> native H3 FL2VA -> Seedance 2.0 Mini I2V` 三镜混合 Provider continuity smoke 的最新 runtime truth、用户质量否决、根因边界与下一步 architecture contract。

本记录取代本文早期“尚未执行 live run”的状态描述。它不是新的 implementation、Provider submit、付费调用、activation、release 或 quality acceptance authorization。代码、tests、Manifest 与当前 runtime evidence 仍是最终 source of truth。

## Current Runtime Truth

已执行的最新 run 位于：

```text
runs/t8-h3-seedance-3shot-continuity-20260822-v7/
```

其最终状态是：

```text
USER_REJECTED__IDENTITY_AND_CAMERA_CONTINUITY_FAIL__FETCHED_UNACTIVATED
```

三镜 Provider 拓扑仍为：

```text
T8 Turbo T2VA Shot 1
  -> exact decoded terminal PNG
native H3 FL2VA Shot 2
  -> exact decoded terminal PNG
Seedance 2.0 Mini I2V Shot 3
```

该拓扑正确利用了当前已 sealed Provider modes：T8 只负责 text-origin Shot 1；native H3 与 Seedance 接收后续 image-conditioned Shot。它证明了技术 handoff 和一次 bounded paid lifecycle，但没有达到用户要求的人物与镜头连续性。

V7 source artifacts：

| Artifact | SHA-256 | Measured media facts |
| --- | --- | --- |
| `raw/shot-01-t8-audio.mp4` | `175f269390be6fc38729412c57164c8c66a329775a28b87d977e4b784be1dfae` | 1344x768, 24 fps, 124 decoded frames, native AAC |
| `handoff/shot-01-terminal.png` | `5744073e55420d77fdb30dc063f209d8f8cb5bd8f1c2f5f5a5eeef5e24846baa` | exact decoded terminal binding for Shot 2 |
| `raw/shot-02-h3-audio.mp4` | `a3437518810b2c67f8687b63c41c19666247a87cd994293877801c95b658b1f9` | 1344x768, 24 fps, 124 decoded frames, native AAC |
| `handoff/shot-02-terminal.png` | `b49071d0cd7009d2880aedf5ad3c972e837d6dccfc451641478e1e301b076446` | exact decoded frame 123 binding for Shot 3 |
| `raw/shot-03-seedance.mp4` | `24f4c0c307480ab1b44057b7ad7ca7782ee3eee1975404a28c28ba4e1a7f683f` | 1280x720, 24 fps, 121 decoded frames, no audio |

`evidence/continuity-review.mp4` 的 SHA-256 是 `fe9402955962caf48a210a3455c4ec089afa72c55574c916819da7c0b6f70d2d`。它只是 15.414-second review derivative：Shot 1 和 Shot 2 保留 native audio，Shot 3 插入 silence；它不是 canonical activated three-shot project、P4 final composition 或 Final Acceptance artifact。

Seedance V7 使用 `doubao-seedance-2-0-mini-260615`、I2V、720p、5 秒、`generate_audio=false`。exact paid preview 上限为 2.484 CNY，finite maximum budget 为 3.0 CNY。该 attempt 恰好执行一次 POST；没有 blind retry 或 Provider fallback。结果已 fetch，但 Manifest 仍停在 `validate`，candidate 未 activation。

## User Rejection And Review Boundary

用户在全速观看后明确否决 V7：人物仍有轻微变化，且三个镜头的 camera motion 不连贯。这个用户 verdict 是当前 subjective acceptance truth。

已有 native reviewer 曾给出 `accept with concerns`，并确认 exact bytes、单次 submit、完整 decode 与方向大体向右。该 review 仍可作为技术 evidence，但不能覆盖用户的质量否决，也不能推进 activation。`evidence/mcp-continuity-review.json` 的空 issue list 是 false negative，不得用作 acceptance evidence。

V7 dense face crops 显示 Seedance 在 frame 0 后改变 nose、lips、jaw、eye shape 与 head geometry。`evidence/camera-motion-v7-user-reject.json` 使用 upper-frame ORB feature matching 与 RANSAC partial affine 测得：

- Shot 1 terminal median background displacement：约 `-2.950 px/frame`；
- Shot 2 initial median：约 `-1.480 px/frame`；
- Shot 2 terminal median：约 `-1.742 px/frame`；
- Shot 3 initial median：约 `-1.259 px/frame`，随后快速接近静止。

两个 junction 的速度幅度存在明显下降。Junction SSIM 为 `0.857990` 与 `0.681400`；它们只证明边界像素接近程度，不能证明人物 identity、camera velocity、步态相位或叙事连续性。

## Root Cause And Architecture Decision

本轮确认失败不是单纯 prompt adherence 问题，也不能通过重复生成同一个 first-frame-only request 稳定解决。

当前 Provider-neutral 层已经有 `first_frame`、`last_frame`、`reference`、`reference_video` 等 semantic/native roles，但当前 executable projection 仍存在以下边界：

1. `ContinuityMode.EXACT_TERMINAL` 在 `VideoGenerationResolver` 中只投影 `required_roles=("first_frame",)`，不会同时携带 canonical identity reference 或未来 endpoint。
2. `VideoGenerationRequest` 的 continuity validation 要求 exact terminal 位于第一个 `image_binding`，其余 binding 最多一个且必须是 `last_frame`；因此 independent `reference` 当前会被拒绝。
3. `default_seedance_capabilities()` 对 Seedance I2V 只声明 `first_frame` 与 optional `last_frame`，并将 `max_reference_count` 设为 0；`REFERENCE_TO_VIDEO` 是分开的 capability。
4. Seedance adapter 已能把 `reference` serialization 为 Ark `reference_image`，但 serialization ability 不能替代正式 request、Router、cardinality 与 model capability contract。

因此下一层连续性不应继续依赖 prompt 重述共同事实，而应形成 multi-anchor motion continuity contract：

| Constraint | Exact binding | Purpose |
| --- | --- | --- |
| Start boundary | accepted upstream exact terminal frame | 固定切点像素、构图与站位 |
| Character identity | independent canonical identity reference | 固定脸、发型、服装与 red satchel |
| Future endpoint | approved exact `last_frame` | 固定站钟附近减速停止姿态 |
| Motion boundary | accepted upstream exact motion tail | 携带步态相位、人物速度、camera direction 与 camera velocity |

前三个 image bindings 是必要的，但不能单独证明 motion continuity。Still frame 不包含 open motion vectors、camera phase 或 audio phase；若目标是让切点运镜连贯，必须由 exact upstream motion tail、正式 `video_extend`/video-reference capability，或等价的 provider-supported motion boundary carrier 承担。

future endpoint 也不能任意绘制后直接提交。它必须通过 feasibility preflight，至少检查 camera axis、screen direction、subject scale、FOV、reachable displacement、scene geography 与 no-teleport。否则 first/last interpolation 会把冲突构图转化为异常 zoom、pan、人物变形或空间跳跃。

## Spec And Plan Routing

该修复属于新的 runtime contract slice，需要 `spec + plan`，不是 narrow bug fix：它改变 Provider-neutral generation requirement、continuity request 的合法 binding shape、Router projection、capability cardinality、paid preview/materialization evidence 与 acceptance semantics。

下一窗口应优先扩展现有 canonical owners：

- `docs/superpowers/specs/2026-08-19-ai-video-shot-continuity.md`
- `docs/superpowers/plans/2026-08-19-ai-video-shot-continuity.md`

只有这些文件存在明确 frozen/closed scope 时，才创建新的 `2026-08-22-multi-anchor-motion-continuity` spec/plan；不得建立平行 canonical owner。

建议新增明确的 continuity tier，例如 `C4_MULTI_ANCHOR_MOTION_CONTINUITY`，并把 static multi-anchor 与 motion-tail acceptance 分开。Plan 至少覆盖：

1. RED tests：mixed bindings、missing/duplicate/wrong-order/tampered inputs 与 capability rejection；
2. Provider-neutral request 与 `VideoBindingCardinalityConstraint`；
3. Router 对 terminal、identity、endpoint、motion tail 的 exact projection；
4. Provider-specific capability proof；没有正式 evidence 不得放宽 Seedance Mini seal；
5. 每个 input 的 Registry identity、revision、SHA-256、provenance、materialization receipt、cloud-egress 与 paid permit fingerprint；
6. offline payload、replay、unknown-outcome recovery、focused tests、Harness 与 native reviewer；
7. technical、static-boundary、motion-boundary 与 subjective quality 的独立 acceptance gates。

## Verification And Repository State

本记录更新时 checkout 为 `main`，HEAD `164012883ef71e9824acd5b97dde90f092b0ebc3`，相对 `origin/main` ahead 7。working tree 存在大量其他 session 的 staged/dirty changes，涉及 Harness policy、Seedance、T8、continuity review、tests 与 workflows。本次记录没有修改、stage、commit、reset、checkout、clean 或覆盖这些 changes。

当前两个 native reviewer agents 均已完成，没有 live writer。后续任何 writer 仍必须重新检查 live agents、allowed paths 与 exact target-file overlap；本记录不能证明未来 ownership 状态。

本轮用于记录的只读 verification 包括：

- 读取 V7 `SUMMARY.md`、camera-motion evidence 与 safe lifecycle summary；
- 重新计算三个 source clips、两个 terminal PNG 和 review derivative 的 SHA-256；
- 对照当前 `video.py`、`shot_router.py`、`_video_requirement_routing.py`、`seedance_capabilities.py` 与 `seedance.py` 的 executable contracts；
- 确认 `docs/record_for_agent/**` 当前 Harness policy category 是 documentation-only，未要求 full repository tests。

本次 record update 没有运行新的 generation、上传、Ark lookup、Provider submit、付费调用、媒体修改或 runtime tests。V7 的单次 paid submit 是此前 smoke 的历史 evidence，不是本次记录动作。

## Remaining Risks Or Next Work

1. 仍缺少 `doubao-seedance-2-0-mini-260615` 对完整 mixed binding combination 的精确正式 API/capability proof。官方的通用多模态宣传或 payload serializer 不能直接作为 model-mode seal evidence。
2. 若 Mini 不支持完整组合，Router 必须在 paid preview/POST 前 fail closed；不得降级为 prompt-only continuity、T2V 或其他 Provider。
3. V7 已消费其 one-use paid submit。新的 paid regeneration 需要新的 task-scoped authorization、fresh preview、finite budget、durable intent 与 one-use permit；本记录不提供该授权。
4. 下一步先完成 canonical spec/plan。由于当前 Seedance/test paths 有其他 session dirty changes，code implementation 前必须重新解决 exact target-file ownership；不得依赖或覆盖未知 edits。
5. `.agent/context/session-handoff.md` 中旧的 5-minute rough-cut 与本任务无关，不得恢复。

## Agent Guardrails

- 用户 subjective rejection 高于 reviewer 的历史 `accept with concerns`；不得将 V7 activation 或标记为 Final Acceptance。
- 不把 exact terminal-frame SSIM 当 identity 或 motion continuity proof。
- 不把 local Registry ID 伪装成 Ark `asset://` identity，不伪造 materialization receipt。
- 不改变 `ProductionStateCommitter`、Manifest、Asset Registry、Dependency Graph、`ResolvedTimeline`、HyperFrames 或 P4 audio 的 canonical ownership。
- External Skills 只提供 authoring advice；AI-VIDEO 继续拥有 artifacts、Provider lifecycle、capability truth 与 acceptance。
- 不读取、打印、保存或写入 raw credentials；稳定 reference 仍是 `ARK_API_KEY`。
- 不 blind retry、remint permit、fallback Provider，或在正式 capability evidence 之前放宽 Seedance Mini seal。
- 不覆盖、stage 或 commit其他 session 的 dirty/staged files。
